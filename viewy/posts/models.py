# Python standard library
from datetime import datetime
from io import BytesIO
from tempfile import NamedTemporaryFile
import os
import subprocess
import json
from django.conf import settings

# Third-party libraries
from django.core.files.base import File, ContentFile
from django.core.files.storage import default_storage
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from moviepy.editor import VideoFileClip
from PIL import Image
import requests
import imageio_ffmpeg as ffmpeg

# Local application/library specific imports
from accounts.models import Users

from django.core.files.uploadedfile import InMemoryUploadedFile
import sys
from PIL import ImageSequence




class Posts(models.Model):
    poster = models.ForeignKey(Users, on_delete=models.CASCADE, related_name='posted_posts')
    ismanga = models.BooleanField(default=False)
    title = models.CharField(max_length=30)
    hashtag1 = models.CharField(max_length=20)
    hashtag2 = models.CharField(max_length=20)
    hashtag3 = models.CharField(max_length=20)
    caption = models.CharField(max_length=100)
    url = models.URLField(max_length=80, null=True)
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
        if 'twitter' in self.url:
            return 'x'
        elif 'x.com' in self.url:
            return 'x'
        elif 'youtube' in self.url:
            return 'youtube'
        elif 'fantia' in self.url:
            return 'fantia'
        elif 'myfans' in self.url:
            return 'myfans'
        elif 'pornhub' in self.url:
            return 'pornhub'      
        elif 'candfans' in self.url:
            return 'candfans'            
        elif 'lit.link' in self.url:
            return 'lit.link'      
        elif 'dlsite' in self.url:
            return 'dlsite'      
        elif 'amazon' in self.url:
            return 'amazon'      
        elif 'fanza' in self.url:
            return 'fanza'      
        elif 'skeb' in self.url:
            return 'skeb'      
        elif 'shikoshiko' in self.url:
            return 'cherrylive'      
        elif 'profu.link' in self.url:
            return 'profu.link'      
        elif 'knip' in self.url:
            return 'knip'      
        else:
            return 'default'
        
    def increment_report_count(self):
      self.report_count += 1
      if self.report_count > 50:    # 通報が５０回より多くなったら非表示にする
        self.is_hidden = True
      self.save()

    def get_report_count(self):
      return self.report_count

    def update_favorite_rate(self):
        if self.views_count == 0:
            self.favorite_rate = 0
        else:
            self.favorite_rate = (self.favorite_count / self.views_count) * 100



class Ads(models.Model):
    title = models.CharField(max_length=20)
    hashtag1 = models.CharField(max_length=20, default='')
    hashtag2 = models.CharField(max_length=20, default='')
    hashtag3 = models.CharField(max_length=20, default='')
    caption = models.CharField(max_length=100, default='')
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


class WideAds(models.Model):
    title = models.CharField(max_length=20)
    url = models.URLField(max_length=200, null=True, blank=True)
    ad_tag = models.TextField()  # 広告タグを保存するフィールド
    views_count = models.PositiveIntegerField(default=0)
    click_count = models.PositiveIntegerField(default=0)
    click_rate = models.FloatField(default=0.0)

    class Meta:
        db_table = 'wideads'

    def update_click_rate(self):
        if self.views_count == 0:
            self.click_rate = 0
        else:
            self.click_rate = (self.click_count / self.views_count) * 100 
        
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
    # 新規オブジェクトの場合、一時的に画像を保存
    old_image_name = self.visual.name if self.visual else None  # 元の画像の名前を保存

    # 新規オブジェクトの場合、一時的に画像を保存
    if self.pk is None:
        saved_image = self.visual
        self.visual = None
        super().save(*args, **kwargs)
        self.visual = saved_image

    # 画像の解像度変更処理
    if self.visual:
        # 画像を開く
        image = Image.open(self.visual)

        # 画像のモードに応じて保存方法を分岐
        if image.format == 'GIF':
            output_size = 480
            frames = [frame.copy() for frame in ImageSequence.Iterator(image)]
            resized_frames = [frame.resize((output_size, output_size * frame.height // frame.width), Image.LANCZOS) if frame.width > frame.height else frame.resize((output_size * frame.width // frame.height, output_size), Image.LANCZOS) for frame in frames]
            output = BytesIO()
            resized_frames[0].save(output, format='GIF', append_images=resized_frames[1:], save_all=True, duration=image.info['duration'], loop=0)
            output_format = 'GIF'
            content_type = 'image/gif'
        else:
            output_size = (1080, 1080)
            image.thumbnail(output_size)
            output = BytesIO()
            if image.mode != 'RGB':
                image = image.convert('RGB')
            image.save(output, format='JPEG', quality=85)
            output_format = 'JPEG'
            content_type = 'image/jpeg'

        output.seek(0)

        # InMemoryUploadedFileに変換して、元の画像フィールドに再設定
        self.visual = InMemoryUploadedFile(output, 'ImageField', f"{self.visual.name.split('.')[0]}.{output_format.lower()}", content_type, sys.getsizeof(output), None)

    super().save(*args, **kwargs)

    # 以前の画像を削除
    if old_image_name and old_image_name != self.visual.name:
        if default_storage.exists(old_image_name):
            default_storage.delete(old_image_name)
    
    
    
class Videos(models.Model):
    post = models.ForeignKey(
        Posts, 
        on_delete=models.CASCADE,
        related_name='videos'
    )
    video = models.FileField(upload_to='posts_videos')
    thumbnail = models.ImageField(upload_to='posts_videos_thumbnails', null=True, blank=True)
    encoding_done = models.BooleanField(default=False)

    class Meta:
        db_table = 'videos'

    def __str__(self):
        return self.post.title + ':' + str(self.id)

    def save(self, *args, **kwargs):
        print("save method started.")
        if not self.encoding_done:
            # 最初にデータを保存
            super().save(*args, **kwargs)
            print("Original data saved.")

            original_video_name = self.video.name

            # エンコード中に問題発生した場合、finallyで一時ファイルを削除
            try:
                # エンコード処理
                print(f"Encoding video: {original_video_name}")
                self.encode_video()

                # サムネイルの作成
                if not self.thumbnail:
                    print("Creating thumbnail.")
                    self.create_thumbnail()

                # フラグの更新
                self.encoding_done = True
                super().save(*args, **kwargs)
                print("Encoded data saved.")

                # エンコード後、元の高画質の動画を削除
                if default_storage.exists(original_video_name):
                    default_storage.delete(original_video_name)
                    print(f"Deleted original video: {original_video_name}")

            except Exception as e:
                # エンコードに失敗した場合、作成したレコードも削除する
                self.delete()
                error_msg = "ビデオの投稿中にエラーが発生しました。投稿中は他の操作をしないでください。"
                print(f"Deleted the record due to: {e}")
                raise e

        else:
            super().save(*args, **kwargs)
            print("save method completed without encoding.")

# エンコードの処理
    def encode_video(self):
        print("encode_video method started.")
        video_url = self.video.url
        response = requests.get(video_url, stream=True)
        response.raise_for_status()

        temp_path = None
        output_path = None
        try:
            with NamedTemporaryFile(delete=False, suffix=".mp4") as temp_file:
                for chunk in response.iter_content(chunk_size=8192):
                    temp_file.write(chunk)
                temp_path = temp_file.name
                print(f"Video downloaded to: {temp_path}")

            # コーデックを取得する関数を呼び出す（後に記述）
            codec = self.get_video_codec(temp_path)
        
            # エンコード後の動画ファイルの名前に_encodedを追加
            output_path = os.path.splitext(temp_path)[0] + "_encoded.mp4"

            # 圧縮の種類（コーデック）によってエンコードの処理を分ける
            if codec == "hevc":
                cmd = [
                    "ffmpeg",
                    "-i", temp_path,
                    "-c:v", "libx265",
                    "-vf", "scale=-2:720",
                    output_path
                ]
            else:
                cmd = [
                    "ffmpeg",
                    "-i", temp_path,
                    "-c:v", "libx264",
                    "-vf", "scale=-2:720",
                    output_path
                ]

            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            if result.returncode != 0:
                error_message = f"FFmpeg command failed with error: {result.stderr.decode()}"
                print(error_message)
                raise Exception(error_message)

            with open(output_path, 'rb') as f:
                encoded_video_basename = os.path.basename(self.video.name)
                encoded_video_name = os.path.splitext(encoded_video_basename)[0] + "_encoded.mp4"
                self.video.save(encoded_video_name, File(f), save=False)

        finally:
            # 一時ファイルを確実に削除
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)
            if output_path and os.path.exists(output_path):
                os.remove(output_path)

        print("encode_video method completed.")


# コーデックの種類を取得する関数
    def get_video_codec(self, video_path):
        cmd = [
            'ffprobe',
            '-v', 'quiet',
            '-print_format', 'json',
            '-show_streams',
            video_path
        ]

        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output = result.stdout.decode('utf-8')
        data = json.loads(output)

        for stream in data['streams']:
            if stream['codec_type'] == 'video':
                return stream['codec_name']

        return None

# サムネイルを作る関数
    def create_thumbnail(self):
        print("create_thumbnail method started.")
        video_url = self.video.url
        response = requests.get(video_url, stream=True)
        response.raise_for_status()

        with NamedTemporaryFile(delete=False, suffix=".mp4") as temp_file:
            for chunk in response.iter_content(chunk_size=8192):
                temp_file.write(chunk)
            temp_path = temp_file.name
            print(f"Video downloaded for thumbnail: {temp_path}")

        try:
            clip = VideoFileClip(temp_path)
            frame = clip.get_frame(0)
            video_aspect_ratio = clip.size[0] / clip.size[1]

            img = Image.fromarray(frame)
            thumbnail_io = BytesIO()

        # 縦長の動画なのに横長のサムネイルが保存されてる場合はここで修正
            if video_aspect_ratio <= 1:
                if video_aspect_ratio == 1920 / 1440:
                    new_size = (720, 960)
                    img = img.resize(new_size)
                elif video_aspect_ratio == 1920 / 1080:
                    new_size = (540, 960)
                    img = img.resize(new_size)

            img.save(thumbnail_io, format='JPEG')

            thumbnail_file = ContentFile(thumbnail_io.getvalue())
            thumbnail_name = f"{os.path.splitext(self.video.name)[0]}_{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg"
            self.thumbnail.save(thumbnail_name, thumbnail_file, save=False)
            print(f"Thumbnail saved as: {thumbnail_name}")

        finally:
            clip.close()
            os.remove(temp_path)
            print("create_thumbnail method completed.")

  
  
  
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

class KanjiHiraganaSet(models.Model):
    kanji = models.CharField(max_length=100, unique=True)
    hiragana = models.TextField()  # 複数のひらがなクエリをカンマ区切りなどで保存することができます。
    
    def __str__(self):
        return self.kanji

class RecommendedUser(models.Model):
    user = models.ForeignKey(Users, on_delete=models.CASCADE)
    order = models.PositiveIntegerField(unique=True)  # 各順序は一意でなければなりません

    class Meta:
        ordering = ['order']