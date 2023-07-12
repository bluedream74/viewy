from django.urls import path
from .views import (
  RegistUserView, HomeView, UserLoginView, UserLogoutView, FollowView, EditPrfView,CheckAgeView, VerifyView
)
from . import views

app_name = 'accounts'
urlpatterns = [
  path('home/', HomeView.as_view(), name='home'),  
  path('regist/', RegistUserView.as_view(), name='regist'),  
  path('user_login/', UserLoginView.as_view(), name='user_login'),  
  path('user_logout/', UserLogoutView.as_view(), name='user_logout'),
  path('follow/<int:pk>/', FollowView.as_view(), name='follow'),
  path('edit_prf/', EditPrfView.as_view(), name='edit_prf'),
  path('check_age/', CheckAgeView.as_view(), name='check_age'),
  path('verify/', VerifyView.as_view(), name='verify'),
]