import json
import os
from collections import Counter
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Iterable, Optional

UTC = timezone.utc


def load_dataset(dataset_file_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load KPI input dataset built from ETL records.

    Expected shape:
    {
      "campaign_id": "...",
      "campaign_name": "...",
      "records": [ { ... dynamic fields ... } ]
    }
    """

    target = dataset_file_path or os.getenv("KPI_DATASET_FILE", "")
    if not target:
        return {
            "campaign_id": "campaign_001",
            "campaign_name": "Demo Campaign",
            "records": [],
            "columns": [],
        }

    with open(target, "r", encoding="utf-8") as fp:
        payload = json.load(fp)
    if not isinstance(payload, dict):
        return {"campaign_id": "campaign_001", "campaign_name": "Unknown", "records": []}
    return payload


def _safe_divide(numerator: float, denominator: float) -> float:
    return (numerator / denominator) if denominator else 0.0


def _to_float(value: Any, default: float = 0.0) -> float:
    if value is None:
        return default
    if isinstance(value, bool):
        return float(value)
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip()
    if not text:
        return default
    try:
        return float(text.replace(",", "."))
    except ValueError:
        return default


def _to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    text = str(value).strip().lower()
    return text in {"1", "true", "yes", "y", "ok", "success", "connected", "converted"}


def _parse_datetime(value: Any) -> Optional[datetime]:
    if value in (None, ""):
        return None
    if isinstance(value, datetime):
        return value.astimezone(UTC) if value.tzinfo else value.replace(tzinfo=UTC)
    text = str(value).strip()
    if not text:
        return None
    # Support ISO values that end with Z.
    normalized = text.replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    return dt.astimezone(UTC) if dt.tzinfo else dt.replace(tzinfo=UTC)


def _extract(record: Dict[str, Any], keys: Iterable[str], default: Any = None) -> Any:
    normalized = {str(k).lower(): v for k, v in record.items()}
    for key in keys:
        k = str(key).lower()
        if k in normalized:
            return normalized[k]

    nested = record.get("normalized_fields")
    if isinstance(nested, dict):
        normalized_nested = {str(k).lower(): v for k, v in nested.items()}
        for key in keys:
            k = str(key).lower()
            if k in normalized_nested:
                return normalized_nested[k]
    return default


def _is_connected(record: Dict[str, Any]) -> bool:
    explicit = _extract(record, ["is_connected", "connected", "call_connected"], None)
    if explicit is not None:
        return _to_bool(explicit)

    status_text = str(_extract(record, ["status", "call_status", "last_attempt_outcome"], "")).lower()
    success_tokens = ("connected", "answered", "success", "completed")
    return any(token in status_text for token in success_tokens)


def _is_converted(record: Dict[str, Any]) -> bool:
    explicit = _extract(record, ["is_converted", "converted", "lead_converted"], None)
    if explicit is not None:
        return _to_bool(explicit)

    outcome_text = str(_extract(record, ["outcome", "conversion_status", "status"], "")).lower()
    return any(token in outcome_text for token in ("converted", "sale", "won"))


def _window_filter(records: Iterable[Dict[str, Any]], campaign_id: str, days_back: int) -> list[Dict[str, Any]]:
    now_utc = datetime.now(tz=UTC)
    start_utc = now_utc - timedelta(days=days_back)
    filtered: list[Dict[str, Any]] = []

    for record in records:
        row_campaign_id = str(_extract(record, ["campaign_id"], "")).strip()
        if campaign_id and row_campaign_id and row_campaign_id != campaign_id:
            continue

        call_time = _parse_datetime(
            _extract(
                record,
                [
                    "call_timestamp",
                    "timestamp",
                    "created_at",
                    "updated_at",
                    "call_time",
                    "last_attempt_at",
                ],
            )
        )
        if call_time is not None and not (start_utc <= call_time < now_utc):
            continue
        filtered.append(record)
    return filtered


def generate_kpis(campaign_id: str = "campaign_001", days_back: int = 30, dataset_file_path: Optional[str] = None) -> Dict[str, Any]:
    dataset = load_dataset(dataset_file_path)
    dataset_campaign_id = str(dataset.get("campaign_id") or "").strip()
    effective_campaign_id = campaign_id or dataset_campaign_id or "campaign_001"
    campaign_name = str(dataset.get("campaign_name") or effective_campaign_id)

    records = dataset.get("records", [])
    if not isinstance(records, list):
        records = []
    scoped_records = _window_filter(records, effective_campaign_id, days_back)

    total_calls = len(scoped_records)
    connected_calls = sum(1 for row in scoped_records if _is_connected(row))
    converted_leads = sum(1 for row in scoped_records if _is_converted(row))

    durations = [
        _to_float(_extract(row, ["duration", "call_duration", "duration_seconds", "talk_duration"]), 0.0)
        for row in scoped_records
    ]
    positive_durations = [value for value in durations if value > 0]

    spend_total = sum(
        _to_float(
            _extract(
                row,
                ["campaign_cost", "cost", "total_cost", "spend", "billing_amount"],
                0.0,
            ),
            0.0,
        )
        for row in scoped_records
    )
    revenue_total = sum(
        _to_float(_extract(row, ["revenue", "campaign_revenue", "amount_won", "sale_amount"], 0.0), 0.0)
        for row in scoped_records
    )
    generated_leads = sum(
        1
        for row in scoped_records
        if _to_bool(_extract(row, ["is_lead", "lead_generated", "generated_lead"], False))
    )
    if generated_leads == 0:
        generated_leads = converted_leads

    sentiments = [
        _to_float(_extract(row, ["sentiment_score", "sentiment", "avg_sentiment"], 0.0), 0.0)
        for row in scoped_records
    ]
    sentiments = [value for value in sentiments if -1.0 <= value <= 1.0]
    positive_sentiments = [value for value in sentiments if value > 0.3]

    agent_talk_total = sum(
        _to_float(_extract(row, ["agent_talk_time", "agent_speaking_time", "agent_duration"], 0.0), 0.0)
        for row in scoped_records
    )
    client_talk_total = sum(
        _to_float(_extract(row, ["client_talk_time", "customer_talk_time", "listen_time"], 0.0), 0.0)
        for row in scoped_records
    )

    objection_counter: Counter[str] = Counter()
    for row in scoped_records:
        objections = _extract(row, ["objections", "top_objections", "nlp_objections"], None)
        if isinstance(objections, list):
            values = objections
        elif isinstance(objections, str):
            values = [piece.strip() for piece in objections.split(",") if piece.strip()]
        else:
            values = []
        objection_counter.update(str(item).strip().lower() for item in values if str(item).strip())

    time_buckets: Dict[str, Dict[str, int]] = {}
    for row in scoped_records:
        ts = _parse_datetime(_extract(row, ["call_timestamp", "timestamp", "created_at", "last_attempt_at"], None))
        if ts is None:
            continue
        day_key = ts.strftime("%A")
        hour_key = f"{ts.hour:02d}:00"

        bucket = time_buckets.setdefault(day_key, {})
        bucket.setdefault(hour_key, 0)
        if _is_connected(row):
            bucket[hour_key] += 1

    call_success_rate = _safe_divide(connected_calls * 100.0, total_calls)
    conversion_rate = _safe_divide(converted_leads * 100.0, total_calls)
    avg_call_duration = _safe_divide(sum(positive_durations), len(positive_durations))
    cost_per_lead = _safe_divide(spend_total, generated_leads)
    campaign_roi = _safe_divide((revenue_total - spend_total) * 100.0, spend_total)
    average_sentiment_score = _safe_divide(sum(sentiments), len(sentiments))
    positive_sentiment_rate = _safe_divide(len(positive_sentiments) * 100.0, len(sentiments))
    talk_to_listen_ratio = _safe_divide(agent_talk_total, client_talk_total)

    return {
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "campaign_id": effective_campaign_id,
        "campaign_name": campaign_name,
        "days_back": int(days_back),
        "records_in_scope": total_calls,
        "axe_1_performance_campagne_client": {
            "total_calls_made": total_calls,
            "call_success_rate_pct": round(call_success_rate, 2),
            "conversion_rate_pct": round(conversion_rate, 2),
            "average_call_duration_seconds": round(avg_call_duration, 2),
            "cost_per_lead": round(cost_per_lead, 2),
            "campaign_roi_pct": round(campaign_roi, 2),
            "components": {
                "connected_calls": connected_calls,
                "converted_leads": converted_leads,
                "generated_leads": generated_leads,
                "campaign_cost_total": round(spend_total, 2),
                "campaign_revenue_total": round(revenue_total, 2),
            },
        },
        "axe_2_qualite_interactions_client": {
            "average_sentiment_score": round(average_sentiment_score, 4),
            "positive_sentiment_rate_pct": round(positive_sentiment_rate, 2),
            "talk_to_listen_ratio": round(talk_to_listen_ratio, 4),
            "top_objections": [
                {"objection": key, "count": count}
                for key, count in objection_counter.most_common(5)
            ],
            "lead_response_rate_by_time": time_buckets,
        },
    }


if __name__ == "__main__":
    print(json.dumps(generate_kpis(), ensure_ascii=False))
