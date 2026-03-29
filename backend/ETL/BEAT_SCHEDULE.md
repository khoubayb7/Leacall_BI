# Nightly ETL Beat Schedule

## Overview

A scheduled Celery Beat job that automatically reruns ETL every night for all active client campaigns.

## Architecture

### Beat Schedule Entry
Location: `ETL_Project/settings.py` → `CELERY_BEAT_SCHEDULE["refresh-all-campaign-etls"]`

**Default Schedule:** 1:00 UTC daily (configurable)

```python
"refresh-all-campaign-etls": {
    "task": "ETL.refresh_all_campaign_etls",
    "schedule": crontab(
        hour=int(os.getenv("ETL_BEAT_HOUR_UTC", "1")), 
        -minute=int(os.getenv("ETL_BEAT_MINUTE_UTC", "0"))
    ),
},
```

### Tasks

#### 1. `refresh_all_campaign_etls_task()` (Beat Entry Point)
- **Module:** `ETL.tasks`
- **Type:** Celery Beat scheduled task
- **Purpose:** Query all active campaigns and enqueue ETL work
- **Frequency:** Nightly at configured time

**Behavior:**
1. Queries all `ClientDataSource` objects with `is_active=True`
2. Validates each data source:
   - Ensures client exists (`client_id` is not null)
   - Logs any missing/invalid configurations
3. Enqueues `run_single_campaign_etl_task` for each valid campaign
4. Returns summary with counts: `total_sources`, `queued`, `skipped`, `failures`

**Logging:** All actions logged to `etl_logger` at INFO/ERROR levels

#### 2. `run_single_campaign_etl_task(data_source_id: int)` (Worker Task)
- **Module:** `ETL.tasks`
- **Type:** Celery async task (can run in parallel)
- **Purpose:** Execute ETL for a single campaign

**Behavior:**
1. Fetches the `ClientDataSource` by ID (validates `is_active=True`)
2. Calls `refresh_campaign_etl_and_schema(data_source)` which:
   - Executes the ETL pipeline using `ETLPipelineExecutor`
   - Extracts schema columns from the ETL run
   - Computes schema signature hash
   - Persists schema state to disk
   - Regenerates E/T/L Python artifacts
3. Logs result: success/failure, run_id, schema changes, column count
4. Returns operation summary

**Error Handling:** Skips inactive/missing campaigns safely; logs details for audit

## Configuration

### Environment Variables

Location: `.env` (or `.env.example` for reference)

```bash
# ETL Beat schedule (default: 1:00 UTC daily)
ETL_BEAT_HOUR_UTC=1
ETL_BEAT_MINUTE_UTC=0

# KPI Beat schedule (default: 2:00 UTC daily) — also configurable
KPI_BEAT_HOUR_UTC=2
KPI_BEAT_MINUTE_UTC=0
```

**To change the schedule time:**
1. Update `ETL_BEAT_HOUR_UTC` and `ETL_BEAT_MINUTE_UTC` in `.env`
2. Restart Celery Beat: `celery -A ETL_Project beat -l info`

**Note:** Timezone is UTC. To convert to local time:
- 1:00 UTC = 2:00 CET (summer) / 3:00 CET (winter)
- For 3:00 CET, set `ETL_BEAT_HOUR_UTC=1` (or `2` for 4:00 CET)

## Running the Service

### Start Celery Worker
```bash
cd backend
celery -A ETL_Project worker -l info --pool=solo
```

### Start Celery Beat Scheduler
```bash
cd backend
celery -A ETL_Project beat -l info
```

### View Scheduled Tasks
```bash
celery -A ETL_Project inspect scheduled
```

### Monitor Progress
- Check Celery worker logs: `worker -l info` output
- View database: Check `ETL.ETLRun` records and status
- Check logs in application logger output

## Logging

### Log Levels & Formats

All logging goes to the standard Django logger framework (`logging.getLogger(__name__)`).

#### Beat Task (`refresh_all_campaign_etls_task`)
```
INFO  Beat ETL refresh STARTED: scanning active campaigns for nightly refresh
INFO  Beat ETL refresh QUEUED: client=john_doe (id=5), campaign=Marketing (id=camp_001, datasource_id=42)
WARN  Beat ETL refresh SKIP: campaign=camp_002 has no client_id (datasource_id=43)
ERROR Beat ETL refresh FAILED-TO-QUEUE: client=jane_smith, campaign=Vente, error=...
INFO  Beat ETL refresh COMPLETED: total=150, queued=145, skipped=5
```

#### Worker Task (`run_single_campaign_etl_task`)
```
INFO  ETL refresh START: client=john_doe (id=5), campaign=Marketing (id=camp_001)
INFO  ETL refresh SUCCESS: client=john_doe, campaign=Marketing, run_id=1234, schema_change=True, columns=42
ERROR ETL refresh FAILED: client=john_doe, campaign=Marketing, run_id=1234, error=...
```

### Audit Trail

Failed queuing attempts are returned in the task summary:
```python
{
    "status": "completed",
    "total_sources": 150,
    "queued": 145,
    "skipped": 5,
    "failures": [
        {
            "client_id": None,
            "campaign_id": "camp_004",
            "campaign_name": "Invalid Campaign",
            "reason": "missing_client_id"
        },
        {
            "client_id": 7,
            "campaign_id": "camp_005",
            "campaign_name": "Failed Campaign",
            "reason": "Connection timeout to Redis"
        }
    ]
}
```

## Implementation Details

### Database Models Used

- **`CustomUser`** (user.models): Client accounts with JWT
- **`ClientDataSource`** (ETL.models): Campaign configuration
  - `is_active` field: Filters which campaigns to refresh
  - `client_id` field: Links campaign to user
  - `campaign_id`, `campaign_name`: Campaign identifiers
- **`ETLRun`** (ETL.models): ETL execution records
  - Tracks status, start/end times, error messages

### File Locations

- **Settings:** `backend/ETL_Project/settings.py` (lines ~147-151)
- **Tasks:** `backend/ETL/tasks.py` (new tasks at end of file)
- **Config:** `backend/.env` or `backend/.env.example`

## Acceptance Criteria Met

✅ **Nightly schedule exists for ETL reruns**
- Beat schedule configured in settings: daily at 1:00 UTC
- Configurable via `ETL_BEAT_HOUR_UTC` and `ETL_BEAT_MINUTE_UTC` env vars

✅ **Job enqueues ETL work for all valid user/campaign pairs**
- `refresh_all_campaign_etls_task()` queries `ClientDataSource` with `is_active=True`
- Enqueues `run_single_campaign_etl_task()` for each valid campaign
- Runs tasks in parallel (Celery worker pool)

✅ **Invalid or missing campaign config is skipped safely and logged**
- Validates `client_id` exists before queuing
- Wraps task queueing in try/except
- Logs each skip/failure with reason in failures array

✅ **Schedule time can be changed without code changes**
- Fully configurable via environment variables
- No hardcoded hour/minute values

✅ **Logs clearly show which ETL tasks were queued**
- Beat task logs each queued campaign with: client username, campaign name, datasource ID
- Worker task logs result: success/failure, run_id, schema changes
- All failures returned in summary with reasons

## Testing

### Manual Test: Trigger Beat Task Immediately
```python
# In Django shell:
from ETL.tasks import refresh_all_campaign_etls_task
result = refresh_all_campaign_etls_task()
print(result)
# Output: {"status": "completed", "total_sources": X, "queued": Y, "skipped": Z, "failures": [...]}
```

### Check Queue Length
```bash
celery -A ETL_Project inspect active_queues
```

### View Scheduled Runs
```bash
celery -A ETL_Project inspect scheduled
```

### Database Verification
```python
# In Django shell:
from ETL.models import ETLRun
# Find recent runs (should see new entries after beat trigger):
ETLRun.objects.filter(created_at__gte=timezone.now() - timedelta(hours=1)).order_by("-created_at")
```

## Troubleshooting

### Beat Task Not Running

1. **Check if Beat is running:**
   ```bash
   celery -A ETL_Project inspect active
   ```

2. **Verify schedule in Celery:**
   ```bash
   celery -A ETL_Project inspect scheduled
   ```

3. **Check Beat logs for errors**

4. **Verify Redis connection:**
   ```bash
   redis-cli ping
   # Should return: PONG
   ```

### Tasks Queued But Not Running

1. **Check if Worker is running:**
   ```bash
   celery -A ETL_Project inspect active
   ```

2. **Check worker logs for errors**

3. **Verify queue names match:**
   ```bash
   celery -A ETL_Project inspect active_queues
   ```

### Configuration Not Taking Effect

1. **Restart Beat process** (changes only read at startup):
   ```bash
   pkill -f "celery.*beat"
   celery -A ETL_Project beat -l info
   ```

2. **Verify environment variables loaded:**
   ```bash
   python manage.py shell
   >>> from django.conf import settings
   >>> settings.CELERY_BEAT_SCHEDULE
   ```

### Schema Signature File Issues

Schema state files stored at: `workspace/etl_output/datasets/schema_<client_id>_<campaign_id>.json`

If schema detection fails:
1. Delete invalid state files
2. Next ETL run will create new state files
3. Check logs for "ETL refresh SUCCESS/FAILED"

## Performance Considerations

- **Parallel Execution:** Each campaign runs as a separate task; up to N tasks can run in parallel (Celery pool size)
- **Database Load:** Queries all active campaigns once per night; queries are indexed
- **Lock Management:** No explicit locks; Redis handles task queueing atomically
- **Retry Policy:** Tasks configured to retry with exponential backoff on exception

**For large deployments (1000+ campaigns):**
- Consider increasing Celery pool size or prefork workers
- Monitor Redis memory usage
- Stagger start times if needed to avoid peak load
