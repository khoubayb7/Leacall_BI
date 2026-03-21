import json
from datetime import datetime
from typing import List, Dict


def load_dataset(file_path: str) -> Dict:
    """
    Load the dataset from a JSON file.
    """
    with open(file_path, 'r') as file:
        return json.load(file)


def _safe_divide(numerator: float, denominator: float) -> float:
    return (numerator / denominator) if denominator else 0.0


def generate_kpis(records: List[Dict]) -> Dict:
    """
    Generate KPI metrics from the dataset records.
    """
    impressions = sum(record.get('impressions', 0) for record in records)
    clicks = sum(record.get('clicks', 0) for record in records)
    conversions = sum(record.get('conversions', 0) for record in records)
    spend_usd = sum(record.get('spend_usd', 0.0) for record in records)
    revenue_usd = sum(record.get('revenue_usd', 0.0) for record in records)

    ctr = _safe_divide(clicks, impressions)
    conversion_rate = _safe_divide(conversions, clicks)
    cpa = _safe_divide(spend_usd, conversions)
    roas = _safe_divide(revenue_usd, spend_usd)

    return {
        "generated_at": datetime.utcnow().isoformat() + 'Z',
        "campaign_id": "cc779bde-6a35-4a00-b52b-da3003ac8f5e",
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


def main():
    dataset_file_path = "C:\\Users\\khoub\\OneDrive\\Bureau\\BI_System\\backend\\workspace\\etl_output\\datasets\\dataset_24_cc779bde-6a35-4a00-b52b-da3003ac8f5e.json"
    dataset = load_dataset(dataset_file_path)
    kpis = generate_kpis(dataset['records'])
    print(json.dumps(kpis, indent=4))


if __name__ == "__main__":
    main()