from django import template

register = template.Library()

@register.filter
def is_poster(user):
    return user.groups.filter(name='Poster').exists()
  
@register.filter
def is_premium(user):
    return user.groups.filter(name='Premium').exists()