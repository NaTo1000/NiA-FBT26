"""Known protocol definitions stored as Python dataclasses."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class ProtocolField:
    """A single field within a protocol packet."""

    name: str
    bit_offset: int
    bit_length: int
    data_type: str  # e.g. "uint8", "bytes", "enum", "string"
    description: str
    values: Optional[Dict[int, str]] = None  # enum value mapping


@dataclass
class ProtocolDefinition:
    """Definition of a communication protocol."""

    name: str
    description: str
    category: str  # "serial", "sub_ghz", "nfc", "ble"
    fields: List[ProtocolField] = field(default_factory=list)
    notes: str = ""


# ---------------------------------------------------------------------------
# Flipper Zero Serial Protocol (protobuf-based RPC over UART)
# ---------------------------------------------------------------------------

FLIPPER_SERIAL = ProtocolDefinition(
    name="flipper_serial",
    description=(
        "Flipper Zero USB/UART serial protocol. Uses length-prefixed protobuf "
        "messages. Each frame begins with a varint-encoded payload length "
        "followed by the serialised protobuf RPC message."
    ),
    category="serial",
    fields=[
        ProtocolField(
            name="length_prefix",
            bit_offset=0,
            bit_length=0,  # variable-length varint
            data_type="varint",
            description="Protobuf varint encoding the byte length of the payload.",
        ),
        ProtocolField(
            name="command_id",
            bit_offset=0,
            bit_length=32,
            data_type="uint32",
            description="Unique identifier for matching responses to requests.",
        ),
        ProtocolField(
            name="command_status",
            bit_offset=32,
            bit_length=32,
            data_type="enum",
            description="Result status of the command.",
            values={0: "OK", 1: "ERROR", 2: "ERROR_DECODE", 3: "ERROR_NOT_IMPLEMENTED"},
        ),
        ProtocolField(
            name="content",
            bit_offset=64,
            bit_length=0,  # variable
            data_type="bytes",
            description="Serialised protobuf oneof payload (e.g. StorageReadRequest).",
        ),
    ],
    notes=(
        "Reference: https://github.com/flipperdevices/flipperzero-protobuf. "
        "Connect at 115200 baud 8N1. Send 0x0D 0x0A to enter RPC mode."
    ),
)

# ---------------------------------------------------------------------------
# Sub-GHz Protocols
# ---------------------------------------------------------------------------

AM_OOK = ProtocolDefinition(
    name="am_ook",
    description=(
        "Amplitude-Modulated On-Off Keying. Carrier is fully switched on (1) "
        "or off (0). Widely used for simple remote controls and sensor modules."
    ),
    category="sub_ghz",
    fields=[
        ProtocolField(
            name="preamble",
            bit_offset=0,
            bit_length=0,
            data_type="bits",
            description="Alternating high/low pulses used for receiver AGC sync.",
        ),
        ProtocolField(
            name="sync",
            bit_offset=0,
            bit_length=0,
            data_type="bits",
            description="Distinguishable pattern marking start of data payload.",
        ),
        ProtocolField(
            name="data",
            bit_offset=0,
            bit_length=0,
            data_type="bits",
            description="Encoded payload bits (encoding varies by device).",
        ),
    ],
    notes=(
        "Common frequencies: 315 MHz (US), 433.92 MHz (EU/AU), 868 MHz (EU). "
        "Common encodings: Manchester, PWM, PPM."
    ),
)

FM_FSK = ProtocolDefinition(
    name="fm_fsk",
    description=(
        "Frequency-Shift Keying. Two discrete frequencies represent binary 0 "
        "and 1. More noise-immune than OOK and used by garage door remotes, "
        "car key fobs, and sensor networks."
    ),
    category="sub_ghz",
    fields=[
        ProtocolField(
            name="deviation",
            bit_offset=0,
            bit_length=0,
            data_type="uint16",
            description="Frequency deviation in Hz between mark and space frequencies.",
        ),
        ProtocolField(
            name="data_rate",
            bit_offset=0,
            bit_length=0,
            data_type="uint32",
            description="Symbol rate in baud (bits per second).",
        ),
        ProtocolField(
            name="payload",
            bit_offset=0,
            bit_length=0,
            data_type="bytes",
            description="Raw data bytes transmitted after preamble and sync word.",
        ),
    ],
    notes="Typical data rates: 1.2 kbaud – 250 kbaud.",
)

# ---------------------------------------------------------------------------
# NFC Protocols
# ---------------------------------------------------------------------------

NFC_NDEF = ProtocolDefinition(
    name="nfc_ndef",
    description=(
        "NFC Data Exchange Format (NDEF). A lightweight binary message format "
        "for encoding application-defined payloads carried over ISO 14443 / "
        "ISO 15693 NFC tags."
    ),
    category="nfc",
    fields=[
        ProtocolField(
            name="tnf",
            bit_offset=0,
            bit_length=3,
            data_type="enum",
            description="Type Name Format — defines the record type.",
            values={
                0: "Empty",
                1: "Well-Known",
                2: "MIME Media",
                3: "Absolute URI",
                4: "External",
                5: "Unknown",
                6: "Unchanged",
                7: "Reserved",
            },
        ),
        ProtocolField(
            name="flags",
            bit_offset=3,
            bit_length=5,
            data_type="uint8",
            description="MB (Message Begin), ME (End), CF (Chunk), SR (Short), IL (ID Length).",
        ),
        ProtocolField(
            name="type_length",
            bit_offset=8,
            bit_length=8,
            data_type="uint8",
            description="Length of the TYPE field in bytes.",
        ),
        ProtocolField(
            name="payload_length",
            bit_offset=16,
            bit_length=32,
            data_type="uint32",
            description="Length of PAYLOAD in bytes (1 byte when SR flag is set).",
        ),
        ProtocolField(
            name="id_length",
            bit_offset=48,
            bit_length=8,
            data_type="uint8",
            description="Length of ID field (present only when IL flag is set).",
        ),
        ProtocolField(
            name="type",
            bit_offset=56,
            bit_length=0,
            data_type="bytes",
            description="Record type (e.g. 'T' for text, 'U' for URI).",
        ),
        ProtocolField(
            name="payload",
            bit_offset=0,
            bit_length=0,
            data_type="bytes",
            description="Application payload data.",
        ),
    ],
    notes="Spec: NFC Forum NDEF Technical Specification 1.0.",
)

NFC_MIFARE = ProtocolDefinition(
    name="nfc_mifare_classic",
    description=(
        "MIFARE Classic 1K/4K memory card protocol. ISO/IEC 14443-3 Type A "
        "contactless smart card. Memory divided into sectors, each protected "
        "by two 48-bit keys (Key A and Key B)."
    ),
    category="nfc",
    fields=[
        ProtocolField(
            name="uid",
            bit_offset=0,
            bit_length=32,
            data_type="bytes",
            description="Unique Identifier (4 or 7 bytes depending on card variant).",
        ),
        ProtocolField(
            name="atqa",
            bit_offset=32,
            bit_length=16,
            data_type="uint16",
            description="Answer To Request Type A — identifies card type.",
        ),
        ProtocolField(
            name="sak",
            bit_offset=48,
            bit_length=8,
            data_type="uint8",
            description="Select AcKnowledge — cascade level indicator.",
        ),
        ProtocolField(
            name="sector",
            bit_offset=0,
            bit_length=8,
            data_type="uint8",
            description="Sector number (0-15 for 1K, 0-39 for 4K).",
        ),
        ProtocolField(
            name="block_data",
            bit_offset=0,
            bit_length=128,
            data_type="bytes",
            description="16-byte block contents.",
        ),
        ProtocolField(
            name="access_bits",
            bit_offset=0,
            bit_length=32,
            data_type="bytes",
            description="3-byte access condition bits + 1-byte user data in sector trailer.",
        ),
    ],
    notes=(
        "Authentication uses proprietary CRYPTO1 cipher. "
        "Default keys are 0xFFFFFFFFFFFF (Key A and B)."
    ),
)

# ---------------------------------------------------------------------------
# BLE GATT
# ---------------------------------------------------------------------------

BLE_GATT = ProtocolDefinition(
    name="ble_gatt",
    description=(
        "Bluetooth Low Energy Generic Attribute Profile (GATT). Defines how "
        "BLE devices expose and exchange data through a hierarchy of Services "
        "and Characteristics."
    ),
    category="ble",
    fields=[
        ProtocolField(
            name="att_opcode",
            bit_offset=0,
            bit_length=8,
            data_type="enum",
            description="ATT Protocol opcode.",
            values={
                0x01: "Error Response",
                0x02: "Exchange MTU Request",
                0x03: "Exchange MTU Response",
                0x08: "Read By Type Request",
                0x09: "Read By Type Response",
                0x0A: "Read Request",
                0x0B: "Read Response",
                0x12: "Write Request",
                0x13: "Write Response",
                0x1B: "Handle Value Notification",
                0x1D: "Handle Value Indication",
            },
        ),
        ProtocolField(
            name="handle",
            bit_offset=8,
            bit_length=16,
            data_type="uint16",
            description="Attribute handle — 16-bit identifier for the attribute.",
        ),
        ProtocolField(
            name="uuid",
            bit_offset=24,
            bit_length=128,
            data_type="bytes",
            description=(
                "Characteristic UUID. 16-bit SIG-assigned (e.g. 0x2A37 = Heart Rate) "
                "or 128-bit custom UUID."
            ),
        ),
        ProtocolField(
            name="value",
            bit_offset=0,
            bit_length=0,
            data_type="bytes",
            description="Characteristic value payload.",
        ),
    ],
    notes=(
        "Common GATT Services: 0x180D Heart Rate, 0x180F Battery, "
        "0x1800 Generic Access, 0x1801 Generic Attribute."
    ),
)

# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

PROTOCOL_REGISTRY: Dict[str, ProtocolDefinition] = {
    "flipper_serial": FLIPPER_SERIAL,
    "am_ook": AM_OOK,
    "fm_fsk": FM_FSK,
    "nfc_ndef": NFC_NDEF,
    "nfc_mifare_classic": NFC_MIFARE,
    "ble_gatt": BLE_GATT,
}
