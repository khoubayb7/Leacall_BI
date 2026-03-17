from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0003_customuser_leacall_api_key'),
    ]

    operations = [
        migrations.AddField(
            model_name='customuser',
            name='leacall_bi_api_key',
            field=models.CharField(
                blank=True,
                default='',
                help_text='BI API key (X-BI-API-Key) for read-only BI endpoints on the LeaCall server.',
                max_length=512,
            ),
        ),
    ]
