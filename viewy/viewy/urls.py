from django.contrib import admin
from django.urls import path, include
from accounts.views import CheckAgeView, GuideView, GuideLineView, TermsView, PolicyView
from . import settings
from django.contrib.staticfiles.urls import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')), 
    path('posts/', include('posts.urls')),
    path('guide/', GuideView.as_view(), name='guide'),
    path('guideline/', GuideLineView.as_view(), name='guideline'),
    path('terms/', TermsView.as_view(), name='terms'),
    path('policy/', PolicyView.as_view(), name='policy'),
    path('', CheckAgeView.as_view(), name='home'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
