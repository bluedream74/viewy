# Python standard library
from datetime import datetime
from io import BytesIO
import os

# Third-party libraries
from django.core.files.base import ContentFile
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from moviepy.editor import VideoFileClip
from tempfile import NamedTemporaryFile
from PIL import Image

# Local application/library specific
from accounts.models import Users

class Posts(models.Model):
    poster = models.ForeignKey(Users, on_delete=models.CASCADE, related_name='posted_posts')
    ismanga = models.BooleanField(default=False)
    title = models.CharField(max_length=50)
    hashtag1 = models.CharField(max_length=30)
    hashtag2 = models.CharField(max_length=30)
    hashtag3 = models.CharField(max_length=30)
    caption = models.CharField(max_length=300)
    url = models.URLField(max_length=200, null=True)
    posted_at = models.DateTimeField(auto_now_add=True)
    favorite = models.ManyToManyField(Users, through='Favorites', related_name='favorite_posts')
    favorite_count = models.PositiveIntegerField(default=0)
    views_count = models.PositiveIntegerField(default=0)
    viewed_by = models.ManyToManyField(Users, related_name='viewed_posts')
    report_count = models.PositiveIntegerField(default=0)
    is_hidden = models.BooleanField(default=False)
    favorite_rate = models.FloatField(default=0.0)  # 追加

    class Meta:
      db_table = 'posts'

    def __str__(self):
      return self.title

    def get_url_prefix(self):
      if self.url.startswith('https://twitter.com'):
          return 'twitter'
      elif self.url.startswith('https://www.youtube.com'):
          return 'youtube'
      else:
          return 'default'
        
    def increment_report_count(self):
      self.report_count += 1
      self.save()
      if self.report_count > 5:
        self.is_hidden = True
      self.save()

    def get_report_count(self):
      return self.report_count

    def update_favorite_rate(self):
        if self.views_count == 0:
            self.favorite_rate = 0
        else:
            self.favorite_rate = (self.favorite_count / self.views_count) * 100
        self.save()  # Here, we are saving the favorite_rate right after updating it


class Ads(models.Model):
    title = models.CharField(max_length=50)
    hashtag1 = models.CharField(max_length=30, default='')
    hashtag2 = models.CharField(max_length=30, default='')
    hashtag3 = models.CharField(max_length=30, default='')
    caption = models.CharField(max_length=300, default='')
    url = models.URLField(max_length=200, null=True, blank=True)
    ad_tag = models.TextField()  # 広告タグを保存するフィールドを追加
    views_count = models.PositiveIntegerField(default=0)
    click_count = models.PositiveIntegerField(default=0)
    click_rate = models.FloatField(default=0.0)  # 追加
    
    class Meta:
        db_table = 'ads'
        
    def update_click_rate(self):
      if self.views_count == 0:
          self.click_rate = 0
      else:
          self.click_rate = (self.click_count / self.views_count) * 100
      self.save()  # Here, we are saving the favorite_rate right after updating it

class Visuals(models.Model):
  # related_name引数を使用して、PostオブジェクトからVisualオブジェクトにアクセスするための逆参照名を設定している
  post = models.ForeignKey(
    Posts, 
    on_delete=models.CASCADE,
    related_name='visuals'
    )
  visual = models.ImageField(upload_to='posts_visuals')
  
  class Meta:
    db_table = 'visuals'
    
  def __str__(self):
    return self.post.title + ':' + str(self.id)
  
  def save(self, *args, **kwargs):
    if self.pk is None:
        saved_image = self.visual
        self.visual = None
        super().save(*args, **kwargs)
        self.visual = saved_image
    super().save(*args, **kwargs)
    
    
class Videos(models.Model):
    post = models.ForeignKey(
        Posts, 
        on_delete=models.CASCADE,
        related_name='videos'
    )
    video = models.FileField(upload_to='posts_videos')
    thumbnail = models.ImageField(upload_to='posts_videos_thumbnails', null=True, blank=True)
    
    class Meta:
        db_table = 'videos'
    
    def __str__(self):
        return self.post.title + ':' + str(self.id)
    
    def save(self, *args, **kwargs):
        if self.pk is None:
            saved_video = self.video
            self.video = None
            super().save(*args, **kwargs)
            self.video = saved_video
        super().save(*args, **kwargs)
        
    def create_thumbnail(self):
      
      # 画面収録で撮影したり、LINEなどから保存した動画（つまりあらかじめ圧縮されたいた動画）はサムネイルがもともとうまくいっていた。問題が起きているのはそのスマホで撮影した動画を投稿するときである。しかしスマホが圧縮している段階に介入して操作するのはめんどっちいから、バグった比率のサムネイルを検出して無理やり変形して適応することにした。

        with NamedTemporaryFile(delete=False) as temp:
            for chunk in self.video.chunks():
                temp.write(chunk)
            temp_path = temp.name

        try:
            clip = VideoFileClip(temp_path)
            frame = clip.get_frame(0)  # サムネイルにするフレームを取得

            # PIL.Imageを使用してframeを画像として保存
            img = Image.fromarray(frame)
            thumbnail_io = BytesIO()
            
            # オリジナルの画像の解像度を取得
            original_size = img.size  # (width, height) のタプルが返されます

            # オリジナルの画像が1920:1440（比率が反転してるバグ画像）をもっているか確認
            if (original_size[0] / original_size[1] == 1920 / 1440):
                # 画像のサイズを指定した値に変更
                new_size = (720,960)  # このサイズは適切に調整してください
                img = img.resize(new_size)
                
            # オリジナルの画像が1920:1080をもっているか確認
            elif original_size[0] / original_size[1] == 1920 / 1080:
                # 画像のサイズを指定した値に変更
                new_size = (540,960)
                img = img.resize(new_size)
            
            img.save(thumbnail_io, format='JPEG')

            # ContentFileを使用してDjango Fileオブジェクトを生成
            thumbnail_file = ContentFile(thumbnail_io.getvalue())

            # 動画のファイル名と現在の日時を組み合わせた名前でサムネイルを保存
            thumbnail_name = f"{os.path.splitext(self.video.name)[0]}_{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg"
            self.thumbnail.save(thumbnail_name, thumbnail_file, save=False)
        finally:
            clip.close()  # クリップを閉じる
            temp.close()  # ファイルを閉じる
            os.remove(temp_path)  # 一時ファイルを削除

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if not self.thumbnail:
            self.create_thumbnail()
            self.save()
  
  
  
class Favorites(models.Model):
  user = models.ForeignKey(Users, on_delete=models.CASCADE, related_name='favorite_received')
  post = models.ForeignKey(Posts, on_delete=models.CASCADE)
  created_at = models.DateTimeField(auto_now_add=True)
  
  
  
# 報告のモデル
class Report(models.Model):
    REASON_CHOICES = (
        ('underage', '未成年者が出演している'),
        ('insufficient_mosaic', 'モザイク処理が十分でない'),
        ('violent', '暴力的な内容'),
        ('inappropriate', '不適切な内容'),
        ('other', 'その他'),
    )

    reporter = models.ForeignKey(Users, on_delete=models.CASCADE, related_name='reported_posts')
    post = models.ForeignKey(Posts, on_delete=models.CASCADE, related_name='reports')
    reason = models.CharField(max_length=20, choices=REASON_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'reports'
        
    def __str__(self):
      return self.post.poster.username + ' : ' + self.post.title + ' : ' + self.reason
    
    
class HotHashtags(models.Model):
    hashtag1 = models.CharField(max_length=50, blank=True)
    hashtag2 = models.CharField(max_length=50, blank=True)
    hashtag3 = models.CharField(max_length=50, blank=True)
    hashtag4 = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'hothashtags'