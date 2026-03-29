import json
from datetime import datetime, timezone


def _load_dataset():
    with open('C:\\Users\\khoub\\OneDrive\\Bureau\\BI_System\\backend\\workspace\\etl_output\\datasets\\dataset_24_dca5a18a-46fd-4d69-b3a9-46e1fe2b7077.json', "r", encoding="utf-8") as fp:
        return json.load(fp)


def generate_kpis():
    dataset = _load_dataset()
    records = dataset.get("records", [])
    latest_run = dataset.get("latest_success_run") or {}

    return {
        "campaign_id": 'dca5a18a-46fd-4d69-b3a9-46e1fe2b7077',
        "campaign_name": 'yy',
        "campaign_type": 'leacall_campaign',
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "fallback_template",
        "records_count": len(records),
        "latest_loaded_count": latest_run.get("loaded_count", 0),
        "sample_fields": sorted(list(records[0].keys())) if records else [],
    }


if __name__ == "__main__":
    print(json.dumps(generate_kpis()))
