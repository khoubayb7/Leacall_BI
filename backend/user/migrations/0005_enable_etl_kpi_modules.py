# Generated migration to update default enabled_modules

from django.db import migrations


def update_existing_clients(apps, schema_editor):
    """Update existing clients to have etl_pipeline and kpi_dashboard enabled."""
    User = apps.get_model('user', 'CustomUser')
    for user in User.objects.filter(role='client'):
        # Add etl_pipeline and kpi_dashboard to existing modules
        current = user.enabled_modules or ['dashboard']
        if 'etl_pipeline' not in current:
            current = list(current) if isinstance(current, list) else [current]
            current.extend(['etl_pipeline', 'kpi_dashboard'])
            user.enabled_modules = current
            user.save(update_fields=['enabled_modules'])


def revert_clients(apps, schema_editor):
    """Revert to original enabled_modules."""
    User = apps.get_model('user', 'CustomUser')
    for user in User.objects.filter(role='client'):
        current = user.enabled_modules or ['dashboard']
        current = [m for m in current if m not in ('etl_pipeline', 'kpi_dashboard')]
        if not current:
            current = ['dashboard']
        user.enabled_modules = current
        user.save(update_fields=['enabled_modules'])


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0004_customuser_leacall_bi_api_key'),
    ]

    operations = [
        migrations.RunPython(update_existing_clients, revert_clients),
    ]
