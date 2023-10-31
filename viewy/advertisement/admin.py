from django.contrib import admin
from .models import (
  AndFeatures, AdCampaigns, AdInfos, RequestDocument, SetMeeting, MonthlyAdCost
)

class AdCampaignsAdmin(admin.ModelAdmin):
    raw_id_fields = ('created_by', 'andfeatures')

admin.site.register(AdCampaigns, AdCampaignsAdmin)

admin.site.register(
  [AndFeatures, AdInfos, RequestDocument, SetMeeting,MonthlyAdCost]
)
