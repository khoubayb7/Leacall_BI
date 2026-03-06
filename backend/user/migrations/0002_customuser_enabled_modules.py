from django.db import migrations, models

import user.models


class Migration(migrations.Migration):

    dependencies = [
        ("user", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="customuser",
            name="enabled_modules",
            field=models.JSONField(blank=True, default=user.models.default_client_modules, help_text="Enabled modules for the client workspace."),
        ),
    ]

