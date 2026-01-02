"""JSON schema loading and validation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

try:
    import jsonschema
except ImportError:  # pragma: no cover - optional dependency
    jsonschema = None


def load_graph_schema() -> Dict[str, Any]:
    schema_path = Path(__file__).resolve().parent.parent / "schema" / "graph_schema.json"
    with schema_path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def validate_graph_data(data: Dict[str, Any]) -> None:
    if jsonschema is None:
        raise RuntimeError("jsonschema is required for schema validation")
    schema = load_graph_schema()
    jsonschema.validate(instance=data, schema=schema)
