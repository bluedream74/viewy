from django.db import models
from posts.models import Posts
from accounts.models import Features, Users
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Sum, Q
from decimal import Decimal, ROUND_UP
from django.db import transaction
import math

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

    # 割引率を定義
    DISCOUNT_RATE = 0.9  # 10%の割引

    def calculate_cpm(self, views, user):
        base_cpm = float(self.cpm)
        final_cpm = base_cpm

        if views >= 200000:
            final_cpm = base_cpm - 100

        if user.is_specialadvertiser:
            final_cpm *= self.DISCOUNT_RATE

        return final_cpm

    def calculate_cpc(self, clicks, user):
        base_cpc = float(self.cpc)
        final_cpc = base_cpc

        if clicks > 2000:
            final_cpc = base_cpc - 10

        if user.is_specialadvertiser:
            final_cpc *= self.DISCOUNT_RATE

        return final_cpc


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
    target_views = models.PositiveIntegerField(default=0, null=True, blank=True)
    target_clicks = models.PositiveIntegerField(default=0, null=True, blank=True) 
    fee = models.PositiveIntegerField(default=0, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    monthly_ad_cost = models.ForeignKey(MonthlyAdCost, on_delete=models.SET_NULL, null=True, blank=True)
    first_time = models.BooleanField(default=False)

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

    def recalculate_campaign(self, user):

        # actual_cpc_or_cpm と fee の再計算
        if self.pricing_model == 'CPM':
            # 実際の表示回数が10万回未満の場合、10万回分の料金を計算
            self.total_views_count = max(self.total_views_count, 100000)
            self.actual_cpc_or_cpm = Decimal(self.monthly_ad_cost.calculate_cpm(self.total_views_count, user))
            self.fee = math.ceil(Decimal(self.total_views_count / 1000) * self.actual_cpc_or_cpm)
        elif self.pricing_model == 'CPC':
            # 実際のクリック数が1000未満の場合、1000クリック分の料金を計算
            self.total_clicks_count = max(self.total_clicks_count, 1000)
            self.actual_cpc_or_cpm = Decimal(self.monthly_ad_cost.calculate_cpc(self.total_clicks_count, user))
            self.fee = math.ceil(Decimal(self.total_clicks_count) * self.actual_cpc_or_cpm)
        
        # 小数第一位まで保存し、それ以降は切り上げ
        self.actual_cpc_or_cpm = self.actual_cpc_or_cpm.quantize(Decimal('0.1'), rounding=ROUND_UP)
        

class AdInfos(models.Model):
    post = models.OneToOneField(Posts, on_delete=models.CASCADE)
    ad_campaign = models.ForeignKey(AdCampaigns, on_delete=models.CASCADE, related_name='ad_infos')
    clicks_count = models.PositiveIntegerField(default=0)
    fee = models.PositiveIntegerField(default=0)

    STATUS_CHOICES = [
        ('pending', '審査中'),
        ('failed', '審査失敗'),
        ('approved', '承認済み'),
    ]

    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='pending',
    )
    
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
    @transaction.atomic
    def calculate_monthly_billing(now=None):

        now = now or datetime.now()
        print(f"現在の日時: {now}")  
        # now = datetime.now()# 本番はこれ
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        print(f"月初めの日時: {month_start}")  # 月初めの日時を表示

        # 月の途中で終了したキャンペーンまたは実行中のキャンペーンを検索する
        campaigns = AdCampaigns.objects.filter(
            Q(status='running') |
            (
                Q(status='expired') | 
                Q(status='achieved') | 
                Q(status='stopped')
            ) & Q(end_date__range=(month_start, now))
        )
        print(f"該当するキャンペーン数: {campaigns.count()}")

        user_totals = {}

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

            print(f"キャンペーンID {campaign.id}: 表示回数 {monthly_views}, クリック回数 {monthly_clicks}, 料金 {monthly_fee}")

            # MonthlyBillingオブジェクトを作成する
            MonthlyBilling.objects.create(
                ad_campaign=campaign,
                month_year=now.date().replace(day=1),
                monthly_views=monthly_views,
                monthly_clicks=monthly_clicks,
                monthly_fee=monthly_fee
            )

            # ユーザーの合計を更新
            user_id = campaign.created_by_id
            user_totals[user_id] = user_totals.get(user_id, 0) + monthly_fee

        # UserMonthlyBillingSummary を保存
        for user_id, total_fee in user_totals.items():
            print(f"ユーザーID {user_id}: 合計料金 {total_fee}")
            user = Users.objects.get(id=user_id)
            billing_summary = UserMonthlyBillingSummary(
                user=user,
                month_year=month_start,
                total_fee=total_fee
            )
            billing_summary.save()

class UserMonthlyBillingSummary(models.Model):
    user = models.ForeignKey(Users, on_delete=models.CASCADE, related_name='monthly_billing_summaries')
    month_year = models.DateField()  # 集計する月の年と月
    total_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # 合計料金
    total_fee_with_tax = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # 税込み合計料金

    class Meta:
        unique_together = (('user', 'month_year'),)

    def __str__(self):
        return f"{self.user.username} - {self.month_year.strftime('%Y-%m')} - Total Fee: {self.total_fee} - Total Fee with Tax: {self.total_fee_with_tax}"

    def save(self, *args, **kwargs):
        # 税込み料金を計算する
        self.total_fee_with_tax = self.total_fee * Decimal('1.10')
        super(UserMonthlyBillingSummary, self).save(*args, **kwargs)
