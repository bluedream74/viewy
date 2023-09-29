from django.db import models
from posts.models import Posts
from accounts.models import Features, Users
from datetime import datetime, timedelta
from django.utils import timezone

class AndFeatures(models.Model):
    orfeatures = models.ManyToManyField(Features)
    is_all = models.BooleanField(default=False)

    def __str__(self):
        feature_names_ja = [str(feature.name_ja) for feature in self.orfeatures.all()]
        features_str_ja = "または".join(feature_names_ja)
        return features_str_ja

class AdCampaigns(models.Model):
    created_by = models.ForeignKey(Users, on_delete=models.CASCADE, related_name='created_campaigns')
    title = models.CharField(max_length=100)
    start_date = models.DateTimeField(default=datetime.now)
    end_date = models.DateTimeField()
    budget = models.PositiveIntegerField()
    total_views_count = models.PositiveIntegerField(default=0)
    is_hidden = models.BooleanField(default=False)  # キャンペーンの停止/再開を判断するカラム
    andfeatures = models.ManyToManyField(AndFeatures, blank=True)

    class Meta:
        db_table = 'adcampaigns'

    def __str__(self):
        return self.title

    # キャンペーンの状態を判断するためのメソッド
    def is_ongoing(self):
        now = timezone.now()
        return now <= self.end_date


    # AdInfosの視聴回数の合計を更新し、total_views_countに保存するメソッド
    def update_total_views(self):
        self.total_views_count = sum(ad_info.post.views_count for ad_info in self.ad_infos.all())
        self.save()

class AdInfos(models.Model):
    post = models.OneToOneField(Posts, on_delete=models.CASCADE)
    ad_campaign = models.ForeignKey(AdCampaigns, on_delete=models.CASCADE, related_name='ad_infos')
    clicks_count = models.PositiveIntegerField(default=0)
    
    def __str__(self):
        return f"{self.post.title} - {self.ad_campaign.title} - {self.clicks_count}"
    
    def click_through_rate(self):
        if self.post.views_count == 0:
            return 0
        return (self.clicks_count / self.post.views_count) * 100

    def __str__(self):
        return f"{self.ad_campaign.title} - {self.post.title}"

