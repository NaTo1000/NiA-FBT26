"""AI engine for parsing and explaining device communication protocols.

Supports Flipper Zero serial, Sub-GHz (AM/FSK), NFC, and BLE via the
HuggingFace Inference API or a locally hosted model endpoint.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict, List, Optional

import requests

from .protocol_definitions import PROTOCOL_REGISTRY, ProtocolDefinition

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "meta-llama/Meta-Llama-3.1-8B-Instruct"
HUGGINGFACE_API_URL = "https://api-inference.huggingface.co/models/{model}"


class ProtocolParserError(Exception):
    """Raised when protocol parsing or AI inference fails."""


class ProtocolParser:
    """AI-powered protocol parsing and explanation engine.

    Parameters
    ----------
    model:
        HuggingFace model ID or a fully-qualified local endpoint URL.
    api_key:
        HuggingFace API token. Falls back to the ``HUGGINGFACE_API_KEY``
        environment variable when omitted.
    local_endpoint:
        Optional URL of a locally hosted inference server that exposes the
        same ``/v1/chat/completions`` API (e.g. llama.cpp, vLLM, Ollama).
    temperature:
        Sampling temperature passed to the model. Lower values produce more
        deterministic output.
    max_new_tokens:
        Maximum number of tokens generated per request.
    """

    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        api_key: Optional[str] = None,
        local_endpoint: Optional[str] = None,
        temperature: float = 0.2,
        max_new_tokens: int = 1024,
    ) -> None:
        self.model = model
        self.api_key = api_key or os.environ.get("HUGGINGFACE_API_KEY", "")
        self.local_endpoint = local_endpoint
        self.temperature = temperature
        self.max_new_tokens = max_new_tokens

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_headers(self) -> Dict[str, str]:
        headers: Dict[str, str] = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def _infer(self, prompt: str) -> str:
        """Send *prompt* to the configured model and return the response text.

        Raises
        ------
        ProtocolParserError
            On HTTP errors or unexpected response shapes.
        """
        payload: Dict[str, Any] = {
            "inputs": prompt,
            "parameters": {
                "temperature": self.temperature,
                "max_new_tokens": self.max_new_tokens,
                "return_full_text": False,
            },
        }

        if self.local_endpoint:
            url = self.local_endpoint
        else:
            url = HUGGINGFACE_API_URL.format(model=self.model)

        try:
            response = requests.post(
                url,
                headers=self._build_headers(),
                json=payload,
                timeout=60,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            raise ProtocolParserError(f"Inference request failed: {exc}") from exc

        data = response.json()

        # HuggingFace text-generation pipeline returns a list of dicts.
        if isinstance(data, list) and data:
            return data[0].get("generated_text", "").strip()

        # Local endpoints may return {"choices": [{"message": {"content": …}}]}
        if isinstance(data, dict):
            choices = data.get("choices", [])
            if choices:
                return choices[0].get("message", {}).get("content", "").strip()
            if "generated_text" in data:
                return data["generated_text"].strip()

        raise ProtocolParserError(f"Unrecognised inference response: {data!r}")

    @staticmethod
    def _protocol_context(protocol_name: str) -> str:
        """Return a concise description of *protocol_name* for use in prompts."""
        defn: Optional[ProtocolDefinition] = PROTOCOL_REGISTRY.get(
            protocol_name.lower().replace("-", "_").replace(" ", "_")
        )
        if defn is None:
            return f"Protocol: {protocol_name}"
        field_summary = ", ".join(f.name for f in defn.fields)
        return (
            f"Protocol: {defn.name}\n"
            f"Category: {defn.category}\n"
            f"Description: {defn.description}\n"
            f"Fields: {field_summary}\n"
            f"Notes: {defn.notes}"
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def parse_serial_data(
        self,
        raw_bytes: bytes,
        protocol: str = "flipper_serial",
    ) -> Dict[str, Any]:
        """Parse *raw_bytes* according to *protocol* and return a structured breakdown.

        Parameters
        ----------
        raw_bytes:
            Raw binary data to parse.
        protocol:
            Protocol name (e.g. ``"flipper_serial"``).

        Returns
        -------
        dict
            Structured packet breakdown with fields ``hex``, ``protocol``,
            ``length``, and ``ai_analysis``.
        """
        hex_data = raw_bytes.hex()
        context = self._protocol_context(protocol)
        prompt = (
            f"{context}\n\n"
            f"Parse the following raw hex bytes and produce a structured field-by-field "
            f"breakdown. Identify each field name, byte offset, raw value, and decoded meaning.\n"
            f"Hex: {hex_data}\n\n"
            "Respond in JSON with a 'fields' list."
        )
        ai_analysis = self._infer(prompt)
        return {
            "hex": hex_data,
            "protocol": protocol,
            "length": len(raw_bytes),
            "ai_analysis": ai_analysis,
        }

    def explain_protocol(self, protocol_name: str) -> str:
        """Return a human-readable documentation summary for *protocol_name*.

        Parameters
        ----------
        protocol_name:
            Name of the protocol to explain.

        Returns
        -------
        str
            Markdown-formatted protocol documentation summary.
        """
        context = self._protocol_context(protocol_name)
        prompt = (
            f"{context}\n\n"
            "Write a concise developer-focused documentation summary for this protocol. "
            "Include: purpose, physical/link layer details, packet structure, "
            "common use cases, and key implementation notes. Format as Markdown."
        )
        return self._infer(prompt)

    def decode_packet(
        self,
        hex_data: str,
        protocol: str,
    ) -> List[Dict[str, Any]]:
        """Decode *hex_data* field-by-field for *protocol*.

        Parameters
        ----------
        hex_data:
            Hexadecimal string representation of the packet (with or without
            spaces / ``0x`` prefixes).
        protocol:
            Protocol name.

        Returns
        -------
        list of dict
            Each element contains ``field``, ``offset``, ``raw``, and
            ``decoded`` keys as produced by the model.
        """
        cleaned = hex_data.replace("0x", "").replace(" ", "").lower()
        context = self._protocol_context(protocol)
        prompt = (
            f"{context}\n\n"
            "Decode the following packet byte-by-byte. For each field return a JSON "
            "object with keys: 'field', 'offset_bytes', 'raw_hex', 'decoded_value', "
            "'description'.\n"
            f"Packet hex: {cleaned}\n\n"
            "Return a JSON array of field objects."
        )
        raw_output = self._infer(prompt)

        # Attempt to extract a JSON array from the model output.
        try:
            start = raw_output.index("[")
            end = raw_output.rindex("]") + 1
            return json.loads(raw_output[start:end])
        except (ValueError, json.JSONDecodeError):
            return [{"raw_output": raw_output}]

    def identify_protocol(self, raw_data: bytes) -> Dict[str, Any]:
        """Best-guess identification of the protocol used in *raw_data*.

        Parameters
        ----------
        raw_data:
            Raw binary data whose protocol is unknown.

        Returns
        -------
        dict
            Contains ``protocol``, ``confidence``, and ``reasoning`` keys.
        """
        hex_data = raw_data.hex()
        known = ", ".join(PROTOCOL_REGISTRY.keys())
        prompt = (
            f"Known protocols: {known}\n\n"
            f"Analyse the following hex dump and identify the most likely protocol. "
            f"Consider byte patterns, preambles, length fields, and magic bytes.\n"
            f"Hex: {hex_data}\n\n"
            "Respond in JSON with keys: 'protocol', 'confidence' (0-100), 'reasoning'."
        )
        raw_output = self._infer(prompt)
        try:
            start = raw_output.index("{")
            end = raw_output.rindex("}") + 1
            return json.loads(raw_output[start:end])
        except (ValueError, json.JSONDecodeError):
            return {"protocol": "unknown", "confidence": 0, "reasoning": raw_output}

    def generate_packet(
        self,
        protocol: str,
        fields_dict: Dict[str, Any],
    ) -> bytes:
        """Generate an encoded packet for *protocol* from *fields_dict*.

        Parameters
        ----------
        protocol:
            Protocol name.
        fields_dict:
            Mapping of field names to their desired values.

        Returns
        -------
        bytes
            Encoded packet bytes.
        """
        context = self._protocol_context(protocol)
        fields_json = json.dumps(fields_dict, indent=2)
        prompt = (
            f"{context}\n\n"
            "Generate a valid packet for the protocol above using the field values below. "
            "Return ONLY the hex-encoded bytes of the complete packet with no extra text.\n"
            f"Fields:\n{fields_json}"
        )
        raw_output = self._infer(prompt)
        # Strip any non-hex characters and decode to bytes.
        cleaned = "".join(c for c in raw_output if c in "0123456789abcdefABCDEF")
        if not cleaned:
            raise ProtocolParserError(
                f"Model returned non-hex output: {raw_output!r}"
            )
        if len(cleaned) % 2 != 0:
            logger.warning(
                "generate_packet: model returned odd-length hex string (%d chars); "
                "last nibble will be discarded. Raw output: %r",
                len(cleaned),
                raw_output,
            )
            cleaned = cleaned[:-1]
        try:
            return bytes.fromhex(cleaned)
        except ValueError as exc:
            raise ProtocolParserError(
                f"Model returned non-hex output: {raw_output!r}"
            ) from exc
