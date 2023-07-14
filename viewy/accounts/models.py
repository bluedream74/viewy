from django.db import models
from django.contrib.auth.models import (
    BaseUserManager, AbstractBaseUser, PermissionsMixin,
)
from django.urls import reverse_lazy
import random
import string
from django.contrib.auth import get_user_model


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
    caption = models.CharField(max_length=300, null=True, blank=True)
    url1 = models.URLField(max_length=200, null=True, blank=True) 
    url2 = models.URLField(max_length=200, null=True, blank=True) 
    url3 = models.URLField(max_length=200, null=True, blank=True) 
    url4 = models.URLField(max_length=200, null=True, blank=True) 
    url5 = models.URLField(max_length=200, null=True, blank=True) 
    is_active = models.BooleanField(default=True)  # 有効化が大変なのでいったん初めから有効にしておく
    is_staff = models.BooleanField(default=False)
    view_post_count = models.PositiveIntegerField(default=0)  # 視聴ポスト数のフィールド
    follow = models.ManyToManyField('self', through='Follows', symmetrical=False, related_name='followed_by')
    follow_count = models.PositiveIntegerField(default=0)
    report_count = models.PositiveIntegerField(default=0)  # 報告回数のフィールド
    verification_code = models.CharField(max_length=5, null=True, blank=True)   # 認証用のコード

    
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
        if self.url1.startswith('https://twitter.com'):
            return 'twitter'
        elif self.url1.startswith('https://www.youtube.com'):
            return 'youtube'
        elif self.url1.startswith('https://www.pixiv.net'):
            return 'pixiv'
        elif self.url1.startswith('https://www.fantia.jp'):
            return 'fantia'
        elif self.url1.startswith('https://www.myfans.jp'):
            return 'myfans'
        else:
            return 'default'

    def get_url2_prefix(self):
        if self.url2.startswith('https://twitter.com'):
            return 'twitter'
        elif self.url2.startswith('https://www.youtube.com'):
            return 'youtube'
        elif self.url2.startswith('https://www.pixiv.net'):
            return 'pixiv'
        elif self.url2.startswith('https://www.fantia.jp'):
            return 'fantia'
        elif self.url2.startswith('https://www.myfans.jp'):
            return 'myfans'
        else:
            return 'default'

    def get_url3_prefix(self):
        if self.url3.startswith('https://twitter.com'):
            return 'twitter'
        elif self.url3.startswith('https://www.youtube.com'):
            return 'youtube'
        elif self.url3.startswith('https://www.pixiv.net'):
            return 'pixiv'
        elif self.url3.startswith('https://www.fantia.jp'):
            return 'fantia'
        elif self.url3.startswith('https://www.myfans.jp'):
            return 'myfans'
        else:
            return 'default'
        
    def get_url4_prefix(self):
        if self.url4.startswith('https://twitter.com'):
            return 'twitter'
        elif self.url4.startswith('https://www.youtube.com'):
            return 'youtube'
        elif self.url4.startswith('https://www.pixiv.net'):
            return 'pixiv'
        elif self.url4.startswith('https://www.fantia.jp'):
            return 'fantia'
        elif self.url4.startswith('https://www.myfans.jp'):
            return 'myfans'
        else:
            return 'default'

    def get_url5_prefix(self):
        if self.url5.startswith('https://twitter.com'):
            return 'twitter'
        elif self.url5.startswith('https://www.youtube.com'):
            return 'youtube'
        elif self.url5.startswith('https://www.pixiv.net'):
            return 'pixiv'
        elif self.url5.startswith('https://www.fantia.jp'):
            return 'fantia'
        elif self.url5.startswith('https://www.myfans.jp'):
            return 'myfans'        
        else:
            return 'default'

        
    def increment_report_count(self):
        self.report_count += 1
        self.save()

    def get_report_count(self):
        return self.report_count

# ユーザー登録時にランダムな5桁の認証コードを生成
    def generate_verification_code(self):
        self.verification_code = ''.join(random.choices(string.digits, k=5))

    
    
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