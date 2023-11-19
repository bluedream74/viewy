# Generated by Django 4.2.3 on 2023-11-19 12:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('support', '0002_rename_fantiainquiry_normalinquiry'),
    ]

    operations = [
        migrations.CreateModel(
            name='CorporateInquiry',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('company_name', models.CharField(max_length=100, verbose_name='会社名')),
                ('department_name', models.CharField(blank=True, max_length=100, verbose_name='所属部署名')),
                ('subject', models.CharField(max_length=200, verbose_name='件名')),
                ('content', models.TextField(verbose_name='お問い合わせ内容')),
            ],
        ),
        migrations.AddField(
            model_name='normalinquiry',
            name='subject',
            field=models.CharField(default='', max_length=200, verbose_name='件名'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='normalinquiry',
            name='browser',
            field=models.CharField(max_length=100, verbose_name='ブラウザ'),
        ),
        migrations.AlterField(
            model_name='normalinquiry',
            name='content',
            field=models.TextField(verbose_name='お問い合わせ内容'),
        ),
        migrations.AlterField(
            model_name='normalinquiry',
            name='device',
            field=models.CharField(max_length=100, verbose_name='機種'),
        ),
        migrations.AlterField(
            model_name='normalinquiry',
            name='email',
            field=models.EmailField(max_length=254, verbose_name='メールアドレス'),
        ),
        migrations.AlterField(
            model_name='normalinquiry',
            name='inquiry_type',
            field=models.CharField(choices=[('copyright', '著作権者様のみ'), ('corporate', '法人様からの問い合わせ・取材申し込み等')], max_length=100, verbose_name='お問い合わせ種類'),
        ),
        migrations.AlterField(
            model_name='normalinquiry',
            name='name',
            field=models.CharField(max_length=100, verbose_name='氏名'),
        ),
        migrations.AlterField(
            model_name='normalinquiry',
            name='occurrence_date',
            field=models.DateTimeField(verbose_name='お問い合わせ事項発生日時'),
        ),
        migrations.AlterField(
            model_name='normalinquiry',
            name='occurrence_url',
            field=models.URLField(verbose_name='お問い合わせ事項発生URL'),
        ),
    ]
