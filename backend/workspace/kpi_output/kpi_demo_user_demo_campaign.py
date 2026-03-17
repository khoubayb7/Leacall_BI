import json
from datetime import datetime, timedelta


def generate_kpis() -> dict:
    """
    Generate simple KPI metrics for user engagement in marketing campaigns.
    """
    now = datetime.utcnow()
    start_date = now - timedelta(days=30)

    # Dummy data for demonstration purposes
    user_signups = 150
    active_users = 120
    page_views = 4500
    avg_session_duration = 300  # in seconds

    engagement_rate = active_users / user_signups if user_signups else 0
    avg_page_views_per_user = page_views / active_users if active_users else 0

    return {
        "generated_at": now.isoformat() + 'Z',
        "window_start": start_date.isoformat() + 'Z',
        "window_end": now.isoformat() + 'Z',
        "user_signups": user_signups,
        "active_users": active_users,
        "page_views": page_views,
        "avg_session_duration": avg_session_duration,
        "engagement_rate": round(engagement_rate, 2),
        "avg_page_views_per_user": round(avg_page_views_per_user, 2),
    }


if __name__ == "__main__":
    print(json.dumps(generate_kpis()))
