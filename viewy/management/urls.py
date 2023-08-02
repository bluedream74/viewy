from django.urls import path
from .views import (Account, RecordUserStats, GetUserStats, Partner, Post, Hashtag, Ad
)
from . import views

app_name = 'management'
urlpatterns = [
  path('account/', Account.as_view(), name='account'),  
  path('record_user_stats/', RecordUserStats.as_view(), name='record_user_stats'),
  path('get_user_stats/', GetUserStats.as_view(), name='get_user_stats'),
  path('partner/', Partner.as_view(), name='partner'),  
  path('post/', Post.as_view(), name='post'),
  path('hashtag/', Hashtag.as_view(), name='hashtag'),
  path('ad/', Ad.as_view(), name='ad')
]