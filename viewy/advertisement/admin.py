from django.contrib import admin
from .models import (
  AndFeatures, AdCampaigns, AdInfos,
)

admin.site.register(
  [AndFeatures, AdCampaigns, AdInfos]
)
