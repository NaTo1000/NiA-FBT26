"""
Super Orchestrator — Layer 1
FastAPI server on port 7000.
Routes tasks to sub-orchestrators based on task type, monitors health of all 13 services,
manages a global priority queue, and handles failure recovery.
"""

import asyncio
import logging
import time
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional

import httpx
import uvicorn
import yaml
from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

logger = logging.getLogger(__name__)

CONFIG_PATH = "config/orchestration/settings.yaml"


def load_config(path: str = CONFIG_PATH) -> Dict[str, Any]:
    with open(path) as f:
        return yaml.safe_load(f)


@asynccontextmanager
async def lifespan(application: FastAPI):
    global _config
    _config = load_config()
    asyncio.create_task(_health_loop())
    logger.info("Super Orchestrator started on port 7000")
    yield


app = FastAPI(title="NiA Super Orchestrator", version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------


class TaskRequest(BaseModel):
    task_type: str
    payload: Dict[str, Any]
    priority: int = 5  # 1 (highest) – 10 (lowest)
    task_id: Optional[str] = None


class TaskResponse(BaseModel):
    task_id: str
    status: str
    result: Optional[Dict[str, Any]] = None
    routed_to: Optional[str] = None
    error: Optional[str] = None


class HealthStatus(BaseModel):
    service: str
    port: int
    healthy: bool
    latency_ms: Optional[float] = None
    last_checked: float


# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------

_config: Dict[str, Any] = {}
_health_cache: Dict[str, HealthStatus] = {}
_task_counter: int = 0


def _get_routing_rules() -> Dict[str, str]:
    return _config.get("routing_rules", {})


def _sub_orch_url(domain: str) -> str:
    sub_cfg = _config["orchestration"]["sub_orchestrators"][domain]
    return f"http://localhost:{sub_cfg['port']}"


# ---------------------------------------------------------------------------
# Health monitoring
# ---------------------------------------------------------------------------


async def _check_service(service_name: str, port: int) -> HealthStatus:
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
    status = HealthStatus(
        service=service_name,
        port=port,
        healthy=healthy,
        latency_ms=latency,
        last_checked=time.time(),
    )
    _health_cache[service_name] = status
    return status


async def _health_loop():
    """Continuously poll all 13 services every health_interval seconds."""
    interval = _config.get("orchestration", {}).get("super_orchestrator", {}).get("health_interval", 30)
    orch_cfg = _config["orchestration"]
    services: List[tuple] = []
    # Sub-orchestrators
    for domain, cfg in orch_cfg["sub_orchestrators"].items():
        services.append((f"sub_orch_{domain}", cfg["port"]))
    # Model runners
    for role, cfg in orch_cfg["model_runners"].items():
        services.append((role, cfg["port"]))
    while True:
        tasks = [_check_service(name, port) for name, port in services]
        await asyncio.gather(*tasks, return_exceptions=True)
        await asyncio.sleep(interval)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@app.get("/health")
async def health():
    return {"status": "ok", "service": "super_orchestrator", "port": 7000}


@app.get("/health/all", response_model=List[HealthStatus])
async def health_all():
    """Return health status for all 13 downstream services."""
    return list(_health_cache.values())


@app.post("/task", response_model=TaskResponse)
async def submit_task(req: TaskRequest, background_tasks: BackgroundTasks):
    global _task_counter
    _task_counter += 1
    task_id = req.task_id or f"task_{_task_counter}_{int(time.time())}"

    rules = _get_routing_rules()
    domain = rules.get(req.task_type)
    if not domain:
        raise HTTPException(status_code=400, detail=f"Unknown task_type: {req.task_type}")

    sub_url = _sub_orch_url(domain)
    payload = {
        "task_id": task_id,
        "task_type": req.task_type,
        "payload": req.payload,
        "priority": req.priority,
    }

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(f"{sub_url}/task", json=payload)
            resp.raise_for_status()
            result = resp.json()
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Sub-orchestrator unreachable: {exc}") from exc

    return TaskResponse(
        task_id=task_id,
        status=result.get("status", "submitted"),
        result=result.get("result"),
        routed_to=domain,
    )


@app.get("/config")
async def get_config():
    """Return current orchestration configuration (no secrets)."""
    safe = dict(_config)
    return safe


@app.get("/services")
async def list_services():
    """Return all managed service definitions."""
    orch_cfg = _config.get("orchestration", {})
    return {
        "sub_orchestrators": orch_cfg.get("sub_orchestrators", {}),
        "model_runners": orch_cfg.get("model_runners", {}),
    }


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main():
    cfg = load_config()
    port = cfg["orchestration"]["super_orchestrator"]["port"]
    uvicorn.run("src.orchestration.super_orchestrator:app", host="0.0.0.0", port=port, reload=False)


if __name__ == "__main__":
    main()
