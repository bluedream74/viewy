from django.contrib import admin
from .models import (
  Users, Follows, Blocks, Messages, SearchHistorys, DeleteRequest, Features, Surveys, SurveyResults, Notification, NotificationView, FreezeNotification, FreezeNotificationView
)

admin.site.register(
  [Users,Follows,Blocks,Messages,SearchHistorys,DeleteRequest,Features, Surveys, SurveyResults, Notification, NotificationView, FreezeNotification, FreezeNotificationView]
)

