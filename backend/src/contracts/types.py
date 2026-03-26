"""Shared type aliases for the Loans Analytics platform.

Centralises commonly used domain identifiers so that downstream modules
import typed aliases rather than raw ``str`` everywhere.
"""

from __future__ import annotations

from typing import Dict, Any

# ── Domain identifiers ──────────────────────────────────────────────────
RunId = str
MetricId = str
AgentId = str
CustomerId = str
LoanId = str
CampaignId = str
LeadId = str
CollectorId = str
SegmentLabel = str

# ── Payload containers ──────────────────────────────────────────────────
MartBundle = Dict[str, Any]
MetricBundle = Dict[str, Any]
FeatureBundle = Dict[str, Any]
QualityResult = Dict[str, Any]
ScenarioBundle = Dict[str, Any]
AgentOutputBundle = Dict[str, Any]
