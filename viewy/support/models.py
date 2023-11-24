from django.db import models

class BaseInquiry(models.Model):
    INQUIRY_CHOICES = (
        ('normal', 'Viewyに関して'),
        ('corporate', '法人様からのお問い合わせ'),
    )

    name = models.CharField(max_length=100, verbose_name="氏名")
    email = models.EmailField(verbose_name="メールアドレス")
    inquiry_type = models.CharField(max_length=100, choices=INQUIRY_CHOICES, verbose_name="お問い合わせ種類")

    class Meta:
        abstract = True  # これは抽象モデルです


class NormalInquiry(BaseInquiry):
    subject = models.CharField(max_length=200, verbose_name="件名")
    occurrence_date = models.DateTimeField(verbose_name="お問い合わせ事項発生日時")
    occurrence_url = models.URLField(verbose_name="お問い合わせ事項発生URL")
    device = models.CharField(max_length=100, verbose_name="機種")
    browser = models.CharField(max_length=100, verbose_name="ブラウザ")
    content = models.TextField(verbose_name="お問い合わせ内容")


class CorporateInquiry(BaseInquiry):
    company_name = models.CharField(max_length=100, verbose_name="会社名")
    department_name = models.CharField(max_length=100, blank=True, verbose_name="所属部署名")
    subject = models.CharField(max_length=200, verbose_name="件名")
    content = models.TextField(verbose_name="お問い合わせ内容")
