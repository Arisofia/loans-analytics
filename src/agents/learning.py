import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class FeedbackStore:
    def __init__(self, storage_dir: str = "data/agents/feedback"):
        self.storage_dir = storage_dir
        os.makedirs(self.storage_dir, exist_ok=True)

    def collect_feedback(
        self, agent_name: str, run_id: str, feedback_score: float, comments: Optional[str] = None
    ):
        """Collect and store feedback for a specific agent run."""
        timestamp = datetime.now(timezone.utc).isoformat()
        feedback_data = {
            "agent_name": agent_name,
            "run_id": run_id,
            "score": feedback_score,
            "comments": comments,
            "timestamp": timestamp,
        }

        filename = f"{agent_name}_{run_id}_feedback.json"
        path = os.path.join(self.storage_dir, filename)
        with open(path, "w") as f:
            json.dump(feedback_data, f, indent=2)
        return path

    def get_agent_performance(self, agent_name: str) -> Dict[str, Any]:
        """Aggregate performance metrics for an agent.

        Skips malformed feedback files (bad JSON, missing `score`) to avoid
        failing the aggregation for a single corrupt file.
        """
        files = [f for f in os.listdir(self.storage_dir) if f.startswith(agent_name)]
        scores = []
        for file in files:
            file_path = os.path.join(self.storage_dir, file)
            try:
                with open(file_path, "r") as f:
                    data = json.load(f)
                if not isinstance(data, dict):
                    logger.warning(
                        "Skipping malformed feedback file (not an object): %s", file_path
                    )
                    continue
                if "score" not in data:
                    logger.warning("Skipping feedback missing 'score' key: %s", file_path)
                    continue
                scores.append(float(data["score"]))
            except (json.JSONDecodeError, KeyError, OSError, ValueError) as e:
                logger.warning("Skipping malformed feedback file %s: %s", file_path, e)
                continue

        if not scores:
            return {"average_score": 0.0, "total_feedbacks": 0}

        return {"average_score": sum(scores) / len(scores), "total_feedbacks": len(scores)}


class LearningEngine:
    def __init__(self, feedback_store: FeedbackStore):
        self.feedback_store = feedback_store

    def optimize_agent_prompts(self, agent_name: str):
        """Placeholder for prompt optimization based on feedback."""
        performance = self.feedback_store.get_agent_performance(agent_name)
        if performance["average_score"] < 0.7 and performance["total_feedbacks"] > 5:
            print(
                f"[Learning Engine] Performance for {agent_name} is low ({performance['average_score']}). Triggering prompt optimization..."
            )
            # Logic to refine system prompts or few-shot examples
            return True
        return False
