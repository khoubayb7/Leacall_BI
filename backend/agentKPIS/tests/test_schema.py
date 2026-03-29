"""
Tests for KPI payload schema validation.

Validates that generated KPI payloads conform to the contract.
Ensures backend validation and frontend rendering reliability.
"""

from django.test import TestCase

from agentKPIS.schema import (
    Chart,
    ChartSeries,
    KPIPayload,
    MetricCard,
    Section,
    TableRow,
    validate_kpi_payload,
)
from agentKPIS.tests.fixtures import (
    INVALID_CHART_TYPE,
    INVALID_MISSING_CAMPAIGN_ID,
    INVALID_METRIC_VALUE,
    INVALID_NO_METRICS,
    INVALID_SECTION_TYPE,
    INVALID_TREND,
    VALID_FULL_KPI,
    VALID_MINIMAL_KPI,
)


class MetricCardTests(TestCase):
    """Test individual metric card validation."""

    def test_metric_card_minimal_valid(self):
        """Metric with only required fields."""
        metric = MetricCard(
            label="Revenue",
            value=10000,
        )
        self.assertEqual(metric.label, "Revenue")
        self.assertEqual(metric.value, 10000)
        self.assertIsNone(metric.unit)
        self.assertIsNone(metric.trend)

    def test_metric_card_full_valid(self):
        """Metric with all fields including trend."""
        metric = MetricCard(
            label="Conversion Rate",
            value=3.5,
            unit="%",
            trend="up",
            trend_value="+0.5%",
        )
        self.assertEqual(metric.value, 3.5)
        self.assertEqual(metric.unit, "%")
        self.assertEqual(metric.trend, "up")

    def test_metric_card_invalid_trend(self):
        """Reject invalid trend values."""
        with self.assertRaises(ValueError):
            MetricCard(
                label="Revenue",
                value=10000,
                trend="sideways",  # Invalid
            )

    def test_metric_card_missing_label(self):
        """Reject missing label."""
        with self.assertRaises(ValueError):
            MetricCard(value=10000)

    def test_metric_card_missing_value(self):
        """Reject missing value."""
        with self.assertRaises(ValueError):
            MetricCard(label="Revenue")

    def test_metric_card_string_value(self):
        """Allow string values (e.g., 'N/A')."""
        metric = MetricCard(label="Status", value="Active")
        self.assertEqual(metric.value, "Active")


class ChartTests(TestCase):
    """Test chart validation."""

    def test_chart_valid_line(self):
        """Valid line chart."""
        chart = Chart(
            title="Revenue Trend",
            chart_type="line",
            series=[
                ChartSeries(name="2024", data=[1000, 2000, 3000])
            ],
            labels=["Jan", "Feb", "Mar"],
        )
        self.assertEqual(chart.chart_type, "line")
        self.assertEqual(len(chart.series), 1)

    def test_chart_invalid_type(self):
        """Reject invalid chart_type."""
        with self.assertRaises(ValueError):
            Chart(
                title="Chart",
                chart_type="heatmap",  # Not in allowed types
                series=[
                    ChartSeries(name="Data", data=[1, 2, 3])
                ],
            )

    def test_chart_valid_types(self):
        """All valid chart types are accepted."""
        for chart_type in ["line", "bar", "pie", "area", "scatter", "bubble"]:
            chart = Chart(
                title="Test",
                chart_type=chart_type,
                series=[
                    ChartSeries(name="Series", data=[1, 2])
                ],
            )
            self.assertEqual(chart.chart_type, chart_type)

    def test_chart_empty_series_rejected(self):
        """Charts must have at least one series."""
        with self.assertRaises(ValueError):
            Chart(
                title="Empty",
                chart_type="line",
                series=[],  # Invalid: min_items=1
            )


class SectionTests(TestCase):
    """Test section (table, note, summary) validation."""

    def test_section_note_valid(self):
        """Valid note section."""
        section = Section(
            title="Summary",
            section_type="note",
            content="Lorem ipsum dolor.",
        )
        self.assertEqual(section.section_type, "note")

    def test_section_table_valid(self):
        """Valid table section."""
        section = Section(
            title="Data",
            section_type="table",
            columns=["Name", "Value"],
            rows=[
                TableRow(cells={"Name": "Item A", "Value": 100}),
                TableRow(cells={"Name": "Item B", "Value": 200}),
            ],
        )
        self.assertEqual(len(section.rows), 2)

    def test_section_invalid_type(self):
        """Reject invalid section_type."""
        with self.assertRaises(ValueError):
            Section(
                title="Bad",
                section_type="blog_post",  # Invalid
                content="Text",
            )

    def test_section_valid_types(self):
        """All valid section types are accepted."""
        for section_type in ["table", "note", "summary", "text"]:
            section = Section(
                title="Test",
                section_type=section_type,
                content="Content",
            )
            self.assertEqual(section.section_type, section_type)


class KPIPayloadTests(TestCase):
    """Test complete KPI payload validation."""

    def test_valid_minimal_payload(self):
        """Minimal valid payload with only required fields."""
        is_valid, error_msg, payload = validate_kpi_payload(VALID_MINIMAL_KPI)
        self.assertTrue(is_valid)
        self.assertEqual(error_msg, "")
        self.assertIsNotNone(payload)
        self.assertEqual(payload.campaign_id, "cmp-001")
        self.assertEqual(len(payload.metrics), 1)

    def test_valid_full_payload(self):
        """Full valid payload with sections and charts."""
        is_valid, error_msg, payload = validate_kpi_payload(VALID_FULL_KPI)
        self.assertTrue(is_valid)
        self.assertEqual(error_msg, "")
        self.assertIsNotNone(payload)
        self.assertEqual(len(payload.metrics), 3)
        self.assertEqual(len(payload.sections), 2)
        self.assertEqual(len(payload.charts), 2)

    def test_invalid_missing_campaign_id(self):
        """Reject payload without campaign_id."""
        is_valid, error_msg, payload = validate_kpi_payload(INVALID_MISSING_CAMPAIGN_ID)
        self.assertFalse(is_valid)
        self.assertIn("campaign_id", error_msg.lower())
        self.assertIsNone(payload)

    def test_invalid_no_metrics(self):
        """Reject payload with empty metrics list."""
        is_valid, error_msg, payload = validate_kpi_payload(INVALID_NO_METRICS)
        self.assertFalse(is_valid)
        self.assertIn("metrics", error_msg.lower())
        self.assertIsNone(payload)

    def test_invalid_trend(self):
        """Reject metric with invalid trend."""
        is_valid, error_msg, payload = validate_kpi_payload(INVALID_TREND)
        self.assertFalse(is_valid)
        self.assertIn("trend", error_msg.lower())
        self.assertIsNone(payload)

    def test_invalid_metric_missing_value(self):
        """Reject metric without value."""
        is_valid, error_msg, payload = validate_kpi_payload(INVALID_METRIC_VALUE)
        self.assertFalse(is_valid)
        self.assertIn("value", error_msg.lower())
        self.assertIsNone(payload)

    def test_invalid_chart_type(self):
        """Reject chart with invalid type."""
        is_valid, error_msg, payload = validate_kpi_payload(INVALID_CHART_TYPE)
        self.assertFalse(is_valid)
        self.assertIn("chart_type", error_msg.lower())
        self.assertIsNone(payload)

    def test_invalid_section_type(self):
        """Reject section with invalid type."""
        is_valid, error_msg, payload = validate_kpi_payload(INVALID_SECTION_TYPE)
        self.assertFalse(is_valid)
        self.assertIn("section_type", error_msg.lower())
        self.assertIsNone(payload)

    def test_payload_model_dump_for_serialization(self):
        """Payload can be serialized to dict for JSON response."""
        is_valid, _, payload = validate_kpi_payload(VALID_MINIMAL_KPI)
        self.assertTrue(is_valid)

        serialized = payload.model_dump()
        self.assertIsInstance(serialized, dict)
        self.assertIn("campaign_id", serialized)
        self.assertIn("metrics", serialized)

    def test_all_required_top_level_keys(self):
        """Payload includes all required top-level keys."""
        is_valid, _, payload = validate_kpi_payload(VALID_FULL_KPI)
        self.assertTrue(is_valid)

        required_keys = [
            "campaign_id",
            "campaign_name",
            "campaign_type",
            "generated_at",
            "metrics",
        ]
        for key in required_keys:
            self.assertTrue(hasattr(payload, key))

    def test_optional_sections_present(self):
        """Payload includes optional fields when provided."""
        is_valid, _, payload = validate_kpi_payload(VALID_FULL_KPI)
        self.assertTrue(is_valid)

        self.assertIsNotNone(payload.sections)
        self.assertIsNotNone(payload.charts)
        self.assertIsNotNone(payload.metadata)

    def test_optional_sections_absent(self):
        """Payload works without optional fields."""
        is_valid, _, payload = validate_kpi_payload(VALID_MINIMAL_KPI)
        self.assertTrue(is_valid)

        self.assertIsNone(payload.sections)
        self.assertIsNone(payload.charts)
        self.assertIsNone(payload.metadata)

    def test_invalid_campaign_id_empty_string(self):
        """Empty campaign_id is invalid."""
        data = {
            "campaign_id": "",  # Invalid
            "campaign_name": "Q1",
            "campaign_type": "leacall_campaign",
            "generated_at": "2024-03-29T14:30:00Z",
            "metrics": [{"label": "Revenue", "value": 1000}],
        }
        is_valid, error_msg, _ = validate_kpi_payload(data)
        self.assertFalse(is_valid)

    def test_datetime_parsing_iso_string(self):
        """Datetime can be parsed from ISO string with or without Z."""
        for dt_str in ["2024-03-29T14:30:00Z", "2024-03-29T14:30:00+00:00"]:
            data = {
                "campaign_id": "cmp-001",
                "campaign_name": "Q1",
                "campaign_type": "leacall_campaign",
                "generated_at": dt_str,
                "metrics": [{"label": "Revenue", "value": 1000}],
            }
            is_valid, _, payload = validate_kpi_payload(data)
            self.assertTrue(is_valid)
            self.assertIsNotNone(payload.generated_at)

    def test_numeric_values_int_and_float(self):
        """Metrics accept both int and float values."""
        for value in [1000, 1000.50, 3.25]:
            data = {
                "campaign_id": "cmp-001",
                "campaign_name": "Q1",
                "campaign_type": "leacall_campaign",
                "generated_at": "2024-03-29T14:30:00Z",
                "metrics": [{"label": "Metric", "value": value}],
            }
            is_valid, _, payload = validate_kpi_payload(data)
            self.assertTrue(is_valid)
            self.assertEqual(payload.metrics[0].value, value)


class SchemaDocumentationTests(TestCase):
    """Verify schema serves as documentation."""

    def test_metric_card_has_field_descriptions(self):
        """MetricCard fields have descriptions for documentation."""
        schema = MetricCard.model_json_schema()
        properties = schema.get("properties", {})

        self.assertIn("description", properties.get("label", {}))
        self.assertIn("description", properties.get("value", {}))
        self.assertIn("description", properties.get("unit", {}))

    def test_kpi_payload_has_docstring(self):
        """KPIPayload has comprehensive docstring."""
        self.assertIsNotNone(KPIPayload.__doc__)
        self.assertIn("Example", KPIPayload.__doc__)
        self.assertIn("metrics", KPIPayload.__doc__)

    def test_schema_json_output_for_frontend(self):
        """Schema can be exported as JSON for frontend developers."""
        schema = KPIPayload.model_json_schema()
        self.assertIn("properties", schema)
        self.assertIn("required", schema)
        self.assertIn("campaign_id", schema["properties"])
        self.assertIn("metrics", schema["required"])
