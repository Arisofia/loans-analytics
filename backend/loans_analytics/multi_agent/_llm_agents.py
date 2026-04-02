"""Backward-compatibility shim — canonical module is llm_agents.py."""

from .llm_agents import ComplianceAgent, GrowthStrategistAgent, OpsOptimizerAgent, RiskAnalystAgent

__all__ = ["ComplianceAgent", "GrowthStrategistAgent", "OpsOptimizerAgent", "RiskAnalystAgent"]
