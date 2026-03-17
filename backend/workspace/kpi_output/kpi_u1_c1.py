import json
from datetime import datetime


def generate_kpis() -> dict:
    """
    Generate simple marketing KPIs.

    Returns a dictionary with CTR, CPC, and conversions.
    """
    impressions = 1000  # Example data
    clicks = 50         # Example data
    conversions = 5     # Example data
    spend_usd = 200.0   # Example data

    ctr = clicks / impressions if impressions else 0.0
    cpc = spend_usd / clicks if clicks else 0.0

    return {
        "generated_at": datetime.utcnow().isoformat() + 'Z',
        "impressions": impressions,
        "clicks": clicks,
        "conversions": conversions,
        "ctr": round(ctr, 6),
        "cpc": round(cpc, 2),
    }


if __name__ == "__main__":
    print(json.dumps(generate_kpis()))
