# Generated by Django 4.2.3 on 2023-09-25 11:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('advertisement', '0014_alter_adcampaigns_end_date_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='andfeatures',
            name='is_all',
            field=models.BooleanField(default=False),
        ),
    ]
