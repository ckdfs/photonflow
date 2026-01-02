"""Composite block templates."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Tuple


@dataclass
class CompositeTemplate:
    name: str
    ports: Dict[str, str]
    spec: Dict[str, Dict[str, Dict[str, object]]]
    expand: Callable[[str, Dict[str, Any], Dict[str, Any]], Tuple[List[dict], List[dict], Dict[str, Tuple[str, str]]]]


class CompositeRegistry:
    def __init__(self) -> None:
        self._templates: Dict[str, CompositeTemplate] = {}

    def register(self, template: CompositeTemplate) -> None:
        self._templates[template.name] = template

    def get(self, name: str) -> CompositeTemplate | None:
        return self._templates.get(name)

    def types(self) -> list[str]:
        return sorted(self._templates.keys())

    def specs(self) -> Dict[str, Dict[str, object]]:
        return {
            name: {"ports": dict(t.ports), "spec": _normalize_spec(t.spec), "composite": True}
            for name, t in self._templates.items()
        }


def expand_graph_data(
    data: Dict[str, Any],
    registry: CompositeRegistry,
    annotate: bool = False,
) -> Dict[str, Any]:
    nodes = list(data.get("nodes", []))
    edges = list(data.get("edges", []))
    outputs = data.get("outputs", {})
    expansion_map: Dict[str, Any] = {}

    changed = True
    while changed:
        changed = False
        new_nodes: List[dict] = []
        for node in nodes:
            template = registry.get(node["type"])
            if template is None:
                new_nodes.append(node)
                continue
            changed = True
            params = dict(node.get("params", {}))
            nonideal = dict(node.get("nonideal", {}))
            _apply_defaults(template.spec, params, nonideal)
            _validate_spec(template, params, nonideal, node["id"])
            expanded_nodes, expanded_edges, port_map = template.expand(
                node["id"], params, nonideal
            )
            if annotate:
                _annotate_expansion(
                    expanded_nodes,
                    node_id=node["id"],
                    template=template,
                    params=params,
                    nonideal=nonideal,
                    port_map=port_map,
                    expansion_map=expansion_map,
                )
            new_nodes.extend(expanded_nodes)
            edges = _rewire_edges(edges, node["id"], port_map)
            outputs = _rewire_outputs(outputs, node["id"], port_map)
            edges.extend(expanded_edges)
        nodes = new_nodes
    result = {**data, "nodes": nodes, "edges": edges, "outputs": outputs}
    if annotate:
        result["expansion_map"] = expansion_map
    return result


def _rewire_edges(edges: List[dict], node_id: str, port_map: Dict[str, Tuple[str, str]]) -> List[dict]:
    new_edges: List[dict] = []
    for edge in edges:
        if edge["src"] == node_id:
            if edge["src_port"] not in port_map:
                raise ValueError(f"Composite {node_id} missing port {edge['src_port']}")
            new_src, new_port = port_map[edge["src_port"]]
            new_edges.append({**edge, "src": new_src, "src_port": new_port})
        elif edge["dst"] == node_id:
            if edge["dst_port"] not in port_map:
                raise ValueError(f"Composite {node_id} missing port {edge['dst_port']}")
            new_dst, new_port = port_map[edge["dst_port"]]
            new_edges.append({**edge, "dst": new_dst, "dst_port": new_port})
        else:
            new_edges.append(edge)
    return new_edges


def _rewire_outputs(outputs: Dict[str, Any], node_id: str, port_map: Dict[str, Tuple[str, str]]) -> Dict[str, Any]:
    new_outputs: Dict[str, Any] = {}
    for key, spec in outputs.items():
        if key == "extra" and isinstance(spec, list):
            new_outputs[key] = [_rewire_output_item(item, node_id, port_map) for item in spec]
        else:
            new_outputs[key] = _rewire_output_item(spec, node_id, port_map)
    return new_outputs


def _annotate_expansion(
    expanded_nodes: List[dict],
    node_id: str,
    template: CompositeTemplate,
    params: Dict[str, Any],
    nonideal: Dict[str, Any],
    port_map: Dict[str, Tuple[str, str]],
    expansion_map: Dict[str, Any],
) -> None:
    children = []
    for node in expanded_nodes:
        meta = node.setdefault("meta", {})
        meta["composite_parent"] = node_id
        meta["composite_template"] = template.name
        children.append(node["id"])
    expansion_map[node_id] = {
        "template": template.name,
        "children": children,
        "port_map": port_map,
        "params": params,
        "nonideal": nonideal,
    }


def _apply_defaults(spec: Dict[str, Dict[str, Dict[str, object]]], params: Dict[str, Any], nonideal: Dict[str, Any]) -> None:
    for key, entry in spec.get("params", {}).items():
        if key not in params:
            params[key] = entry.get("default", _fallback_default(entry))
    for key, entry in spec.get("nonideal", {}).items():
        if key not in nonideal:
            nonideal[key] = entry.get("default", _fallback_default(entry))


def _validate_spec(
    template: CompositeTemplate,
    params: Dict[str, Any],
    nonideal: Dict[str, Any],
    node_id: str,
) -> None:
    _validate_section(template.spec.get("params", {}), params, node_id, "params")
    _validate_section(template.spec.get("nonideal", {}), nonideal, node_id, "nonideal")


def _validate_section(
    spec: Dict[str, Dict[str, object]],
    values: Dict[str, Any],
    node_id: str,
    section: str,
) -> None:
    for key in values.keys():
        if key not in spec:
            raise ValueError(f"{node_id}: unknown {section} key '{key}'")
    for key, entry in spec.items():
        if "options" in entry and key in values:
            options = entry["options"]
            if values[key] not in options:
                raise ValueError(
                    f"{node_id}: {section}.{key}={values[key]} not in {options}"
                )


def _normalize_spec(spec: Dict[str, Dict[str, Dict[str, object]]]) -> Dict[str, Dict[str, Dict[str, object]]]:
    normalized: Dict[str, Dict[str, Dict[str, object]]] = {**spec}
    for section in ("params", "nonideal"):
        entries = spec.get(section, {})
        updated: Dict[str, Dict[str, object]] = {}
        for key, entry in entries.items():
            entry = dict(entry)
            if "default" not in entry:
                entry["default"] = _fallback_default(entry)
            updated[key] = entry
        normalized[section] = updated
    return normalized


def _fallback_default(entry: Dict[str, object]) -> object:
    entry_type = str(entry.get("type", "")).lower()
    if entry_type == "bool":
        return False
    if entry_type in ("int", "integer"):
        return 0
    if entry_type in ("float", "number"):
        return 0.0
    if entry_type == "enum":
        options = entry.get("options")
        if isinstance(options, list) and options:
            return options[0]
        return ""
    return ""


def _rewire_output_item(spec: Dict[str, Any], node_id: str, port_map: Dict[str, Tuple[str, str]]) -> Dict[str, Any]:
    if spec.get("node") != node_id:
        return spec
    port = spec.get("port")
    if port not in port_map:
        raise ValueError(f"Composite {node_id} missing output port {port}")
    new_node, new_port = port_map[port]
    return {**spec, "node": new_node, "port": new_port}


composites = CompositeRegistry()


def register_composite(template: CompositeTemplate) -> None:
    composites.register(template)


# Composite definitions


def _mzm_expand(node_id: str, params: Dict[str, Any], nonideal: Dict[str, Any]):
    vpi = float(params.get("Vpi", 3.5))
    phi_bias = float(params.get("phi_bias", 0.0))
    drive_mode = params.get("drive_mode", "push_pull")
    bandwidth_hz = params.get("bandwidth_hz")
    bandwidth_kind = params.get("bandwidth_kind", "rect")

    use_nonideal = bool(nonideal.get("enable", False))
    vpi_err = float(nonideal.get("vpi_error_pct", 0.0)) if use_nonideal else 0.0
    loss_db = nonideal.get("loss_db") if use_nonideal else None
    arm_ratio_db = float(nonideal.get("arm_ratio_db", 0.0)) if use_nonideal else 0.0
    phase_error = float(nonideal.get("phase_error", 0.0)) if use_nonideal else 0.0
    bias_error = float(nonideal.get("bias_error_rad", 0.0)) if use_nonideal else 0.0
    drive_noise_rms = float(nonideal.get("drive_noise_rms", 0.0)) if use_nonideal else 0.0

    def _node(suffix: str, type_name: str, p: Dict[str, Any] | None = None, n: Dict[str, Any] | None = None):
        node = {"id": f"{node_id}__{suffix}", "type": type_name}
        if p:
            node["params"] = p
        if n:
            node["nonideal"] = n
        return node

    nodes = [
        _node("cpl_in", "Coupler", {"split_ratio": 0.5}),
        _node(
            "pm1",
            "PM",
            {
                "Vpi": vpi,
                "phi_bias": phi_bias + bias_error,
                "bandwidth_hz": bandwidth_hz,
                "bandwidth_kind": bandwidth_kind,
            },
            {"enable": use_nonideal, "vpi_error_pct": vpi_err, "drive_noise_rms": drive_noise_rms},
        ),
        _node(
            "pm2",
            "PM",
            {
                "Vpi": vpi,
                "phi_bias": -phi_bias + bias_error,
                "bandwidth_hz": bandwidth_hz,
                "bandwidth_kind": bandwidth_kind,
            },
            {"enable": use_nonideal, "vpi_error_pct": vpi_err, "drive_noise_rms": drive_noise_rms},
        ),
        _node("cpl_out", "Coupler", {"split_ratio": 0.5}),
        _node("esplit", "ElecSplitter"),
        _node("egain_p", "ElecGain", {"gain": 0.5}),
        _node("egain_n", "ElecGain", {"gain": -0.5}),
    ]

    edges = [
        {"src": f"{node_id}__cpl_in", "src_port": "opt_out1", "dst": f"{node_id}__pm1", "dst_port": "opt_in"},
        {"src": f"{node_id}__cpl_in", "src_port": "opt_out2", "dst": f"{node_id}__pm2", "dst_port": "opt_in"},
        {"src": f"{node_id}__pm1", "src_port": "opt_out", "dst": f"{node_id}__cpl_out", "dst_port": "opt_in1"},
        {"src": f"{node_id}__esplit", "src_port": "elec_out1", "dst": f"{node_id}__egain_p", "dst_port": "elec_in"},
        {"src": f"{node_id}__esplit", "src_port": "elec_out2", "dst": f"{node_id}__egain_n", "dst_port": "elec_in"},
        {"src": f"{node_id}__egain_p", "src_port": "elec_out", "dst": f"{node_id}__pm1", "dst_port": "elec_in"},
        {"src": f"{node_id}__egain_n", "src_port": "elec_out", "dst": f"{node_id}__pm2", "dst_port": "elec_in"},
    ]

    if drive_mode == "single_arm":
        for node in nodes:
            if node["id"].endswith("egain_n"):
                node.setdefault("params", {})["gain"] = 0.0
            if node["id"].endswith("egain_p"):
                node.setdefault("params", {})["gain"] = 1.0

    arm2_src = f"{node_id}__pm2"
    arm2_port = "opt_out"
    if arm_ratio_db != 0.0:
        nodes.append(_node("arm2_att", "Attenuator", {"loss_db": abs(arm_ratio_db)}))
        edges.append(
            {"src": arm2_src, "src_port": arm2_port, "dst": f"{node_id}__arm2_att", "dst_port": "opt_in"}
        )
        arm2_src = f"{node_id}__arm2_att"
        arm2_port = "opt_out"
    if phase_error != 0.0:
        nodes.append(_node("arm2_ph", "PhaseShifter", {"phi": phase_error}))
        edges.append(
            {"src": arm2_src, "src_port": arm2_port, "dst": f"{node_id}__arm2_ph", "dst_port": "opt_in"}
        )
        arm2_src = f"{node_id}__arm2_ph"
        arm2_port = "opt_out"
    edges.append(
        {"src": arm2_src, "src_port": arm2_port, "dst": f"{node_id}__cpl_out", "dst_port": "opt_in2"}
    )

    out_port = f"{node_id}__cpl_out"
    if loss_db is not None and float(loss_db) != 0.0:
        nodes.append(_node("out_att", "Attenuator", {"loss_db": float(loss_db)}))
        edges.append(
            {"src": f"{node_id}__cpl_out", "src_port": "opt_out1", "dst": f"{node_id}__out_att", "dst_port": "opt_in"}
        )
        out_port = f"{node_id}__out_att"

    port_map = {
        "opt_in": (f"{node_id}__cpl_in", "opt_in1"),
        "elec_in": (f"{node_id}__esplit", "elec_in"),
        "opt_out": (out_port, "opt_out" if out_port.endswith("out_att") else "opt_out1"),
    }

    return nodes, edges, port_map


def _dpmzm_expand(node_id: str, params: Dict[str, Any], nonideal: Dict[str, Any]):
    vpi = float(params.get("Vpi", 3.5))
    drive_mode = params.get("drive_mode", "push_pull")
    phi_bias_i = float(params.get("phi_bias_i", 0.0))
    phi_bias_q = float(params.get("phi_bias_q", 0.0))
    phi_q = float(params.get("phi_q", 1.57079632679))
    bandwidth_hz = params.get("bandwidth_hz")
    bandwidth_kind = params.get("bandwidth_kind", "rect")

    use_nonideal = bool(nonideal.get("enable", False))
    iq_phase_error = float(nonideal.get("iq_phase_error", 0.0)) if use_nonideal else 0.0
    iq_imbalance_db = float(nonideal.get("iq_imbalance_db", 0.0)) if use_nonideal else 0.0
    loss_db = nonideal.get("loss_db") if use_nonideal else None

    mzm_template = composites.get("MZMComposite")
    mzm_nonideal: Dict[str, Any] = {}
    if mzm_template is not None:
        allowed = set(mzm_template.spec.get("nonideal", {}).keys())
        mzm_nonideal = {k: nonideal[k] for k in allowed if k in nonideal}

    def _node(suffix: str, type_name: str, p: Dict[str, Any] | None = None, n: Dict[str, Any] | None = None):
        node = {"id": f"{node_id}__{suffix}", "type": type_name}
        if p:
            node["params"] = p
        if n:
            node["nonideal"] = n
        return node

    nodes = [
        _node("cpl_in", "Coupler", {"split_ratio": 0.5}),
        _node(
            "mzm_i",
            "MZMComposite",
            {
                "Vpi": vpi,
                "phi_bias": phi_bias_i,
                "drive_mode": drive_mode,
                "bandwidth_hz": bandwidth_hz,
                "bandwidth_kind": bandwidth_kind,
            },
            mzm_nonideal,
        ),
        _node(
            "mzm_q",
            "MZMComposite",
            {
                "Vpi": vpi,
                "phi_bias": phi_bias_q,
                "drive_mode": drive_mode,
                "bandwidth_hz": bandwidth_hz,
                "bandwidth_kind": bandwidth_kind,
            },
            mzm_nonideal,
        ),
        _node("q_phase", "PhaseShifter", {"phi": phi_q + iq_phase_error}),
        _node("cpl_out", "Coupler", {"split_ratio": 0.5}),
    ]

    edges = [
        {"src": f"{node_id}__cpl_in", "src_port": "opt_out1", "dst": f"{node_id}__mzm_i", "dst_port": "opt_in"},
        {"src": f"{node_id}__cpl_in", "src_port": "opt_out2", "dst": f"{node_id}__mzm_q", "dst_port": "opt_in"},
        {"src": f"{node_id}__mzm_q", "src_port": "opt_out", "dst": f"{node_id}__q_phase", "dst_port": "opt_in"},
    ]

    i_src = f"{node_id}__mzm_i"
    i_port = "opt_out"
    q_src = f"{node_id}__q_phase"
    q_port = "opt_out"

    if iq_imbalance_db > 0.0:
        nodes.append(_node("iq_att_q", "Attenuator", {"loss_db": abs(iq_imbalance_db)}))
        edges.append(
            {"src": q_src, "src_port": q_port, "dst": f"{node_id}__iq_att_q", "dst_port": "opt_in"}
        )
        q_src = f"{node_id}__iq_att_q"
        q_port = "opt_out"
    elif iq_imbalance_db < 0.0:
        nodes.append(_node("iq_att_i", "Attenuator", {"loss_db": abs(iq_imbalance_db)}))
        edges.append(
            {"src": i_src, "src_port": i_port, "dst": f"{node_id}__iq_att_i", "dst_port": "opt_in"}
        )
        i_src = f"{node_id}__iq_att_i"
        i_port = "opt_out"

    edges.extend(
        [
            {"src": i_src, "src_port": i_port, "dst": f"{node_id}__cpl_out", "dst_port": "opt_in1"},
            {"src": q_src, "src_port": q_port, "dst": f"{node_id}__cpl_out", "dst_port": "opt_in2"},
        ]
    )

    out_port = f"{node_id}__cpl_out"
    if loss_db is not None and float(loss_db) != 0.0:
        nodes.append(_node("out_att", "Attenuator", {"loss_db": float(loss_db)}))
        edges.append(
            {"src": f"{node_id}__cpl_out", "src_port": "opt_out1", "dst": f"{node_id}__out_att", "dst_port": "opt_in"}
        )
        out_port = f"{node_id}__out_att"

    port_map = {
        "opt_in": (f"{node_id}__cpl_in", "opt_in1"),
        "elec_i": (f"{node_id}__mzm_i", "elec_in"),
        "elec_q": (f"{node_id}__mzm_q", "elec_in"),
        "opt_out": (out_port, "opt_out" if out_port.endswith("out_att") else "opt_out1"),
    }

    return nodes, edges, port_map


register_composite(
    CompositeTemplate(
        name="MZMComposite",
        ports={"opt_in": "optical", "elec_in": "electrical", "opt_out": "optical"},
        spec={
            "params": {
                "Vpi": {"type": "float", "default": 3.5, "unit": "V"},
                "phi_bias": {"type": "float", "default": 0.0, "unit": "rad"},
                "drive_mode": {"type": "enum", "default": "push_pull", "options": ["push_pull", "single_arm"]},
                "bandwidth_hz": {"type": "float", "default": 0.0, "unit": "Hz"},
                "bandwidth_kind": {
                    "type": "enum",
                    "default": "rect",
                    "options": ["rect", "rc"],
                },
            },
            "nonideal": {
                "enable": {"type": "bool", "default": False},
                "loss_db": {"type": "float", "default": 0.0, "unit": "dB"},
                "vpi_error_pct": {"type": "float", "default": 0.0, "unit": "%"},
                "arm_ratio_db": {"type": "float", "default": 0.0, "unit": "dB"},
                "phase_error": {"type": "float", "default": 0.0, "unit": "rad"},
                "drive_noise_rms": {"type": "float", "default": 0.0, "unit": "V"},
                "bias_error_rad": {"type": "float", "default": 0.0, "unit": "rad"},
            },
        },
        expand=_mzm_expand,
    )
)

register_composite(
    CompositeTemplate(
        name="DPMZMComposite",
        ports={
            "opt_in": "optical",
            "elec_i": "electrical",
            "elec_q": "electrical",
            "opt_out": "optical",
        },
        spec={
            "params": {
                "Vpi": {"type": "float", "default": 3.5, "unit": "V"},
                "drive_mode": {"type": "enum", "default": "push_pull", "options": ["push_pull", "single_arm"]},
                "phi_bias_i": {"type": "float", "default": 0.0, "unit": "rad"},
                "phi_bias_q": {"type": "float", "default": 0.0, "unit": "rad"},
                "phi_q": {"type": "float", "default": 1.57079632679, "unit": "rad"},
                "bandwidth_hz": {"type": "float", "default": 0.0, "unit": "Hz"},
                "bandwidth_kind": {
                    "type": "enum",
                    "default": "rect",
                    "options": ["rect", "rc"],
                },
            },
            "nonideal": {
                "enable": {"type": "bool", "default": False},
                "loss_db": {"type": "float", "default": 0.0, "unit": "dB"},
                "iq_phase_error": {"type": "float", "default": 0.0, "unit": "rad"},
                "iq_imbalance_db": {"type": "float", "default": 0.0, "unit": "dB"},
                "vpi_error_pct": {"type": "float", "default": 0.0, "unit": "%"},
                "arm_ratio_db": {"type": "float", "default": 0.0, "unit": "dB"},
                "phase_error": {"type": "float", "default": 0.0, "unit": "rad"},
                "drive_noise_rms": {"type": "float", "default": 0.0, "unit": "V"},
                "bias_error_rad": {"type": "float", "default": 0.0, "unit": "rad"},
            },
        },
        expand=_dpmzm_expand,
    )
)
