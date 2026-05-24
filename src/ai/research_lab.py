import concurrent.futures
import yaml
import requests
from pathlib import Path


class ResearchLab:
    """Multi-model research conferencing with guided guardrails."""

    DEFAULT_GUARDRAILS_PATH = Path("config/guardrails/research_lab.yaml")

    def __init__(self, hf_api_key: str = "", guardrails_path: Path = None):
        self.hf_api_key = hf_api_key
        self.guardrails_path = guardrails_path or self.DEFAULT_GUARDRAILS_PATH

    # ------------------------------------------------------------------
    # Guardrails
    # ------------------------------------------------------------------

    def load_guardrails(self) -> list:
        """Load guardrail definitions from YAML config."""
        if self.guardrails_path.exists():
            with open(self.guardrails_path) as f:
                data = yaml.safe_load(f)
            return data.get("guardrails", [])
        return []

    def apply_guardrails(self, prompt: str, guardrail_config: list) -> str:
        """Inject guardrail guidance into the prompt."""
        if not guardrail_config:
            return prompt
        guidance_lines = [g["prompt"] for g in guardrail_config if g.get("prompt")]
        if not guidance_lines:
            return prompt
        guidance = " ".join(guidance_lines)
        return f"{guidance}\n\n{prompt}"

    # ------------------------------------------------------------------
    # Conferencing
    # ------------------------------------------------------------------

    def _query_model(self, model_id: str, prompt: str) -> dict:
        """Query a single HuggingFace Inference API model."""
        try:
            url = f"https://api-inference.huggingface.co/models/{model_id}"
            headers = {}
            if self.hf_api_key:
                headers["Authorization"] = f"Bearer {self.hf_api_key}"
            payload = {"inputs": prompt, "parameters": {"max_new_tokens": 512}}
            response = requests.post(url, json=payload, headers=headers, timeout=60)
            response.raise_for_status()
            data = response.json()
            if isinstance(data, list) and data:
                text = data[0].get("generated_text", "")
            elif isinstance(data, dict):
                text = data.get("generated_text", str(data))
            else:
                text = str(data)
            return {"model": model_id, "response": text, "error": None}
        except Exception as exc:
            return {"model": model_id, "response": "", "error": str(exc)}

    def start_conference(
        self,
        topic: str,
        models_list: list,
        guardrails: list = None,
    ) -> list:
        """Launch parallel model queries and return raw responses.

        Args:
            topic: Research topic (text only).
            models_list: HuggingFace model IDs to query in parallel.
            guardrails: Optional list of guardrail dicts. If *None* the
                guardrails are loaded from :attr:`guardrails_path`.

        Returns:
            List of response dicts with keys ``model``, ``response``, ``error``.
        """
        if guardrails is None:
            guardrails = self.load_guardrails()
        guided_prompt = self.apply_guardrails(topic, guardrails)

        max_workers = min(len(models_list), 5)
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(self._query_model, model_id, guided_prompt): model_id
                for model_id in models_list
            }
            results = []
            for future in concurrent.futures.as_completed(futures):
                results.append(future.result())
        return results

    def aggregate_answers(self, responses: list) -> str:
        """Compile multiple model answers into a single formatted output.

        Args:
            responses: List of dicts returned by :meth:`start_conference`.

        Returns:
            Formatted multi-model answer string.
        """
        sections = []
        for item in responses:
            model = item.get("model", "unknown")
            error = item.get("error")
            text = item.get("response", "")
            if error:
                sections.append(f"[{model}]\nError: {error}\n")
            else:
                sections.append(f"[{model}]\n{text}\n")
        return "\n" + ("-" * 60 + "\n").join(sections)
