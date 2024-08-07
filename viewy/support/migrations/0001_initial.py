# Generated by Django 4.2.3 on 2023-11-19 11:56

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='FantiaInquiry',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('email', models.EmailField(max_length=254)),
                ('inquiry_type', models.CharField(choices=[('copyright', '著作権者様のみ'), ('corporate', '法人様からの問い合わせ・取材申し込み等')], max_length=100)),
                ('occurrence_date', models.DateTimeField()),
                ('occurrence_url', models.URLField()),
                ('device', models.CharField(max_length=100)),
                ('browser', models.CharField(max_length=100)),
                ('content', models.TextField()),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
