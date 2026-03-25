# Sharding, Queueing & Autoscaling

> **Version**: 1.0.0  
> **Status**: Scaffold / Design  
> **Scope**: 10,000-Bot execution plane · 50-stage transform pipeline

---

## 1. Sharding Model

### 1.1 Bot Shard Layout

The 10,000 bots are divided into **5 shards of 2,000 bots** each. Each shard is owned by one sub-orchestrator, enabling independent scaling and isolated failure domains.

```
┌──────────────────────────────────────────────────────────────────┐
│                    Bot Shard Allocation                          │
│                                                                  │
│  Shard 0  │  Shard 1   │  Shard 2   │  Shard 3   │  Shard 4     │
│  0–1,999  │ 2,000–3,999│ 4,000–5,999│ 6,000–7,999│ 8,000–9,999  │
│  Sub-Orch1│  Sub-Orch2 │  Sub-Orch3 │  Sub-Orch4 │  Sub-Orch5   │
│  (Ingest) │(Normalize) │  (Infer)   │ (Validate) │ (Optimize)   │
└──────────────────────────────────────────────────────────────────┘
```

### 1.2 Shard Key Derivation

```
shard_id = consistent_hash(record.domain_classifier_result) % 5
bot_id   = shard_id * 2000 + consistent_hash(record.record_id) % 2000
```

**Consistent hashing** (jump hash or rendezvous) is used so that adding shards in the future requires only O(1/n) key re-mapping.

### 1.3 Shard Rebalancing

| Trigger | Action |
|---------|--------|
| New shard added | Rebalance using virtual-node ring; migrate 1/n of keys |
| Shard removed | Drain shard; redistribute keys to remaining shards |
| Hot-shard detected (queue depth >80% high-watermark) | Temporarily split shard into two virtual nodes |

### 1.4 Cross-Shard Consistency

- Within a shard: **strong consistency** via per-shard coordinator bot.
- Across shards: **eventual consistency**; cross-shard reads use read-your-writes tokens.
- Global state (topology, circuit-breaker state): replicated to all sub-orchestrators by the Superior Orchestrator via a Raft-based log.

---

## 2. Queue Strategy

### 2.1 Queue Topology

```
Upstream Source
      │
      ▼
[Ingest Queue] ──priority: high/normal/low──► Sub-Orch 1 (Ingest stages)
                                                    │
                                              [Stage Queue: normalize.*]
                                                    │
                                              [Stage Queue: route.*]
                                                    │
                                              [Stage Queue: infer.*]
                                                    │
                                              [Stage Queue: validate.*]
                                                    │
                                              [Stage Queue: optimize.*]
                                                    │
                                              [Output / DLQ]
```

### 2.2 Queue Properties

| Queue | Type | Max Depth | Retention | Priority Levels |
|-------|------|-----------|-----------|-----------------|
| Ingest Queue | Partitioned (per-source) | 500 000 | 24 h | 3 (high/normal/low) |
| Stage Queues (×50) | FIFO + priority | 100 000 | 4 h | 2 (urgent/normal) |
| Dead-Letter Queue (DLQ) | FIFO | Unlimited | 7 days | 1 |
| Replay Queue | FIFO | 50 000 | 7 days | 1 |

### 2.3 Message Broker Options

The queue layer is abstraction-agnostic. Supported backends (configure in `topology.example.yaml`):

| Backend | Mode | Notes |
|---------|------|-------|
| Apache Kafka | Streaming | Default for high-throughput production |
| AWS SQS + SNS | Managed | Serverless / cloud-native deployments |
| RabbitMQ | AMQP | On-premise, lower throughput |
| Redis Streams | Embedded | Development / single-node testing |

---

## 3. Backpressure Handling

### 3.1 Backpressure Levels

```
Queue Depth as % of Max Depth

  0%   ──── Normal ──────────────────────────────────── 60%
  60%  ──── Warning (slow ingest rate by 50%) ──────── 80%
  80%  ──── High-Watermark (pause new ingest) ──────── 90%
  90%  ──── Critical (activate shed + alert) ─────── 100%
 100%  ──── Overflow (reject with 429, DLQ) ──────────
```

### 3.2 Backpressure Actions by Level

| Level | Threshold | Consumer Action | Producer Action |
|-------|-----------|-----------------|-----------------|
| Warning | depth ≥ 60% | Increase concurrency +25% | Reduce publish rate by 50% |
| High-Watermark | depth ≥ 80% | Spawn additional worker pods | Pause publishing; buffer locally |
| Critical | depth ≥ 90% | Activate load-shedding (drop low-priority) | Reject new messages (429) |
| Overflow | depth = 100% | Route overflow to DLQ | Hard reject with backpressure header |

### 3.3 Backpressure Propagation

Backpressure signals flow **upstream** through the pipeline:

```
optimize stage queue full
         │  (NACK with Retry-After header)
         ▼
validate stage pauses dispatch
         │
         ▼
infer stage pauses dispatch
         │  ... propagates up ...
         ▼
ingest stage reduces consumer poll rate
         │
         ▼
upstream source receives flow-control signal
```

### 3.4 Load Shedding Policy

When `Critical` level is reached, records are shed in this priority order (lowest shed first):

1. `priority = low` AND `data_class = public`
2. `priority = low` AND `data_class = internal`
3. `priority = normal` AND over-SLA (age > 80% of TTL)
4. Duplicate records (same `correlation_id` already in pipeline)

---

## 4. Worker Autoscaling

### 4.1 Scaling Dimensions

| Dimension | Unit | Min | Max | Notes |
|-----------|------|-----|-----|-------|
| Bot workers per shard | pods/threads | 10 | 2 000 | Scale per queue depth |
| Sub-orchestrator replicas | pods | 1 | 5 | Scale on CPU + queue lag |
| Transform stage concurrency | goroutines/threads | 2 | 64 | Scale per stage queue depth |

### 4.2 Horizontal Pod Autoscaler (HPA) Config

```yaml
# Example HPA for a sub-orchestrator deployment
autoscaling:
  enabled: true
  min_replicas: 1
  max_replicas: 5
  metrics:
    - type: queue_depth
      target_average_value: 5000        # scale up if avg queue > 5k
    - type: cpu_utilization
      target_average_utilization: 70    # scale up at 70% CPU
    - type: custom
      name: pipeline_lag_seconds
      target_average_value: 10          # scale up if lag > 10s
  scale_up:
    stabilization_window_seconds: 30
    step_percent: 50                    # add up to 50% more replicas
  scale_down:
    stabilization_window_seconds: 300   # wait 5 min before scale-down
    step_percent: 25
```

### 4.3 Bot Pool Autoscaling Algorithm

```
Every 15s:
  for each shard S in [0..4]:
    lag = queue_depth(S) / throughput_per_bot(S)
    desired_bots = ceil(lag / target_lag_per_bot)   # target: 5s lag per bot
    desired_bots = clamp(desired_bots, MIN_BOTS, MAX_BOTS)
    if desired_bots > current_bots(S):
      scale_up(S, desired_bots - current_bots(S))
    elif desired_bots < current_bots(S) * 0.8:     # 20% hysteresis
      scale_down(S, current_bots(S) - desired_bots)
```

### 4.4 Scale-Down Safety

- **Drain before terminate**: bots finishing an active task are never killed mid-execution.
- **Minimum healthy shard capacity**: never scale below `min_bots_per_shard` (default: 10).
- **Cooldown**: 5-minute cooldown after any scale-down event per shard.

---

## 5. Observability Integration Points

| Signal | Source | Destination |
|--------|--------|-------------|
| Queue depth gauge | Message broker | Prometheus → Grafana |
| Bot lag histogram | Sub-orchestrator | Prometheus |
| Backpressure events | Pipeline record headers | Structured log → ELK |
| Shard health | Superior Orchestrator health API | Status page |
| Autoscaling events | HPA controller | Slack alert + audit log |

---

## 6. Future Integration Hooks

| Hook | Interface | Notes |
|------|-----------|-------|
| `QUEUE_BACKEND_ADAPTER` | `QueueBackend` abstract class (`publish/consume/ack/nack`) | Swap broker without pipeline code changes |
| `BACKPRESSURE_POLICY` | `BackpressurePolicy.evaluate(queue_state) → action` | Custom shed/pause logic per tenant |
| `AUTOSCALER_PROVIDER` | `AutoscalerProvider.desired_replicas(metrics) → int` | Plug in KEDA, Knative, or custom controller |
| `SHARD_REBALANCER` | `ShardRebalancer.rebalance(topology_change)` | Custom key migration strategy |
| `COST_OPTIMIZER` | `CostOptimizer.suggest_scale(cost_budget, metrics)` | Cloud-cost-aware scaling decisions |
| `CHAOS_HOOK` | `ChaosHook.inject(fault_spec)` | Chaos engineering test injection point |

---

*See also: [`../architecture/super_orchestrator.md`](../architecture/super_orchestrator.md) · [`../architecture/transform_pipeline.md`](../architecture/transform_pipeline.md)*
