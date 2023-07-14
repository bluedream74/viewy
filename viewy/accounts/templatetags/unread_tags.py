
from django import template
from django.db.models import Q
from django.contrib.auth import get_user_model
from accounts.models import Messages  # replace with your actual model

register = template.Library()

@register.filter
def has_unread_messages(user):
    User = get_user_model()
    universal_user = User.objects.get(id=1) #ID＝1に送られたメッセージは全員への一斉送信として扱う
    return Messages.objects.filter(
        Q(recipient=user, is_read=False) | Q(recipient=universal_user, is_read=False)
    ).exists()