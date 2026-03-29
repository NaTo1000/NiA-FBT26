/**
 * api/stream.ts
 *
 * Vercel Serverless Function — Streaming AI Responses via Server-Sent Events
 *
 * Accepts a POST body with `{ task, prompt, model? }` and streams tokens back
 * to the client as `text/event-stream`.  Falls back to a chunked plain-text
 * response when the upstream does not support streaming.
 *
 * Max duration: 60 s (configured in vercel.json).
 * Memory:       1024 MB (configured in vercel.json).
 */

import type { NextApiRequest, NextApiResponse } from "next";

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

/** 5-second safety margin below the 60 s Vercel function limit. */
const STREAM_TIMEOUT_MS = 55_000;
/** Maximum allowed duration for this Vercel function (see vercel.json). */
const _MAX_FUNCTION_DURATION_MS = 60_000; // eslint-disable-line @typescript-eslint/no-unused-vars

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface StreamRequest {
  task: string;
  prompt: string;
  model?: string;
  maxTokens?: number;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/** Write a single SSE event to the response. */
function sendEvent(
  res: NextApiResponse,
  event: string,
  data: unknown
): void {
  const payload = typeof data === "string" ? data : JSON.stringify(data);
  res.write(`event: ${event}\ndata: ${payload}\n\n`);
  // Flush if the underlying stream supports it
  if (typeof (res as { flush?: () => void }).flush === "function") {
    (res as { flush: () => void }).flush();
  }
}

/** Select HuggingFace streaming endpoint for the requested model/task. */
function resolveEndpoint(task: string, model?: string): string {
  const hfBase = "https://api-inference.huggingface.co/models";

  // Allow callers to supply an explicit model slug
  if (model) return `${hfBase}/${model}`;

  const defaults: Record<string, string> = {
    code_gen: "deepseek-ai/deepseek-coder-6.7b-instruct",
    code_review: "codellama/CodeLlama-7b-Instruct-hf",
    nl_to_cli: "meta-llama/Meta-Llama-3-70B-Instruct",
    docs: "mistralai/Mistral-7B-Instruct-v0.3",
    firmware_analysis: "bigcode/starcoder2-7b",
    log_analyze: "microsoft/Phi-3-mini-4k-instruct",
    build_diag: "deepseek-ai/deepseek-coder-1.3b-instruct",
    protocol_parse: "meta-llama/Meta-Llama-3-8B-Instruct",
  };

  const hfRepo = defaults[task] ?? defaults["code_gen"];
  return `${hfBase}/${hfRepo}`;
}

// ---------------------------------------------------------------------------
// Handler
// ---------------------------------------------------------------------------

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse
) {
  // CORS pre-flight
  if (req.method === "OPTIONS") {
    res.setHeader("Access-Control-Allow-Origin", "*");
    res.setHeader("Access-Control-Allow-Methods", "POST, OPTIONS");
    res.setHeader("Access-Control-Allow-Headers", "Content-Type, Authorization");
    return res.status(204).end();
  }

  if (req.method !== "POST") {
    return res.status(405).json({ error: "Method not allowed" });
  }

  let body: StreamRequest;
  try {
    body = req.body as StreamRequest;
    if (!body?.prompt) throw new Error("Missing required field: prompt");
  } catch (err) {
    const msg = err instanceof Error ? err.message : "Invalid request body";
    return res.status(400).json({ error: msg });
  }

  const { task = "code_gen", prompt, model, maxTokens = 512 } = body;
  const endpoint = resolveEndpoint(task, model);
  const hfToken = process.env.HUGGINGFACE_API_TOKEN ?? "";

  // Set up SSE headers
  res.setHeader("Content-Type", "text/event-stream");
  res.setHeader("Cache-Control", "no-cache, no-transform");
  res.setHeader("Connection", "keep-alive");
  res.setHeader("X-Accel-Buffering", "no"); // disable nginx proxy buffering
  res.setHeader("Access-Control-Allow-Origin", "*");
  res.status(200);

  // Emit a "start" event so the client knows we're connected
  sendEvent(res, "start", { task, model: model ?? task, endpoint });

  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), STREAM_TIMEOUT_MS);

  try {
    const upstream = await fetch(endpoint, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(hfToken ? { Authorization: `Bearer ${hfToken}` } : {}),
      },
      body: JSON.stringify({
        inputs: prompt,
        parameters: {
          max_new_tokens: maxTokens,
          return_full_text: false,
          stream: true,
        },
        stream: true,
      }),
      signal: controller.signal,
    });

    if (!upstream.ok || !upstream.body) {
      const errText = await upstream.text();
      sendEvent(res, "error", {
        message: `Upstream error ${upstream.status}: ${errText}`,
      });
      return res.end();
    }

    // Stream NDJSON tokens from HuggingFace Text-Generation-Inference
    const reader = upstream.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop() ?? ""; // keep incomplete line in buffer

      for (const line of lines) {
        const trimmed = line.trim();
        if (!trimmed || trimmed === "data: [DONE]") continue;

        const jsonStr = trimmed.startsWith("data:") ? trimmed.slice(5).trim() : trimmed;
        try {
          const chunk = JSON.parse(jsonStr) as {
            token?: { text?: string };
            generated_text?: string;
          };

          if (chunk.token?.text) {
            sendEvent(res, "token", { text: chunk.token.text });
          } else if (chunk.generated_text) {
            sendEvent(res, "token", { text: chunk.generated_text });
          }
        } catch {
          // Non-JSON line — forward as raw text
          if (jsonStr) sendEvent(res, "token", { text: jsonStr });
        }
      }
    }

    sendEvent(res, "done", { message: "Stream complete" });
  } catch (err) {
    if ((err as Error).name === "AbortError") {
      sendEvent(res, "error", { message: `Request timed out after ${STREAM_TIMEOUT_MS / 1000} s` });
    } else {
      const message = err instanceof Error ? err.message : String(err);
      sendEvent(res, "error", { message });
    }
  } finally {
    clearTimeout(timer);
    res.end();
  }
}
