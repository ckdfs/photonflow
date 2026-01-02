"""Lightweight async job manager."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from threading import Lock
from typing import Any, Callable, Dict, Optional
import uuid
from concurrent.futures import Future, ThreadPoolExecutor


@dataclass
class JobRecord:
    job_id: str
    status: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


class JobManager:
    def __init__(self, max_workers: int = 2) -> None:
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self._jobs: Dict[str, JobRecord] = {}
        self._lock = Lock()

    def submit(self, func: Callable[[], Dict[str, Any]]) -> JobRecord:
        job_id = uuid.uuid4().hex
        record = JobRecord(job_id=job_id, status="queued")
        with self._lock:
            self._jobs[job_id] = record

        future = self._executor.submit(func)
        record.status = "running"
        record.updated_at = datetime.utcnow()

        def _done_callback(fut: Future) -> None:
            with self._lock:
                if fut.cancelled():
                    record.status = "error"
                    record.error = "cancelled"
                else:
                    try:
                        record.result = fut.result()
                        record.status = "done"
                    except Exception as exc:  # noqa: BLE001
                        record.status = "error"
                        record.error = str(exc)
                record.updated_at = datetime.utcnow()

        future.add_done_callback(_done_callback)
        return record

    def get(self, job_id: str) -> Optional[JobRecord]:
        with self._lock:
            return self._jobs.get(job_id)
