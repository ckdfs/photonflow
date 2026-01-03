# Graph JSON Schema（严格版）

本文件给出一个更严格的 Graph JSON Schema，用于前后端对齐与校验。
Schema 采用 JSON Schema Draft 2020-12 语法。

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://photonflow.local/schema/graph.json",
  "title": "PhotonFlow Graph",
  "type": "object",
  "additionalProperties": false,
  "required": ["version", "sim", "nodes", "edges", "outputs"],
  "properties": {
    "version": {"type": "string", "pattern": "^0\\.[0-9]+$"},
    "sim": {"$ref": "#/$defs/sim"},
    "nodes": {
      "type": "array",
      "minItems": 1,
      "items": {"$ref": "#/$defs/node"}
    },
    "edges": {
      "type": "array",
      "items": {"$ref": "#/$defs/edge"}
    },
    "outputs": {"$ref": "#/$defs/outputs"}
  },
  "$defs": {
    "sim": {
      "type": "object",
      "additionalProperties": false,
      "required": ["backend", "device", "fs", "oversample", "seed", "window"],
      "properties": {
        "backend": {"type": "string", "enum": ["torch"]},
        "device": {"type": "string", "enum": ["cpu", "cuda"]},
        "fs": {
          "oneOf": [
            {"type": "number", "exclusiveMinimum": 0},
            {"type": "string", "enum": ["auto"]}
          ]
        },
        "fs_min": {"type": "number", "minimum": 0},
        "fs_max": {"type": "number", "minimum": 0},
        "oversample": {"type": "integer", "minimum": 1, "maximum": 32},
        "seed": {"type": "integer", "minimum": 0},
        "window": {
          "type": "string",
          "enum": ["hann", "hamming", "blackman", "rect", "kaiser"]
        },
        "chunk": {"type": "integer", "minimum": 0},
        "duration_s": {"type": "number", "exclusiveMinimum": 0},
        "n_samples": {"type": "integer", "minimum": 2},
        "min_samples": {"type": "integer", "minimum": 0},
        "max_samples": {"type": "integer", "minimum": 0}
      }
    },
    "node": {
      "type": "object",
      "additionalProperties": false,
      "required": ["id", "type"],
      "properties": {
        "id": {"type": "string", "pattern": "^[A-Za-z_][A-Za-z0-9_\\-]*$"},
        "type": {"type": "string"},
        "params": {"type": "object", "additionalProperties": true},
        "nonideal": {"type": "object", "additionalProperties": true},
        "meta": {"type": "object", "additionalProperties": true}
      }
    },
    "edge": {
      "type": "object",
      "additionalProperties": false,
      "required": ["src", "src_port", "dst", "dst_port"],
      "properties": {
        "src": {"type": "string"},
        "src_port": {"type": "string"},
        "dst": {"type": "string"},
        "dst_port": {"type": "string"},
        "meta": {"type": "object", "additionalProperties": true}
      }
    },
    "outputs": {
      "type": "object",
      "additionalProperties": false,
      "required": ["extra"],
      "properties": {
        "extra": {
          "type": "array",
          "minItems": 1,
          "items": {"$ref": "#/$defs/measure_ref"}
        }
      }
    },
    "measure_ref": {
      "type": "object",
      "additionalProperties": false,
      "required": ["node", "port"],
      "properties": {
        "node": {"type": "string"},
        "port": {"type": "string"},
        "kind": {"type": "string", "enum": ["osa", "esa", "time"]},
        "params": {"type": "object", "additionalProperties": true}
      }
    }
  }
}
```

## 说明与约束补充
- `nodes[].type` 不在 Schema 中枚举，实际可在运行时与 Block 库对齐校验。
- `params` 与 `nonideal` 的详细字段由 Block 库定义，可通过 UI 动态渲染。
- `outputs.extra` 为唯一输出入口，必须至少包含一个观测仪器节点（OSA/ESA/示波器），且 `port` 使用观测仪器的输入端口（`opt_in` / `elec_in`）。
- `window` 列表可扩展，但建议前后端保持一致。

## 运行时校验建议（不在 JSON Schema 中）
- 端口类型兼容性校验（optical/electrical/control）。
- 必需参数校验（由 Block 库定义）。
- 图可达性和拓扑合法性校验（无孤立节点或无效连线）。
- 复合器件展开后再次校验。
