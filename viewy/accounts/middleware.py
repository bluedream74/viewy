from urllib.parse import urlencode
from django.urls import reverse
from django.shortcuts import redirect
from django.conf import settings

class AgeVerificationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # 年齢確認ページのURLを取得
        # age_verification_url = reverse('home')

        # 静的ファイルとメディアファイルへのリクエストは除外
        if request.path.startswith(settings.STATIC_URL) or request.path.startswith(settings.MEDIA_URL):
            return self.get_response(request)

        # 現在のページが年齢確認ページではない場合のみリダイレクト処理を行う
        # if request.path != age_verification_url and not request.COOKIES.get('is_over_18'):
        #     # nextパラメータに現在のページのパスを設定
        #     query_string = urlencode({'next': request.path})
        #     redirect_url = age_verification_url + '?' + query_string
        #     return redirect(redirect_url)

        response = self.get_response(request)
        return response