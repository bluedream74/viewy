from urllib.parse import urlencode
from django.urls import reverse
from django.shortcuts import redirect
from django.conf import settings

class AgeVerificationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # 年齢確認ページのURLを取得
        age_verification_url = reverse('home')

        # 静的ファイルとメディアファイルへのリクエストは除外
        if request.path.startswith(settings.STATIC_URL) or request.path.startswith(settings.MEDIA_URL):
            return self.get_response(request)


        # # クローラー向けの特別なリダイレクト先
        # crawler_redirect_url = reverse('posts:visitor_postlist')

        # # クローラーのユーザーエージェントを識別する
        # crawler_user_agents = ['Googlebot', 'Bingbot', 'Yahoo', 'DuckDuckBot', 'Baiduspider', 'YandexBot', 'Sogou']
        
        # # リクエストのユーザーエージェントをチェック
        # user_agent = request.META.get('HTTP_USER_AGENT', '')

        # print("Current User-Agent:", user_agent) 

        # if any(crawler in user_agent for crawler in crawler_user_agents):
        #     print("Detected crawler:", user_agent)
        #     # クローラーの場合は年齢確認をスキップ
        #     if request.path == crawler_redirect_url:
        #         return self.get_response(request)
        #     return redirect(crawler_redirect_url)

        # 除外したいURLのリスト
        excluded_urls = [
            "/for_invited/",
            "/guide/",
            "/for_advertiser/",
            "/set_meeting/",
            "/set_meeting_success/",
            # crawler_redirect_url,
        ]

        # 現在のページが除外したいURLのいずれでもない場合のみリダイレクト処理を行う
        if not any(request.path.startswith(url) for url in excluded_urls):
            # 現在のページが年齢確認ページではない場合のみリダイレクト処理を行う
            if request.path != age_verification_url and not request.COOKIES.get('is_over_18'):
                # nextパラメータに現在のページのパスを設定
                query_string = urlencode({'next': request.path})
                redirect_url = age_verification_url + '?' + query_string
                return redirect(redirect_url)

        response = self.get_response(request)
        return response