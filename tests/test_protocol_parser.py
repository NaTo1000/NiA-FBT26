"""Unit tests for the Protocol Parser AI engine.

Tests use ``unittest.mock`` to patch HTTP calls so that no real inference
endpoint is required during CI.
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Ensure the project root is on sys.path so imports work from any directory.
_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from src.ai.protocol_definitions import (  # noqa: E402
    PROTOCOL_REGISTRY,
    BLE_GATT,
    FLIPPER_SERIAL,
    NFC_NDEF,
    NFC_MIFARE,
    AM_OOK,
    FM_FSK,
    ProtocolDefinition,
    ProtocolField,
)
from src.ai.protocol_parser import (  # noqa: E402
    DEFAULT_MODEL,
    ProtocolParser,
    ProtocolParserError,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_parser(**kwargs) -> ProtocolParser:
    """Return a ProtocolParser with a dummy API key."""
    return ProtocolParser(api_key="test-key", **kwargs)


def _mock_response(text: str) -> MagicMock:
    """Return a mock requests.Response that yields *text* as generated_text."""
    resp = MagicMock()
    resp.json.return_value = [{"generated_text": text}]
    resp.raise_for_status.return_value = None
    return resp


# ---------------------------------------------------------------------------
# Protocol definitions tests
# ---------------------------------------------------------------------------


class TestProtocolDefinitions(unittest.TestCase):
    def test_registry_contains_all_protocols(self):
        expected = {
            "flipper_serial",
            "am_ook",
            "fm_fsk",
            "nfc_ndef",
            "nfc_mifare_classic",
            "ble_gatt",
        }
        self.assertEqual(set(PROTOCOL_REGISTRY.keys()), expected)

    def test_protocol_definition_type(self):
        for name, defn in PROTOCOL_REGISTRY.items():
            with self.subTest(protocol=name):
                self.assertIsInstance(defn, ProtocolDefinition)

    def test_flipper_serial_fields(self):
        self.assertTrue(len(FLIPPER_SERIAL.fields) > 0)
        field_names = {f.name for f in FLIPPER_SERIAL.fields}
        self.assertIn("length_prefix", field_names)
        self.assertIn("command_id", field_names)

    def test_nfc_ndef_has_tnf_field(self):
        field_names = {f.name for f in NFC_NDEF.fields}
        self.assertIn("tnf", field_names)

    def test_ble_gatt_has_handle_field(self):
        field_names = {f.name for f in BLE_GATT.fields}
        self.assertIn("handle", field_names)

    def test_protocol_field_is_dataclass(self):
        field = FLIPPER_SERIAL.fields[0]
        self.assertIsInstance(field, ProtocolField)
        self.assertIsInstance(field.name, str)
        self.assertIsInstance(field.description, str)

    def test_categories(self):
        self.assertEqual(FLIPPER_SERIAL.category, "serial")
        self.assertEqual(AM_OOK.category, "sub_ghz")
        self.assertEqual(FM_FSK.category, "sub_ghz")
        self.assertEqual(NFC_NDEF.category, "nfc")
        self.assertEqual(NFC_MIFARE.category, "nfc")
        self.assertEqual(BLE_GATT.category, "ble")


# ---------------------------------------------------------------------------
# ProtocolParser initialisation tests
# ---------------------------------------------------------------------------


class TestProtocolParserInit(unittest.TestCase):
    def test_default_model(self):
        parser = ProtocolParser(api_key="k")
        self.assertEqual(parser.model, DEFAULT_MODEL)

    def test_custom_model(self):
        parser = ProtocolParser(model="my/model", api_key="k")
        self.assertEqual(parser.model, "my/model")

    def test_api_key_from_env(self):
        import os

        os.environ["HUGGINGFACE_API_KEY"] = "env-key"
        parser = ProtocolParser()
        self.assertEqual(parser.api_key, "env-key")
        del os.environ["HUGGINGFACE_API_KEY"]

    def test_temperature_stored(self):
        parser = ProtocolParser(api_key="k", temperature=0.5)
        self.assertAlmostEqual(parser.temperature, 0.5)

    def test_local_endpoint_stored(self):
        parser = ProtocolParser(api_key="k", local_endpoint="http://localhost:11434")
        self.assertEqual(parser.local_endpoint, "http://localhost:11434")


# ---------------------------------------------------------------------------
# parse_serial_data tests
# ---------------------------------------------------------------------------


class TestParseSerialData(unittest.TestCase):
    @patch("src.ai.protocol_parser.requests.post")
    def test_returns_dict_with_expected_keys(self, mock_post):
        mock_post.return_value = _mock_response('{"fields": []}')
        parser = _make_parser()
        result = parser.parse_serial_data(b"\x00\x01\x02", "flipper_serial")
        self.assertIn("hex", result)
        self.assertIn("protocol", result)
        self.assertIn("length", result)
        self.assertIn("ai_analysis", result)

    @patch("src.ai.protocol_parser.requests.post")
    def test_hex_matches_input(self, mock_post):
        mock_post.return_value = _mock_response("")
        parser = _make_parser()
        raw = b"\xde\xad\xbe\xef"
        result = parser.parse_serial_data(raw, "flipper_serial")
        self.assertEqual(result["hex"], "deadbeef")

    @patch("src.ai.protocol_parser.requests.post")
    def test_length_matches_input(self, mock_post):
        mock_post.return_value = _mock_response("")
        parser = _make_parser()
        raw = b"\x01\x02\x03"
        result = parser.parse_serial_data(raw, "flipper_serial")
        self.assertEqual(result["length"], 3)

    @patch("src.ai.protocol_parser.requests.post")
    def test_protocol_echoed(self, mock_post):
        mock_post.return_value = _mock_response("")
        parser = _make_parser()
        result = parser.parse_serial_data(b"\x00", "nfc_ndef")
        self.assertEqual(result["protocol"], "nfc_ndef")

    @patch("src.ai.protocol_parser.requests.post")
    def test_http_error_raises_protocol_parser_error(self, mock_post):
        import requests as req

        mock_post.side_effect = req.RequestException("timeout")
        parser = _make_parser()
        with self.assertRaises(ProtocolParserError):
            parser.parse_serial_data(b"\x00", "flipper_serial")


# ---------------------------------------------------------------------------
# explain_protocol tests
# ---------------------------------------------------------------------------


class TestExplainProtocol(unittest.TestCase):
    @patch("src.ai.protocol_parser.requests.post")
    def test_returns_string(self, mock_post):
        mock_post.return_value = _mock_response("## Flipper Serial\n\nSome docs.")
        parser = _make_parser()
        result = parser.explain_protocol("flipper_serial")
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 0)

    @patch("src.ai.protocol_parser.requests.post")
    def test_unknown_protocol_does_not_raise(self, mock_post):
        mock_post.return_value = _mock_response("Unknown protocol docs.")
        parser = _make_parser()
        result = parser.explain_protocol("totally_unknown_protocol")
        self.assertIsInstance(result, str)


# ---------------------------------------------------------------------------
# decode_packet tests
# ---------------------------------------------------------------------------


class TestDecodePacket(unittest.TestCase):
    @patch("src.ai.protocol_parser.requests.post")
    def test_valid_json_array_returned(self, mock_post):
        payload = json.dumps(
            [{"field": "uid", "offset_bytes": 0, "raw_hex": "deadbeef", "decoded_value": "DE:AD:BE:EF", "description": "Card UID"}]
        )
        mock_post.return_value = _mock_response(payload)
        parser = _make_parser()
        result = parser.decode_packet("deadbeef", "nfc_mifare_classic")
        self.assertIsInstance(result, list)
        self.assertEqual(result[0]["field"], "uid")

    @patch("src.ai.protocol_parser.requests.post")
    def test_non_json_returns_raw_output(self, mock_post):
        mock_post.return_value = _mock_response("Unable to parse.")
        parser = _make_parser()
        result = parser.decode_packet("deadbeef", "nfc_mifare_classic")
        self.assertIsInstance(result, list)
        self.assertIn("raw_output", result[0])

    @patch("src.ai.protocol_parser.requests.post")
    def test_hex_cleaned_before_send(self, mock_post):
        mock_post.return_value = _mock_response("[]")
        parser = _make_parser()
        parser.decode_packet("0xDE 0xAD 0xBE 0xEF", "flipper_serial")
        # Verify the POST was called (hex cleaning happens silently)
        mock_post.assert_called_once()


# ---------------------------------------------------------------------------
# identify_protocol tests
# ---------------------------------------------------------------------------


class TestIdentifyProtocol(unittest.TestCase):
    @patch("src.ai.protocol_parser.requests.post")
    def test_returns_dict_with_protocol_key(self, mock_post):
        payload = json.dumps({"protocol": "nfc_ndef", "confidence": 85, "reasoning": "NDEF magic byte found."})
        mock_post.return_value = _mock_response(payload)
        parser = _make_parser()
        result = parser.identify_protocol(b"\xd1\x01\x0e\x55\x04example.com")
        self.assertIn("protocol", result)
        self.assertIn("confidence", result)
        self.assertIn("reasoning", result)

    @patch("src.ai.protocol_parser.requests.post")
    def test_non_json_fallback(self, mock_post):
        mock_post.return_value = _mock_response("Looks like BLE.")
        parser = _make_parser()
        result = parser.identify_protocol(b"\x00")
        self.assertEqual(result["protocol"], "unknown")
        self.assertEqual(result["confidence"], 0)


# ---------------------------------------------------------------------------
# generate_packet tests
# ---------------------------------------------------------------------------


class TestGeneratePacket(unittest.TestCase):
    @patch("src.ai.protocol_parser.requests.post")
    def test_returns_bytes(self, mock_post):
        mock_post.return_value = _mock_response("deadbeef01020304")
        parser = _make_parser()
        result = parser.generate_packet("flipper_serial", {"command_id": 1})
        self.assertIsInstance(result, bytes)
        self.assertEqual(result, bytes.fromhex("deadbeef01020304"))

    @patch("src.ai.protocol_parser.requests.post")
    def test_non_hex_output_raises(self, mock_post):
        # "xyz ghj klm" contains only characters outside 0-9 and a-f/A-F,
        # so after stripping all non-hex chars the result is empty → ProtocolParserError.
        mock_post.return_value = _mock_response("xyz ghj klm")
        parser = _make_parser()
        with self.assertRaises(ProtocolParserError):
            parser.generate_packet("flipper_serial", {"command_id": 1})

    @patch("src.ai.protocol_parser.requests.post")
    def test_uses_local_endpoint_when_set(self, mock_post):
        mock_post.return_value = _mock_response("aabbccdd")
        parser = ProtocolParser(
            api_key="k",
            local_endpoint="http://localhost:11434/api",
        )
        parser.generate_packet("am_ook", {"data": "01010101"})
        call_args = mock_post.call_args
        self.assertEqual(call_args[0][0], "http://localhost:11434/api")


# ---------------------------------------------------------------------------
# _protocol_context tests
# ---------------------------------------------------------------------------


class TestProtocolContext(unittest.TestCase):
    def test_known_protocol_includes_name(self):
        ctx = ProtocolParser._protocol_context("flipper_serial")
        self.assertIn("flipper_serial", ctx)

    def test_unknown_protocol_returns_fallback(self):
        ctx = ProtocolParser._protocol_context("mystery_proto")
        self.assertIn("mystery_proto", ctx)


if __name__ == "__main__":
    unittest.main()
