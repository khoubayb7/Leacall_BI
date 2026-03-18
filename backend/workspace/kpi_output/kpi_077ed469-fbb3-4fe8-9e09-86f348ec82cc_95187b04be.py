import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

@dataclass(frozen=True)
class CampaignWindow:
    campaign_id: str
    start_utc: datetime
    end_utc: datetime


def _iso_utc(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat()


def _build_window(campaign_id: str, days_back: int) -> CampaignWindow:
    now_utc = datetime.now(timezone.utc)
    return CampaignWindow(
        campaign_id=campaign_id,
        start_utc=now_utc - timedelta(days=days_back),
        end_utc=now_utc,
    )


def generate_kpis(campaign_id: str = "077ed469-fbb3-4fe8-9e09-86f348ec82cc", days_back: int = 30) -> dict:
    window = _build_window(campaign_id, days_back)

    # Mock data for demonstration purposes
    impressions = 1000
    clicks = 100
    conversions = 10
    spend_usd = 500.0
    revenue_usd = 1500.0

    ctr = clicks / impressions if impressions else 0.0
    conversion_rate = conversions / clicks if clicks else 0.0
    cpa = spend_usd / conversions if conversions else 0.0
    roas = revenue_usd / spend_usd if spend_usd else 0.0

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
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
