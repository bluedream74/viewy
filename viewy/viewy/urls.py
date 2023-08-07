from django.contrib import admin
from django.urls import path, include
from accounts.views import CheckAgeView, GuideView, GuideLineView, TermsView, PolicyView, AboutViewyView
# from . import settings
from django.conf import settings
from django.contrib.staticfiles.urls import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')), 
    path('posts/', include('posts.urls')),
    path('management/', include('management.urls')),
    path('about_viewy/', AboutViewyView.as_view(), name='about_viewy'),
    path('guide/', GuideView.as_view(), name='guide'),
    path('guideline/', GuideLineView.as_view(), name='guideline'),
    path('terms/', TermsView.as_view(), name='terms'),
    path('policy/', PolicyView.as_view(), name='policy'),
    path('', CheckAgeView.as_view(), name='home'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
