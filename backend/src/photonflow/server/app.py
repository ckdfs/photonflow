"""FastAPI application for PhotonFlow."""

from __future__ import annotations

import asyncio
from typing import Any, Dict, Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, ConfigDict, Field

from photonflow.blocks import registry
from photonflow.core.composites import composites, expand_graph_data
from photonflow.core import Graph
from photonflow.core.schema import validate_graph_data
from photonflow.server.job_manager import JobManager
from photonflow.server.sim_runner import run_graph_job


class GraphJobRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    graph: Dict[str, Any]
    validate_schema: bool = Field(default=True, alias="validate")
    sim_override: Optional[Dict[str, Any]] = None
    max_points: int = Field(default=4096, ge=256, le=200000)


class JobResponse(BaseModel):
    job_id: str


class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    error: Optional[str] = None


class JobResultResponse(BaseModel):
    job_id: str
    status: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class GraphValidateRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    graph: Dict[str, Any]
    validate_schema: bool = Field(default=True, alias="validate")


class GraphValidateResponse(BaseModel):
    status: str
    error: Optional[str] = None


class GraphExpandRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    graph: Dict[str, Any]
    validate_schema: bool = Field(default=True, alias="validate")
    annotate: bool = True


class GraphExpandResponse(BaseModel):
    graph: Dict[str, Any]


job_manager = JobManager(max_workers=2)
app = FastAPI(title="PhotonFlow API", version="0.1")


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.get("/blocks")
def blocks() -> Dict[str, list[str]]:
    return {"types": registry.types()}


@app.get("/blocks/specs")
def block_specs() -> Dict[str, Dict[str, Any]]:
    specs = registry.specs()
    specs.update(composites.specs())
    return specs


@app.post("/graph/validate", response_model=GraphValidateResponse)
def graph_validate(payload: GraphValidateRequest) -> GraphValidateResponse:
    try:
        graph = Graph.from_dict(payload.graph, validate=payload.validate_schema)
        graph.compile()
        _validate_outputs(payload.graph)
    except Exception as exc:  # noqa: BLE001
        return GraphValidateResponse(status="error", error=str(exc))
    return GraphValidateResponse(status="ok")


@app.post("/graph/expand", response_model=GraphExpandResponse)
def graph_expand(payload: GraphExpandRequest) -> GraphExpandResponse:
    if payload.validate_schema:
        validate_graph_data(payload.graph)
    expanded = expand_graph_data(payload.graph, composites, annotate=payload.annotate)
    return GraphExpandResponse(graph=expanded)


def _validate_outputs(graph_data: Dict[str, Any]) -> None:
    outputs = graph_data.get("outputs", {})
    for key, spec in outputs.items():
        if key == "extra" and isinstance(spec, list):
            for item in spec:
                _validate_output_item(item)
        else:
            _validate_output_item(spec)


def _validate_output_item(spec: Dict[str, Any]) -> None:
    if "node" not in spec or "port" not in spec:
        raise ValueError("Output spec must include node and port")


@app.post("/jobs/submit", response_model=JobResponse)
def submit_job(payload: GraphJobRequest) -> JobResponse:
    def _runner() -> Dict[str, Any]:
        return run_graph_job(
            graph_data=payload.graph,
            validate=payload.validate_schema,
            sim_override=payload.sim_override,
            max_points=payload.max_points,
        )

    record = job_manager.submit(_runner)
    return JobResponse(job_id=record.job_id)


@app.get("/jobs/{job_id}/status", response_model=JobStatusResponse)
def job_status(job_id: str) -> JobStatusResponse:
    record = job_manager.get(job_id)
    if record is None:
        return JobStatusResponse(job_id=job_id, status="not_found")
    return JobStatusResponse(job_id=job_id, status=record.status, error=record.error)


@app.get("/jobs/{job_id}/result", response_model=JobResultResponse)
def job_result(job_id: str) -> JobResultResponse:
    record = job_manager.get(job_id)
    if record is None:
        return JobResultResponse(job_id=job_id, status="not_found")
    return JobResultResponse(job_id=job_id, status=record.status, result=record.result, error=record.error)


@app.websocket("/ws/jobs/{job_id}")
async def job_ws(websocket: WebSocket, job_id: str) -> None:
    await websocket.accept()
    try:
        while True:
            record = job_manager.get(job_id)
            if record is None:
                await websocket.send_json({"job_id": job_id, "status": "not_found"})
                break
            await websocket.send_json(
                {"job_id": job_id, "status": record.status, "error": record.error}
            )
            if record.status in ("done", "error"):
                break
            await asyncio.sleep(0.5)
    except WebSocketDisconnect:
        return
