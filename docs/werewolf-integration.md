# Werewolf defensive simulation

NiA FBT26 includes a clean-room C++17/Qt6 implementation of a defensive-only
Werewolf + Sasquach simulation. The behavioral reference is
[`skizzophrenic/Talking-Sasquach@66347dd`](https://github.com/skizzophrenic/Talking-Sasquach/commit/66347dd263cb8b358ca10afdb9f9f347bd14e181),
the commit associated with `skizzophrenic/Talking-Sasquach#11`. This project
uses the documented behavior as a contract; it does not copy or vendor that
project's Python source and neither executable invokes or depends on Python.

## Safety and trust contract

- Nearby devices never activate defence. Only a `VerifiedAttackAlert` created
  by the simulation verifier can enter guard mode.
- JSON produces a `RawAlert`. The schema-v1 adapter cannot construct a verified
  alert or expose a public trusted-boolean constructor.
- `SimulationAlertVerifier` exists for deterministic tests and demonstrations.
  It is not production authentication and is explicitly unavailable for
  production use.
- Defence is bound to the verified target and a resolved alert is single-use.
- The sole containment capability records a local `block_and_isolate` request.
  The adapter has no network, serial, firmware, remote-modification, retaliation,
  or operating-system policy API.
- Invalid, unknown, malformed, duplicate, out-of-range, future, expired,
  overlong, replayed, or oversized input fails closed.

The engine caps energy at 100, shield at 60, events at 500, alert and resolved
replay IDs at 1,024 each, and beacon lifetime at 300 seconds. Live unexpired
beacon replay state has a hard limit of 4,096: expired entries are pruned first,
then new entries are rejected rather than evicting still-live replay evidence.

## Scenario schema v1

The complete example is
[`cpp/tests/fixtures/golden-scenario-v1.json`](../cpp/tests/fixtures/golden-scenario-v1.json).
Every object rejects unknown fields. Every listed field is required except the
top-level `attack_alert`, `shield_charge`, and `attacker_device_id`.

```json
{
  "schema_version": 1,
  "current_time": 1000,
  "devices": [{
    "device_id": "rotating-id",
    "device_class": "flipper",
    "signal_dbm": -43,
    "opted_in": true,
    "game_beacon_valid": true,
    "battle_power": 30,
    "connected_first": false,
    "beacon_id": "single-use-beacon",
    "issued_at": 990,
    "expires_at": 1010
  }],
  "attack_alert": {
    "alert_id": "simulation-alert",
    "detector": "test-simulation-verifier",
    "target_device_id": "rotating-id",
    "reason": "simulated protected-route access",
    "severity": 4,
    "simulation_trusted": true
  },
  "shield_charge": 20,
  "attacker_device_id": "rotating-id"
}
```

Scenarios are limited to 1 MiB. Boolean values must be JSON booleans; numeric
values must be integers in their documented range. Device and beacon IDs must
be unique within a scenario.

## Native surfaces

The **Defensive Simulation** tab loads, validates, runs, and clears scenarios.
Text badges expose mode, skin, energy, and shield state; tables and text expose
metrics, events, and limitations without relying on untracked assets.

The CLI uses the same domain library:

```text
nia-werewolf check
nia-werewolf run scenario.json
nia-werewolf report scenario.json --output report.json
```

All successful commands emit JSON. Exit `0` means success, `2` means an input
or contract rejection, and `3` means an atomic report write failed.

## Explicit limitations

This is a deterministic local simulation, not a security control. It has no
hardware integration, production detector authentication, cryptographic beacon
verification, operating-system containment, network action, serial action,
firmware flashing, or remote modification. A production integration would
require an independently reviewed authenticated verifier, durable replay policy,
rate limiting, concurrency and failure-injection testing, hardware-in-the-loop
evidence, and a reversible OS-specific containment implementation outside this
capability-limited prototype.
