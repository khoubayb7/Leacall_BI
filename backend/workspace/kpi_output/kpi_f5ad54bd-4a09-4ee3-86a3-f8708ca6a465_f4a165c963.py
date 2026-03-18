import json
from dataclasses import dataclass
from datetime import datetime, timedelta
dataclass
class CampaignWindow:
    campaign_id: str
    start_utc: datetime
    end_utc: datetime

def _iso_utc(dt: datetime) -> str:
    return dt.isoformat()

def _fetch_sum(data: list, field: str) -> float:
    return sum(item.get(field, 0) for item in data)

def _safe_divide(numerator: float, denominator: float) -> float:
    return (numerator / denominator) if denominator else 0.0

def _build_window(campaign_id: str, days_back: int) -> CampaignWindow:
    now_utc = datetime.utcnow()
    return CampaignWindow(
        campaign_id=campaign_id,
        start_utc=now_utc - timedelta(days=days_back),
        end_utc=now_utc,
    )
def generate_kpis(campaign_id: str = "f5ad54bd-4a09-4ee3-86a3-f8708ca6a465", days_back: int = 30) -> dict:
    window = _build_window(campaign_id, days_back)
    # Mock data for demonstration purposes
    data = [
        {"impressions": 1000, "clicks": 100, "conversions": 10, "spend_usd": 500, "revenue_usd": 1000},
    ]
    impressions = int(_fetch_sum(data, "impressions"))
    clicks = int(_fetch_sum(data, "clicks"))
    conversions = int(_fetch_sum(data, "conversions"))
    spend_usd = _fetch_sum(data, "spend_usd")
    revenue_usd = _fetch_sum(data, "revenue_usd")
    ctr = _safe_divide(clicks, impressions)
    conversion_rate = _safe_divide(conversions, clicks)
    cpa = _safe_divide(spend_usd, conversions)
    roas = _safe_divide(revenue_usd, spend_usd)
    return {
        "generated_at": datetime.utcnow().isoformat(),
        "window_start": _iso_utc(window.start_utc),
        "window_end": _iso_utc(window.end_utc),
        "campaign_id": campaign_id,
        "impressions": impressions,
        "clicks": clicks,
        "conversions": conversions,
        "spend_usd": round(spend_usd, 2),
        "revenue_usd": round(revenue_usd, 2),
        "ctr": round(ctr, 6),
        "conversion_rate": round(conversion_rate, 6),
        "cpa": round(cpa, 2),
        "roas": round(roas, 4),
    }
if __name__ == "__main__":
    print(json.dumps(generate_kpis()))
