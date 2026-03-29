from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("agentKPIS", "0002_backfill_campaign_columns"),
        ("user", "0005_enable_etl_kpi_modules"),
    ]

    operations = [
        migrations.AddField(
            model_name="kpiexecution",
            name="client",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=models.deletion.SET_NULL,
                related_name="kpi_executions",
                to="user.customuser",
            ),
        ),
    ]
