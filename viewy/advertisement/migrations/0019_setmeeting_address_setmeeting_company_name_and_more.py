# Generated by Django 4.2.3 on 2023-09-30 08:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('advertisement', '0018_setmeeting'),
    ]

    operations = [
        migrations.AddField(
            model_name='setmeeting',
            name='address',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='setmeeting',
            name='company_name',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='setmeeting',
            name='phone_number',
            field=models.CharField(blank=True, max_length=15, null=True),
        ),
    ]