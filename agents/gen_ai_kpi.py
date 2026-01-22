import logging
import os
from typing import Any, Dict

import google.generativeai as genai

logger = logging.getLogger(__name__)


class KPIQuestionAnsweringAgent:
    """
    Agent that answers natural language questions about KPIs using Generative AI (Gemini).
    """

    def __init__(self, model_name: str = "gemini-1.5-flash"):
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.model_name = model_name
        self.client = None

        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel(model_name)
        else:
            logger.warning("GEMINI_API_KEY not found. Agent will run in mock mode.")

    def answer_query(self, query: str, context_metrics: Dict[str, Any]) -> str:
        """
        Answers a query based on the provided metrics context.
        """
        if not self.api_key:
            return self._mock_response(query, context_metrics)

        try:
            # Construct prompt
            prompt = self._construct_prompt(query, context_metrics)
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            logger.error("Error generating content: %s", e)
            return "I encountered an error while processing your request."

    def _construct_prompt(self, query: str, metrics: Dict[str, Any]) -> str:
        """
        Constructs the prompt with context.
        """
        # Simplify context for the prompt
        context_str = "\n".join(
            [
                f"{k}: {v}"
                for k, v in metrics.items()
                if isinstance(v, (int, float, str))
            ]
        )

        prompt = f"""
        You are an expert financial analyst. Answer the following question based ONLY on the provided KPI data.
        
        KPI Data:
        {context_str}
        
        Question: {query}
        
        Answer (concise and professional):
        """
        return prompt

    def _mock_response(self, query: str, metrics: Dict[str, Any]) -> str:
        """
        Returns a mock response for testing/offline mode.
        """
        return f"[MOCK] Based on the data, the answer to '{query}' involves analyzing the provided metrics. (API Key missing)"


if __name__ == "__main__":
    # Test
    agent = KPIQuestionAnsweringAgent()
    metrics = {"PAR30": 2.5, "CollectionRate": 98.2, "PortfolioHealth": 9.5}
    print(agent.answer_query("How is the portfolio health?", metrics))
