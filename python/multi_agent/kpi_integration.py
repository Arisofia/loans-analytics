"""
KPI Integration Layer for Multi-Agent System
Connects KPI definitions and registry with agent context and validation.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from python.models.kpi_models import KpiDefinition, KpiRegistry


class KpiValue(BaseModel):
    """Represents a KPI value at a specific point in time."""

    kpi_name: str = Field(..., description="Name of the KPI")
    value: float = Field(..., description="Computed KPI value")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When this value was recorded",
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional context about this value"
    )


class KpiValidationResult(BaseModel):
    """Result of validating a KPI value against its definition."""

    kpi_name: str
    value: float
    is_valid: bool
    validation_message: Optional[str] = None
    breach_type: Optional[str] = None  # "upper_bound", "lower_bound", or None


class KpiAnomaly(BaseModel):
    """Detected anomaly in KPI values."""

    kpi_name: str
    current_value: float
    expected_range: tuple[Optional[float], Optional[float]]
    severity: str  # "critical", "warning", "info"
    description: str
    detected_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class KpiContextProvider:
    """
    Provides KPI context to agents.
    Integrates KPI definitions, current values, and validation logic.
    """

    def __init__(self, kpi_registry: KpiRegistry):
        """
        Initialize with a KPI registry.

        Args:
            kpi_registry: Registry containing KPI definitions
        """
        self.registry = kpi_registry
        self.current_values: Dict[str, KpiValue] = {}

    def update_kpi_value(
        self, kpi_name: str, value: float, metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Update the current value for a KPI.

        Args:
            kpi_name: Name of the KPI to update
            value: New value
            metadata: Optional metadata about this value
        """
        kpi_value = KpiValue(kpi_name=kpi_name, value=value, metadata=metadata or {})
        self.current_values[kpi_name] = kpi_value

    def get_kpi_definition(self, kpi_name: str) -> KpiDefinition:
        """
        Get the definition for a specific KPI.

        Args:
            kpi_name: Name of the KPI

        Returns:
            KpiDefinition object

        Raises:
            KeyError: If KPI not found in registry
        """
        return self.registry.by_name(kpi_name)

    def validate_kpi_value(self, kpi_name: str, value: float) -> KpiValidationResult:
        """
        Validate a KPI value against its definition.

        Args:
            kpi_name: Name of the KPI
            value: Value to validate

        Returns:
            KpiValidationResult with validation status
        """
        try:
            kpi_def = self.get_kpi_definition(kpi_name)
        except KeyError:
            return KpiValidationResult(
                kpi_name=kpi_name,
                value=value,
                is_valid=False,
                validation_message=f"KPI '{kpi_name}' not found in registry",
            )

        # Check validation range if configured
        if kpi_def.validation.validation_range:
            min_val, max_val = kpi_def.validation.validation_range

            # Check lower bound
            if min_val is not None and value < min_val:
                return KpiValidationResult(
                    kpi_name=kpi_name,
                    value=value,
                    is_valid=False,
                    validation_message=f"Value {value} below minimum {min_val}",
                    breach_type="lower_bound",
                )

            # Check upper bound
            if max_val is not None and value > max_val:
                return KpiValidationResult(
                    kpi_name=kpi_name,
                    value=value,
                    is_valid=False,
                    validation_message=f"Value {value} above maximum {max_val}",
                    breach_type="upper_bound",
                )

        # Value is valid
        return KpiValidationResult(
            kpi_name=kpi_name,
            value=value,
            is_valid=True,
            validation_message="Value within acceptable range",
        )

    def detect_anomalies(self, kpi_values: Dict[str, float]) -> List[KpiAnomaly]:
        """
        Detect anomalies across multiple KPI values.

        Args:
            kpi_values: Dictionary of KPI names to current values

        Returns:
            List of detected anomalies
        """
        anomalies: List[KpiAnomaly] = []

        for kpi_name, value in kpi_values.items():
            validation_result = self.validate_kpi_value(kpi_name, value)

            if not validation_result.is_valid:
                try:
                    kpi_def = self.get_kpi_definition(kpi_name)
                    expected_range = kpi_def.validation.validation_range or (None, None)

                    # Determine severity based on breach magnitude
                    severity = self._determine_severity(
                        value, expected_range, validation_result.breach_type
                    )

                    anomaly = KpiAnomaly(
                        kpi_name=kpi_name,
                        current_value=value,
                        expected_range=expected_range,
                        severity=severity,
                        description=validation_result.validation_message
                        or "Value outside acceptable range",
                    )
                    anomalies.append(anomaly)

                except KeyError:
                    # KPI not in registry, skip
                    continue

        return anomalies

    def _determine_severity(
        self,
        value: float,
        expected_range: tuple[Optional[float], Optional[float]],
        breach_type: Optional[str],
    ) -> str:
        """
        Determine severity of a KPI breach.

        Args:
            value: Current value
            expected_range: Expected min/max range
            breach_type: Type of breach (upper_bound, lower_bound)

        Returns:
            Severity level: "critical", "warning", or "info"
        """
        min_val, max_val = expected_range

        if breach_type == "upper_bound" and max_val is not None:
            # Calculate percentage over max
            pct_over = ((value - max_val) / max_val) * 100
            if pct_over > 20:
                return "critical"
            if pct_over > 10:
                return "warning"
            return "info"

        if breach_type == "lower_bound" and min_val is not None:
            # Calculate percentage under min
            pct_under = ((min_val - value) / min_val) * 100
            if pct_under > 20:
                return "critical"
            if pct_under > 10:
                return "warning"
            return "info"

        return "warning"

    def get_kpi_context_for_agent(self, kpi_names: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Generate KPI context suitable for passing to agents.

        Args:
            kpi_names: Specific KPIs to include, or None for all

        Returns:
            Dictionary with KPI definitions, current values, and validation status
        """
        if kpi_names is None:
            kpi_names = [kpi.name for kpi in self.registry.kpis]

        context: Dict[str, Any] = {
            "kpis": {},
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total_kpis": len(kpi_names),
        }

        for kpi_name in kpi_names:
            try:
                kpi_def = self.get_kpi_definition(kpi_name)
                current_value = self.current_values.get(kpi_name)

                kpi_context: Dict[str, Any] = {
                    "definition": {
                        "name": kpi_def.name,
                        "formula": kpi_def.formula,
                        "source_table": kpi_def.source_table,
                        "description": kpi_def.description,
                    }
                }

                if current_value:
                    validation = self.validate_kpi_value(kpi_name, current_value.value)
                    kpi_context["current_value"] = current_value.value
                    kpi_context["last_updated"] = current_value.timestamp.isoformat()
                    kpi_context["is_valid"] = validation.is_valid
                    kpi_context["validation_message"] = validation.validation_message

                context["kpis"][kpi_name] = kpi_context

            except KeyError:
                # KPI not found, skip
                continue

        return context

    def format_kpi_summary(self, kpi_names: Optional[List[str]] = None) -> str:
        """
        Generate a human-readable summary of KPI status.

        Args:
            kpi_names: Specific KPIs to include, or None for all

        Returns:
            Formatted string with KPI summary
        """
        context = self.get_kpi_context_for_agent(kpi_names)
        lines = ["📊 KPI Summary", "=" * 50, ""]

        for kpi_name, kpi_data in context["kpis"].items():
            definition = kpi_data["definition"]
            lines.append(f"**{kpi_name}**")
            lines.append(f"  Formula: {definition['formula']}")
            lines.append(f"  Source: {definition['source_table']}")

            if "current_value" in kpi_data:
                status_icon = "✅" if kpi_data["is_valid"] else "❌"
                lines.append(f"  Current Value: {kpi_data['current_value']} {status_icon}")
                lines.append(f"  Status: {kpi_data['validation_message']}")
            else:
                lines.append("  Current Value: Not available")

            lines.append("")

        return "\n".join(lines)
