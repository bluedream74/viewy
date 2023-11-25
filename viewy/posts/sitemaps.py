from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from accounts.models import Users

class PosterPageSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.6
    protocol = "https"

    def items(self):
        # Posterグループに属するユーザーのみを取得
        return Users.objects.filter(groups__name='Poster')

    def location(self, obj):
        return reverse('posts:poster_page', args=[obj.username])

class HashtagPageSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.3
    protocol = "https"

    def items(self):
        return ['おっぱい', 'ギャル', 'ハメ撮り', '裏垢女子', '中出し', '巨乳', 'オナニー', '潮吹き', '人妻', 'フェラ', 'コスプレ', 'ロリ', 'アナル', 'tiktok', '露出', '寝取られ', '素人', 'JK', '騎乗位', '乱交', '熟女', '爆乳']  

    def location(self, hashtag):
        return reverse('posts:hashtag', args=[hashtag])


class SupportSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.5
    protocol = "https"

    def items(self):
        # すべての動的URLパターンを列挙
        dynamic_urls = [
            ('about_viewy',),
            ('about_viewy', 'regist_login'),
            ('about_viewy', 'regist_login', 'regist'),
            ('about_viewy', 'regist_login', 'n_login'),
            ('about_viewy', 'use'),
            ('about_viewy', 'use', 'viewy'),
            ('partner',),
            ('partner', 'account_page'),
            ('partner', 'account_page', 'mypost'),
            ('partner', 'post', 'img_error'),
            ('partner', 'post', 'img'),
            ('partner', 'post', 'video_error'),
            ('partner', 'post', 'video'),
            ('partner', 'regist'),
            ('partner', 'regist', 'who'),
            ('service',),
            ('service', 'amusement'),
            ('service', 'amusement', 'notification'),
            ('service', 'general'),
            ('service', 'general', 'campany'),
            ('service', 'general', 'term'),
            ('user',),
            ('user', 'campaign'),
            ('user', 'campaign', 'fee'),
            ('user', 'campaign', 'join'),
            ('user', 'campaign', 'winning'),
            ('user', 'error'),
            ('user', 'error', 'n_view'),
            ('user', 'function'),
            ('user', 'function', 'collection'),
        ]
        return dynamic_urls

    def location(self, item):
        # タプルの長さに基づいて適切なURLを生成
        if len(item) == 3:
            return reverse('support:subtitle_page', kwargs={'pretitle': item[0], 'title': item[1], 'subtitle': item[2]})
        elif len(item) == 2:
            return reverse('support:title_page', kwargs={'pretitle': item[0], 'title': item[1]})
        elif len(item) == 1:
            return reverse('support:pretitle_page', kwargs={'pretitle': item[0]})

class StaticViewSitemap(Sitemap):
    priority = 0.9
    changefreq = 'weekly'
    protocol = 'https'

    def items(self):
        return [
            'posts:visitor_postlist',
            'posts:hothashtag',
            'accounts:user_login',
            'accounts:regist',
            'accounts:password_reset',
            'terms',
            'policy',
            'guideline',
            'support:first',
            'support:inquiry_form'
        ]

    def location(self, item):
        return reverse(item)