# Generated by Django 4.2.3 on 2023-09-15 10:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0019_features'),
    ]

    operations = [
        migrations.AddField(
            model_name='users',
            name='features',
            field=models.ManyToManyField(blank=True, to='accounts.features'),
        ),
    ]
