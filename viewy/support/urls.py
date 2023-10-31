from django.urls import path
from django.views.generic import TemplateView

app_name = 'support'

class DynamicTemplateView(TemplateView):
    def get_template_names(self):
        pretitle = self.kwargs.get('pretitle')
        title = self.kwargs.get('title')
        subtitle = self.kwargs.get('subtitle')

        # 3つのパラメーターが指定された場合
        if pretitle and title and subtitle:
            return [f'support/{pretitle}/{title}/{subtitle}.html']

        # 2つのパラメーターが指定された場合
        if pretitle and title:
            return [f'support/{pretitle}/{title}/index.html']  # ここを変更

        # 1つのパラメーターが指定された場合
        if pretitle:
            return [f'support/{pretitle}/index.html']

        # パラメーターが指定されていない場合
        return ['support/first.html']

urlpatterns = [
  path('', TemplateView.as_view(template_name='support/first.html'), name='first'),
  # path('detail_base/', TemplateView.as_view(template_name='support/detail_base.html'), name='detail_base'),
  path('<str:pretitle>/<str:title>/<str:subtitle>/', DynamicTemplateView.as_view(), name='subtitle_page'),
  path('<str:pretitle>/<str:title>/', DynamicTemplateView.as_view(), name='title_page'),
  path('<str:pretitle>/', DynamicTemplateView.as_view(), name='pretitle_page'),
]