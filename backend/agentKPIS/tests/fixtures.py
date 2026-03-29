"""
Test fixtures for KPI payload validation.

These are example payloads that demonstrate valid and invalid KPI structures.
Used in schema tests and as documentation for frontend/backend developers.
"""

from datetime import datetime

# Valid minimal payload
VALID_MINIMAL_KPI = {
    "campaign_id": "cmp-001",
    "campaign_name": "Q1 Campaign",
    "campaign_type": "leacall_campaign",
    "generated_at": datetime.utcnow().isoformat(),
    "metrics": [
        {
            "label": "Total Revenue",
            "value": 15000.50,
            "unit": "USD",
        }
    ],
}

# Valid full payload with sections and charts
VALID_FULL_KPI = {
    "campaign_id": "cmp-001",
    "campaign_name": "Spring Sale 2024",
    "campaign_type": "leacall_campaign",
    "generated_at": datetime.utcnow().isoformat(),
    "metrics": [
        {
            "label": "Total Revenue",
            "value": 15000.50,
            "unit": "USD",
            "trend": "up",
            "trend_value": "+12.5%",
        },
        {
            "label": "Conversion Rate",
            "value": 3.25,
            "unit": "%",
            "trend": "neutral",
        },
        {
            "label": "Click Through Rate",
            "value": 2.1,
            "unit": "%",
            "trend": "down",
            "trend_value": "-0.5%",
        },
    ],
    "sections": [
        {
            "title": "Campaign Summary",
            "section_type": "note",
            "content": "Strong Q1 performance. Focus on ROAS optimization next quarter.",
        },
        {
            "title": "Top Performing Channels",
            "section_type": "table",
            "columns": ["Channel", "Revenue", "Conversion %"],
            "rows": [
                {"cells": {"Channel": "Email", "Revenue": 5000, "Conversion %": 4.5}},
                {"cells": {"Channel": "Social", "Revenue": 4000, "Conversion %": 3.2}},
                {"cells": {"Channel": "Organic", "Revenue": 6000, "Conversion %": 2.8}},
            ],
        },
    ],
    "charts": [
        {
            "title": "Revenue Trend",
            "chart_type": "line",
            "series": [
                {"name": "2024", "data": [1000, 1200, 1500, 2000, 2500, 3000], "color": "#4CAF50"}
            ],
            "labels": ["Week 1", "Week 2", "Week 3", "Week 4", "Week 5", "Week 6"],
            "y_axis_label": "Revenue (USD)",
            "x_axis_label": "Week",
        },
        {
            "title": "Channel Distribution",
            "chart_type": "pie",
            "series": [
                {"name": "Revenue Distribution", "data": [5000, 4000, 6000]}
            ],
            "labels": ["Email", "Social", "Organic"],
        },
    ],
    "metadata": {
        "source": "leacall_api",
        "records_processed": 5000,
        "execution_time_seconds": 42,
    },
}

# Invalid: missing required campaign_id
INVALID_MISSING_CAMPAIGN_ID = {
    "campaign_name": "Q1 Campaign",
    "campaign_type": "leacall_campaign",
    "generated_at": datetime.utcnow().isoformat(),
    "metrics": [
        {
            "label": "Total Revenue",
            "value": 15000.50,
        }
    ],
}

# Invalid: no metrics
INVALID_NO_METRICS = {
    "campaign_id": "cmp-001",
    "campaign_name": "Q1 Campaign",
    "campaign_type": "leacall_campaign",
    "generated_at": datetime.utcnow().isoformat(),
    "metrics": [],
}

# Invalid: invalid trend value
INVALID_TREND = {
    "campaign_id": "cmp-001",
    "campaign_name": "Q1 Campaign",
    "campaign_type": "leacall_campaign",
    "generated_at": datetime.utcnow().isoformat(),
    "metrics": [
        {
            "label": "Total Revenue",
            "value": 15000.50,
            "trend": "sideways",  # Invalid: must be up, down, or neutral
        }
    ],
}

# Invalid: metric value missing
INVALID_METRIC_VALUE = {
    "campaign_id": "cmp-001",
    "campaign_name": "Q1 Campaign",
    "campaign_type": "leacall_campaign",
    "generated_at": datetime.utcnow().isoformat(),
    "metrics": [
        {
            "label": "Total Revenue",
            # Missing required "value" field
        }
    ],
}

# Invalid: chart_type not in allowed values
INVALID_CHART_TYPE = {
    "campaign_id": "cmp-001",
    "campaign_name": "Q1 Campaign",
    "campaign_type": "leacall_campaign",
    "generated_at": datetime.utcnow().isoformat(),
    "metrics": [
        {
            "label": "Total Revenue",
            "value": 15000.50,
        }
    ],
    "charts": [
        {
            "title": "Revenue",
            "chart_type": "heatmap",  # Invalid: not in choices
            "series": [
                {"name": "2024", "data": [1000, 2000]}
            ],
        }
    ],
}

# Invalid: section_type not in allowed values
INVALID_SECTION_TYPE = {
    "campaign_id": "cmp-001",
    "campaign_name": "Q1 Campaign",
    "campaign_type": "leacall_campaign",
    "generated_at": datetime.utcnow().isoformat(),
    "metrics": [
        {
            "label": "Total Revenue",
            "value": 15000.50,
        }
    ],
    "sections": [
        {
            "title": "Summary",
            "section_type": "blog_post",  # Invalid: not in choices
            "content": "Lorem ipsum",
        }
    ],
}
