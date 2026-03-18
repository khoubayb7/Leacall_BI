import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable

UTC = timezone.utc


def _safe_divide(numerator: float, denominator: float) -> float:
    return (numerator / denominator) if denominator else 0.0


def _to_number(value: Any, default: float = 0.0) -> float:
    if value is None:
        return default
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)

    text = str(value).strip()
    if not text:
        return default

    text = text.replace(" ", "")
    if "," in text and "." in text:
        text = text.replace(",", "")
    elif "," in text:
        text = text.replace(",", ".")

    text = re.sub(r"[^0-9.\-]", "", text)
    try:
        return float(text)
    except ValueError:
        return default


def _to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on", "won", "closed_won"}


def _first_value(record: Dict[str, Any], keys: Iterable[str], default: Any = None) -> Any:
    for key in keys:
        if key in record and record[key] not in (None, ""):
            return record[key]
    return default


def load_dataset(dataset_file_path: str) -> Dict[str, Any]:
    target = Path(dataset_file_path)
    if not target.exists():
        raise FileNotFoundError(f"Dataset file not found: {target}")
    return json.loads(target.read_text(encoding="utf-8"))


def generate_kpis(dataset_file_path: str) -> Dict[str, Any]:
    dataset = load_dataset(dataset_file_path)
    records = dataset.get("records", []) or []
    latest_run = dataset.get("latest_success_run") or {}

    leads_count = len(records)

    total_attempts = 0.0
    connected_leads = 0
    converted_leads = 0
    qualified_leads = 0
    revenue_total = 0.0

    missing_id_count = 0

    for row in records:
        lead_id = _first_value(row, ["id", "lead_id", "uuid"], default="")
        if str(lead_id).strip() == "":
            missing_id_count += 1

        attempts = _to_number(_first_value(row, ["attempts", "call_attempts", "total_attempts"], default=0))
        total_attempts += attempts

        connected = _to_bool(_first_value(row, ["connected", "is_connected", "answered", "contacted"], default=False))
        if connected:
            connected_leads += 1

        qualified = _to_bool(_first_value(row, ["qualified", "is_qualified"], default=False))
        if qualified:
            qualified_leads += 1

        converted = _to_bool(_first_value(row, ["converted", "is_converted", "sale", "won"], default=False))
        if converted:
            converted_leads += 1

        revenue = _to_number(_first_value(row, ["revenue", "amount", "revenue_usd", "deal_value"], default=0))
        revenue_total += revenue

    avg_attempts_per_lead = _safe_divide(total_attempts, leads_count)
    contact_rate = _safe_divide(connected_leads, leads_count)
    qualification_rate = _safe_divide(qualified_leads, leads_count)
    conversion_rate = _safe_divide(converted_leads, leads_count)
    revenue_per_lead = _safe_divide(revenue_total, leads_count)
    revenue_per_conversion = _safe_divide(revenue_total, converted_leads)

    loaded_count = int(latest_run.get("loaded_count", 0) or 0)
    transformed_count = int(latest_run.get("transformed_count", 0) or 0)
    raw_count = int(latest_run.get("raw_count", 0) or 0)

    load_success_rate = _safe_divide(loaded_count, transformed_count) if transformed_count else 0.0
    transform_success_rate = _safe_divide(transformed_count, raw_count) if raw_count else 0.0

    return {
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "campaign_id": dataset.get("campaign_id", ""),
        "campaign_name": dataset.get("campaign_name", ""),
        "dataset_records_count": leads_count,
        "etl_loaded_count": loaded_count,
        "etl_transformed_count": transformed_count,
        "etl_raw_count": raw_count,
        "transform_success_rate": round(transform_success_rate, 6),
        "load_success_rate": round(load_success_rate, 6),
        "connected_leads": connected_leads,
        "qualified_leads": qualified_leads,
        "converted_leads": converted_leads,
        "total_attempts": round(total_attempts, 2),
        "avg_attempts_per_lead": round(avg_attempts_per_lead, 4),
        "contact_rate": round(contact_rate, 6),
        "qualification_rate": round(qualification_rate, 6),
        "conversion_rate": round(conversion_rate, 6),
        "revenue_total": round(revenue_total, 2),
        "revenue_per_lead": round(revenue_per_lead, 2),
        "revenue_per_conversion": round(revenue_per_conversion, 2),
        "data_quality": {
            "missing_id_count": missing_id_count,
            "records_with_id_rate": round(_safe_divide(leads_count - missing_id_count, leads_count), 6) if leads_count else 0.0,
        },
    }


if __name__ == "__main__":
    dataset_file_path = "C:\\Users\\khoub\\OneDrive\\Bureau\\BI_System\\backend\\workspace\\kpi_output\\datasets\\dataset_077ed469-fbb3-4fe8-9e09-86f348ec82cc_c369b402.json"
    payload = generate_kpis(dataset_file_path=dataset_file_path)
    print(json.dumps(payload, ensure_ascii=False))
