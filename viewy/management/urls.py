from django.urls import path
from .views import (Account, RecordUserStats, GetUserStats, Partner, Post, Hashtag, Ad, KanjiRegist, PosterWaiterList, AddToPosterGroup, RemoveFromWaitList
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
  path('kanji_regist/', KanjiRegist.as_view(), name='kanji_regist'),
  path('ad/', Ad.as_view(), name='ad'),
  path('poster_waiter_list/', PosterWaiterList.as_view(), name='poster_waiter_list'),
  path('add_to_poster_group/<int:user_id>/', AddToPosterGroup.as_view(), name='add_to_poster_group'),
  path('remove_from_wait_list/<int:user_id>/', RemoveFromWaitList.as_view(), name='remove_from_wait_list'),
]