from django.contrib import admin
from .models import (
  Posts, Visuals, Videos, Favorites, Report, Ads, KanjiHiraganaSet, WideAds, ViewDurations, TomsTalk
)

admin.site.register(
  [Posts,Visuals,Videos,Favorites,Report,Ads,KanjiHiraganaSet, WideAds, ViewDurations, TomsTalk]
)
