from django.contrib import admin
from .models import (
  AndFeatures, AdCampaigns, AdInfos, RequestDocument, SetMeeting
)

admin.site.register(
  [AndFeatures, AdCampaigns, AdInfos, RequestDocument, SetMeeting]
)
