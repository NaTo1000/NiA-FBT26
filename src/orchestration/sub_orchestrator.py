"""
Sub-Orchestrator Base Class — Layer 2
Shared logic for all three domain sub-orchestrators.
Handles task delegation to model runners, Redis queue management, and metrics.
"""

import asyncio
import json
import logging
import time
import uuid
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional

import httpx
import uvicorn
import yaml
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

logger = logging.getLogger(__name__)

CONFIG_PATH = "config/orchestration/settings.yaml"


def load_config(path: str = CONFIG_PATH) -> Dict[str, Any]:
    with open(path) as f:
        return yaml.safe_load(f)


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------


class TaskRequest(BaseModel):
    task_id: Optional[str] = None
    task_type: str
    payload: Dict[str, Any]
    priority: int = 5


class TaskResponse(BaseModel):
    task_id: str
    status: str
    result: Optional[Dict[str, Any]] = None
    model_runner_port: Optional[int] = None
    error: Optional[str] = None


class RunnerHealth(BaseModel):
    port: int
    healthy: bool
    latency_ms: Optional[float] = None


# ---------------------------------------------------------------------------
# Base Sub-Orchestrator
# ---------------------------------------------------------------------------


class SubOrchestrator:
    """
    Base class for domain sub-orchestrators.

    Subclasses set:
        domain      — string key matching the routing rule
        port        — TCP port this sub-orchestrator listens on
        task_types  — list of task_type strings this domain handles
        runner_ports — list of model runner ports
    """

    domain: str = "base"
    port: int = 7100
    task_types: List[str] = []
    runner_ports: List[int] = []

    def __init__(self):
        self.config = load_config()
        self._runner_health: Dict[int, RunnerHealth] = {p: RunnerHealth(port=p, healthy=False) for p in self.runner_ports}
        self._metrics: Dict[str, Any] = {"tasks_processed": 0, "tasks_failed": 0}
        self._task_queue: asyncio.Queue = asyncio.Queue()
        self.app = self._build_app()

    # ------------------------------------------------------------------
    # FastAPI application factory
    # ------------------------------------------------------------------

    def _build_app(self) -> FastAPI:
        @asynccontextmanager
        async def lifespan(application: FastAPI):
            asyncio.create_task(self._health_loop())
            asyncio.create_task(self._process_queue())
            logger.info("Sub-orchestrator [%s] started on port %d", self.domain, self.port)
            yield

        app = FastAPI(title=f"NiA Sub-Orchestrator [{self.domain}]", version="1.0.0", lifespan=lifespan)
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_methods=["*"],
            allow_headers=["*"],
        )

        @app.get("/health")
        async def _health():
            return {"status": "ok", "domain": self.domain, "port": self.port}

        @app.get("/runners/health")
        async def _runner_health_all():
            return list(self._runner_health.values())

        @app.get("/metrics")
        async def _metrics_endpoint():
            return self._metrics

        @app.post("/task", response_model=TaskResponse)
        async def _submit_task(req: TaskRequest):
            task_id = req.task_id or str(uuid.uuid4())
            if req.task_type not in self.task_types:
                raise HTTPException(
                    status_code=400,
                    detail=f"Task type '{req.task_type}' not handled by [{self.domain}] sub-orchestrator",
                )
            result = await self._delegate(task_id, req.task_type, req.payload, req.priority)
            return result

        return app

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _runner_url_for_task(self, task_type: str) -> Optional[int]:
        """Return the port of the model runner responsible for this task_type."""
        runners = self.config["orchestration"]["model_runners"]
        runner_cfg = runners.get(task_type)
        if runner_cfg and runner_cfg["port"] in self.runner_ports:
            return runner_cfg["port"]
        # Fallback: first healthy runner
        for port, health in self._runner_health.items():
            if health.healthy:
                return port
        return self.runner_ports[0] if self.runner_ports else None

    async def _delegate(
        self,
        task_id: str,
        task_type: str,
        payload: Dict[str, Any],
        priority: int,
    ) -> TaskResponse:
        port = self._runner_url_for_task(task_type)
        if port is None:
            self._metrics["tasks_failed"] = self._metrics.get("tasks_failed", 0) + 1
            return TaskResponse(task_id=task_id, status="error", error="No available model runner")

        url = f"http://localhost:{port}/run"
        body = {"task_id": task_id, "task_type": task_type, "payload": payload}
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                resp = await client.post(url, json=body)
                resp.raise_for_status()
                data = resp.json()
                self._metrics["tasks_processed"] = self._metrics.get("tasks_processed", 0) + 1
                return TaskResponse(
                    task_id=task_id,
                    status="completed",
                    result=data,
                    model_runner_port=port,
                )
        except Exception as exc:
            self._metrics["tasks_failed"] = self._metrics.get("tasks_failed", 0) + 1
            return TaskResponse(task_id=task_id, status="error", error=str(exc))

    async def _health_loop(self):
        interval = (
            self.config.get("orchestration", {})
            .get("super_orchestrator", {})
            .get("health_interval", 30)
        )
        while True:
            tasks = [self._check_runner(p) for p in self.runner_ports]
            await asyncio.gather(*tasks, return_exceptions=True)
            await asyncio.sleep(interval)

    async def _check_runner(self, port: int):
        url = f"http://localhost:{port}/health"
        start = time.monotonic()
        healthy = False
        latency = None
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(url)
                healthy = resp.status_code == 200
                latency = (time.monotonic() - start) * 1000
        except Exception:
            pass
        self._runner_health[port] = RunnerHealth(port=port, healthy=healthy, latency_ms=latency)

    async def _process_queue(self):
        """Drain in-memory task queue (used when Redis is unavailable)."""
        while True:
            item = await self._task_queue.get()
            try:
                await self._delegate(**item)
            finally:
                self._task_queue.task_done()

    # ------------------------------------------------------------------
    # Launch
    # ------------------------------------------------------------------

    def run(self):
        uvicorn.run(self.app, host="0.0.0.0", port=self.port, reload=False)
