import json
from datetime import datetime, timezone


def generate_kpis():
    return {
        "campaign_id": 'f5ad54bd-4a09-4ee3-86a3-f8708ca6a465',
        "campaign_name": 'Kacicall Campaign',
        "campaign_type": 'other',
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": "fallback_template",
    }


if __name__ == "__main__":
    print(json.dumps(generate_kpis()))
