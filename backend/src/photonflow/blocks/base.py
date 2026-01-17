"""Block base classes and registry."""

from __future__ import annotations

from typing import Dict, Optional

from photonflow.core.sim import SimContext
from photonflow.core.signal import Signal


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


class BlockRegistry:
    def __init__(self) -> None:
        self._blocks: Dict[str, type[BaseBlock]] = {}

    def register(self, name: str, cls: type["BaseBlock"]) -> None:
        self._blocks[name] = cls

    def get(self, name: str) -> Optional[type["BaseBlock"]]:
        return self._blocks.get(name)

    def types(self) -> list[str]:
        return sorted(self._blocks.keys())

    def specs(self) -> Dict[str, Dict[str, Dict[str, object]]]:
        return {
            name: {**cls.describe(), "composite": False}
            for name, cls in self._blocks.items()
        }


def register_block(name: str):
    def decorator(cls: type[BaseBlock]) -> type[BaseBlock]:
        registry.register(name, cls)
        cls.BLOCK_TYPE = name
        return cls

    return decorator


class BaseBlock:
    BLOCK_TYPE: str = "Base"
    PORTS: Dict[str, str] = {}
    SPEC: Dict[str, Dict[str, Dict[str, object]]] = {"params": {}, "nonideal": {}}

    def __init__(self, node_id: str, params: Optional[dict] = None, nonideal: Optional[dict] = None):
        self.id = node_id
        self.params = params or {}
        self.nonideal = nonideal or {}

    def port_type(self, port: str) -> Optional[str]:
        return self.PORTS.get(port)

    @classmethod
    def spec(cls) -> Dict[str, Dict[str, Dict[str, object]]]:
        return cls.SPEC

    @classmethod
    def describe(cls) -> Dict[str, object]:
        doc = cls.__doc__ or ""
        # Clean up docstring: strip leading/trailing whitespace
        doc = doc.strip()
        return {"ports": dict(cls.PORTS), "spec": _normalize_spec(cls.spec()), "doc": doc}

    def apply_defaults(self) -> None:
        for key, spec in self.SPEC.get("params", {}).items():
            if key not in self.params:
                self.params[key] = spec.get("default", _fallback_default(spec))
        for key, spec in self.SPEC.get("nonideal", {}).items():
            if key not in self.nonideal:
                self.nonideal[key] = spec.get("default", _fallback_default(spec))

    def validate_params(self) -> None:
        self._validate_section(self.params, "params")
        self._validate_section(self.nonideal, "nonideal")

    def _validate_section(self, values: Dict[str, object], section: str) -> None:
        spec = self.SPEC.get(section, {})
        for key in values.keys():
            if key not in spec:
                raise ValueError(f"{self.id}: unknown {section} key '{key}'")
        for key, entry in spec.items():
            if "options" in entry and key in values:
                options = entry["options"]
                if values[key] not in options:
                    raise ValueError(
                        f"{self.id}: {section}.{key}={values[key]} not in {options}"
                    )
    def estimate_fmax(self) -> Optional[float]:
        return None

    def process(self, inputs: Dict[str, Signal], ctx: SimContext) -> Dict[str, Signal]:
        raise NotImplementedError


registry = BlockRegistry()
