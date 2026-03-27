"""Tests for the contracts module — types and report_schema."""

from __future__ import annotations

from datetime import date, datetime


from backend.src.contracts.types import RunId, MetricId, AgentId
from backend.src.contracts.report_schema import (
    ReportSection,
    ExecutiveBrief,
    InvestorSummary,
    LenderPack,
    WeeklyOperatingMemo,
)


class TestContractTypes:
    def test_type_aliases_are_str(self):
        # Type aliases should accept string values
        run_id: RunId = "run-001"
        metric_id: MetricId = "par_30"
        agent_id: AgentId = "risk_agent"
        assert isinstance(run_id, str)
        assert isinstance(metric_id, str)
        assert isinstance(agent_id, str)


class TestReportSchema:
    def test_report_section_creation(self):
        section = ReportSection(title="Test", body="Content")
        assert section.title == "Test"
        assert section.body == "Content"

    def test_executive_brief_creation(self):
        brief = ExecutiveBrief(
            sections=[ReportSection(title="KPIs", body="All good")],
            generated_at=datetime.now(),
            as_of_date=date.today(),
            business_state="healthy",
        )
        assert len(brief.sections) == 1

    def test_investor_summary_creation(self):
        summary = InvestorSummary(
            sections=[], generated_at=datetime.now(), as_of_date=date.today(),
        )
        assert isinstance(summary.sections, list)

    def test_lender_pack_creation(self):
        pack = LenderPack(
            sections=[], generated_at=datetime.now(), as_of_date=date.today(),
        )
        assert isinstance(pack.sections, list)

    def test_weekly_memo_creation(self):
        memo = WeeklyOperatingMemo(
            sections=[], generated_at=datetime.now(), week_ending=date.today(),
        )
        assert isinstance(memo.sections, list)
