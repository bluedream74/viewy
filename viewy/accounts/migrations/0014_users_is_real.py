# Generated by Django 4.2.3 on 2023-09-11 09:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0013_alter_deleterequest_case_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='users',
            name='is_real',
            field=models.BooleanField(default=False),
        ),
    ]