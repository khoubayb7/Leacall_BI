import json
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass

@dataclass(frozen=True)
class CampaignWindow:
    campaign_id: str
    start_utc: datetime
    end_utc: datetime

UTC = timezone.utc


def _iso_utc(dt: datetime) -> str:
    return dt.astimezone(UTC).isoformat()


def _fetch_sum(field: str) -> float:
    # Placeholder for fetching sum from a data source
    return 100.0


def _safe_divide(numerator: float, denominator: float) -> float:
    return (numerator / denominator) if denominator else 0.0


def _build_window(campaign_id: str, days_back: int) -> CampaignWindow:
    now_utc = datetime.now(UTC)
    return CampaignWindow(
        campaign_id=campaign_id,
        start_utc=now_utc - timedelta(days=days_back),
        end_utc=now_utc,
    )


def generate_kpis(campaign_id: str = "077ed469-fbb3-4fe8-9e09-86f348ec82cc", days_back: int = 30) -> dict:
    window = _build_window(campaign_id, days_back)

    impressions = int(_fetch_sum("impressions"))
    clicks = int(_fetch_sum("clicks"))
    conversions = int(_fetch_sum("conversions"))
    spend_usd = _fetch_sum("spend_usd")
    revenue_usd = _fetch_sum("revenue_usd")

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
