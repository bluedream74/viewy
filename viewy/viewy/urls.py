from django.contrib import admin
from django.urls import path, include
from accounts.views import CheckAgeView, GuideView, GuideLineView, TermsView, PolicyView, AboutViewyView, ForInvitedView, ForAdvertiserView, RequestDocumentsView, RequestSuccessView, SetMeetingView, SetMeetingSuccessView, DeleteRequestView, DeleteRequestSuccessView, PartnerApplicationGuideView, ForbiddenView, NotFoundView, BadRequestView, UnauthorizedView, ForbiddenView, NotFoundView, ServerErrorView, BadGatewayView, ServiceUnavailableView, ServerErrorView
# from . import settings
from django.conf import settings
from django.contrib.staticfiles.urls import static

urlpatterns = [
    path('accounts/', include('accounts.urls')), 
    path('posts/', include('posts.urls')),
    path('management/', include('management.urls')),
    path('advertisement/', include('advertisement.urls')),
    path('about_viewy/', AboutViewyView.as_view(), name='about_viewy'),
    path('partner_application_guide/', PartnerApplicationGuideView.as_view(), name='partner_application_guide'),
    path('for_invited/', ForInvitedView.as_view(), name='for_invited'),
    path('for_advertiser/', ForAdvertiserView.as_view(), name='for_advertiser'),
    path('request_documents/', RequestDocumentsView.as_view(), name='request_documents'),
    path('request_success/', RequestSuccessView.as_view(), name='request_success'),
    path('set_meeting/', SetMeetingView.as_view(), name='set_meeting'),
    path('set_meeting_success/', SetMeetingSuccessView.as_view(), name='set_meeting_success'),
    path('guide/', GuideView.as_view(), name='guide'),
    path('guideline/', GuideLineView.as_view(), name='guideline'),
    path('terms/', TermsView.as_view(), name='terms'),
    path('policy/', PolicyView.as_view(), name='policy'),
    path('delete_request/', DeleteRequestView.as_view(), name='delete_request'),
    path('delete_request_success/', DeleteRequestSuccessView.as_view(), name='delete_request_success'),
    path('', CheckAgeView.as_view(), name='home'),
]

handler400 = BadRequestView.as_view()
handler401 = UnauthorizedView.as_view()
handler403 = ForbiddenView.as_view()
handler404 = NotFoundView.as_view()
handler500 = ServerErrorView.as_view()
handler502 = BadGatewayView.as_view()
handler503 = ServiceUnavailableView.as_view()

if settings.DEBUG:
    import debug_toolbar
    urlpatterns += [
        path('admin/', admin.site.urls),
        path('__debug__/', include(debug_toolbar.urls)),
    ]
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
