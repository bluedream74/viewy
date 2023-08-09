import json
import math
from datetime import datetime, timedelta

from django.contrib.auth.mixins import UserPassesTestMixin
from django.core import serializers
from django.db.models import (Avg, Case, CharField, Count, F, FloatField, Q, 
                              Sum, Value, When)
from django.db.models.functions import Concat, TruncMonth
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import redirect, render, get_object_or_404
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import ListView
from django.views.generic.base import TemplateView
from django.views.generic.edit import FormView

from accounts.models import Users, SearchHistorys
from posts.models import Ads, Favorites, HotHashtags, Posts, KanjiHiraganaSet
from .forms import HashTagSearchForm
from .models import UserStats

from django.contrib.auth.models import Group


class SuperUserCheck(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_superuser

    def get_login_url(self):
        return reverse_lazy('accounts:user_login')  # Replace 'your-login-url' with the URL or name of your login view


class Account(SuperUserCheck, TemplateView):
    template_name = 'management/account.html'
  
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # 登録されている総ユーザー数
        total_users = Users.objects.filter(is_active=True).count()
        context['total_users'] = total_users
        
        # 今日登録されたユーザー数
        today = timezone.now().date()
        new_users = Users.objects.filter(verification_code_generated_at__date=today, is_active=True).count()
        context['new_users'] = new_users
        
        # 過去7日間で一度でもいいねを押したユーザー数
        seven_days_ago = timezone.now() - timedelta(days=7)
        active_users = Users.objects.filter(favorite_received__created_at__gte=seven_days_ago).distinct().count()
        context['active_users'] = active_users
        
        # アクティブ率
        if total_users > 0:
            active_rate = (active_users / total_users) * 100
            # 小数第二で切り上げ
            active_rate = math.ceil(active_rate * 100) / 100
        else:
            active_rate = 0
        context['active_rate'] = active_rate

        return context



class RecordUserStats(SuperUserCheck, View):
    def get(self, request, *args, **kwargs):
        today = timezone.now().date()
        total_users = Users.objects.count()
        UserStats.objects.create(date=today, total_users=total_users)
        return JsonResponse({"status": "success"})

class GetUserStats(SuperUserCheck, View):
    def get(self, request, *args, **kwargs):
        user_stats = UserStats.objects.all()
        user_stats_json = serializers.serialize('json', user_stats)
        user_stats_python = json.loads(user_stats_json)
        return JsonResponse(user_stats_python, safe=False)
    

class Partner(SuperUserCheck, View):
    template_name = 'management/partner.html'

    def get(self, request, *args, **kwargs):
        users = Users.objects.annotate(
            total_posts=Count('posted_posts'),
            avg_favorite_rate=Avg('posted_posts__favorite_rate'),
            total_views=Sum('posted_posts__views_count'),
            total_favorites=Sum('posted_posts__favorite_count')
        ).annotate(
            views_per_post=Case(
                When(total_posts=0, then=Value(0)),
                default=F('total_views') / F('total_posts'),
                output_field=FloatField()
            ),
            favorites_per_post=Case(
                When(total_posts=0, then=Value(0)),
                default=F('total_favorites') / F('total_posts'),
                output_field=FloatField()
            )
        ).exclude(total_posts=0)

        context = {'users': users}
        return render(request, self.template_name, context)
    
    
class Post(SuperUserCheck, View):
    template_name = 'management/post.html'

    def get(self, request, *args, **kwargs):
        posts = Posts.objects.all().order_by('-favorite_rate')  # すべての投稿をいいね率の高い順に取得
        for post in posts:
            post.update_favorite_rate()  # 各投稿のいいね率を更新
        context = {'posts': posts}
        return render(request, self.template_name, context)
    

class Hashtag(SuperUserCheck, TemplateView):
    template_name = 'management/hashtag.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get all hashtags
        hashtags = Posts.objects.annotate(
            all_hashtags=Concat(
                'hashtag1', Value(','),
                'hashtag2', Value(','),
                'hashtag3',
                output_field=CharField()
            )
        ).values('all_hashtags')

        hashtags_list = []
        for item in hashtags:
            hashtags_list.extend([hashtag for hashtag in item['all_hashtags'].split(',') if hashtag])

        hashtag_counts = {i: hashtags_list.count(i) for i in hashtags_list}

        #SearchHistorysから検索回数を取得
        search_counts = SearchHistorys.objects.values('query').annotate(search_count=Sum('search_count')).order_by('-search_count')

        # Combine post hashtag counts with search counts
        for hashtag, count in hashtag_counts.items():
            search_count = next((item['search_count'] for item in search_counts if item['query'] == hashtag), 0)

            hashtag_counts[hashtag] = (count, search_count)

        # 投稿数でソート
        sorted_by_post_counts = sorted(hashtag_counts.items(), key=lambda x: x[1][0], reverse=True)
        context['hashtags_by_post'] = sorted_by_post_counts

        # 検索回数でソート
        sorted_by_search_counts = sorted(hashtag_counts.items(), key=lambda x: x[1][1], reverse=True)
        context['hashtags_by_search'] = sorted_by_search_counts

        # Get the latest hot hashtags
        try:
            hot_hashtags = HotHashtags.objects.latest('id')
        except HotHashtags.DoesNotExist:
            hot_hashtags = None

        # Populate the form with the latest hot hashtags
        context['form'] = HashTagSearchForm(initial={
            'hashtag1': getattr(hot_hashtags, 'hashtag1', ''),
            'hashtag2': getattr(hot_hashtags, 'hashtag2', ''),
            'hashtag3': getattr(hot_hashtags, 'hashtag3', ''),
            'hashtag4': getattr(hot_hashtags, 'hashtag4', ''),
        })

        return context

    def post(self, request, *args, **kwargs):
        form = HashTagSearchForm(request.POST)

        if form.is_valid():
            hashtags = {
                'hashtag1': form.cleaned_data['hashtag1'],
                'hashtag2': form.cleaned_data['hashtag2'],
                'hashtag3': form.cleaned_data['hashtag3'],
                'hashtag4': form.cleaned_data['hashtag4']
            }

            HotHashtags.objects.create(**hashtags)

            return redirect('management:hashtag')

        # If the form is not valid, re-render the page with the form errors
        return self.get(request, *args, **kwargs)

class KanjiRegist(View):
    template_name = 'management/kanji_regist.html'

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        kanji = request.POST['kanji']
        hiragana = request.POST['hiragana']

        # 逐次的なひらがなクエリを生成
        hiragana_queries = [hiragana[:i+1] for i in range(len(hiragana))]

        # モデルに保存
        obj = KanjiHiraganaSet(kanji=kanji, hiragana=','.join(hiragana_queries))
        obj.save()

        # 保存後のリダイレクト
        return redirect('management:kanji_regist')


class Ad(SuperUserCheck, View):
    template_name = 'management/ad.html'

    def get(self, request, *args, **kwargs):
        ads = Ads.objects.all()  # すべての広告を取得
        for ad in ads:
            ad.update_click_rate()  # 各広告のクリック率を更新
        context = {'ads': ads}
        return render(request, self.template_name, context)

class PosterWaiterList(ListView):
    template_name = 'management/poster_waiter.html'
    context_object_name = 'users'
    model = Users

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.filter(poster_waiter=True)
        # usernameでの検索
        username = self.request.GET.get('username')
        if username:
            queryset = queryset.filter(Q(username__icontains=username))
        
        return queryset

class AddToPosterGroup(View):
    def get(self, request, user_id):
        user = get_object_or_404(Users, id=user_id)
        user.poster_waiter= False

        # ポスターグループを取得し、存在しない場合は作成
        group, created = Group.objects.get_or_create(name='Poster')

        # ユーザーをポスターグループに追加
        group.user_set.add(user)

        user.save()
        return redirect('management:poster_waiter_list') # ここでリダイレクト先を指定します