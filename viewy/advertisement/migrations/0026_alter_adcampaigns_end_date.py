# Generated by Django 4.2.3 on 2023-10-29 05:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('advertisement', '0025_adinfos_fee'),
    ]

    operations = [
        migrations.AlterField(
            model_name='adcampaigns',
            name='end_date',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]