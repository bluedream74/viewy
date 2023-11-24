from django.urls import path
from django.views.generic import TemplateView
from .views import DynamicTemplateView, InquiryFormView, InquirySuccessView

app_name = 'support'


urlpatterns = [
  path('', TemplateView.as_view(template_name='support/first.html'), name='first'),
  path('inquiry_form/', InquiryFormView.as_view(), name='inquiry_form'),
  path('inquiry_success/', InquirySuccessView.as_view(), name='inquiry_success'),
  path('<str:pretitle>/<str:title>/<str:subtitle>/', DynamicTemplateView.as_view(), name='subtitle_page'),
  path('<str:pretitle>/<str:title>/', DynamicTemplateView.as_view(), name='title_page'),
  path('<str:pretitle>/', DynamicTemplateView.as_view(), name='pretitle_page'),
]