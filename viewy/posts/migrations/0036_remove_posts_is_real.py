# Generated by Django 4.2.3 on 2023-09-12 09:15

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0035_merge_0033_alter_posts_caption_0034_posts_qp'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='posts',
            name='is_real',
        ),
    ]