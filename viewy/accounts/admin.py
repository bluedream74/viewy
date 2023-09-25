from django.contrib import admin
from .models import (
  Users, Follows, Messages, SearchHistorys, DeleteRequest, Features, Surveys, SurveyResults
)

admin.site.register(
  [Users,Follows,Messages,SearchHistorys,DeleteRequest,Features, Surveys, SurveyResults]
)

