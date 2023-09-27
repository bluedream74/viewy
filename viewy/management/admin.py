from django.contrib import admin
from .models import (
  UserStats, ClickCount
)

admin.site.register(
  [UserStats,ClickCount]
)
