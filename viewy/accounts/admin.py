from django.contrib import admin
from .models import (
  Users, Follows,
)

admin.site.register(
  [Users,Follows,]
)