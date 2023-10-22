from django.contrib import admin
from .models import (
  Posts, Visuals, Videos, Favorites, Recommends, Collection, Collect, Report, Ads, KanjiHiraganaSet, WideAds, ViewDurations, TomsTalk, PinnedPost
)

class PostsAdmin(admin.ModelAdmin):
    raw_id_fields = ('poster',)  # 大量の関連オブジェクトがあるフィールドを指定

admin.site.register(Posts, PostsAdmin)

admin.site.register(
  [Visuals, Videos, Favorites, Recommends, Collection, Collect, Report, Ads, KanjiHiraganaSet, WideAds, ViewDurations, TomsTalk, PinnedPost]
)
