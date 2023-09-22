from django.urls import path
from .views import (
  RegistUserView, InvitedRegistUserView, RegistAdvertiserView, UserLoginView, UserLogoutView, PasswordResetView, PasswordResetConfirmView, PasswordResetSendView, PasswordResetCompleteView, FollowView, EditPrfView,CheckAgeView, VerifyView, ResendVerificationCodeView, MessageListView, MessageDetailView, MessageDeleteView, SearchHistoryView, SearchHistorySaveView, HideSearchHistoriesView, DeleteUserView, ChangeDimensionView, FirstSettingView
)
from . import views

app_name = 'accounts'
urlpatterns = [ 
  path('regist/', RegistUserView.as_view(), name='regist'),  
  path('invited_regist/', InvitedRegistUserView.as_view(), name='invited_regist'),
  path('regist_advertiser/', RegistAdvertiserView.as_view(), name='regist_advertiser'),
  path('user_login/', UserLoginView.as_view(), name='user_login'),  
  path('user_logout/', UserLogoutView.as_view(), name='user_logout'),
  path('password_reset/', PasswordResetView.as_view(), name='password_reset'),
  path('password_reset_send/', PasswordResetSendView.as_view(), name='password_reset_send'),
  path('password_reset_confirm/<uidb64>/<token>/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
  path('password_reset_complete/', PasswordResetCompleteView.as_view(), name='password_reset_complete'),
  path('follow/<int:pk>/', FollowView.as_view(), name='follow'),
  path('edit_prf/', EditPrfView.as_view(), name='edit_prf'),
  path('check_age/', CheckAgeView.as_view(), name='check_age'),
  path('verify/', VerifyView.as_view(), name='verify'),
  path('resend_verification/', ResendVerificationCodeView.as_view(), name='resend_verification'),
  path('messages/', MessageListView.as_view(), name='message_list'),
  path('messages/<int:pk>/', MessageDetailView.as_view(), name='message_detail'),
  path('messages/delete/<int:pk>/', MessageDeleteView.as_view(), name='message_delete'),
  path('search_history/', views.SearchHistoryView.as_view(), name='search_history'),
  path('save_search_history/', views.SearchHistorySaveView.as_view(), name='save_search_history'),
  path('hide_search_histories/', views.HideSearchHistoriesView.as_view(), name='hide_search_histories'),
  path('delete_user/', DeleteUserView.as_view(), name='delete_user'),   
  path('change_dimension/', ChangeDimensionView.as_view(), name='change_dimension'),
  path('first_setting/', FirstSettingView.as_view(), name='first_setting'),
]