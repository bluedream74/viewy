from django.db import models
from django.contrib.auth.models import (
    BaseUserManager, AbstractBaseUser, PermissionsMixin,
)
from django.urls import reverse_lazy
from django.contrib.auth import get_user_model

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
    url1 = models.URLField(max_length=200, null=True, blank=True) 
    url2 = models.URLField(max_length=200, null=True, blank=True) 
    url3 = models.URLField(max_length=200, null=True, blank=True) 
    url4 = models.URLField(max_length=200, null=True, blank=True) 
    url5 = models.URLField(max_length=200, null=True, blank=True) 
    is_active = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
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
            return 'twitter'
        elif 'youtube' in self.url1:
            return 'youtube'
        elif 'pixiv' in self.url1:
            return 'pixiv'
        elif 'fantia' in self.url1:
            return 'fantia'
        elif 'myfans' in self.url1:
            return 'myfans'
        elif 'pornhub' in self.url1:
            return 'pornhub'        
        else:
            return 'default'

    def get_url2_prefix(self):
        if 'twitter' in self.url2:
            return 'twitter'
        elif 'youtube' in self.url2:
            return 'youtube'
        elif 'pixiv' in self.url2:
            return 'pixiv'
        elif 'fantia' in self.url2:
            return 'fantia'
        elif 'myfans' in self.url2:
            return 'myfans'
        elif 'pornhub' in self.url2:
            return 'pornhub'                
        else:
            return 'default'

    def get_url3_prefix(self):
        if 'twitter' in self.url3:
            return 'twitter'
        elif 'youtube' in self.url3:
            return 'youtube'
        elif 'pixiv' in self.url3:
            return 'pixiv'
        elif 'fantia' in self.url3:
            return 'fantia'
        elif 'myfans' in self.url3:
            return 'myfans'
        elif 'pornhub' in self.url3:
            return 'pornhub'        
        else:
            return 'default'

    def get_url4_prefix(self):
        if 'twitter' in self.url4:
            return 'twitter'
        elif 'youtube' in self.url4:
            return 'youtube'
        elif 'pixiv' in self.url4:
            return 'pixiv'
        elif 'fantia' in self.url4:
            return 'fantia'
        elif 'myfans' in self.url4:
            return 'myfans'
        elif 'pornhub' in self.url4:
            return 'pornhub'        
        else:
            return 'default'

    def get_url5_prefix(self):
        if 'twitter' in self.url5:
            return 'twitter'
        elif 'youtube' in self.url5:
            return 'youtube'
        elif 'pixiv' in self.url5:
            return 'pixiv'
        elif 'fantia' in self.url5:
            return 'fantia'
        elif 'myfans' in self.url5:
            return 'myfans'
        elif 'pornhub' in self.url5:
            return 'pornhub'        
        else:
            return 'default'
        
    def save(self, *args, **kwargs):
        if not self.prf_img:
            self.prf_img = '\others\S__208183299.jpg'
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