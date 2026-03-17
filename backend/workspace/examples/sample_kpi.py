import json
import os
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Iterable, Tuple, Type

import django
from django.apps import apps
from django.conf import settings
from django.db import models
from django.db.models import Sum
from django.utils import timezone

UTC = timezone.utc


@dataclass(frozen=True)
class CampaignWindow:
    campaign_id: str
    start_utc: datetime
    end_utc: datetime


def _iso_utc(dt: datetime) -> str:
    return dt.astimezone(UTC).isoformat()


def _ensure_django() -> None:
    """
    Initialize Django if the module is executed as a standalone script.
    """

    if settings.configured:
        return

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "etl_project.settings")
    django.setup()


def _get_model(label: str) -> Type[models.Model]:
    try:
        app_label, model_name = label.split(".", 1)
    except ValueError as exc:
        raise RuntimeError(
            f"Invalid model label '{label}'. Use the format 'app_label.ModelName'."
        ) from exc

    try:
        return apps.get_model(app_label, model_name)
    except LookupError as exc:
        raise RuntimeError(
            f"Model '{label}' not found. Update the KPI_*_MODEL env vars to match your "
            "project's app labels and model names."
        ) from exc


def _get_kpi_models() -> Tuple[
    Type[models.Model],
    Type[models.Model],
    Type[models.Model],
    Type[models.Model],
    Type[models.Model],
]:
    """
    Resolve the analytics models from env so this file stays reusable.
    """

    impression_label = os.getenv("KPI_IMPRESSION_MODEL", "analytics.AdImpression")
    click_label = os.getenv("KPI_CLICK_MODEL", "analytics.AdClick")
    conversion_label = os.getenv("KPI_CONVERSION_MODEL", "analytics.AdConversion")
    spend_label = os.getenv("KPI_SPEND_MODEL", "analytics.AdSpend")
    revenue_label = os.getenv("KPI_REVENUE_MODEL", "analytics.AdRevenue")

    return (
        _get_model(impression_label),
        _get_model(click_label),
        _get_model(conversion_label),
        _get_model(spend_label),
        _get_model(revenue_label),
    )


def _fetch_sum(
    model: Type[models.Model],
    field: str,
    window: CampaignWindow,
) -> float:
    aggregated = (
        model.objects.filter(
            campaign_id=window.campaign_id,
            occurred_at__gte=window.start_utc,
            occurred_at__lt=window.end_utc,
        )
        .aggregate(total=Sum(field))
    )
    return float(aggregated["total"] or 0)


def _safe_divide(numerator: float, denominator: float) -> float:
    return (numerator / denominator) if denominator else 0.0


def _build_window(campaign_id: str, days_back: int) -> CampaignWindow:
    now_utc = timezone.now()
    return CampaignWindow(
        campaign_id=campaign_id,
        start_utc=now_utc - timedelta(days=days_back),
        end_utc=now_utc,
    )


def generate_kpis(campaign_id: str = "campaign_001", days_back: int = 30) -> dict:
    """
    Generate KPI metrics for a campaign.

    This reference reads aggregated metrics from a Django ORM-backed database and
    returns a concise KPI payload. Update queries or add KPIs as needed.
    """

    _ensure_django()
    window = _build_window(campaign_id, days_back)
    (
        impression_model,
        click_model,
        conversion_model,
        spend_model,
        revenue_model,
    ) = _get_kpi_models()

    impressions = int(_fetch_sum(impression_model, "impressions", window))
    clicks = int(_fetch_sum(click_model, "clicks", window))
    conversions = int(_fetch_sum(conversion_model, "conversions", window))
    spend_usd = _fetch_sum(spend_model, "spend_usd", window)
    revenue_usd = _fetch_sum(revenue_model, "revenue_usd", window)

    ctr = _safe_divide(clicks, impressions)
    conversion_rate = _safe_divide(conversions, clicks)
    cpa = _safe_divide(spend_usd, conversions)
    roas = _safe_divide(revenue_usd, spend_usd)

    return {
        "generated_at": timezone.now().astimezone(UTC).isoformat(),
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
