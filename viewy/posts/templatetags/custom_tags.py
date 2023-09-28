from django import template
from django.core.cache import cache

register = template.Library()

@register.filter
def is_poster(user):
    cache_key = f"is_poster_{user.id}"
    result = cache.get(cache_key)

    # キャッシュに情報がない場合のフォールバック (理論的には発生しないはずですが、一応記述しておきます)
    if result is None:
        result = user.groups.filter(name='Poster').exists()

    return result
  
@register.filter
def is_premium(user):
    return user.groups.filter(name='Premium').exists()

@register.filter
def is_master(user):
    return user.groups.filter(name='Master').exists()

@register.simple_tag
def get_attr(obj, attr_name):
    return getattr(obj, attr_name, None)