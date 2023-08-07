from django.urls import path
from .views import (
  RegistUserView, HomeView, UserLoginView, UserLogoutView, FollowView, EditPrfView,CheckAgeView, VerifyView, MessageListView, MessageDetailView, MessageDeleteView, SearchHistoryView, SearchHistorySaveView, HideSearchHistoriesView, DeleteUserView, InvitedRegistUserView
)
from . import views

app_name = 'accounts'
urlpatterns = [
  path('home/', HomeView.as_view(), name='home'),  
  path('regist/', RegistUserView.as_view(), name='regist'),  
  path('invited_regist/', InvitedRegistUserView.as_view(), name='invited_regist'),
  path('user_login/', UserLoginView.as_view(), name='user_login'),  
  path('user_logout/', UserLogoutView.as_view(), name='user_logout'),
  path('follow/<int:pk>/', FollowView.as_view(), name='follow'),
  path('edit_prf/', EditPrfView.as_view(), name='edit_prf'),
  path('check_age/', CheckAgeView.as_view(), name='check_age'),
  path('verify/', VerifyView.as_view(), name='verify'),
  path('messages/', MessageListView.as_view(), name='message_list'),
  path('messages/<int:pk>/', MessageDetailView.as_view(), name='message_detail'),
  path('messages/delete/<int:pk>/', MessageDeleteView.as_view(), name='message_delete'),
  path('search_history/', views.SearchHistoryView.as_view(), name='search_history'),
  path('save_search_history/', views.SearchHistorySaveView.as_view(), name='save_search_history'),
  path('hide_search_histories/', views.HideSearchHistoriesView.as_view(), name='hide_search_histories'),
  path('delete_user/', DeleteUserView.as_view(), name='delete_user'),   
]