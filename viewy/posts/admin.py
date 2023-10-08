from django.contrib import admin
from .models import (
  Posts, Visuals, Videos, Favorites, Report, Ads, KanjiHiraganaSet, WideAds, ViewDurations, TomsTalk
)

class PostsAdmin(admin.ModelAdmin):
    raw_id_fields = ('poster',)  # 大量の関連オブジェクトがあるフィールドを指定

admin.site.register(Posts, PostsAdmin)

admin.site.register(
  [Visuals,Videos,Favorites,Report,Ads,KanjiHiraganaSet, WideAds, ViewDurations, TomsTalk]
)
