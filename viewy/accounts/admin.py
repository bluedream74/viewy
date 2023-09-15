from django.contrib import admin
from .models import (
  Users, Follows, Messages, SearchHistorys, DeleteRequest ,Features
)

admin.site.register(
  [Users,Follows,Messages,SearchHistorys,DeleteRequest,Features]
)

