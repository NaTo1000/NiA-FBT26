"""
Generic Model Runner
Each instance is configured via environment variables:
  MODEL_ROLE  — e.g. "code_generation"
  MODEL_PORT  — e.g. "8001"
  HUGGINGFACE_API_KEY — optional HF API key

Exposes:
  GET  /health  — liveness check
  POST /run     — run inference
"""

import os
import logging

import requests
import uvicorn
import yaml
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

CONFIG_PATH = "config/orchestration/settings.yaml"

app = FastAPI(title="NiA Model Runner", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

MODEL_ROLE = os.getenv("MODEL_ROLE", "unknown")
MODEL_PORT = int(os.getenv("MODEL_PORT", "8001"))
HF_API_KEY = os.getenv("HUGGINGFACE_API_KEY", "")


def load_config() -> Dict[str, Any]:
    try:
        with open(CONFIG_PATH) as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        return {}


class RunRequest(BaseModel):
    task_id: Optional[str] = None
    task_type: str
    payload: Dict[str, Any]


@app.get("/health")
async def health():
    return {"status": "ok", "role": MODEL_ROLE, "port": MODEL_PORT}


@app.post("/run")
async def run(req: RunRequest):
    """
    Route to the appropriate backend (HuggingFace API or local model).
    This is a scaffold — plug in your preferred inference library.
    """
    cfg = load_config()
    runner_cfg = cfg.get("orchestration", {}).get("model_runners", {}).get(MODEL_ROLE, {})
    model_id = runner_cfg.get("model", "unknown")
    is_local = runner_cfg.get("local", False)

    if is_local:
        result = _run_local(model_id, req.payload)
    else:
        result = _run_huggingface(model_id, req.payload)

    return {
        "task_id": req.task_id,
        "role": MODEL_ROLE,
        "model": model_id,
        "result": result,
    }


def _run_huggingface(model_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """Call HuggingFace Inference API."""
    prompt = payload.get("prompt", "")
    headers = {"Content-Type": "application/json"}
    if HF_API_KEY:
        headers["Authorization"] = f"Bearer {HF_API_KEY}"

    url = f"https://api-inference.huggingface.co/models/{model_id}"
    try:
        resp = requests.post(url, json={"inputs": prompt}, headers=headers, timeout=60)
        resp.raise_for_status()
        return {"output": resp.json()}
    except Exception as exc:
        return {"error": str(exc)}


def _run_local(model_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """Run a local ONNX or transformers model. Scaffold — implement as needed."""
    return {
        "note": f"Local model '{model_id}' scaffold — implement inference here.",
        "prompt_received": payload.get("prompt", ""),
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=MODEL_PORT)
