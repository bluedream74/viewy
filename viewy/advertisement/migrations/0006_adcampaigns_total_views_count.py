# Generated by Django 4.2.3 on 2023-09-19 08:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('advertisement', '0005_alter_adinfos_ad_campaign'),
    ]

    operations = [
        migrations.AddField(
            model_name='adcampaigns',
            name='total_views_count',
            field=models.PositiveIntegerField(default=0),
        ),
    ]
