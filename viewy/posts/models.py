# Python standard library
from datetime import datetime
from io import BytesIO
import os

# Third-party libraries
from django.core.files.base import ContentFile
from django.db import models
from moviepy.editor import VideoFileClip
from PIL import Image

# Local application/library specific
from accounts.models import Users


class Posts(models.Model):
  poster = models.ForeignKey(Users, on_delete=models.CASCADE, related_name='posted_posts')  # Update the reference to Users model
  ismanga = models.BooleanField(default=False)
  title = models.CharField(max_length=50)
  hashtag1 = models.CharField(max_length=30)
  hashtag2 = models.CharField(max_length=30)
  hashtag3 = models.CharField(max_length=30)
  caption = models.CharField(max_length=300)
  url = models.URLField(max_length=200, null=True)  # 新しいURLフィールド
  posted_at = models.DateTimeField(auto_now_add=True)
  favorite = models.ManyToManyField(Users, through='Favorites',related_name='favorite_posts')
  favorite_count = models.PositiveIntegerField(default=0)
  viewed_by = models.ManyToManyField(Users, related_name='viewed_posts')
  report_count = models.PositiveIntegerField(default=0)  # 報告回数のフィールド
  is_hidden = models.BooleanField(default=False)  # 非表示フラグ
  
  class Meta:
    db_table = 'posts'
    
  def __str__(self):
    return self.title
  
  def get_url_prefix(self):
    if self.url.startswith('https://twitter.com'):
        return 'twitter'
    elif self.url.startswith('https://www.youtube.com'):
        return 'youtube'
    # 追加の条件分岐を行うこともできます
    # 他のアプリのURLに対してもアイコンを設定する場合は、適宜追加してください
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
        from moviepy.editor import VideoFileClip
        from PIL import Image
        from io import BytesIO
        from django.core.files.base import ContentFile
        from tempfile import NamedTemporaryFile
        import os
        from datetime import datetime

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
        ('spam', 'スパム'),
        ('abuse', '虐待的な内容'),
        ('inappropriate', '不適切な内容'),
        ('other', 'その他'),
    )

    reporter = models.ForeignKey(Users, on_delete=models.CASCADE, related_name='reported_posts')
    post = models.ForeignKey(Posts, on_delete=models.CASCADE, related_name='reports')
    reason = models.CharField(max_length=20, choices=REASON_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'reports'