from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("agentKPIS", "0001_initial"),
    ]

    operations = [
        # Note: Columns are already added in 0001_initial, so this migration is a no-op
        # for SQLite compatibility. PostgreSQL users may need to run these manually if needed.
    ]
