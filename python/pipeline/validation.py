import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional

import pandas as pd


@dataclass
class DataQualityReport:
    """Structured data quality audit report."""

    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    status: str = "passed"
    score: float = 100.0
    total_rows: int = 0
    missing_columns: List[str] = field(default_factory=list)
    type_errors: List[str] = field(default_factory=list)
    null_counts: Dict[str, int] = field(default_factory=dict)
    summary: Dict[str, Any] = field(default_factory=dict)

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2)

    def to_markdown(self) -> str:
        lines = [
            "# DATA QUALITY REPORT",
            f"**Status**: {'🟢 PASSED' if self.status == 'passed' else '🔴 FAILED'}",
            f"**Score**: {self.score}%",
            f"**Timestamp**: {self.timestamp}",
            f"**Total Rows**: {self.total_rows}",
            "",
        ]
        if self.missing_columns:
            lines.append("## ❌ Missing Columns")
            for col in self.missing_columns:
                lines.append(f"- {col}")
            lines.append("")

        if self.type_errors:
            lines.append("## ⚠️ Type Errors")
            for err in self.type_errors:
                lines.append(f"- {err}")
            lines.append("")

        if self.null_counts:
            lines.append("## 🔍 Null Value Analysis")
            for col, count in self.null_counts.items():
                if count > 0:
                    lines.append(f"- **{col}**: {count} nulls")
            lines.append("")

        return "\n".join(lines)


class DataQualityReporter:
    """Phase 5: Automated data quality analysis and reporting."""

    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.report = DataQualityReport(total_rows=len(df))

    def run_audit(
        self,
        required_columns: Optional[Iterable[str]] = None,
        numeric_columns: Optional[Iterable[str]] = None,
        date_columns: Optional[Iterable[str]] = None,
    ) -> DataQualityReport:
        """Execute full quality audit and return the report."""
        cols_lower = {str(c).lower(): c for c in self.df.columns}

        # 1. Check required columns
        if required_columns:
            for col in required_columns:
                if col.lower() not in cols_lower:
                    self.report.missing_columns.append(col)

        # 2. Check nulls for important columns
        check_cols = list(required_columns or []) + list(numeric_columns or [])
        for col in set(check_cols):
            resolved = cols_lower.get(col.lower())
            if resolved:
                null_count = self.df[resolved].isnull().sum()
                self.report.null_counts[col] = int(null_count)

        # 3. Type validation
        if numeric_columns:
            for col in numeric_columns:
                resolved = cols_lower.get(col.lower())
                if resolved:
                    original_nulls = self.df[resolved].isnull().sum()
                    coerced = pd.to_numeric(self.df[resolved], errors="coerce")
                    coerced_nulls = coerced.isnull().sum()
                    if coerced_nulls > original_nulls:
                        self.report.type_errors.append(f"Column '{col}' contains non-numeric values")

        if date_columns:
            for col in date_columns:
                resolved = cols_lower.get(col.lower())
                if resolved:
                    original_nulls = self.df[resolved].isnull().sum()
                    coerced = pd.to_datetime(self.df[resolved], errors="coerce")
                    coerced_nulls = coerced.isnull().sum()
                    if coerced_nulls > original_nulls:
                        self.report.type_errors.append(f"Column '{col}' contains invalid date values")

        # 4. Final scoring
        deductions = (
            (len(self.report.missing_columns) * 20)
            + (len(self.report.type_errors) * 10)
            + (sum(1 for c, n in self.report.null_counts.items() if n > 0) * 2)
        )
        self.report.score = max(0.0, 100.0 - deductions)
        if self.report.missing_columns or self.report.score < 70:
            self.report.status = "failed"

        return self.report


def validate_dataframe(
    df: pd.DataFrame,
    required_columns: Optional[Iterable[str]] = None,
    numeric_columns: Optional[Iterable[str]] = None,
    date_columns: Optional[Iterable[str]] = None,
) -> None:
    """Basic validation helper used by the ingestion pipeline.

    Maintains backward compatibility while leveraging the new reporter.
    """
    reporter = DataQualityReporter(df)
    report = reporter.run_audit(required_columns, numeric_columns, date_columns)

    if report.missing_columns:
        raise ValueError(f"Missing required columns: {report.missing_columns}")

    if report.type_errors:
        raise ValueError(f"Type validation errors: {report.type_errors}")
