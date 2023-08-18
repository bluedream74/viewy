from django.contrib import admin
from django.urls import path, include
from accounts.views import CheckAgeView, GuideView, GuideLineView, TermsView, PolicyView, AboutViewyView, ForInvitedView, DeleteRequestView, DeleteRequestSuccessView
# from . import settings
from django.conf import settings
from django.contrib.staticfiles.urls import static

urlpatterns = [
    path('accounts/', include('accounts.urls')), 
    path('posts/', include('posts.urls')),
    path('management/', include('management.urls')),
    path('about_viewy/', AboutViewyView.as_view(), name='about_viewy'),
    path('for_invited/', ForInvitedView.as_view(), name='for_invited'),
    path('guide/', GuideView.as_view(), name='guide'),
    path('guideline/', GuideLineView.as_view(), name='guideline'),
    path('terms/', TermsView.as_view(), name='terms'),
    path('policy/', PolicyView.as_view(), name='policy'),
    path('delete_request/', DeleteRequestView.as_view(), name='delete_request'),
    path('delete_request_success/', DeleteRequestSuccessView.as_view(), name='delete_request_success'),
    path('', CheckAgeView.as_view(), name=''),
]

if settings.DEBUG:
    urlpatterns += [
        path('admin/', admin.site.urls),
    ]
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
