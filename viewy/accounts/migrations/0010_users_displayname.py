# Generated by Django 4.2.3 on 2023-08-09 01:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0009_alter_users_poster_waiter'),
    ]

    operations = [
        migrations.AddField(
            model_name='users',
            name='displayname',
            field=models.CharField(blank=True, max_length=30, null=True),
        ),
    ]