from django.contrib import admin
from .models import (
  Users, Follows, Messages, SearchHistorys
)

admin.site.register(
  [Users,Follows,Messages,SearchHistorys]
)