"""FastAPI server for the Protocol Parser AI service.

Endpoints
---------
POST /parse        — parse raw serial bytes
POST /decode       — field-by-field packet decode
POST /identify     — identify unknown protocol
POST /explain      — protocol documentation summary
POST /generate-packet — encode a packet from field values
GET  /health       — liveness probe
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# Ensure src/ is importable when running from the docker/protocol-parser dir.
import sys
from pathlib import Path

_root = Path(__file__).resolve().parents[2]
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from src.ai.protocol_parser import ProtocolParser, ProtocolParserError  # noqa: E402

app = FastAPI(title="Protocol Parser AI Service", version="1.0.0")

_parser = ProtocolParser(
    model=os.environ.get(
        "MODEL_ID", "meta-llama/Meta-Llama-3.1-8B-Instruct"
    ),
    api_key=os.environ.get("HUGGINGFACE_API_KEY", ""),
    local_endpoint=os.environ.get("LOCAL_MODEL_ENDPOINT", "") or None,
    temperature=float(os.environ.get("TEMPERATURE", "0.2")),
    max_new_tokens=int(os.environ.get("MAX_NEW_TOKENS", "1024")),
)


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------


class ParseRequest(BaseModel):
    hex_bytes: str
    protocol: str = "flipper_serial"


class DecodeRequest(BaseModel):
    hex_data: str
    protocol: str


class IdentifyRequest(BaseModel):
    hex_bytes: str


class ExplainRequest(BaseModel):
    protocol_name: str


class GeneratePacketRequest(BaseModel):
    protocol: str
    fields: Dict[str, Any]


class HealthResponse(BaseModel):
    status: str
    model: str


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", model=_parser.model)


@app.post("/parse")
def parse(req: ParseRequest) -> Dict[str, Any]:
    try:
        raw = bytes.fromhex(req.hex_bytes.replace(" ", "").replace("0x", ""))
        return _parser.parse_serial_data(raw, req.protocol)
    except ProtocolParserError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"Invalid hex input: {exc}") from exc


@app.post("/decode")
def decode(req: DecodeRequest) -> List[Dict[str, Any]]:
    try:
        return _parser.decode_packet(req.hex_data, req.protocol)
    except ProtocolParserError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.post("/identify")
def identify(req: IdentifyRequest) -> Dict[str, Any]:
    try:
        raw = bytes.fromhex(req.hex_bytes.replace(" ", "").replace("0x", ""))
        return _parser.identify_protocol(raw)
    except ProtocolParserError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"Invalid hex input: {exc}") from exc


@app.post("/explain")
def explain(req: ExplainRequest) -> Dict[str, str]:
    try:
        result = _parser.explain_protocol(req.protocol_name)
        return {"explanation": result}
    except ProtocolParserError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.post("/generate-packet")
def generate_packet(req: GeneratePacketRequest) -> Dict[str, str]:
    try:
        packet_bytes = _parser.generate_packet(req.protocol, req.fields)
        return {"hex": packet_bytes.hex()}
    except ProtocolParserError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=int(os.environ.get("PORT", "8010")),
        reload=False,
    )
