# Super Orchestrator Architecture

> **Version**: 1.0.0  
> **Status**: Scaffold / Design  
> **Scope**: 1 Superior Orchestrator · 5 Sub-Orchestrators · 50 Transform Stages · 10 000 Bots

---

## 1. Hierarchy Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    CONTROL PLANE                            │
│                                                             │
│   ┌──────────────────────────────────────────────────────┐  │
│   │           Superior Orchestrator (SO)                 │  │
│   │  • Global policy enforcement                         │  │
│   │  • Cross-domain routing decisions                    │  │
│   │  • Health aggregation & global circuit-breaking      │  │
│   │  • Topology config source-of-truth                   │  │
│   └──────────┬───────────┬───────────┬──────────┬───────┘  │
│              │           │           │          │           │
│   ┌──────────▼──┐ ┌──────▼─────┐ ┌──▼──────┐ ┌▼──────┐ ┌─▼──────┐ │
│   │  Sub-Orch 1  │ │ Sub-Orch 2  │ │Sub-Orch3│ │SubO-4 │ │SubO-5  │ │
│   │  (Ingest)    │ │(Normalize) │ │(Infer)  │ │(Valid)│ │(Optim) │ │
│   └──────────────┘ └────────────┘ └─────────┘ └───────┘ └────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                   EXECUTION PLANE                           │
│                                                             │
│  Transform Pipeline (50 stages, see transform_pipeline.md)  │
│       │          │          │          │         │          │
│  ┌────▼────┐ ┌───▼────┐ ┌──▼─────┐ ┌──▼────┐ ┌─▼──────┐   │
│  │Bot Shard│ │Bot Shard│ │Bot Shard│ │Bot ...│ │Bot Shard│  │
│  │  0-1999 │ │2000-3999│ │4000-5999│ │ 6000- │ │ 8000-  │  │
│  │         │ │         │ │         │ │  7999 │ │  9999  │  │
│  └─────────┘ └─────────┘ └─────────┘ └───────┘ └────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Plane Responsibilities

| Plane | Components | Responsibilities |
|-------|-----------|-----------------|
| Control | Superior Orchestrator, 5 Sub-Orchestrators | Policy, routing, health, config propagation |
| Execution | Transform Pipeline, Bot Shards | Data processing, specialised task execution |

---

## 2. Orchestration Contracts

All orchestrator-to-orchestrator and orchestrator-to-transform communications use a common envelope:

```json
{
  "envelope_version": "1.0",
  "message_id": "<uuid-v4>",
  "correlation_id": "<trace-root-id>",
  "source": {
    "plane": "control | execution",
    "component_type": "superior | sub | transform | bot",
    "component_id": "<string>"
  },
  "destination": {
    "component_type": "...",
    "component_id": "<string | broadcast>"
  },
  "timestamp_utc": "<ISO-8601>",
  "ttl_ms": 30000,
  "payload_schema": "<schema-ref>",
  "payload": { }
}
```

### Contract Rules

1. **Idempotency key** — every mutating command carries `message_id`; receivers deduplicate by key within a configurable window (default 5 min).
2. **TTL enforcement** — messages exceeding `ttl_ms` since `timestamp_utc` are dead-lettered, not retried.
3. **Schema versioning** — `payload_schema` references a versioned schema registry entry; consumers reject unknown major versions.
4. **Acknowledgment** — all commands require an explicit `ACK` or `NACK` within `ttl_ms / 2`; absence triggers the sender's retry policy.

---

## 3. Lifecycle States

### 3.1 Superior Orchestrator Lifecycle

```
INIT ──► BOOTSTRAPPING ──► ACTIVE ──► DRAINING ──► STOPPED
                 │                        ▲
                 └──── DEGRADED ──────────┘
                              │
                              └──► FAILOVER
```

| State | Description | Allowed Transitions |
|-------|-------------|---------------------|
| `INIT` | Process start, loading topology config | → `BOOTSTRAPPING` |
| `BOOTSTRAPPING` | Registering sub-orchestrators, warming caches | → `ACTIVE`, → `DEGRADED` |
| `ACTIVE` | Fully operational, accepting all traffic | → `DRAINING`, → `DEGRADED` |
| `DEGRADED` | Partial capacity (≥1 sub-orch unreachable) | → `ACTIVE`, → `FAILOVER` |
| `DRAINING` | Graceful shutdown, finishing in-flight work | → `STOPPED` |
| `FAILOVER` | Transferring leadership to standby SO | → `STOPPED` |
| `STOPPED` | Terminated | — |

### 3.2 Sub-Orchestrator Lifecycle

```
INIT ──► REGISTERING ──► IDLE ──► BUSY ──► DRAINING ──► STOPPED
                              ▲      │
                              └──────┘
                              │
                        CIRCUIT_OPEN
```

| State | Description |
|-------|-------------|
| `REGISTERING` | Announcing presence to Superior Orchestrator |
| `IDLE` | Registered, no active transform batches |
| `BUSY` | Processing one or more transform stage queues |
| `CIRCUIT_OPEN` | Downstream failure detected; refusing new work |
| `DRAINING` | Completing outstanding work before shutdown |

### 3.3 Transform Stage Lifecycle

```
PENDING ──► SCHEDULED ──► EXECUTING ──► SUCCEEDED
                               │
                          RETRY_PENDING ──► (back to EXECUTING)
                               │
                           FAILED (dead-letter)
```

### 3.4 Bot Lifecycle

```
UNREGISTERED ──► REGISTERED ──► AVAILABLE ──► ASSIGNED ──► EXECUTING
                                     ▲             │
                                     └─────────────┘
                                          │
                                    UNAVAILABLE (health-fail)
                                          │
                                      EVICTED
```

---

## 4. Failure Domains & Fallback Routing

### 4.1 Failure Domain Map

```
Domain 0 (Global):   Superior Orchestrator failure
Domain 1 (Cluster):  ≥2 Sub-Orchestrators unreachable simultaneously
Domain 2 (Pipeline): A transform stage queue depth > high-watermark
Domain 3 (Shard):    A bot shard (2000-bot group) health < 50%
Domain 4 (Bot):      Individual bot crash or timeout
```

### 4.2 Fallback Routing Table

| Failure Domain | Detection Mechanism | Fallback Action |
|----------------|---------------------|-----------------|
| Domain 0 | Heartbeat miss × 3 (15 s) | Hot-standby SO takes over via Raft leader election |
| Domain 1 | Sub-orch health probe fails | Route traffic to healthy sub-orchs; shed load if <2 healthy |
| Domain 2 | Queue depth metric breach | Activate backpressure (see `sharding_and_queueing.md`); pause upstream ingest |
| Domain 3 | >50% bots in shard return errors | Mark shard `DEGRADED`; re-route tasks to healthy shard |
| Domain 4 | Bot heartbeat timeout (10 s) | Reassign task to next available bot in same specialization group |

### 4.3 Circuit-Breaker Parameters

```yaml
# Defaults — overridable per component in topology.example.yaml
circuit_breaker:
  failure_rate_threshold: 0.5      # open after 50% failures in window
  sliding_window_size: 20          # last N calls evaluated
  wait_duration_open_ms: 30000     # time in OPEN before trying HALF_OPEN
  permitted_calls_half_open: 5     # test calls in HALF_OPEN
```

---

## 5. Future Integration Hooks

> These extension points are intentionally left unimplemented in this scaffold. They define stable interfaces for future runtime integration.

| Hook | Interface | Notes |
|------|-----------|-------|
| `SO_POLICY_PROVIDER` | gRPC service stub `PolicyProvider.GetPolicy(domain)` | Swap built-in policy for external OPA/Rego rules |
| `SO_HEALTH_EXPORTER` | Prometheus `/metrics` endpoint | Expose orchestrator state machine metrics |
| `SUB_ORCH_PLUGIN` | Python ABC `SubOrchestratorPlugin` | Custom scheduling algorithms per domain |
| `TRANSFORM_INTERCEPTOR` | Middleware chain `(ctx, msg) → msg` | Inject tracing, auth, schema validation |
| `BOT_REGISTRY_BACKEND` | Key-value store interface (`get/set/watch`) | Swap in-memory registry for etcd/Consul |
| `DEAD_LETTER_HANDLER` | `DeadLetterSink.consume(envelope)` | Route failed messages to alerting, replay queue |

---

*See also: [`transform_pipeline.md`](transform_pipeline.md) · [`../scalability/sharding_and_queueing.md`](../scalability/sharding_and_queueing.md)*
