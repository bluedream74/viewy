# Generated by Django 4.2.3 on 2023-09-27 04:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0045_posts_emote_total_count'),
    ]

    operations = [
        migrations.AddField(
            model_name='posts',
            name='is_by_affiliateadvertiser',
            field=models.BooleanField(default=False),
        ),
    ]