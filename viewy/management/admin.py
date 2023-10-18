from django.contrib import admin
from .models import (
  UserStats, ClickCount, SupportRate, DailyVisitorCount
)

admin.site.register(
  [UserStats,ClickCount,SupportRate,DailyVisitorCount]
)
