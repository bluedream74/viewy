from django.contrib import admin
from .models import (
  Users, Follows, Messages
)

admin.site.register(
  [Users,Follows,Messages]
)