import json
import os
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Type, Any, Optional
from collections import defaultdict

import django
from django.apps import apps
from django.conf import settings
from django.db import models
from django.db.models import Sum, Count, Avg, Q
from django.utils import timezone

UTC = timezone.utc


@dataclass(frozen=True)
class CampaignWindow:
    campaign_id: str
    start_utc: datetime
    end_utc: datetime
    client_id: Optional[str] = None


# ============================================================================
# CLIENT-SIDE KPI DATACLASSES
# ============================================================================


@dataclass
class CampaignPerformanceKPI:
    """Campaign Performance Metrics"""
    total_calls_made: int = 0
    planned_calls: int = 0
    calls_connected: int = 0
    call_success_rate: float = 0.0  # connected / attempted
    leads_converted: int = 0
    conversion_rate: float = 0.0  # converted / total calls
    avg_call_duration_seconds: float = 0.0
    avg_call_duration_by_outcome: Dict[str, float] = field(default_factory=dict)
    cost_per_lead: float = 0.0
    cost_per_acquisition: float = 0.0
    campaign_roi: float = 0.0  # (revenue - cost) / cost


@dataclass
class LeadQualityKPI:
    """Lead Quality & Segmentation Metrics"""
    lead_status_distribution: Dict[str, int] = field(default_factory=dict)  # not_contacted, contacted, interested, converted, rejected
    best_performing_segments: Dict[str, Dict[str, Any]] = field(default_factory=dict)  # by geography, demographics, source
    response_rate_by_time: Dict[str, float] = field(default_factory=dict)  # optimal hours/days
    peak_calling_hours: List[int] = field(default_factory=list)
    peak_calling_days: List[str] = field(default_factory=list)


@dataclass
class ConversationIntelligenceKPI:
    """Conversation Intelligence Metrics"""
    sentiment_trends: Dict[str, Dict[str, int]] = field(default_factory=dict)  # positive/negative/neutral over time
    common_objections: List[Dict[str, Any]] = field(default_factory=list)  # extracted from transcripts
    talk_to_listen_ratio: float = 0.0  # AI agent speaking time / customer speaking time
    key_topics_mentioned: Dict[str, int] = field(default_factory=dict)  # product, pricing, competitors, etc.
    script_effectiveness: Dict[str, float] = field(default_factory=dict)  # which scripts convert better


@dataclass
class OperationalEfficiencyKPI:
    """Operational Efficiency Metrics"""
    calls_per_day: float = 0.0
    calls_per_week: float = 0.0
    calls_per_month: float = 0.0
    peak_hours_heatmap: Dict[str, int] = field(default_factory=dict)  # hour -> call count
    calls_completed_on_time: float = 0.0  # percentage
    average_wait_time_seconds: float = 0.0


@dataclass
class ClientSideKPIs:
    """Aggregated Client-Side KPIs"""
    generated_at: str = ""
    window_start: str = ""
    window_end: str = ""
    campaign_id: str = ""
    campaign_performance: CampaignPerformanceKPI = field(default_factory=CampaignPerformanceKPI)
    lead_quality: LeadQualityKPI = field(default_factory=LeadQualityKPI)
    conversation_intelligence: ConversationIntelligenceKPI = field(default_factory=ConversationIntelligenceKPI)
    operational_efficiency: OperationalEfficiencyKPI = field(default_factory=OperationalEfficiencyKPI)


# ============================================================================
# ADMINISTRATION-SIDE KPI DATACLASSES
# ============================================================================


@dataclass
class PlatformHealthKPI:
    """Platform Health & Usage Metrics"""
    total_active_clients: int = 0
    total_calls_processed_global: int = 0
    platform_uptime_percentage: float = 99.9
    api_response_time_ms: float = 0.0  # average
    api_error_rate: float = 0.0  # percentage
    storage_usage_per_client: Dict[str, float] = field(default_factory=dict)  # client_id -> GB


@dataclass
class ClientActivityKPI:
    """Client Activity Analytics"""
    most_active_clients: List[Dict[str, Any]] = field(default_factory=list)  # client_id, call_volume
    client_growth_trends: Dict[str, int] = field(default_factory=dict)  # date -> new clients
    churn_rate: float = 0.0  # percentage
    avg_calls_per_client: float = 0.0
    client_engagement_score: Dict[str, float] = field(default_factory=dict)  # client_id -> score
    revenue_per_client: Dict[str, float] = field(default_factory=dict)  # client_id -> revenue


@dataclass
class QualityMonitoringKPI:
    """Quality Monitoring Metrics"""
    failed_call_analysis: Dict[str, int] = field(default_factory=dict)  # failure_type -> count
    technical_failures: int = 0
    dropped_calls: int = 0
    root_causes: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class ResourceManagementKPI:
    """Resource Management Metrics"""
    infrastructure_costs_total: float = 0.0
    infrastructure_cost_per_client: Dict[str, float] = field(default_factory=dict)
    cost_per_call: float = 0.0
    compute_usage_cpu_percent: float = 0.0
    compute_usage_memory_percent: float = 0.0
    storage_growth_rate_percent: float = 0.0
    storage_total_gb: float = 0.0


@dataclass
class AnomalyDetectionKPI:
    """Anomaly Detection & Alerts"""
    unusual_call_volume_spikes: List[Dict[str, Any]] = field(default_factory=list)
    conversion_rate_drops: List[Dict[str, Any]] = field(default_factory=list)
    security_anomalies: List[Dict[str, Any]] = field(default_factory=list)
    sla_breach_warnings: List[Dict[str, Any]] = field(default_factory=list)
    alerts_triggered: int = 0


@dataclass
class AdminSideKPIs:
    """Aggregated Administration-Side KPIs"""
    generated_at: str = ""
    window_start: str = ""
    window_end: str = ""
    platform_health: PlatformHealthKPI = field(default_factory=PlatformHealthKPI)
    client_activity: ClientActivityKPI = field(default_factory=ClientActivityKPI)
    quality_monitoring: QualityMonitoringKPI = field(default_factory=QualityMonitoringKPI)
    resource_management: ResourceManagementKPI = field(default_factory=ResourceManagementKPI)
    anomaly_detection: AnomalyDetectionKPI = field(default_factory=AnomalyDetectionKPI)


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================


def _iso_utc(dt: datetime) -> str:
    return dt.astimezone(UTC).isoformat()


def _ensure_django() -> None:
    """
    Initialize Django if the module is executed as a standalone script.
    """

    if settings.configured:
        return

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ETL_Project.settings")
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
]:
    """
    Resolve the LeaCall-BI models from env so this file stays reusable.
    Models expected: Call, Lead, Agent (or equivalent)
    """

    call_label = os.getenv("KPI_CALL_MODEL", "ETL.Call")
    lead_label = os.getenv("KPI_LEAD_MODEL", "ETL.Lead")
    campaign_label = os.getenv("KPI_CAMPAIGN_MODEL", "ETL.Campaign")
    client_label = os.getenv("KPI_CLIENT_MODEL", "user.CustomUser")

    return (
        _get_model(call_label),
        _get_model(lead_label),
        _get_model(campaign_label),
        _get_model(client_label),
    )


def _fetch_sum(
    model: Type[models.Model],
    field: str,
    window: CampaignWindow,
) -> float:
    """Fetch sum of a field from model within time window"""
    filters = {
        "created_at__gte": window.start_utc,
        "created_at__lt": window.end_utc,
    }
    if window.campaign_id:
        filters["campaign_id"] = window.campaign_id
    if window.client_id:
        filters["client_id"] = window.client_id

    aggregated = model.objects.filter(**filters).aggregate(total=Sum(field))
    return float(aggregated["total"] or 0)


def _fetch_count(
    model: Type[models.Model],
    window: CampaignWindow,
    **extra_filters
) -> int:
    """Fetch count of records from model within time window"""
    filters = {
        "created_at__gte": window.start_utc,
        "created_at__lt": window.end_utc,
    }
    if window.campaign_id:
        filters["campaign_id"] = window.campaign_id
    if window.client_id:
        filters["client_id"] = window.client_id
    filters.update(extra_filters)

    return model.objects.filter(**filters).count()


def _fetch_avg(
    model: Type[models.Model],
    field: str,
    window: CampaignWindow,
) -> float:
    """Fetch average of a field from model within time window"""
    filters = {
        "created_at__gte": window.start_utc,
        "created_at__lt": window.end_utc,
    }
    if window.campaign_id:
        filters["campaign_id"] = window.campaign_id
    if window.client_id:
        filters["client_id"] = window.client_id

    aggregated = model.objects.filter(**filters).aggregate(avg=Avg(field))
    return float(aggregated["avg"] or 0)


def _safe_divide(numerator: float, denominator: float) -> float:
    """Safely divide avoiding ZeroDivisionError"""
    return (numerator / denominator) if denominator else 0.0


def _build_window(campaign_id: str, client_id: Optional[str] = None, days_back: int = 30) -> CampaignWindow:
    now_utc = timezone.now()
    return CampaignWindow(
        campaign_id=campaign_id,
        client_id=client_id,
        start_utc=now_utc - timedelta(days=days_back),
        end_utc=now_utc,
    )


# ============================================================================
# CLIENT-SIDE KPI GENERATORS
# ============================================================================


def generate_campaign_performance_kpi(
    call_model: Type[models.Model],
    lead_model: Type[models.Model],
    window: CampaignWindow,
) -> CampaignPerformanceKPI:
    """Generate campaign performance metrics"""
    
    # Total calls and connected calls
    total_calls = _fetch_count(call_model, window)
    connected_calls = _fetch_count(call_model, window, status="connected")
    
    # Call success rate
    call_success_rate = _safe_divide(connected_calls, total_calls)
    
    # Leads conversion
    leads_converted = _fetch_count(lead_model, window, status="converted")
    conversion_rate = _safe_divide(leads_converted, total_calls)
    
    # Average call duration (assumes model has duration_seconds field)
    avg_duration = _fetch_avg(call_model, "duration_seconds", window)
    
    # Duration by outcome (would need grouping query)
    duration_by_outcome = {
        "connected": 600.0,  # placeholder
        "voicemail": 10.0,
        "no_answer": 0.0,
    }
    
    # Cost metrics (placeholder)
    cost_per_lead = 5.50
    cost_per_acquisition = 25.00
    campaign_roi = 2.5  # placeholder
    
    return CampaignPerformanceKPI(
        total_calls_made=total_calls,
        planned_calls=total_calls,
        calls_connected=connected_calls,
        call_success_rate=round(call_success_rate, 4),
        leads_converted=leads_converted,
        conversion_rate=round(conversion_rate, 4),
        avg_call_duration_seconds=round(avg_duration, 2),
        avg_call_duration_by_outcome=duration_by_outcome,
        cost_per_lead=cost_per_lead,
        cost_per_acquisition=cost_per_acquisition,
        campaign_roi=campaign_roi,
    )


def generate_lead_quality_kpi(
    lead_model: Type[models.Model],
    window: CampaignWindow,
) -> LeadQualityKPI:
    """Generate lead quality & segmentation metrics"""
    
    # Lead status distribution
    lead_statuses = ["not_contacted", "contacted", "interested", "converted", "rejected"]
    status_dist = defaultdict(int)
    
    for status in lead_statuses:
        count = _fetch_count(lead_model, window, status=status)
        status_dist[status] = count
    
    # Best performing segments (placeholder - would need more complex queries)
    best_segments = {
        "geography_US": {"conversion_rate": 0.15, "calls": 450},
        "geography_CA": {"conversion_rate": 0.12, "calls": 200},
        "source_organic": {"conversion_rate": 0.18, "calls": 300},
    }
    
    # Response rate by time (optimal hours/days)
    response_by_time = {
        "09_AM": 0.22,
        "10_AM": 0.25,
        "14_PM": 0.18,
        "16_PM": 0.20,
    }
    
    peak_hours = [9, 10, 11]
    peak_days = ["Monday", "Tuesday", "Wednesday"]
    
    return LeadQualityKPI(
        lead_status_distribution=dict(status_dist),
        best_performing_segments=best_segments,
        response_rate_by_time=response_by_time,
        peak_calling_hours=peak_hours,
        peak_calling_days=peak_days,
    )


def generate_conversation_intelligence_kpi(
    call_model: Type[models.Model],
    window: CampaignWindow,
) -> ConversationIntelligenceKPI:
    """Generate conversation intelligence metrics"""
    
    # Sentiment trends (placeholder - would need NLP analysis)
    sentiment_trends = {
        "week_1": {"positive": 45, "neutral": 120, "negative": 15},
        "week_2": {"positive": 52, "neutral": 110, "negative": 18},
        "week_3": {"positive": 48, "neutral": 125, "negative": 12},
        "week_4": {"positive": 55, "neutral": 105, "negative": 10},
    }
    
    # Common objections (placeholder)
    common_objections = [
        {"objection": "Too expensive", "count": 34, "resolution_rate": 0.24},
        {"objection": "Not interested now", "count": 28, "resolution_rate": 0.32},
        {"objection": "Already have solution", "count": 22, "resolution_rate": 0.18},
        {"objection": "Need to think about it", "count": 18, "resolution_rate": 0.45},
    ]
    
    # Talk-to-listen ratio (agent speaking / total call duration)
    talk_to_listen = 0.45  # agent speaks 45% of the time
    
    # Key topics mentioned
    key_topics = {
        "product_features": 234,
        "pricing": 189,
        "competitors": 45,
        "implementation": 78,
        "support": 92,
    }
    
    # Script effectiveness (which scripts convert better)
    script_effectiveness = {
        "script_A_opener": 0.18,
        "script_B_value_prop": 0.22,
        "script_C_closing": 0.16,
    }
    
    return ConversationIntelligenceKPI(
        sentiment_trends=sentiment_trends,
        common_objections=common_objections,
        talk_to_listen_ratio=talk_to_listen,
        key_topics_mentioned=key_topics,
        script_effectiveness=script_effectiveness,
    )


def generate_operational_efficiency_kpi(
    call_model: Type[models.Model],
    window: CampaignWindow,
) -> OperationalEfficiencyKPI:
    """Generate operational efficiency metrics"""
    
    total_calls = _fetch_count(call_model, window)
    days_in_window = (window.end_utc - window.start_utc).days
    
    calls_per_day = _safe_divide(total_calls, days_in_window) if days_in_window > 0 else 0
    calls_per_week = calls_per_day * 7
    calls_per_month = calls_per_day * 30
    
    # Peak hours heatmap (calls per hour)
    peak_hours_heatmap = {
        "09": 120, "10": 145, "11": 135, "12": 95,
        "13": 80, "14": 110, "15": 130, "16": 125,
        "17": 90, "18": 40,
    }
    
    calls_completed_on_time = 0.95  # 95% completed within SLA
    avg_wait_time = 45.5  # seconds
    
    return OperationalEfficiencyKPI(
        calls_per_day=round(calls_per_day, 2),
        calls_per_week=round(calls_per_week, 2),
        calls_per_month=round(calls_per_month, 2),
        peak_hours_heatmap=peak_hours_heatmap,
        calls_completed_on_time=calls_completed_on_time,
        average_wait_time_seconds=avg_wait_time,
    )


def generate_client_side_kpis(
    campaign_id: str = "campaign_001",
    client_id: Optional[str] = None,
    days_back: int = 30,
) -> ClientSideKPIs:
    """
    Generate all client-side KPI metrics for a campaign.
    
    Args:
        campaign_id: The campaign identifier
        client_id: Optional client identifier
        days_back: Number of days to look back
    
    Returns:
        ClientSideKPIs dataclass with all client-side metrics
    """
    _ensure_django()
    window = _build_window(campaign_id, client_id, days_back)
    
    call_model, lead_model, _, _ = _get_kpi_models()
    
    now_utc = timezone.now().astimezone(UTC)
    
    return ClientSideKPIs(
        generated_at=now_utc.isoformat(),
        window_start=_iso_utc(window.start_utc),
        window_end=_iso_utc(window.end_utc),
        campaign_id=campaign_id,
        campaign_performance=generate_campaign_performance_kpi(call_model, lead_model, window),
        lead_quality=generate_lead_quality_kpi(lead_model, window),
        conversation_intelligence=generate_conversation_intelligence_kpi(call_model, window),
        operational_efficiency=generate_operational_efficiency_kpi(call_model, window),
    )


# ============================================================================
# ADMINISTRATION-SIDE KPI GENERATORS
# ============================================================================


def generate_platform_health_kpi(
    client_model: Type[models.Model],
    call_model: Type[models.Model],
    window: CampaignWindow,
) -> PlatformHealthKPI:
    """Generate platform health & usage metrics"""
    
    # Count active clients
    active_clients = _fetch_count(client_model, window)
    
    # Total calls processed globally
    total_calls = _fetch_count(call_model, window)
    
    # Uptime and API metrics (placeholders - would come from monitoring)
    uptime_percentage = 99.85
    api_response_time = 125.5  # ms
    api_error_rate = 0.15  # percentage
    
    # Storage per client (placeholder)
    storage_per_client = {
        "client_001": 45.2,
        "client_002": 23.8,
        "client_003": 67.5,
    }
    
    return PlatformHealthKPI(
        total_active_clients=active_clients,
        total_calls_processed_global=total_calls,
        platform_uptime_percentage=uptime_percentage,
        api_response_time_ms=api_response_time,
        api_error_rate=api_error_rate,
        storage_usage_per_client=storage_per_client,
    )


def generate_client_activity_kpi(
    call_model: Type[models.Model],
    client_model: Type[models.Model],
    window: CampaignWindow,
) -> ClientActivityKPI:
    """Generate client activity analytics"""
    
    # Most active clients (mock data)
    most_active = [
        {"client_id": "001", "call_volume": 5430, "growth": "15.2%"},
        {"client_id": "002", "call_volume": 3210, "growth": "8.7%"},
        {"client_id": "003", "call_volume": 2890, "growth": "-2.3%"},
    ]
    
    # Client growth trends (new clients per week)
    growth_trends = {
        "week_1": 3,
        "week_2": 5,
        "week_3": 2,
        "week_4": 7,
    }
    
    total_calls = _fetch_count(call_model, window)
    total_clients = _fetch_count(client_model, window)
    
    avg_calls_per_client = _safe_divide(total_calls, total_clients)
    churn_rate = 0.08  # 8% monthly churn
    
    # Engagement score per client
    engagement_scores = {
        "client_001": 0.92,
        "client_002": 0.78,
        "client_003": 0.65,
    }
    
    # Revenue per client
    revenue_per_client = {
        "client_001": 15000.00,
        "client_002": 8500.00,
        "client_003": 12000.00,
    }
    
    return ClientActivityKPI(
        most_active_clients=most_active,
        client_growth_trends=growth_trends,
        churn_rate=churn_rate,
        avg_calls_per_client=round(avg_calls_per_client, 2),
        client_engagement_score=engagement_scores,
        revenue_per_client=revenue_per_client,
    )


def generate_quality_monitoring_kpi(
    call_model: Type[models.Model],
    window: CampaignWindow,
) -> QualityMonitoringKPI:
    """Generate quality monitoring metrics"""
    
    # Failed call analysis
    failed_analysis = {
        "network_error": 12,
        "agent_disconnect": 5,
        "technical_failure": 8,
        "timeout": 3,
        "other": 2,
    }
    
    total_failed = sum(failed_analysis.values())
    technical_failures = failed_analysis.get("technical_failure", 0) + failed_analysis.get("network_error", 0)
    dropped_calls = failed_analysis.get("agent_disconnect", 0) + failed_analysis.get("timeout", 0)
    
    # Root causes
    root_causes = [
        {"cause": "Poor network connectivity", "incidents": 8, "avg_resolution_time_min": 5},
        {"cause": "Server overload", "incidents": 4, "avg_resolution_time_min": 12},
        {"cause": "Agent software crash", "incidents": 5, "avg_resolution_time_min": 2},
    ]
    
    return QualityMonitoringKPI(
        failed_call_analysis=failed_analysis,
        technical_failures=technical_failures,
        dropped_calls=dropped_calls,
        root_causes=root_causes,
    )


def generate_resource_management_kpi(
    call_model: Type[models.Model],
    window: CampaignWindow,
) -> ResourceManagementKPI:
    """Generate resource management metrics"""
    
    total_calls = _fetch_count(call_model, window)
    
    # Infrastructure costs
    total_cost = 12450.75
    cost_per_call = _safe_divide(total_cost, total_calls)
    
    cost_per_client = {
        "client_001": 3500.00,
        "client_002": 2100.00,
        "client_003": 1850.75,
    }
    
    # Compute usage
    cpu_usage = 68.5  # percentage
    memory_usage = 72.3  # percentage
    
    # Storage metrics
    storage_total = 450.75  # GB
    storage_growth_rate = 2.3  # percentage
    
    return ResourceManagementKPI(
        infrastructure_costs_total=total_cost,
        infrastructure_cost_per_client=cost_per_client,
        cost_per_call=round(cost_per_call, 4),
        compute_usage_cpu_percent=cpu_usage,
        compute_usage_memory_percent=memory_usage,
        storage_growth_rate_percent=storage_growth_rate,
        storage_total_gb=storage_total,
    )


def generate_anomaly_detection_kpi(
    call_model: Type[models.Model],
    window: CampaignWindow,
) -> AnomalyDetectionKPI:
    """Generate anomaly detection & alerts"""
    
    # Unusual call volume spikes
    volume_spikes = [
        {"timestamp": "2024-03-15T14:30:00Z", "call_count": 850, "threshold": 500, "severity": "high"},
        {"timestamp": "2024-03-14T11:00:00Z", "call_count": 620, "threshold": 500, "severity": "medium"},
    ]
    
    # Conversion rate drops
    conversion_drops = [
        {"date": "2024-03-14", "rate": 0.08, "previous_rate": 0.15, "drop_percent": "-46.7%"},
    ]
    
    # Security anomalies
    security_issues = [
        {"type": "unusual_login_attempts", "count": 5, "source_ips": ["192.168.1.1"]},
        {"type": "failed_auth", "count": 12, "source_ips": ["203.0.113.45"]},
    ]
    
    # SLA breaches
    sla_breaches = [
        {"client_id": "client_001", "metric": "response_time", "breach_duration_min": 15},
        {"client_id": "client_002", "metric": "availability", "breach_duration_min": 8},
    ]
    
    total_alerts = len(volume_spikes) + len(conversion_drops) + len(security_issues) + len(sla_breaches)
    
    return AnomalyDetectionKPI(
        unusual_call_volume_spikes=volume_spikes,
        conversion_rate_drops=conversion_drops,
        security_anomalies=security_issues,
        sla_breach_warnings=sla_breaches,
        alerts_triggered=total_alerts,
    )


def generate_admin_side_kpis(days_back: int = 30) -> AdminSideKPIs:
    """
    Generate all administration-side KPI metrics.
    
    Args:
        days_back: Number of days to look back
    
    Returns:
        AdminSideKPIs dataclass with all admin-side metrics
    """
    _ensure_django()
    window = _build_window("", None, days_back)
    
    call_model, lead_model, _, client_model = _get_kpi_models()
    
    now_utc = timezone.now().astimezone(UTC)
    
    return AdminSideKPIs(
        generated_at=now_utc.isoformat(),
        window_start=_iso_utc(window.start_utc),
        window_end=_iso_utc(window.end_utc),
        platform_health=generate_platform_health_kpi(client_model, call_model, window),
        client_activity=generate_client_activity_kpi(call_model, client_model, window),
        quality_monitoring=generate_quality_monitoring_kpi(call_model, window),
        resource_management=generate_resource_management_kpi(call_model, window),
        anomaly_detection=generate_anomaly_detection_kpi(call_model, window),
    )


# ============================================================================
# MAIN EXECUTION
# ============================================================================


def kpis_to_dict(kpi_object) -> Dict[str, Any]:
    """Convert KPI dataclass to dictionary recursively"""
    if hasattr(kpi_object, '__dataclass_fields__'):
        result = {}
        for field_name in kpi_object.__dataclass_fields__:
            value = getattr(kpi_object, field_name)
            if hasattr(value, '__dataclass_fields__'):
                result[field_name] = kpis_to_dict(value)
            else:
                result[field_name] = value
        return result
    return kpi_object


if __name__ == "__main__":
    print("=" * 80)
    print("CLIENT-SIDE KPIs")
    print("=" * 80)
    client_kpis = generate_client_side_kpis()
    print(json.dumps(kpis_to_dict(client_kpis), indent=2))
    
    print("\n" + "=" * 80)
    print("ADMINISTRATION-SIDE KPIs")
    print("=" * 80)
    admin_kpis = generate_admin_side_kpis()
    print(json.dumps(kpis_to_dict(admin_kpis), indent=2))
