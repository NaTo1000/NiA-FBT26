# Transform Pipeline — 50-Stage Taxonomy

> **Version**: 1.0.0  
> **Status**: Scaffold / Design  
> **Pipeline capacity**: 50 named transform stages across 6 phase groups

---

## 1. Stage Taxonomy

The 50 stages are organised into six phase groups. Each phase group is owned by one sub-orchestrator (see `topology.example.yaml`).

| # | Stage ID | Phase Group | Description |
|---|----------|-------------|-------------|
| 1 | `ingest.http_receiver` | Ingest | Accept raw HTTP/HTTPS payloads |
| 2 | `ingest.grpc_receiver` | Ingest | Accept gRPC stream frames |
| 3 | `ingest.file_watcher` | Ingest | Watch filesystem drop-zone for new files |
| 4 | `ingest.queue_consumer` | Ingest | Pull from upstream message queue (Kafka/SQS) |
| 5 | `ingest.webhook_handler` | Ingest | Validate and enqueue webhook events |
| 6 | `ingest.batch_splitter` | Ingest | Chunk large payloads into pipeline-sized records |
| 7 | `ingest.schema_detect` | Ingest | Auto-detect payload schema version |
| 8 | `ingest.dedup_gate` | Ingest | Drop exact-duplicate messages by content hash |
| 9 | `normalize.charset_convert` | Normalize | Transcode bytes to UTF-8 |
| 10 | `normalize.json_flatten` | Normalize | Flatten nested JSON to dot-path keys |
| 11 | `normalize.timestamp_norm` | Normalize | Convert all timestamps to ISO-8601 UTC |
| 12 | `normalize.field_rename` | Normalize | Apply field alias map from config |
| 13 | `normalize.null_coerce` | Normalize | Replace absent/null fields with schema defaults |
| 14 | `normalize.type_cast` | Normalize | Coerce string numerics, booleans |
| 15 | `normalize.unit_convert` | Normalize | SI unit normalization (e.g., kb → bytes) |
| 16 | `normalize.pii_mask` | Normalize | Mask/hash PII fields per data-class labels |
| 17 | `route.domain_classifier` | Route | Classify record to target domain (bot specialization) |
| 18 | `route.priority_scorer` | Route | Assign priority score 0–100 |
| 19 | `route.shard_selector` | Route | Deterministically select target bot shard |
| 20 | `route.load_balancer` | Route | Weighted round-robin across healthy sub-orchs |
| 21 | `route.geo_router` | Route | Route based on geographic metadata |
| 22 | `route.experiment_splitter` | Route | A/B / canary traffic splitting |
| 23 | `route.fallback_router` | Route | Re-route on downstream failure (see failure domains) |
| 24 | `route.dead_letter_sink` | Route | Capture unroutable records |
| 25 | `infer.feature_extract` | Infer | Extract ML features from normalized record |
| 26 | `infer.embedding_gen` | Infer | Generate vector embeddings |
| 27 | `infer.classifier` | Infer | Run domain classification model |
| 28 | `infer.anomaly_detect` | Infer | Flag statistical anomalies |
| 29 | `infer.intent_parser` | Infer | NLU intent extraction for text records |
| 30 | `infer.sentiment_score` | Infer | Sentiment polarity scoring |
| 31 | `infer.entity_extract` | Infer | Named-entity recognition |
| 32 | `infer.confidence_gate` | Infer | Drop records below confidence threshold |
| 33 | `infer.model_version_check` | Infer | Ensure model artifact version matches config |
| 34 | `validate.schema_check` | Validate | Validate record against JSON Schema |
| 35 | `validate.business_rules` | Validate | Apply domain-specific business rule engine |
| 36 | `validate.referential_integrity` | Validate | Check foreign-key / cross-record consistency |
| 37 | `validate.range_check` | Validate | Numeric field within min/max bounds |
| 38 | `validate.regex_check` | Validate | Pattern validation for string fields |
| 39 | `validate.enum_check` | Validate | Value contained in allowed set |
| 40 | `validate.signature_verify` | Validate | Verify HMAC/JWT signature on trusted fields |
| 41 | `validate.quarantine_tag` | Validate | Tag invalid records for manual review queue |
| 42 | `optimize.dedup_aggregate` | Optimize | Merge duplicate records within time window |
| 43 | `optimize.compress` | Optimize | Compress large binary payloads (zstd) |
| 44 | `optimize.cache_lookup` | Optimize | Serve cached result for repeated requests |
| 45 | `optimize.cache_write` | Optimize | Populate cache with computed results |
| 46 | `optimize.batch_pack` | Optimize | Pack multiple small records into micro-batches |
| 47 | `optimize.rate_limit` | Optimize | Enforce per-tenant rate limits |
| 48 | `optimize.cost_score` | Optimize | Attach estimated compute cost for billing |
| 49 | `optimize.emit_metrics` | Optimize | Publish per-record latency/throughput counters |
| 50 | `optimize.output_dispatch` | Optimize | Fan-out to final sinks (DB, queue, webhook) |

---

## 2. Input / Output Schema Expectations

### 2.1 Pipeline Record Envelope

Every record entering or exiting a stage is wrapped in a **PipelineRecord**:

```json
{
  "record_id":       "<uuid-v4>",
  "correlation_id":  "<trace-root-id>",
  "stage_sequence":  ["ingest.http_receiver", "normalize.charset_convert", "..."],
  "current_stage":   "<stage_id>",
  "attempt":         1,
  "created_utc":     "<ISO-8601>",
  "updated_utc":     "<ISO-8601>",
  "ttl_utc":         "<ISO-8601>",
  "schema_ref":      "<schema-id>@<version>",
  "headers": {
    "source_system": "<string>",
    "data_class":    "public | internal | confidential | restricted",
    "priority":      0
  },
  "payload": { },
  "errors": [ ]
}
```

> **Priority field**: `headers.priority` is an integer **0–100** (0 = lowest priority).
> `route.priority_scorer` assigns the numeric score. Queue backends map score bands
> to named queue tiers: 0–33 → `low`, 34–66 → `normal`, 67–100 → `high`.

### 2.2 Stage I/O Contract

Each stage **must** honour the following contract:

| Property | Rule |
|----------|------|
| Input type | `PipelineRecord` (read-only access to upstream fields) |
| Output type | `PipelineRecord` (may mutate `payload`, append to `errors`, advance `stage_sequence`) |
| Side-effects | Must be idempotent when `attempt > 1` |
| Null output | Allowed only for filter/gate stages; must set `filter_reason` in `errors` |
| Latency SLO | P99 ≤ 200 ms per stage (override in config per stage) |

### 2.3 Phase-Group I/O Summary

| Phase Group | Accepts | Emits |
|-------------|---------|-------|
| Ingest | Raw bytes / HTTP request / queue message | `PipelineRecord` (schema TBD) |
| Normalize | `PipelineRecord` (raw payload) | `PipelineRecord` (clean payload, UTF-8) |
| Route | `PipelineRecord` (normalized) | Routing decision + `PipelineRecord` on target channel |
| Infer | `PipelineRecord` (routed) | `PipelineRecord` + `infer_annotations` map |
| Validate | `PipelineRecord` + annotations | `PipelineRecord` marked `valid` or `quarantine` |
| Optimize | `PipelineRecord` (validated) | Final sink payload or cached result |

---

## 3. Retry & Idempotency Rules

### 3.1 Retry Policy (per stage)

```yaml
retry:
  max_attempts: 3
  backoff:
    strategy: exponential          # fixed | linear | exponential
    initial_interval_ms: 100
    multiplier: 2.0
    max_interval_ms: 5000
    jitter: true                   # adds ±25% random jitter
  retryable_errors:
    - TRANSIENT_UPSTREAM_ERROR
    - TIMEOUT
    - RATE_LIMITED
  non_retryable_errors:
    - SCHEMA_VIOLATION
    - AUTHENTICATION_FAILURE
    - RECORD_TOO_LARGE
```

### 3.2 Idempotency Contract

1. **Key derivation** — `idempotency_key = SHA-256("<record_id>|<stage_id>|<attempt>")` (pipe-delimited to avoid concatenation collisions). Stages store this key before mutating state.
2. **Deduplication window** — default **5 minutes** (configurable per stage). The key is stored in a shared idempotency store (Redis / DynamoDB).
3. **Safe re-execution** — on retry, if the key already exists in the store, return the previously stored output without re-executing side-effects.
4. **Exactly-once semantics** — for stages with external side-effects (e.g., `optimize.output_dispatch`), the idempotency store is written transactionally with the external write.

### 3.3 Dead-Letter Flow

```
Stage fails after max_attempts
         │
         ▼
  Record tagged FAILED
  + error payload appended
         │
         ▼
route.dead_letter_sink
         │
         ├──► Dead-Letter Queue (DLQ)
         │         └── Manual review / replay
         └──► Alert (PagerDuty / Slack via webhook)
```

### 3.4 Idempotency Store Schema

```json
{
  "key":         "<idempotency_key>",
  "record_id":   "<uuid-v4>",
  "stage_id":    "<stage_id>",
  "attempt":     1,
  "status":      "SUCCESS | FAILED",
  "output_ref":  "<storage-pointer>",
  "created_utc": "<ISO-8601>",
  "expires_utc": "<ISO-8601>"
}
```

---

## 4. Stage Configuration Schema

Each stage can be individually tuned in `topology.example.yaml`:

```yaml
stage:
  id: normalize.pii_mask
  enabled: true
  owner_sub_orchestrator: sub_orch_normalize
  concurrency: 8
  timeout_ms: 150
  retry:
    max_attempts: 2
    backoff:
      strategy: fixed
      initial_interval_ms: 50
  slo:
    latency_p99_ms: 200
    error_rate_max: 0.01
  config:
    pii_fields: ["email", "phone", "ip_address"]
    hash_algorithm: sha256
    salt_env_var: PII_SALT
```

---

## 5. Future Integration Hooks

| Hook | Purpose |
|------|---------|
| `STAGE_MIDDLEWARE_CHAIN` | Plug-in chain for cross-cutting concerns (tracing, auth, metrics) |
| `SCHEMA_REGISTRY_CLIENT` | Swap static `schema_ref` validation for live Confluent/AWS Glue schema registry |
| `INFER_MODEL_LOADER` | Abstract model serving backend (TorchServe, Triton, SageMaker, local) |
| `IDEMPOTENCY_STORE_BACKEND` | Swap in-memory store for Redis/DynamoDB in production |
| `DLQ_CONSUMER` | Replay tooling to re-inject dead-lettered records into the pipeline |
| `STAGE_METRICS_EXPORTER` | Per-stage Prometheus metrics with stage-level labels |

---

*See also: [`super_orchestrator.md`](super_orchestrator.md) · [`../scalability/sharding_and_queueing.md`](../scalability/sharding_and_queueing.md)*
