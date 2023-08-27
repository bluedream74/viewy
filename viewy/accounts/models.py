from django.db import models
from django.contrib.auth.models import (
    BaseUserManager, AbstractBaseUser, PermissionsMixin,
)
from django.urls import reverse_lazy
from django.contrib.auth import get_user_model

from PIL import Image
from io import BytesIO
from django.core.files.uploadedfile import InMemoryUploadedFile
import sys

from django.conf import settings

class UserManager(BaseUserManager):
    def create_user(self, username, email, password=None):
        user = self.model(
            username=username,
            email=email
        )
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, username, email, password=None):
        user = self.model(
            username=username,
            email=email,
        )
        user.set_password(password)
        user.is_staff = True
        user.is_active = True
        user.is_superuser = True
        user.save(using=self._db)
        return user
    
      
class Users(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(max_length=30, unique=True)
    email = models.EmailField(max_length=255, unique=True)
    prf_img = models.ImageField(upload_to='accounts_prf_imgs', null=True, blank=True)
    caption = models.CharField(max_length=120, null=True, blank=True)
    displayname = models.CharField(max_length=30, null=True, blank=True)
    url1 = models.URLField(max_length=200, null=True, blank=True) 
    url2 = models.URLField(max_length=200, null=True, blank=True) 
    url3 = models.URLField(max_length=200, null=True, blank=True) 
    url4 = models.URLField(max_length=200, null=True, blank=True) 
    url5 = models.URLField(max_length=200, null=True, blank=True) 
    is_active = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    poster_waiter = models.BooleanField(default=False)
    view_post_count = models.PositiveIntegerField(default=0)  # 視聴ポスト数のフィールド
    follow = models.ManyToManyField('self', through='Follows', symmetrical=False, related_name='followed_by')
    follow_count = models.PositiveIntegerField(default=0)
    report_count = models.PositiveIntegerField(default=0)  # 報告回数のフィールド
    verification_code = models.CharField(max_length=5, null=True, blank=True)   # 認証用のコード
    verification_code_generated_at = models.DateTimeField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    # ここの二つを同じフィールドに指定することが推奨されていないため仕方なくメールアドレスの項目を追加した
    
    objects = UserManager()
    
    def get_absolute_url(self):
        return reverse_lazy('accounts:home')
    
    def __str__(self):
        return self.username
    
    def increment_view_post_count(self):
        self.view_post_count += 1
        self.save()

    def get_view_post_count(self):
        return self.view_post_count
    
    def get_url1_prefix(self):
        if 'twitter' in self.url1:
            return 'x'
        elif 'x.com' in self.url1:
            return 'x'
        elif 'youtube' in self.url1:
            return 'youtube'
        elif 'fantia' in self.url1:
            return 'fantia'
        elif 'myfans' in self.url1:
            return 'myfans'
        elif 'pornhub' in self.url1:
            return 'pornhub'      
        elif 'candfans' in self.url1:
            return 'candfans'            
        elif 'lit.link' in self.url1:
            return 'lit.link'      
        elif 'dlsite' in self.url1:
            return 'dlsite'      
        elif 'amazon' in self.url1:
            return 'amazon'      
        elif 'fanza' in self.url1:
            return 'fanza'      
        elif 'skeb' in self.url1:
            return 'skeb'      
        elif 'dlsite' in self.url1:
            return 'dlsite'      
        elif 'shikoshiko' in self.url1:
            return 'cherrylive'      
        elif 'profu.link' in self.url1:
            return 'profu.link'      
        elif 'knip' in self.url1:
            return 'knip'      
        else:
            return 'link'


    def get_url2_prefix(self):
        if 'twitter' in self.url2:
            return 'x'
        elif 'x.com' in self.url2:
            return 'x'
        elif 'youtube' in self.url2:
            return 'youtube'
        elif 'fantia' in self.url2:
            return 'fantia'
        elif 'myfans' in self.url2:
            return 'myfans'
        elif 'pornhub' in self.url2:
            return 'pornhub'      
        elif 'candfans' in self.url2:
            return 'candfans'            
        elif 'lit.link' in self.url2:
            return 'lit.link'      
        elif 'dlsite' in self.url2:
            return 'dlsite'      
        elif 'amazon' in self.url2:
            return 'amazon'      
        elif 'fanza' in self.url2:
            return 'fanza'      
        elif 'skeb' in self.url2:
            return 'skeb'      
        elif 'dlsite' in self.url2:
            return 'dlsite'      
        elif 'shikoshiko' in self.url2:
            return 'cherrylive'      
        elif 'profu.link' in self.url2:
            return 'profu.link'      
        elif 'knip' in self.url2:
            return 'knip'      
        else:
            return 'link'

    def get_url3_prefix(self):
        if 'twitter' in self.url3:
            return 'x'
        elif 'x.com' in self.url3:
            return 'x'
        elif 'youtube' in self.url3:
            return 'youtube'
        elif 'fantia' in self.url3:
            return 'fantia'
        elif 'myfans' in self.url3:
            return 'myfans'
        elif 'pornhub' in self.url3:
            return 'pornhub'      
        elif 'candfans' in self.url3:
            return 'candfans'            
        elif 'lit.link' in self.url3:
            return 'lit.link'      
        elif 'dlsite' in self.url3:
            return 'dlsite'      
        elif 'amazon' in self.url3:
            return 'amazon'      
        elif 'fanza' in self.url3:
            return 'fanza'      
        elif 'skeb' in self.url3:
            return 'skeb'     
        elif 'dlsite' in self.url3:
            return 'dlsite'      
        elif 'shikoshiko' in self.url3:
            return 'cherrylive'      
        elif 'profu.link' in self.url3:
            return 'profu.link'      
        elif 'knip' in self.url3:
            return 'knip'      
        else:
            return 'link'

    def get_url4_prefix(self):
        if 'twitter' in self.url4:
            return 'x'
        elif 'x.com' in self.url4:
            return 'x'
        elif 'youtube' in self.url4:
            return 'youtube'
        elif 'fantia' in self.url4:
            return 'fantia'
        elif 'myfans' in self.url4:
            return 'myfans'
        elif 'pornhub' in self.url4:
            return 'pornhub'      
        elif 'candfans' in self.url4:
            return 'candfans'            
        elif 'lit.link' in self.url4:
            return 'lit.link'      
        elif 'dlsite' in self.url4:
            return 'dlsite'      
        elif 'amazon' in self.url4:
            return 'amazon'      
        elif 'fanza' in self.url4:
            return 'fanza'      
        elif 'skeb' in self.url4:
            return 'skeb'     
        elif 'dlsite' in self.url4:
            return 'dlsite'      
        elif 'shikoshiko' in self.url4:
            return 'cherrylive'      
        elif 'profu.link' in self.url4:
            return 'profu.link'      
        elif 'knip' in self.url4:
            return 'knip'      
        else:
            return 'link'

    def get_url5_prefix(self):
        if 'twitter' in self.url5:
            return 'x'
        elif 'x.com' in self.url5:
            return 'x'
        elif 'youtube' in self.url5:
            return 'youtube'
        elif 'fantia' in self.url5:
            return 'fantia'
        elif 'myfans' in self.url5:
            return 'myfans'
        elif 'pornhub' in self.url5:
            return 'pornhub'      
        elif 'candfans' in self.url5:
            return 'candfans'            
        elif 'lit.link' in self.url5:
            return 'lit.link'      
        elif 'dlsite' in self.url5:
            return 'dlsite'      
        elif 'amazon' in self.url5:
            return 'amazon'      
        elif 'fanza' in self.url5:
            return 'fanza'      
        elif 'skeb' in self.url5:
            return 'skeb'      
        elif 'dlsite' in self.url5:
            return 'dlsite'      
        elif 'shikoshiko' in self.url5:
            return 'cherrylive'      
        elif 'profu.link' in self.url5:
            return 'profu.link'      
        elif 'knip' in self.url5:
            return 'knip'      
        else:
            return 'link'
        
    def save(self, *args, **kwargs):
        # 既存のプロフィール画像設定
        if not self.prf_img:
            self.prf_img = 'others/初期プロフ.jpg'
        
        # プロフィール画像が提供された場合のリサイズ処理
        if self.prf_img and not self.prf_img.name == 'others/初期プロフ.jpg':
            # 画像を開く
            image = Image.open(self.prf_img)

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
            self.prf_img = InMemoryUploadedFile(output, 'ImageField', f"{self.prf_img.name.split('.')[0]}.jpeg", 'image/jpeg', sys.getsizeof(output), None)
        
        super(Users, self).save(*args, **kwargs)
        
    def increment_report_count(self):
        self.report_count += 1
        self.save()

    def get_report_count(self):
        return self.report_count


class SearchHistorys(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='search_histories')
    query = models.CharField(max_length=255)
    searched_at = models.DateTimeField(auto_now_add=True)
    visible = models.BooleanField(default=True)
    search_count = models.PositiveIntegerField(default=1)  

    def __str__(self):
        return f"{self.user.username} - {self.query} - {self.searched_at}"
    
    
class Follows(models.Model):
  poster = models.ForeignKey(Users, on_delete=models.CASCADE, related_name='follow_received')
  user = models.ForeignKey(Users, on_delete=models.CASCADE)
  created_at = models.DateTimeField(auto_now_add=True)




#運営からのメッセージ機能
class Messages(models.Model):
    recipient = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name='received_messages')  # 受信者
    title = models.TextField() #件名
    content = models.TextField()  # メッセージ内容
    is_read = models.BooleanField(default=False)  # 未読・既読ステータス
    sent_at = models.DateTimeField(auto_now_add=True)  # 送信日時
    
    def __str__(self):
        return self.title
    
# 投稿の削除依頼    
class DeleteRequest(models.Model):
    email = models.EmailField('メールアドレス')
    
    CO_PERFORMER = 'co_performer'
    ACCIDENTALLY_IN_VIDEO = 'accidentally_in_video'
    COPYRIGHT_INFRINGEMENT = 'copyright_infringement'
    OTHERS = 'others'

    CASE_CHOICES = [
        (CO_PERFORMER, '自身が共演している'),
        (ACCIDENTALLY_IN_VIDEO, '自身が映り込んでいる'),
        (COPYRIGHT_INFRINGEMENT, '自身の著作物が映っている'),
        (OTHERS, 'その他'),
    ]

    case_type = models.CharField('ケースの種類', max_length=50, choices=CASE_CHOICES)
    postername = models.CharField('投稿者のユーザーネーム', max_length=255)
    post_title = models.CharField('投稿のタイトル', max_length=255)
    details = models.TextField('詳細')

    def __str__(self):
        return self.email