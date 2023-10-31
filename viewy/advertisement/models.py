from django.db import models
from posts.models import Posts
from accounts.models import Features, Users
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Sum
from decimal import Decimal, ROUND_UP

class AndFeatures(models.Model):
    orfeatures = models.ManyToManyField(Features)
    is_all = models.BooleanField(default=False)

    def __str__(self):
        feature_names_ja = [str(feature.name_ja) for feature in self.orfeatures.all()]
        features_str_ja = "または".join(feature_names_ja)
        return features_str_ja

class MonthlyAdCost(models.Model):
    year_month = models.DateField(unique=True)  # 年と月の情報を持つフィールド
    cpc = models.IntegerField()  # IntegerFieldに変更
    cpm = models.IntegerField() 

    def __str__(self):
        return f"{self.year_month} - CPC:{self.cpc} - CPM:{self.cpm}"

    def calculate_cpm(self, views):
        base_cpm = float(self.cpm)

        if views <= 50000:  # 5万まで
            return base_cpm
        elif views <= 100000:  # 10万まで
            # 5万と10万の間での線形補間
            return base_cpm - 50 * (views - 50000) / 50000
        elif views <= 200000:  # 20万まで
            # 10万と20万の間での線形補間
            return (base_cpm - 50) - 50 * (views - 100000) / 100000
        else:
            return base_cpm - 100


    def calculate_cpc(self, views):
        base_cpc = float(self.cpc)

        if views <= 50000:  # 5万まで
            return base_cpc
        elif views <= 100000:  # 10万まで
            # 5万と10万の間での線形補間
            return base_cpc - 5 * (views - 50000) / 50000
        elif views <= 200000:  # 20万まで
            # 10万と20万の間での線形補間
            return (base_cpc - 5) - 5 * (views - 100000) / 100000
        else:
            return base_cpc - 10


class AdCampaigns(models.Model):
    created_by = models.ForeignKey(Users, on_delete=models.CASCADE, related_name='created_campaigns')
    title = models.CharField(max_length=100)
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField(null=True, blank=True)
    budget = models.PositiveIntegerField()
    total_views_count = models.PositiveIntegerField(default=0)
    total_clicks_count = models.PositiveIntegerField(default=0)
    is_hidden = models.BooleanField(default=False)  # キャンペーンの停止/再開を判断するカラム
    andfeatures = models.ManyToManyField(AndFeatures, blank=True)
    target_views = models.PositiveIntegerField(default=0)
    fee = models.PositiveIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    monthly_ad_cost = models.ForeignKey(MonthlyAdCost, on_delete=models.SET_NULL, null=True, blank=True)

    PRICING_MODEL_CHOICES = [
        ('CPC', 'CPC'),
        ('CPM', 'CPM'),
    ]

    pricing_model = models.CharField(
        max_length=3,
        choices=PRICING_MODEL_CHOICES,
        default='CPC',
    )

    actual_cpc_or_cpm = models.DecimalField(
        max_digits=4, 
        decimal_places=1,
        null=True,
        blank=True
    )

    STATUS_CHOICES = [
        ('pending', 'Pending'),  # 公開前
        ('running', 'Running'),  # 公開中
        ('achieved', 'Achieved'),  # 目標達成
        ('expired', 'Expired'),  # 終了期限が来た
        ('stopped', 'Stopped'),  # ストップした
    ]

    status = models.CharField(
        max_length=8, 
        choices=STATUS_CHOICES, 
        default='pending'  # デフォルトを「公開前」に設定
    )

    class Meta:
        db_table = 'adcampaigns'

    def __str__(self):
        return self.title

    # キャンペーンの状態を判断するためのメソッド
    def is_ongoing(self):
        now = timezone.now()

        # start_dateが設定されていない場合、またはstart_dateが現在の日時よりも前の場合にTrueを返す
        if self.start_date and now < self.start_date:
            return False

        if self.end_date is None:
            return True  # end_dateが設定されていない場合は、キャンペーンは進行中と見なす
        return now <= self.end_date

    def recalculate_campaign(self):
        # total_views_count の再計算
        total_views = sum(ad_info.post.views_count for ad_info in self.ad_infos.all())
        self.total_views_count = total_views

        # 実際の表示回数(total_views_count)でactual_cpc_or_cpm と fee の再計算
        if self.pricing_model == 'CPM':
            self.actual_cpc_or_cpm = Decimal(self.monthly_ad_cost.calculate_cpm(self.total_views_count))
            self.fee = Decimal(self.total_views_count / 1000) * self.actual_cpc_or_cpm
        elif self.pricing_model == 'CPC':
            total_clicks = AdInfos.objects.filter(ad_campaign=self).aggregate(total_clicks=Sum('clicks_count'))['total_clicks']
            total_clicks = total_clicks or 0
            self.total_clicks_count = total_clicks
            self.actual_cpc_or_cpm = Decimal(self.monthly_ad_cost.calculate_cpc(self.total_views_count))
            self.fee = Decimal(self.total_clicks_count) * self.actual_cpc_or_cpm
        
        # 小数第一位まで保存し、それ以降は切り上げ
        self.actual_cpc_or_cpm = self.actual_cpc_or_cpm.quantize(Decimal('0.1'), rounding=ROUND_UP)
        self.fee = self.fee.quantize(Decimal('0.1'), rounding=ROUND_UP)
        
        self.save()

class AdInfos(models.Model):
    post = models.OneToOneField(Posts, on_delete=models.CASCADE)
    ad_campaign = models.ForeignKey(AdCampaigns, on_delete=models.CASCADE, related_name='ad_infos')
    clicks_count = models.PositiveIntegerField(default=0)
    fee = models.PositiveIntegerField(default=0)
    
    def __str__(self):
        return f"{self.post.title} - {self.ad_campaign.title} - {self.clicks_count}"
    
    def click_through_rate(self):
        if self.post.views_count == 0:
            return 0
        return (self.clicks_count / self.post.views_count) * 100

    def __str__(self):
        return f"{self.ad_campaign.title} - {self.post.title}"

    def update_fee(self):
        if self.ad_campaign.pricing_model == 'CPM':
            views_count_decimal = Decimal(self.post.views_count) / Decimal(1000)
            self.fee = views_count_decimal * self.ad_campaign.actual_cpc_or_cpm
        elif self.ad_campaign.pricing_model == 'CPC':
            self.fee = Decimal(self.clicks_count) * self.ad_campaign.actual_cpc_or_cpm
    
    
class RequestDocument(models.Model):
    company_name = models.CharField(max_length=255, verbose_name='社名')
    email = models.EmailField(verbose_name='メールアドレス')
    address = models.CharField(max_length=255, verbose_name='住所')
    phone_number = models.CharField(max_length=20, verbose_name='電話番号')
    
    def __str__(self):
        return f"{self.company_name} - {self.email}"


class SetMeeting(models.Model):
    MEETING_CHOICES = [
        ('zoom', 'Zoom'),
        ('email', 'Email'),
        ('chat', 'Chat'),
    ]
    company_name = models.CharField(max_length=100, null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    phone_number = models.CharField(max_length=15, null=True, blank=True)
    meeting_type = models.CharField(max_length=5, choices=MEETING_CHOICES)
    date_time_1 = models.DateTimeField(null=True, blank=True)
    date_time_2 = models.DateTimeField(null=True, blank=True)
    date_time_3 = models.DateTimeField(null=True, blank=True)
    date_time_4 = models.DateTimeField(null=True, blank=True)
    date_time_5 = models.DateTimeField(null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    x_account = models.CharField(max_length=15, null=True, blank=True)
    
    def __str__(self):
        return f"{self.company_name} - {self.meeting_type}"

class MonthlyBilling(models.Model):
    ad_campaign = models.ForeignKey(AdCampaigns, on_delete=models.CASCADE, related_name='monthly_billings')
    month_year = models.DateField()  # YYYY-MM-DD形式で保存
    monthly_fee = models.DecimalField(max_digits=10, decimal_places=2)  # その月の料金
    monthly_views = models.PositiveIntegerField(default=0)  # その月の表示回数
    monthly_clicks = models.PositiveIntegerField(default=0)  # その月のクリック回数
    
    class Meta:
        unique_together = (('ad_campaign', 'month_year'),)

    def __str__(self):
        return f"{self.ad_campaign.title} - {self.month_year.strftime('%Y-%m')}"

    @staticmethod
    def calculate_monthly_billing():
        now = datetime.now()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        # 月の途中で終了したキャンペーンまたは実行中のキャンペーンを検索する
        campaigns = AdCampaigns.objects.filter(
            Q(status='running') |
            (
                Q(status='expired') | 
                Q(status='achieved') | 
                Q(status='stopped')
            ) & Q(end_date__range=(month_start, now))
        )

        # 各キャンペーンに対して月末の料金を計算し、MonthlyBillingオブジェクトを作成する
        for campaign in campaigns:
            # 関連する全てのMonthlyBillingを取得し、値の合計を計算する
            aggregate_data = MonthlyBilling.objects.filter(
                ad_campaign=campaign
            ).aggregate(
                total_views=Sum('monthly_views'),
                total_clicks=Sum('monthly_clicks'),
                total_fee=Sum('monthly_fee')
            )

            # 月末の表示回数、クリック回数、料金を計算する
            monthly_views = campaign.total_views_count - (aggregate_data['total_views'] or 0)
            monthly_clicks = campaign.total_clicks_count - (aggregate_data['total_clicks'] or 0)
            monthly_fee = campaign.fee - (aggregate_data['total_fee'] or 0)

            # MonthlyBillingオブジェクトを作成する
            MonthlyBilling.objects.create(
                ad_campaign=campaign,
                month_year=now.date().replace(day=1),
                monthly_views=monthly_views,
                monthly_clicks=monthly_clicks,
                monthly_fee=monthly_fee
            )

