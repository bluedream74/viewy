# Python standard library
from datetime import datetime
from io import BytesIO
from tempfile import NamedTemporaryFile
import os
import re
import subprocess
import boto3
import json
import time
import tempfile
import shutil
import re
from django.conf import settings

# Third-party libraries
from django.core.files.base import File, ContentFile
from django.core.files.storage import default_storage
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.db.models import Sum, Count
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from moviepy.editor import VideoFileClip
from PIL import Image
import requests
import imageio_ffmpeg as ffmpeg

# Local application/library specific imports
from accounts.models import Users
from management.models import SupportRate

from django.core.files.uploadedfile import InMemoryUploadedFile
import sys
from PIL import ImageSequence
from .tasks import async_encode_video



class Posts(models.Model):
    poster = models.ForeignKey(Users, on_delete=models.CASCADE, related_name='posted_posts')
    ismanga = models.BooleanField(default=False)
    title = models.CharField(max_length=40)
    hashtag1 = models.CharField(max_length=20, blank=True, null=True)
    hashtag2 = models.CharField(max_length=20, blank=True, null=True)
    hashtag3 = models.CharField(max_length=20, blank=True, null=True)
    caption = models.CharField(max_length=140, blank=True)
    url = models.URLField(max_length=500, blank=True, null=True)
    affiliate_tag = models.TextField(max_length=1000, blank=True, null=True)  # 広告タグを保存するフィールドを追加
    scheduled_post_time = models.DateTimeField(blank=True, null=True)  # 予約投稿用の日時フィールド
    posted_at = models.DateTimeField(auto_now_add=True)
    content_length = models.PositiveIntegerField(default=0)
    favorite = models.ManyToManyField(Users, through='Favorites', related_name='favorite_posts')
    favorite_count = models.PositiveIntegerField(default=0)
    support_favorite_count = models.PositiveIntegerField(default=0)
    views_count = models.PositiveIntegerField(default=0)
    support_views_count = models.FloatField(default=0.0) 
    report_count = models.PositiveIntegerField(default=0)
    is_hidden = models.BooleanField(default=False)
    favorite_rate = models.FloatField(default=0.0) 
    avg_duration = models.FloatField(default=0.0)
    qp = models.FloatField(default=1.0)
    emote1_count = models.PositiveIntegerField(default=0)
    emote2_count = models.PositiveIntegerField(default=0)
    emote3_count = models.PositiveIntegerField(default=0)
    emote4_count = models.PositiveIntegerField(default=0)
    emote5_count = models.PositiveIntegerField(default=0)
    emote_total_count = models.PositiveIntegerField(default=0)

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

    def get_report_count(self):
      return self.report_count

    def update_favorite_rate(self):
        if self.views_count == 0:
            self.favorite_rate = 0
        else:
            self.favorite_rate = (self.favorite_count / self.views_count) * 100

    def update_avg_duration(self, new_duration):
        """新しい滞在時間を使用して平均滞在時間を更新するメソッド"""
        total_duration = (self.avg_duration * self.views_count) + new_duration
        self.avg_duration = total_duration / (self.views_count + 1)  # まだviews_countを更新していないので+1をします
    
    # def average_duration(self):
    #     """滞在時間の平均を返すメソッド"""     
    #     # 合計視聴期間,視聴回数をまとめて取得
    #     aggregates = self.viewed_post.aggregate(
    #         total_duration=Sum('duration'), total_views=Count('*')
    #     )
    #     total_duration = aggregates['total_duration'] or 0
    #     total_views = aggregates['total_views']

    #     if total_views == 0:
    #         return 0

    #     avg_duration = total_duration / total_views
    #     return avg_duration

    def stay_rate(self):
        """滞在率を算出するメソッド"""
        if self.content_length == 0:
            return 0      
        stay_rate_value = (self.avg_duration / self.content_length) * 100  # 100%を超えても許容
        print(f"平均滞在時間: {self.avg_duration}")
        print(f"滞在率: {stay_rate_value}")
        return stay_rate_value

    def stay_rate_point(self):
        """滞在率に基づいた評価ポイントを算出するメソッド"""
        point = self.stay_rate() * (1 + self.content_length / 15)
        print(f"滞在ポイント: {point}")
        return point

    def calculate_qp(self, requesting_user=None, factor_a=20, factor_b=1):
        """QPを算出するメソッド. factor_aとfactor_bはいいね率と滞在率の重みです"""
        
        boost_multipliers = {
            'normal': 1,
            'firstboost': 1.2,
            'boost': 1.4,
            'superboost': 1.6,
            'viewyboost': 10
        }
        

        # この投稿の投稿者のブーストの倍数を取得
        multiplier = boost_multipliers.get(self.poster.boost_type, 1)  # boost_typeが認識されない場合はデフォルトで1を使用

        self.qp = ((self.favorite_rate / 100 * factor_a) + (self.stay_rate_point() / 100 * factor_b)) * multiplier

        # postのposterのis_realがfalseであれば、SupportRateモデルのsupport_manga_rateでQPを掛ける
        if hasattr(self.poster, 'is_real') and not self.poster.is_real:
            try:
                manga_rate = SupportRate.objects.get(name='support_manga_qp_rate').value
                self.qp *= float(manga_rate)  # manga_rateをfloatにキャスト
                print(f"マンガのQP倍数: {manga_rate}")
            except ObjectDoesNotExist:
                pass  # support_manga_rateが見つからなかった場合、何もしない

        # QPが3より大きい場合、3に制限する
        if self.qp > 3:
            self.qp = 3

        # boostより上のブーストタイプを持つ場合、その状態をprint
        if multiplier > boost_multipliers['boost']:
            print(f"この投稿者は {self.poster.boost_type} 状態です。")

        print(f"QP（{self.poster.boost_type}適用）: {self.qp}")
        
    def update_qp_if_necessary(self):
        """視聴回数に基づき、必要に応じてQPを更新するメソッド"""
        if self.views_count <= 10000 or (self.views_count > 10000 and self.views_count % 30 == 0) or self.views_count == 20000:
            # print(f"Updating QP for view count: {self.views_count}")
            self.calculate_qp()
    
    def calculate_rp_for_user(self, followed_posters_set, viewed_count, followed_recommends_set):
        rp = self.qp
        rp = rp / (3 ** viewed_count)

        # ユーザーがフォローしているポスターによるポストの場合
        if self.id in followed_posters_set:
            rp = rp * 2
        
        # ユーザーがフォローしているユーザーによるリコメンドの場合
        if self.id in followed_recommends_set:
            rp = rp * 2
            print(f"Post ID: {self.id} - Boosted by recommendation from a followed user")

        return rp

    @property
    def emote_total_count_display(self):
        if self.emote_total_count >= 10000:
            return f"{self.emote_total_count / 1000:.1f}K"
        return str(self.emote_total_count)



# 投稿をピン止めするためのモデル
class PinnedPost(models.Model):
    user = models.ForeignKey(Users, on_delete=models.CASCADE, related_name='pinned_by')
    post = models.ForeignKey(Posts, on_delete=models.CASCADE, related_name='pinned_posts')
    created_at = models.DateTimeField(auto_now_add=True)  # ピン留めの日時

    class Meta:
        unique_together = ('user', 'post')  # 同じ投稿を一人のユーザーが複数回ピン止めすることはできません
        ordering = ['-created_at']  # created_atフィールドで降順にソートします




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
    
    
    
# Videosのupload_toのための関数
def adjust_video_pass(instance, filename):
    base, ext = os.path.splitext(filename)
    # ファイル名に既にタイムスタンプが含まれているか確認
    timestamp_pattern = re.compile(r"_\d{14}")
    if timestamp_pattern.search(base):
        # 既にタイムスタンプがある場合、新しいタイムスタンプを付けずに元のファイル名を返す
        return f"posts_videos/{base}{ext}"
    new_name = f"{base}_{instance.post.poster.id}_{datetime.now().strftime('%Y%m%d%H%M%S')}{ext}"
    return f"posts_videos/{new_name}"

    
class Videos(models.Model):
    post = models.ForeignKey(
        Posts, 
        on_delete=models.CASCADE,
        related_name='videos'
    )
    video = models.FileField(upload_to=adjust_video_pass)
    thumbnail = models.ImageField(upload_to='posts_videos_thumbnails', null=True, blank=True)
    encoding_done = models.BooleanField(default=False)
    hls_path = models.CharField(max_length=500, blank=True, null=True)
    dash_path = models.CharField(max_length=500, blank=True, null=True)

    class Meta:
        db_table = 'videos'

    def __str__(self):
        return self.post.title + ':' + str(self.id)

    def save(self, *args, **kwargs):
        print("save method started.")
        super().save(*args, **kwargs)
        if not self.encoding_done:
            async_encode_video.delay(self.id)
        else:
            print("save method completed without encoding.")
            
            
    def get_s3_client(self):  # __init__として呼び出していたのから変更。動画の投稿時（upload_to_s3）だけに呼び出すように。
        # hasattr 関数は、第一引数にオブジェクト、第二引数に属性名の文字列を取り、その属性がオブジェクトに存在するかどうかをブール値（True または False）で返します。
        # このコードの目的は、「もし _s3_client という属性がまだ self オブジェクトに設定されていなければ、新しい boto3 S3 クライアントを作成して _s3_client 属性にセットする」というものです。
        if not hasattr(self, '_s3_client'):
            self._s3_client = boto3.client(
                's3',
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_S3_REGION_NAME
            )
            print("get_s3_clientによるboto3クライアントの設定が行われました")
        return self._s3_client
    
# 縦長か横長か判別        
    def get_video_dimensions(self, video_path):
        cmd = ["ffprobe", "-v", "error", "-select_streams", "v:0", 
               "-show_entries", "stream=width,height", 
               "-of", "csv=s=x:p=0", video_path]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        dimensions = result.stdout.decode().strip().split('x')
        return int(dimensions[0]), int(dimensions[1])
    
    
    def run_ffmpeg_command(self, cmd, format_name):
        try:
            subprocess.run(cmd, check=True)
            print(f"{format_name} conversion successful.")
        except subprocess.CalledProcessError as e:
            print(f"Error during {format_name} conversion: {str(e)}")
            
    def upload_directory_to_s3(self, local_directory_path, bucket_name, s3_directory_path):
        print(f"Starting to upload files from {local_directory_path} to {bucket_name}/{s3_directory_path}")
        for root, dirs, files in os.walk(local_directory_path):
            for file in files:
                local_file_path = os.path.join(root, file)
                relative_path = os.path.relpath(local_file_path, local_directory_path)
                s3_file_path = os.path.join(s3_directory_path, relative_path).replace("\\", "/")
                print(f"Uploading {local_file_path} to {bucket_name}/{s3_file_path}...")
                if self.upload_to_s3(local_file_path, bucket_name, s3_file_path):
                    print(f"Successfully uploaded {local_file_path} to {bucket_name}/{s3_file_path}")
                else:
                    print(f"Failed to upload {local_file_path} to {bucket_name}/{s3_file_path}")
        print("File upload process completed.")
        
    def upload_to_s3(self, local_file_path, bucket_name, s3_file_path):
        s3_client = self.get_s3_client()   # ここでboto3クライアントを生成させる
        try:
            with open(local_file_path, 'rb') as data:
                s3_client.upload_fileobj(data, bucket_name, s3_file_path)
            print(f"{local_file_path} has been uploaded to {bucket_name}/{s3_file_path}")
            return True
        except Exception as e:
            print(f"Upload failed: {e}")
            return False
    
    
    def generate_streaming_formats(self, input_path, output_basename):
        print("Starting streaming format generation.")

        # ここで一旦、FFmpegで変換した動画たちやマニフェストファイルを一時ファイルに保存するようにする
        with tempfile.TemporaryDirectory() as temp_dir:
            # HLSとDASH形式での変換設定を追加
            hls_dir = os.path.join(temp_dir, "hls")
            dash_dir = os.path.join(temp_dir, "dash")
            os.makedirs(hls_dir, exist_ok=True)
            os.makedirs(dash_dir, exist_ok=True)

            # HLS形式での変換コマンド
            hls_playlist_output = os.path.join(hls_dir, f"{output_basename}.m3u8")
            hls_cmd = [
                "ffmpeg",
                "-i", input_path,
                "-c", "copy",  # コピーしてエンコードをスキップ
                "-f", "hls",
                "-hls_time", "2",  # セグメントの持続時間（秒）
                "-hls_playlist_type", "vod",
                hls_playlist_output
            ]

            # DASH形式での変換コマンド
            dash_manifest_output = os.path.join(dash_dir, f"{output_basename}.mpd")
            dash_cmd = [
                "ffmpeg",
                "-i", input_path,
                "-c", "copy",  # コピーしてエンコードをスキップ
                "-f", "dash",
                "-seg_duration", "2",  # セグメントの持続時間（秒）
                "-dash", "1",
                dash_manifest_output
            ]

            # HLS形式での変換を実行
            print("Generating HLS playlist...")
            self.run_ffmpeg_command(hls_cmd, "HLS")
            print("HLS playlist generation completed.")

            # DASH形式での変換を実行
            print("Generating DASH manifest...")
            self.run_ffmpeg_command(dash_cmd, "DASH")
            print("DASH manifest generation completed.")
            
            # settingsからバケット名を取得。無ければエラーを返す
            bucket_name = settings.AWS_STORAGE_BUCKET_NAME
            if not bucket_name:
                print("Error: S3 bucket name is not configured")
                return
            
            # タイムスタンプを取得
            timestamp = time.strftime("%Y%m%d%H%M%S")

            # 一意なディレクトリ名を生成
            unique_dir_name = f"{output_basename}_{timestamp}"

            # HLS チャンクとマニフェストファイルをS3にアップロード
            hls_manifest_path = f"hls/{unique_dir_name}/{output_basename}.m3u8"
            self.upload_directory_to_s3(hls_dir, bucket_name, f"hls/{unique_dir_name}/")
            self.hls_path = hls_manifest_path
            print("HLS files uploaded to S3.")

            # DASH チャンクとマニフェストファイルをS3にアップロード
            dash_manifest_path = f"dash/{unique_dir_name}/{output_basename}.mpd"
            self.upload_directory_to_s3(dash_dir, bucket_name, f"dash/{unique_dir_name}/")
            self.dash_path = dash_manifest_path
            print("DASH files uploaded to S3.")
    

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

            width, height = self.get_video_dimensions(temp_path)

            # この部分で取得した動画の解像度を出力して確認
            print(f"Original dimensions: {width}x{height}")

            # 縦長か横長かを判定
            if width > height:  # 横長の場合
                scale_cmd = "scale=-2:360"
                bitrate = "300k"  # 横長の場合のビットレート
            else:  # 縦長の場合
                scale_cmd = "scale=-2:720"
                bitrate = "500k"  # 縦長の場合のビットレート

            # こちらで変更後のスケールコマンドを出力して確認
            print(f"Scaling command: {scale_cmd}")

            # 元動画のコーデックを確認
            print(f"Detected codec: {codec}")

            framerate_cmd = ["-r", "24"]  # フレームレートを24fpsに指定

            # 圧縮の種類（コーデック）によってエンコードの処理を分ける
            if codec in ["hevc", "h264"]:
                cmd = [
                    "ffmpeg",
                    "-i", temp_path,
                    "-c:v", "libx264",
                    "-vf", scale_cmd,
                    *framerate_cmd,  # リストを展開
                    "-g", "48",  # キーフレーム間の間隔を48に設定
                    "-profile:v", "main",  # プロファイルをmainに設定
                    "-level", "3.0", 
                    output_path
                ]
            else:  # 他のコーデックの場合、デフォルトをlibx264に設定
                cmd = [
                    "ffmpeg",
                    "-i", temp_path,
                    "-c:v", "libx264",
                    "-vf", scale_cmd,
                    *framerate_cmd,  # リストを展開
                    "-g", "48",  # キーフレーム間の間隔を48に設定
                    "-profile:v", "main",  # プロファイルをmainに設定
                    "-level", "3.0", 
                    output_path
                ]


            # FFmpegコマンドの実行
            print(f"FFmpeg command: {' '.join(cmd)}")
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if result.returncode != 0:
                error_message = f"FFmpeg command failed with error: {result.stderr.decode()}"
                print(error_message)
                raise Exception(error_message)

            # エンコードされた動画をFileFieldに保存
            with open(output_path, 'rb') as f:
                encoded_video_basename = os.path.basename(self.video.name)
                encoded_video_name = f"{os.path.splitext(encoded_video_basename)[0]}_{datetime.now().strftime('%Y%m%d%H%M%S')}_encoded.mp4"
                self.video.save(encoded_video_name, File(f), save=False)

            # ストリーミング用の形式変換処理を実行
            self.generate_streaming_formats(self.video.url, encoded_video_basename)

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
    
    def __str__(self):
        return f"{self.post}-{self.user}"
  
  
class Collection(models.Model):
    user = models.ForeignKey(Users, on_delete=models.CASCADE, related_name='collections')
    name = models.CharField(max_length=40)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.user.username}"

class Collect(models.Model):
    collection = models.ForeignKey(Collection, on_delete=models.CASCADE, related_name='collects')
    post = models.ForeignKey(Posts, on_delete=models.CASCADE, related_name='collected_in')
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['collection', 'post']

    def __str__(self):
        return f"{self.collection.name} - {self.post.title}"
    

class Recommends(models.Model):
    user = models.ForeignKey(Users, on_delete=models.CASCADE, related_name='recommend_given')
    post = models.ForeignKey(Posts, on_delete=models.CASCADE, related_name='recommend_received')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'post']  # 同じユーザーが同じポストに複数回リコメンドできないように制約を設定

    def __str__(self):
        return f"{self.user} recommends {self.post}"
    
    
  
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
        
        
# 視聴履歴、滞在時間を管理するモデル
class ViewDurations(models.Model):
    user = models.ForeignKey(Users, on_delete=models.CASCADE, related_name='viewed_user', null=True)
    post = models.ForeignKey(Posts, on_delete=models.CASCADE, related_name='viewed_post', null=True)
    duration = models.PositiveIntegerField(default=0)  # 視聴時間（秒）
    viewed_at = models.DateTimeField(default=datetime.now)  # 視聴または閲覧された日時

    class Meta:
        unique_together = ('user', 'post', 'viewed_at')  # 同一ユーザーが同一投稿を同一日時に複数回閲覧することは考慮しない

    def __str__(self):
        return f"{self.user} - {self.post} - {self.duration} - {self.viewed_at}"
    
    

class TomsTalk(models.Model):
    image = models.ImageField(upload_to='tomstalk', blank=True, null=True)
    name = models.CharField(max_length=25, default='トム')
    status = models.CharField(max_length=25, default='アンバサダー')
    content = models.CharField(max_length=120)
    url = models.URLField(blank=True, null=True)
    display_rate = models.IntegerField(default=1)
    
    def __str__(self):
        return self.content
    
    def save(self, *args, **kwargs):
        # 画像が提供された場合のリサイズ処理
        if self.image:
            # 画像を開く
            image = Image.open(self.image)

            # リサイズしたい解像度を設定
            output_size = (300, 300)  # 例: 300x300
            image.thumbnail(output_size)

            # 透明度情報が含まれている場合はRGBモードに変換
            if image.mode == 'RGBA':
                image = image.convert('RGB')

            # 画像を一時的なバイナリストリームに保存
            output = BytesIO()
            image.save(output, format='JPEG', quality=85)
            output.seek(0)

            # InMemoryUploadedFileに変換して、元の画像フィールドに再設定
            self.image = InMemoryUploadedFile(output, 'ImageField', f"{self.image.name.split('.')[0]}.jpeg", 'image/jpeg', sys.getsizeof(output), None)
        
        super(TomsTalk, self).save(*args, **kwargs)

    def get_url_prefix(self):
        if not self.url:
            return ''
        elif 'twitter' in self.url:
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
            return 'link'