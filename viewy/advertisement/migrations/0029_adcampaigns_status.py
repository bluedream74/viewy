# Generated by Django 4.2.3 on 2023-10-29 09:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('advertisement', '0028_alter_adcampaigns_created_at'),
    ]

    operations = [
        migrations.AddField(
            model_name='adcampaigns',
            name='status',
            field=models.CharField(choices=[('pending', 'Pending'), ('running', 'Running'), ('achieved', 'Achieved'), ('expired', 'Expired'), ('stopped', 'Stopped')], default='pending', max_length=8),
        ),
    ]
