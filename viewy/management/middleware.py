import os
from django.conf import settings
from django.shortcuts import render

class MaintenanceModeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        maintenance_mode = os.environ.get('MAINTENANCE_MODE', 'off')

        # 静的ファイルとメディアファイルへのリクエストは除外
        if request.path.startswith(settings.STATIC_URL) or request.path.startswith(settings.MEDIA_URL):
            return self.get_response(request)

        if maintenance_mode == 'on':
            return render(request, 'management/maintenance.html', status=503) # メンテナンステンプレートのレスポンス

        return self.get_response(request)