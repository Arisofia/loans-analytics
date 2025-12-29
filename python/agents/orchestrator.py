import hashlib
import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import yaml
from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Integer,
    Numeric,
    String,
    Text,
    create_engine,
)
from sqlalchemy.orm import declarative_base, sessionmaker

from python.agents.agent import Agent
from python.agents.llm_provider import MockLLM
from python.agents.tools import registry as global_registry

Base = declarative_base()  # type: ignore[misc]


class AgentRun(Base):  # type: ignore[valid-type,misc]
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
    run_metadata = Column(JSON)
    kpi_snapshot_id = Column(Integer)


def _hash_input(payload: Dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()


class AgentOrchestrator:
    def __init__(self, spec_path: Optional[str] = None, db_url: Optional[str] = None):
        if spec_path:
            with open(spec_path, "r") as f:
                self.spec = yaml.safe_load(f)
        else:
            self.spec = {}
            
        self.db_url = db_url or os.getenv("DATABASE_URL")
        self.engine = create_engine(self.db_url) if self.db_url else None
        self.session_local = sessionmaker(bind=self.engine) if self.engine else None
        
        # Default LLM provider (Mock for now)
        self.llm = MockLLM()
        self.registry = global_registry

    def run(self, input_data: Dict[str, Any], agent_config: Optional[Dict[str, str]] = None, max_retries: int = 3) -> Dict[str, Any]:
        start_time = datetime.now(timezone.utc)
        
        # Configure the agent
        name = agent_config.get("name", "DefaultAgent") if agent_config else "DefaultAgent"
        role = agent_config.get("role", "General Assistant") if agent_config else "General Assistant"
        goal = agent_config.get("goal", "Help the user with their request") if agent_config else "Help the user with their request"
        
        agent = Agent(
            name=name,
            role=role,
            goal=goal,
            llm=self.llm,
            registry=self.registry
        )
        
        user_query = input_data.get("query", str(input_data))
        
        agent_output = "Error: Failed to generate output."
        for attempt in range(max_retries):
            try:
                agent_output = agent.run(user_query)
                if not agent_output.startswith("Error:"):
                    break
            except Exception as e:
                print(f"[Orchestrator] Attempt {attempt + 1} failed for {name}: {str(e)}")
        
        output = {
            "output": agent_output,
            "input": input_data,
            "prompt_version": self.spec.get("version", "v2.0"),
            "model_used": "mock-llm",
            "citations": [],
            "accuracy_score": None,
            "requires_human_review": agent_output.startswith("Error:"),
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
        session_factory = self.session_local
        if session_factory is None:
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
            run_metadata={"input": input_data},
            kpi_snapshot_id=output.get("kpi_snapshot_id"),
        )

        with session_factory() as session:
            session.add(record)
            session.commit()


# Usage example:
# orchestrator = AgentOrchestrator('config/agents/specs/risk_agent.yaml')
# result = orchestrator.run({"kpi": "par_90", "value": 3.2})
