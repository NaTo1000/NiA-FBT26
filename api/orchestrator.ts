/**
 * api/orchestrator.ts
 *
 * Vercel Serverless Function — AI Orchestration Router
 *
 * Routes incoming requests to the appropriate AI backend (HuggingFace, local
 * Docker runners, or a fallback stub) based on the requested task type and the
 * caller's geographic region.  Designed to run within Vercel's execution limits
 * (≤ 30 s, 512 MB).
 */

import type { NextApiRequest, NextApiResponse } from "next";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export type TaskType =
  | "code_gen"
  | "code_review"
  | "nl_to_cli"
  | "docs"
  | "signal_classify"
  | "firmware_analysis"
  | "github_rank"
  | "log_analyze"
  | "build_diag"
  | "protocol_parse"
  | "health";

interface OrchestratorRequest {
  task: TaskType;
  prompt?: string;
  model?: string;
  region?: string;
}

interface OrchestratorResponse {
  status: "ok" | "error";
  task: TaskType;
  model: string;
  endpoint: string;
  result?: string;
  latencyMs?: number;
  error?: string;
}

// ---------------------------------------------------------------------------
// Model → endpoint mapping
// ---------------------------------------------------------------------------

const MODEL_MAP: Record<TaskType, { model: string; hfRepo: string }> = {
  code_gen: {
    model: "deepseek-coder-6.7b-instruct",
    hfRepo: "deepseek-ai/deepseek-coder-6.7b-instruct",
  },
  code_review: {
    model: "codellama-7b-instruct",
    hfRepo: "codellama/CodeLlama-7b-Instruct-hf",
  },
  nl_to_cli: {
    model: "meta-llama-3-70b-instruct",
    hfRepo: "meta-llama/Meta-Llama-3-70B-Instruct",
  },
  docs: {
    model: "mistral-7b-instruct-v0.3",
    hfRepo: "mistralai/Mistral-7B-Instruct-v0.3",
  },
  signal_classify: {
    model: "onnx-signal-classifier",
    hfRepo: "NaTo1000/nia-signal-classifier",
  },
  firmware_analysis: {
    model: "starcoder2-7b",
    hfRepo: "bigcode/starcoder2-7b",
  },
  github_rank: {
    model: "bge-large-en-v1.5",
    hfRepo: "BAAI/bge-large-en-v1.5",
  },
  log_analyze: {
    model: "phi-3-mini-4k-instruct",
    hfRepo: "microsoft/Phi-3-mini-4k-instruct",
  },
  build_diag: {
    model: "deepseek-coder-1.3b-instruct",
    hfRepo: "deepseek-ai/deepseek-coder-1.3b-instruct",
  },
  protocol_parse: {
    model: "meta-llama-3-8b-instruct",
    hfRepo: "meta-llama/Meta-Llama-3-8B-Instruct",
  },
  health: {
    model: "none",
    hfRepo: "",
  },
};

// ---------------------------------------------------------------------------
// Region-aware endpoint selection
// ---------------------------------------------------------------------------

/** Allowed Vercel region identifiers — prevents env-var probing via region param. */
const ALLOWED_REGIONS = new Set(["iad1", "sfo1", "lhr1", "sin1", "cdg1", "hnd1", "bom1", "gru1"]);

function selectEndpoint(region: string, hfRepo: string): string {
  const hfBase = "https://api-inference.huggingface.co/models";

  // Only look up a regional runner for known, validated regions
  if (ALLOWED_REGIONS.has(region)) {
    const regionalRunner = process.env[`AI_RUNNER_${region.toUpperCase()}`];
    if (regionalRunner) return `${regionalRunner}/infer`;
  }

  // Fall back to HuggingFace Inference API
  if (hfRepo) return `${hfBase}/${hfRepo}`;

  return "";
}

// ---------------------------------------------------------------------------
// Inference call (non-streaming, ≤ 30 s budget)
// ---------------------------------------------------------------------------

async function callInference(
  endpoint: string,
  prompt: string,
  timeoutMs = 25_000
): Promise<string> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const hfToken = process.env.HUGGINGFACE_API_TOKEN ?? "";
    const res = await fetch(endpoint, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(hfToken ? { Authorization: `Bearer ${hfToken}` } : {}),
      },
      body: JSON.stringify({ inputs: prompt, parameters: { max_new_tokens: 512 } }),
      signal: controller.signal,
    });

    if (!res.ok) {
      throw new Error(`Upstream returned ${res.status}: ${await res.text()}`);
    }

    const json = await res.json();
    if (Array.isArray(json) && json[0]?.generated_text) {
      return json[0].generated_text as string;
    }
    return JSON.stringify(json);
  } finally {
    clearTimeout(timer);
  }
}

// ---------------------------------------------------------------------------
// Handler
// ---------------------------------------------------------------------------

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse<OrchestratorResponse>
) {
  // CORS pre-flight
  if (req.method === "OPTIONS") {
    res.setHeader("Access-Control-Allow-Origin", "*");
    res.setHeader("Access-Control-Allow-Methods", "GET, POST, OPTIONS");
    res.setHeader("Access-Control-Allow-Headers", "Content-Type, Authorization");
    return res.status(204).end();
  }

  if (req.method !== "GET" && req.method !== "POST") {
    return res.status(405).json({
      status: "error",
      task: "health",
      model: "none",
      endpoint: "",
      error: "Method not allowed",
    });
  }

  // Health-check shortcut (used by the cron job in vercel.json)
  const isCron = req.query["cron"] === "health";
  if (isCron || req.query["task"] === "health") {
    return res.status(200).json({
      status: "ok",
      task: "health",
      model: "none",
      endpoint: "/api/orchestrator",
      result: "healthy",
      latencyMs: 0,
    });
  }

  let body: OrchestratorRequest;
  try {
    body =
      req.method === "POST"
        ? (req.body as OrchestratorRequest)
        : {
            task: (req.query["task"] as TaskType) ?? "code_gen",
            prompt: (req.query["prompt"] as string) ?? "",
            region: (req.query["region"] as string) ?? "iad1",
          };
  } catch {
    return res.status(400).json({
      status: "error",
      task: "health",
      model: "none",
      endpoint: "",
      error: "Invalid request body",
    });
  }

  const { task, prompt = "", region = "iad1" } = body;
  const mapping = MODEL_MAP[task];

  if (!mapping) {
    return res.status(400).json({
      status: "error",
      task,
      model: "none",
      endpoint: "",
      error: `Unknown task type: ${task}`,
    });
  }

  const endpoint = selectEndpoint(region, mapping.hfRepo);
  const start = Date.now();

  try {
    const result = endpoint
      ? await callInference(endpoint, prompt)
      : `[stub] No endpoint configured for task '${task}' in region '${region}'`;

    return res.status(200).json({
      status: "ok",
      task,
      model: mapping.model,
      endpoint,
      result,
      latencyMs: Date.now() - start,
    });
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    return res.status(502).json({
      status: "error",
      task,
      model: mapping.model,
      endpoint,
      error: message,
      latencyMs: Date.now() - start,
    });
  }
}
