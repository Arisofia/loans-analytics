import hashlib
import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import yaml
from sqlalchemy import JSON, Boolean, Column, DateTime, Integer, Numeric, String, Text, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker


Base = declarative_base()


class AgentRun(Base):
    __tablename__ = "agent_runs"

    id = Column(Integer, primary_key=True)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    input_data_hash = Column(String)
    prompt_version = Column(String)
    model_used = Column(String)
    output_markdown = Column(Text)
    citations = Column(JSON)
    accuracy_score = Column(Numeric)
    requires_human_review = Column(Boolean)
    metadata = Column(JSON)
    kpi_snapshot_id = Column(Integer)


def _hash_input(payload: Dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()


# Example: Main agent orchestrator using LangChain/ReAct pattern
class AgentOrchestrator:
    def __init__(self, spec_path: str, db_url: Optional[str] = None):
        with open(spec_path, "r") as f:
            self.spec = yaml.safe_load(f)
        self.db_url = db_url or os.getenv("DATABASE_URL")
        self.engine = create_engine(self.db_url) if self.db_url else None
        self.session_local = sessionmaker(bind=self.engine) if self.engine else None
        # Load tools, prompts, etc.

    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        # Placeholder for agent reasoning logic
        # Integrate with tools, prompts, and input data
        start_time = datetime.now(timezone.utc)
        output = {
            "output": "Agent reasoning result",
            "input": input_data,
            "prompt_version": self.spec.get("version", "draft"),
            "model_used": self.spec.get("model", "gpt-4.1"),
            "citations": self.spec.get("citations", []),
            "accuracy_score": None,
            "requires_human_review": False,
        }
        completed_at = datetime.now(timezone.utc)
        self._log_agent_run(start_time, completed_at, input_data, output)
        return output

    def _log_agent_run(
        self,
        started_at: datetime,
        completed_at: datetime,
        input_data: Dict[str, Any],
        output: Dict[str, Any],
    ) -> None:
        if not self.session_local:
            return

        record = AgentRun(
            started_at=started_at,
            completed_at=completed_at,
            input_data_hash=_hash_input(input_data),
            prompt_version=output.get("prompt_version"),
            model_used=output.get("model_used"),
            output_markdown=output.get("output"),
            citations=output.get("citations", []),
            accuracy_score=output.get("accuracy_score"),
            requires_human_review=output.get("requires_human_review", False),
            metadata={"input": input_data},
            kpi_snapshot_id=output.get("kpi_snapshot_id"),
        )

        with self.session_local() as session:
            session.add(record)
            session.commit()


# Usage example:
# orchestrator = AgentOrchestrator('config/agents/specs/risk_agent.yaml')
# result = orchestrator.run({"kpi": "par_90", "value": 3.2})
