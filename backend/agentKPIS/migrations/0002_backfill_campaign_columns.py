from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("agentKPIS", "0001_initial"),
    ]

    operations = [
        migrations.RunSQL(
            sql="ALTER TABLE \"agentKPIS_kpiexecution\" ADD COLUMN IF NOT EXISTS \"campaign_id\" varchar(255) NOT NULL DEFAULT 'demo_campaign';",
            reverse_sql="ALTER TABLE \"agentKPIS_kpiexecution\" DROP COLUMN IF EXISTS \"campaign_id\";",
        ),
        migrations.RunSQL(
            sql="ALTER TABLE \"agentKPIS_kpiexecution\" ADD COLUMN IF NOT EXISTS \"campaign_name\" varchar(255) NOT NULL DEFAULT '';",
            reverse_sql="ALTER TABLE \"agentKPIS_kpiexecution\" DROP COLUMN IF EXISTS \"campaign_name\";",
        ),
        migrations.RunSQL(
            sql="ALTER TABLE \"agentKPIS_kpiexecution\" ADD COLUMN IF NOT EXISTS \"campaign_type\" varchar(255) NOT NULL DEFAULT 'general';",
            reverse_sql="ALTER TABLE \"agentKPIS_kpiexecution\" DROP COLUMN IF EXISTS \"campaign_type\";",
        ),
    ]
