from django.contrib import admin
from .models import (
  UserStats, ClickCount, SupportRate
)

admin.site.register(
  [UserStats,ClickCount,SupportRate]
)
