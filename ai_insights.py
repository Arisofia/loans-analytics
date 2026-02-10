import os
from functools import lru_cache
from typing import Any, Dict

from openai import OpenAI


@lru_cache(maxsize=1)
def _get_client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not set")
    return OpenAI(api_key=api_key)


def generate_kpi_insights(kpis: Dict[str, Any], context: str = "") -> str:
    client = _get_client()
    kpi_pairs = [f"{key}: {value}" for key, value in kpis.items()]
    kpi_text = "\n".join(kpi_pairs)

    prompt = (
        "You are a senior fintech risk and growth strategist.\n"
        "Given these loan portfolio KPIs and context, provide concise, actionable insights "
        "and next best actions.\n\n"
        "Context:\n"
        f"{context}\n\n"
        "KPIs:\n"
        f"{kpi_text}\n\n"
        "Return:\n"
        "- 3-5 key observations\n"
        "- 3-5 concrete actions for risk, growth, and profitability\n"
        "Use bullet points, no fluff."
    )

    completion = client.responses.create(
        model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
        input=prompt,
        max_output_tokens=600,
    )

    return completion.output[0].content[0].text
