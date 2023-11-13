from django.urls import path
from .views import (Account, RecordUserStats, GetUserStats, UserAnalytics, DailyVisitorCountView, Partner, RandomRecommendedUsers, UpdateBoostTypeView, Post, Hashtag, Ad, UnapprovedAdsView, ApproveView, AffiliateCreateView, KanjiRegist, KanjiDelete, PosterWaiterList, AddToPosterGroup, RemoveFromWaitList, SearchEmailandAddPoster, ClickCountView, FreezeNotificationApproveView, DeleteFreezeNotificationView, PostSearch, TogglePostHiddenStatus, VideoListView, ToggleEncodingStatusView, CalculateMonthlyBilling)


app_name = 'management'
urlpatterns = [
  path('account/', Account.as_view(), name='account'),  
  path('record_user_stats/', RecordUserStats.as_view(), name='record_user_stats'),
  path('get_user_stats/', GetUserStats.as_view(), name='get_user_stats'),
  path('user_analytics/', UserAnalytics.as_view(), name='user_analytics'),
  path('analyze/', DailyVisitorCountView.as_view(), name='daily_visitor_count'),
  path('partner/', Partner.as_view(), name='partner'),  
  path('random-recommended-users/', RandomRecommendedUsers.as_view(), name='random_recommended_users'),
  path('update_boost_type/<int:user_id>/', UpdateBoostTypeView.as_view(), name='update_boost_type'),
  path('post/', Post.as_view(), name='post'),
  path('post_search/', PostSearch.as_view(), name='post_search'),
  path('toggle_post_hidden/<int:post_id>/', TogglePostHiddenStatus.as_view(), name='toggle_post_hidden'),
  path('hashtag/', Hashtag.as_view(), name='hashtag'),
  path('kanji_regist/', KanjiRegist.as_view(), name='kanji_regist'),
  path('kanji_delete/<int:pk>/', KanjiDelete.as_view(), name='kanji_delete'),
  path('ad/', Ad.as_view(), name='ad'),
  path('approve_ad/', UnapprovedAdsView.as_view(), name='approve_ad'),
  path('approve/<int:ad_id>/', ApproveView.as_view(), name='approve'),
  path('affiliate_create/', AffiliateCreateView.as_view(), name='affiliate_create'),
  path('poster_waiter_list/', PosterWaiterList.as_view(), name='poster_waiter_list'),
  path('add_to_poster_group/<int:user_id>/', AddToPosterGroup.as_view(), name='add_to_poster_group'),
  path('remove_from_wait_list/<int:user_id>/', RemoveFromWaitList.as_view(), name='remove_from_wait_list'),
  path('search_user/', SearchEmailandAddPoster.as_view(), name='search_user'),
  path('click_count/<str:name>/', ClickCountView.as_view(), name='click_count'),
  path('freeze_notification_approve/', FreezeNotificationApproveView.as_view(), name='freeze_notification_approve'),
  path('delete_freeze_notification/', DeleteFreezeNotificationView.as_view(), name='delete_freeze_notification'),
  path('video_list/', VideoListView.as_view(), name='video_list'),
   path('toggle-encoding-status/', ToggleEncodingStatusView.as_view(), name='toggle-encoding-status'),
  path('calculate_monthly_billing/', CalculateMonthlyBilling.as_view(), name='calculate_monthly_billing'),
]