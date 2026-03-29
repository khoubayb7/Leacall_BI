"""
KPI Payload Schema Definition

This module defines the canonical JSON contract for all KPI payloads.
Frontend and backend use this schema to ensure data shape consistency.

Design principles:
- Required fields are mandatory in all KPI outputs
- Optional sections allow flexibility for future extensions
- Validation happens automatically via Pydantic models
- Examples in tests and docstrings serve as documentation

Structure:
- Metrics/Cards: Key performance indicators (required)
- Sections: Optional groupings (tables, notes, summaries)
- Charts: Optional visualizations (line, bar, pie, etc.)
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class MetricCard(BaseModel):
    """
    A single KPI metric card.

    Example: revenue_total, conversion_rate, click_through_rate
    """

    label: str = Field(
        ...,
        description="Human-readable label for this metric",
        examples=["Total Revenue", "Conversion Rate %"],
    )
    value: float | int | str = Field(
        ...,
        description="Metric value (numeric or string)",
        examples=[15000.50, 75, "12.5%"],
    )
    unit: Optional[str] = Field(
        None,
        description="Unit of measurement (USD, %, count, etc.)",
        examples=["USD", "%", "count"],
    )
    trend: Optional[str] = Field(
        None,
        description="Trend indicator: up, down, or neutral",
        choices=["up", "down", "neutral"],
    )
    trend_value: Optional[float | str] = Field(
        None,
        description="Trend magnitude (e.g. +10% or -5)",
        examples=["+10.5", "-5"],
    )

    @field_validator("trend")
    @classmethod
    def validate_trend(cls, v):
        if v is not None and v not in ("up", "down", "neutral"):
            raise ValueError('trend must be "up", "down", or "neutral"')
        return v


class ChartSeries(BaseModel):
    """One data series for a chart."""

    name: str = Field(..., description="Series name", examples=["2024 Revenue"])
    data: List[float | int] = Field(..., description="Data points")
    color: Optional[str] = Field(None, description="Hex color", examples=["#FF6B6B"])


class Chart(BaseModel):
    """Visualization (line, bar, pie, etc.)."""

    title: str = Field(..., description="Chart title", examples=["Revenue Trend"])
    chart_type: str = Field(
        ...,
        description="Chart type: line, bar, pie, area",
        choices=["line", "bar", "pie", "area", "scatter", "bubble"],
    )
    series: List[ChartSeries] = Field(
        ...,
        description="Data series",
        min_items=1,
    )
    labels: Optional[List[str]] = Field(
        None,
        description="X-axis labels",
        examples=[["Jan", "Feb", "Mar"]],
    )
    y_axis_label: Optional[str] = Field(None, description="Y-axis label")
    x_axis_label: Optional[str] = Field(None, description="X-axis label")


class TableRow(BaseModel):
    """One row in a data table."""

    cells: Dict[str, Any] = Field(
        ...,
        description="Column name -> cell value",
        examples=[{"campaign": "Campaign A", "revenue": 5000, "roas": 2.5}],
    )


class Section(BaseModel):
    """Optional grouping: tables, notes, summaries."""

    title: str = Field(..., description="Section title", examples=["Top Campaigns"])
    section_type: str = Field(
        ...,
        description="Section type: table, note, summary, text",
        choices=["table", "note", "summary", "text"],
    )
    content: Optional[str] = Field(
        None,
        description="Text content (for note/summary/text sections)",
        examples=["Q4 was strong. Focus on ROAS optimization next quarter."],
    )
    rows: Optional[List[TableRow]] = Field(None, description="Table rows")
    columns: Optional[List[str]] = Field(
        None,
        description="Table column headers",
        examples=[["Campaign", "Revenue", "ROAS"]],
    )


class KPIPayload(BaseModel):
    """
    Canonical KPI result payload.

    All generated KPI files must emit JSON matching this schema.
    Backend validates and saves; frontend renders with confidence.

    Example:
    {
        "campaign_id": "cmp-001",
        "campaign_name": "Spring Sale 2024",
        "campaign_type": "leacall_campaign",
        "generated_at": "2024-03-29T14:30:00Z",
        "metrics": [
            {
                "label": "Total Revenue",
                "value": 15000.50,
                "unit": "USD",
                "trend": "up",
                "trend_value": "+12.5%"
            },
            {
                "label": "Conversion Rate",
                "value": 3.25,
                "unit": "%",
                "trend": "neutral"
            }
        ],
        "sections": [
            {
                "title": "Campaign Summary",
                "section_type": "note",
                "content": "Strong Q1 performance..."
            }
        ],
        "charts": [
            {
                "title": "Revenue Trend",
                "chart_type": "line",
                "series": [
                    {"name": "2024", "data": [1000, 1200, 1500]}
                ],
                "labels": ["Week 1", "Week 2", "Week 3"]
            }
        ]
    }
    """

    # Required fields
    campaign_id: str = Field(
        ...,
        description="Campaign identifier from datasource",
        examples=["cmp-001", "google_ads_campaign_123"],
    )
    campaign_name: str = Field(
        ...,
        description="Human-readable campaign name",
        examples=["Spring Sale 2024", "Q1 Marketing Push"],
    )
    campaign_type: str = Field(
        ...,
        description="Campaign type (leacall_campaign, google_ads, etc.)",
        examples=["leacall_campaign", "google_ads", "facebook_ads"],
    )
    generated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="ISO timestamp when KPI was generated",
    )
    metrics: List[MetricCard] = Field(
        ...,
        description="Core KPI metrics (required, at least 1)",
        min_items=1,
    )

    # Optional fields for extensibility
    sections: Optional[List[Section]] = Field(
        None,
        description="Optional groupings: tables, notes, summaries",
    )
    charts: Optional[List[Chart]] = Field(
        None,
        description="Optional visualizations",
    )
    metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional unstructured data for debug/audit",
        examples=[{"source": "leacall_api", "records_processed": 5000}],
    )

    @field_validator("generated_at", mode="before")
    @classmethod
    def parse_datetime(cls, v):
        if isinstance(v, str):
            try:
                return datetime.fromisoformat(v.replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                raise ValueError("generated_at must be ISO format string or datetime")
        return v


def validate_kpi_payload(data: dict) -> tuple[bool, str, Optional[KPIPayload]]:
    """
    Validate a KPI payload against the schema.

    Returns:
        (is_valid, error_message, parsed_payload)
    """
    try:
        payload = KPIPayload(**data)
        return True, "", payload
    except Exception as exc:
        return False, str(exc), None
