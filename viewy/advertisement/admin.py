from django.contrib import admin
from .models import (
  AndFeatures, AdInfos
)

admin.site.register(
  [AndFeatures, AdInfos]
)
