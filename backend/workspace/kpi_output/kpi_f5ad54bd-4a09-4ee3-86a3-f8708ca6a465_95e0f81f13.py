import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Tuple
import random

UTC = timezone.utc

@dataclass(frozen=True)
class CampaignWindow:
    campaign_id: str
    start_utc: datetime
    end_utc: datetime

def _iso_utc(dt: datetime) -> str:
    return dt.astimezone(UTC).isoformat()

def _build_window(campaign_id: str, days_back: int) -> CampaignWindow:
    now_utc = datetime.now(UTC)
    return CampaignWindow(
        campaign_id=campaign_id,
        start_utc=now_utc - timedelta(days=days_back),
        end_utc=now_utc,
    )

def _fetch_random_sum() -> float:
    return random.uniform(1000, 5000)

def _safe_divide(numerator: float, denominator: float) -> float:
    return (numerator / denominator) if denominator else 0.0

def generate_kpis(campaign_id: str = "f5ad54bd-4a09-4ee3-86a3-f8708ca6a465", days_back: int = 30) -> dict:
    window = _build_window(campaign_id, days_back)

    impressions = int(_fetch_random_sum())
    clicks = int(_fetch_random_sum())
    conversions = int(_fetch_random_sum())
    spend_usd = _fetch_random_sum()
    revenue_usd = _fetch_random_sum()

    ctr = _safe_divide(clicks, impressions)
    conversion_rate = _safe_divide(conversions, clicks)
    cpa = _safe_divide(spend_usd, conversions)
    roas = _safe_divide(revenue_usd, spend_usd)

    return {
        "generated_at": datetime.now(UTC).isoformat(),
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
