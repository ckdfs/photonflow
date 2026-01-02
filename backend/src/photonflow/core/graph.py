"""Graph execution for block-based simulations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Tuple

import torch

from photonflow.core.sim import SimConfig, SimContext
from photonflow.core.signal import Signal
from photonflow.blocks.base import BaseBlock, BlockRegistry, registry as default_registry
from photonflow.core.composites import composites, expand_graph_data


@dataclass(frozen=True)
class Edge:
    src: str
    src_port: str
    dst: str
    dst_port: str


class Graph:
    def __init__(self, nodes: Iterable[BaseBlock], edges: Iterable[Edge]):
        self.nodes: Dict[str, BaseBlock] = {node.id: node for node in nodes}
        self.edges: List[Edge] = list(edges)
        self._order: Optional[List[str]] = None
        self._in_edges: Dict[str, List[Edge]] = {}
        self._out_edges: Dict[str, List[Edge]] = {}

    @classmethod
    def from_dict(
        cls,
        data: dict,
        registry: BlockRegistry | None = None,
        validate: bool = False,
    ) -> "Graph":
        if registry is None:
            registry = default_registry
        if validate:
            from photonflow.core.schema import validate_graph_data

            validate_graph_data(data)
        data = expand_graph_data(data, composites, annotate=validate)
        nodes = []
        for node_data in data.get("nodes", []):
            block_type = node_data["type"]
            block_cls = registry.get(block_type)
            if block_cls is None:
                raise ValueError(f"Unknown block type: {block_type}")
            nodes.append(
                block_cls(
                    node_id=node_data["id"],
                    params=node_data.get("params"),
                    nonideal=node_data.get("nonideal"),
                )
            )
            if validate:
                nodes[-1].apply_defaults()
                nodes[-1].validate_params()
        edges = [Edge(**edge) for edge in data.get("edges", [])]
        return cls(nodes=nodes, edges=edges)

    def compile(self) -> None:
        for edge in self.edges:
            if edge.src not in self.nodes:
                raise ValueError(f"Edge source not found: {edge.src}")
            if edge.dst not in self.nodes:
                raise ValueError(f"Edge destination not found: {edge.dst}")
            src_node = self.nodes[edge.src]
            dst_node = self.nodes[edge.dst]
            src_type = src_node.port_type(edge.src_port)
            dst_type = dst_node.port_type(edge.dst_port)
            if src_type is None:
                raise ValueError(f"Unknown source port {edge.src}:{edge.src_port}")
            if dst_type is None:
                raise ValueError(f"Unknown destination port {edge.dst}:{edge.dst_port}")
            if src_type != dst_type:
                raise ValueError(
                    f"Port type mismatch {edge.src}:{edge.src_port} -> {edge.dst}:{edge.dst_port}"
                )

        self._in_edges = {node_id: [] for node_id in self.nodes}
        self._out_edges = {node_id: [] for node_id in self.nodes}
        for edge in self.edges:
            self._in_edges[edge.dst].append(edge)
            self._out_edges[edge.src].append(edge)

        self._order = self._topological_sort()

    def _topological_sort(self) -> List[str]:
        in_degree = {node_id: 0 for node_id in self.nodes}
        for edge in self.edges:
            in_degree[edge.dst] += 1

        queue = [node_id for node_id, degree in in_degree.items() if degree == 0]
        order = []
        while queue:
            node_id = queue.pop(0)
            order.append(node_id)
            for edge in self._out_edges.get(node_id, []):
                in_degree[edge.dst] -= 1
                if in_degree[edge.dst] == 0:
                    queue.append(edge.dst)

        if len(order) != len(self.nodes):
            raise ValueError("Graph has cycles or disconnected components")
        return order

    def estimate_fs(self, oversample: int) -> float:
        fmax = 0.0
        for node in self.nodes.values():
            est = node.estimate_fmax()
            if est is not None:
                fmax = max(fmax, est)
        if fmax <= 0:
            fmax = 1e9
        return oversample * 2.0 * fmax

    def _resolve_sim_params(self, config: SimConfig) -> tuple[float, int]:
        if config.fs == "auto":
            fs = self.estimate_fs(config.oversample)
        else:
            fs = float(config.fs)
        if config.fs_min > 0.0:
            fs = max(fs, config.fs_min)
        if config.fs_max > 0.0:
            fs = min(fs, config.fs_max)
        config.fs = fs

        if config.n_samples is None:
            n_samples = max(2, int(round(fs * config.duration_s)))
        else:
            n_samples = int(config.n_samples)
        if config.min_samples > 0:
            n_samples = max(n_samples, config.min_samples)
        if config.max_samples > 0:
            n_samples = min(n_samples, config.max_samples)
        config.n_samples = n_samples
        config.duration_s = n_samples / fs
        return fs, n_samples

    def _run_once(self, ctx: SimContext) -> Dict[Tuple[str, str], Signal]:
        outputs: Dict[Tuple[str, str], Signal] = {}
        for node_id in self._order:
            node = self.nodes[node_id]
            inputs: Dict[str, Signal] = {}
            for edge in self._in_edges.get(node_id, []):
                key = (edge.src, edge.src_port)
                if key not in outputs:
                    raise ValueError(f"Missing input from {edge.src}:{edge.src_port}")
                if edge.dst_port in inputs:
                    raise ValueError(
                        f"Multiple inputs for {node_id}:{edge.dst_port}"
                    )
                inputs[edge.dst_port] = outputs[key]
            node_outputs = node.process(inputs=inputs, ctx=ctx)
            for port_name, signal in node_outputs.items():
                outputs[(node_id, port_name)] = signal
        return outputs

    def _run_chunked(self, config: SimConfig, fs: float, n_samples: int) -> List[Dict[Tuple[str, str], Signal]]:
        chunk = int(getattr(config, "chunk", 0) or 0)
        if chunk <= 0 or chunk >= n_samples:
            ctx = SimContext(config=config, fs=fs, n_samples=n_samples)
            return [self._run_once(ctx)]

        outputs_list: List[Dict[Tuple[str, str], Signal]] = []
        offset = 0
        chunk_idx = 0
        while offset < n_samples:
            chunk_len = min(chunk, n_samples - offset)
            t0 = offset / fs
            ctx = SimContext(config=config, fs=fs, n_samples=chunk_len, t0=t0, seed_offset=chunk_idx)
            outputs_list.append(self._run_once(ctx))
            offset += chunk_len
            chunk_idx += 1
        return outputs_list

    def run_chunked(self, config: SimConfig) -> List[Dict[Tuple[str, str], Signal]]:
        if self._order is None:
            self.compile()
        fs, n_samples = self._resolve_sim_params(config)
        return self._run_chunked(config, fs, n_samples)

    def run(self, config: SimConfig) -> Dict[Tuple[str, str], Signal]:
        if self._order is None:
            self.compile()

        fs, n_samples = self._resolve_sim_params(config)
        chunk = int(getattr(config, "chunk", 0) or 0)
        if chunk <= 0 or chunk >= n_samples:
            ctx = SimContext(config=config, fs=fs, n_samples=n_samples)
            return self._run_once(ctx)

        outputs_list = self._run_chunked(config, fs, n_samples)
        stitched: Dict[Tuple[str, str], Signal] = {}
        for key in outputs_list[0].keys():
            segments = [out[key] for out in outputs_list]
            first = segments[0]
            data = torch.cat([seg.data for seg in segments], dim=-1)
            stitched[key] = Signal(
                data=data,
                fs=first.fs,
                t0=0.0,
                center_freq=first.center_freq,
                pol_mode=first.pol_mode,
                meta=dict(first.meta),
            )
        return stitched
