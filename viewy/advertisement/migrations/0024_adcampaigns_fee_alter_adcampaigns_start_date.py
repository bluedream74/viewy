# Generated by Django 4.2.3 on 2023-10-28 03:53

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('advertisement', '0023_adcampaigns_actual_cpc_or_cpm_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='adcampaigns',
            name='fee',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='adcampaigns',
            name='start_date',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
    ]
