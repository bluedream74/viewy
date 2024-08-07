# Generated by Django 4.2.3 on 2023-09-12 12:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0036_remove_posts_is_real'),
    ]

    operations = [
        migrations.AddField(
            model_name='posts',
            name='emote1_count',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='posts',
            name='emote2_count',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='posts',
            name='emote3_count',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='posts',
            name='emote4_count',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='posts',
            name='emote5_count',
            field=models.PositiveIntegerField(default=0),
        ),
    ]
