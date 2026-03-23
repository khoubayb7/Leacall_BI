import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Any, Optional
from collections import defaultdict

# ============================================================================
# CLIENT-SIDE KPI DATACLASSES
# ============================================================================

@dataclass
class CampaignPerformanceKPI:
    total_calls_made: int = 0
    planned_calls: int = 0
    calls_connected: int = 0
    call_success_rate: float = 0.0
    leads_converted: int = 0
    conversion_rate: float = 0.0
    avg_call_duration_seconds: float = 0.0
    avg_call_duration_by_outcome: Dict[str, float] = field(default_factory=dict)
    cost_per_lead: float = 0.0
    cost_per_acquisition: float = 0.0
    campaign_roi: float = 0.0

@dataclass
class LeadQualityKPI:
    lead_status_distribution: Dict[str, int] = field(default_factory=dict)
    best_performing_segments: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    response_rate_by_time: Dict[str, float] = field(default_factory=dict)
    peak_calling_hours: List[int] = field(default_factory=list)
    peak_calling_days: List[str] = field(default_factory=list)

@dataclass
class ConversationIntelligenceKPI:
    sentiment_trends: Dict[str, Dict[str, int]] = field(default_factory=dict)
    common_objections: List[Dict[str, Any]] = field(default_factory=list)
    talk_to_listen_ratio: float = 0.0
    key_topics_mentioned: Dict[str, int] = field(default_factory=dict)
    script_effectiveness: Dict[str, float] = field(default_factory=dict)

@dataclass
class OperationalEfficiencyKPI:
    calls_per_day: float = 0.0
    calls_per_week: float = 0.0
    calls_per_month: float = 0.0
    peak_hours_heatmap: Dict[str, int] = field(default_factory=dict)
    calls_completed_on_time: float = 0.0
    average_wait_time_seconds: float = 0.0

@dataclass
class ClientSideKPIs:
    generated_at: str = ""
    window_start: str = ""
    window_end: str = ""
    campaign_id: str = ""
    campaign_performance: CampaignPerformanceKPI = field(default_factory=CampaignPerformanceKPI)
    lead_quality: LeadQualityKPI = field(default_factory=LeadQualityKPI)
    conversation_intelligence: ConversationIntelligenceKPI = field(default_factory=ConversationIntelligenceKPI)
    operational_efficiency: OperationalEfficiencyKPI = field(default_factory=OperationalEfficiencyKPI)

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def _safe_divide(numerator: float, denominator: float) -> float:
    return (numerator / denominator) if denominator else 0.0

def load_dataset() -> Dict[str, Any]:
    dataset_file_path = r"C:\Users\khoub\OneDrive\Bureau\BI_System\backend\workspace\etl_output\datasets\dataset_24_077ed469-fbb3-4fe8-9e09-86f348ec82cc.json"
    with open(dataset_file_path, 'r') as file:
        return json.load(file)

def generate_kpis() -> Dict[str, Any]:
    dataset = load_dataset()
    records = dataset.get('records', [])
    
    total_calls = len(records)
    connected_calls = sum(1 for r in records if r.get('status') == 'connected')
    leads_converted = sum(1 for r in records if r.get('lead_status') == 'converted')
    
    call_success_rate = _safe_divide(connected_calls, total_calls)
    conversion_rate = _safe_divide(leads_converted, total_calls)
    
    avg_duration = _safe_divide(sum(r.get('duration_seconds', 0) for r in records), total_calls)
    
    duration_by_outcome = defaultdict(float)
    for r in records:
        outcome = r.get('status', 'unknown')
        duration_by_outcome[outcome] += r.get('duration_seconds', 0)
    
    for outcome in duration_by_outcome:
        count = sum(1 for r in records if r.get('status') == outcome)
        duration_by_outcome[outcome] = _safe_divide(duration_by_outcome[outcome], count)
    
    lead_status_distribution = defaultdict(int)
    for r in records:
        status = r.get('lead_status', 'unknown')
        lead_status_distribution[status] += 1
    
    now_utc = datetime.utcnow().isoformat()
    
    return {
        "generated_at": now_utc,
        "window_start": dataset.get('window_start', ''),
        "window_end": dataset.get('window_end', ''),
        "campaign_id": "077ed469-fbb3-4fe8-9e09-86f348ec82cc",
        "campaign_performance": {
            "total_calls_made": total_calls,
            "planned_calls": total_calls,
            "calls_connected": connected_calls,
            "call_success_rate": round(call_success_rate, 4),
            "leads_converted": leads_converted,
            "conversion_rate": round(conversion_rate, 4),
            "avg_call_duration_seconds": round(avg_duration, 2),
            "avg_call_duration_by_outcome": dict(duration_by_outcome),
            "cost_per_lead": 0.0,
            "cost_per_acquisition": 0.0,
            "campaign_roi": 0.0,
        },
        "lead_quality": {
            "lead_status_distribution": dict(lead_status_distribution),
            "best_performing_segments": {},
            "response_rate_by_time": {},
            "peak_calling_hours": [],
            "peak_calling_days": [],
        },
        "conversation_intelligence": {
            "sentiment_trends": {},
            "common_objections": [],
            "talk_to_listen_ratio": 0.0,
            "key_topics_mentioned": {},
            "script_effectiveness": {},
        },
        "operational_efficiency": {
            "calls_per_day": 0.0,
            "calls_per_week": 0.0,
            "calls_per_month": 0.0,
            "peak_hours_heatmap": {},
            "calls_completed_on_time": 0.0,
            "average_wait_time_seconds": 0.0,
        }
    }

if __name__ == "__main__":
    kpis = generate_kpis()
    print(json.dumps(kpis, indent=2))