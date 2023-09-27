import json
import math
import re
from datetime import datetime, timedelta

from django.contrib.auth.mixins import UserPassesTestMixin
from django.core import serializers
from django.db.models import (Avg, Case, CharField, Count, F, FloatField, Q, F, Sum, Value, When)
from django.db.models.functions import Concat, TruncMonth
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.views.decorators.http import require_POST

from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import redirect, render, get_object_or_404
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import ListView, DeleteView
from django.views.generic.base import TemplateView
from django.views.generic.edit import FormView

from accounts.models import Users, SearchHistorys
from posts.models import Ads, WideAds, Favorites, HotHashtags, Posts, KanjiHiraganaSet, RecommendedUser, ViewDurations
from .forms import HashTagSearchForm, RecommendedUserForm, BoostTypeForm
from .models import UserStats, ClickCount

from django.contrib.auth.models import Group

from django.db import IntegrityError, transaction
from collections import OrderedDict

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
        
        # 過去7日間で一度でも投稿を見たアクティブユーザー数
        seven_days_ago = timezone.now() - timedelta(days=7)
        active_users_count = Users.objects.filter(viewed_user__viewed_at__gte=seven_days_ago).distinct().count()
        context['active_users'] = active_users_count

        # アクティブ率
        if total_users > 0:
            active_rate = (active_users_count / total_users) * 100
            # 小数第二位で切り上げ
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
    

class Partner(SuperUserCheck, TemplateView):
    template_name = 'management/partner.html'

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        form = RecommendedUserForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                # Check if recommended users already exist
                if RecommendedUser.objects.exists():
                    RecommendedUser.objects.all().delete()

                # 新しいおすすめユーザーを順に追加
                for i in range(1, 13):
                    user_field = f"user{i}"
                    username = form.cleaned_data[user_field]
                    user_instance = Users.objects.get(username=username)  # ユーザーネームから Users インスタンスを取得
                    RecommendedUser.objects.create(user=user_instance, order=i)  # Users インスタンスを設定

            return redirect('management:partner')

        else:
            error_message = "エラーが発生しました。入力内容をご確認ください。"
            
        # If the form is not valid, re-render the page with the form errors
        context = self.get_context_data(form=form, error_message=error_message)
        return render(request, self.template_name, context)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Posterグループに属しているユーザーの総数を取得
        poster_group = Group.objects.get(name='Poster')
        poster_users_count = poster_group.user_set.count()
        
        # コンテキストに poster_users_count を追加
        context['poster_users_count'] = poster_users_count
        
        poster_users = poster_group.user_set.all()

        users = Users.objects.filter(id__in=poster_users).annotate(
            total_posts=Count('posted_posts'),
            avg_qp=Avg('posted_posts__qp'),
            total_views=Sum('posted_posts__views_count'),
        )

        for user in users:
            user.boost_type_form = BoostTypeForm(instance=user)

        context['users'] = users

        if 'error_message' in kwargs:
            context['error_message'] = kwargs['error_message']

        if 'form' in kwargs:
            context['form'] = kwargs['form']
        else:
            recommended_users = RecommendedUser.objects.order_by('order')
            initial_data = {}
            for i, recommended_user in enumerate(recommended_users, start=1):
                initial_data[f"user{i}"] = recommended_user.user
            context['form'] = RecommendedUserForm(initial=initial_data)

        return context
    
class UpdateBoostTypeView(View):
    def post(self, request, *args, **kwargs):
        user_id = kwargs.get('user_id')
        user = get_object_or_404(Users, id=user_id)
        form = BoostTypeForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
        return redirect('management:partner')
    
    
class Post(SuperUserCheck, View):
    template_name = 'management/post.html'

    def get(self, request, *args, **kwargs):
        # Posts と関連する Users をプリフェッチし、QPが高い投稿順に上位から３０投稿だけ取得
        posts = Posts.objects.all().prefetch_related('poster').order_by('-qp')[:30]

        # すべての投稿の数をカウント
        total_posts = Posts.objects.count()

        # すべての投稿のqpの平均値を計算
        avg_qp = Posts.objects.all().aggregate(Avg('qp'))['qp__avg'] or 0  # avg_qpがNoneの場合は0をセット

        # ismangaがtrueの投稿のqpの平均値を計算
        avg_qp_manga = Posts.objects.filter(ismanga=True).aggregate(Avg('qp'))['qp__avg'] or 0

        # ismangaがfalseの投稿のqpの平均値を計算
        avg_qp_movie = Posts.objects.filter(ismanga=False).aggregate(Avg('qp'))['qp__avg'] or 0

        context = {
            'posts': posts,
            'total_posts': total_posts,  # すべての投稿の数
            'avg_qp': avg_qp,  # すべての投稿のqpの平均値
            'avg_qp_manga': avg_qp_manga,  # ismangaがtrueの投稿のqpの平均値
            'avg_qp_movie': avg_qp_movie  # ismangaがfalseの投稿のqpの平均値
        }
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



class KanjiRegist(SuperUserCheck, View):
    template_name = 'management/kanji_regist.html'

    def get(self, request, error_message=None):
        # データベースから全オブジェクトを取得
        kanji_hiragana_sets = KanjiHiraganaSet.objects.all()

        # 存在する漢字のリストを作成
        existing_kanji = [set.kanji for set in kanji_hiragana_sets]

        # ひらがなに基づいてソート（‘あいうえお’順）
        sorted_kanji_hiragana_sets = sorted(kanji_hiragana_sets, key=lambda x: x.hiragana.split(',')[0])

        sections = OrderedDict()
        for set in sorted_kanji_hiragana_sets:
            initial_hiragana = set.hiragana.split(',')[0][0]
            if initial_hiragana not in sections:
                sections[initial_hiragana] = []
            sections[initial_hiragana].append(set)

        # Hashtagsとそのカウントを取得
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
        
        # ひらがなの正規表現パターン（最初の一文字）
        hiragana_pattern = re.compile(r'^[ぁ-ん]')

        # カタカナの正規表現パターン（最初の一文字）
        katakana_pattern = re.compile(r'^[ァ-ン]')

        # ハッシュタグとして存在するが、漢字として存在しない、かつ、最初の一文字がひらがな、カタカナでないものを特定
        unregistered_hashtags = [
            hashtag 
            for hashtag in hashtag_counts.keys() 
            if hashtag not in existing_kanji
            and not hiragana_pattern.match(hashtag)
            and not katakana_pattern.match(hashtag)
        ]

        # ソートされたオブジェクトと未登録のハッシュタグをテンプレートに渡す
        context = {
            'sections': sections,
            'error_message': error_message,
            'unregistered_hashtags': unregistered_hashtags,
        }
        return render(request, self.template_name, context)

    def post(self, request):
        kanji = request.POST['kanji']
        hiragana = request.POST['hiragana']

        # 逐次的なひらがなクエリを生成
        hiragana_queries = [hiragana[:i+1] for i in range(len(hiragana))]

        try:
            # モデルに保存
            obj = KanjiHiraganaSet(kanji=kanji, hiragana=','.join(hiragana_queries))
            obj.save()
        except IntegrityError:
            # 重複エラーの場合
            error_message = 'すでに保存されています'
            return self.get(request, error_message=error_message) # getメソッドを呼び出してエラーメッセージを渡す

        # 保存後のリダイレクト
        return redirect('management:kanji_regist')
    
    

class KanjiDelete(SuperUserCheck, View):
    def post(self, request, pk):
        kanji_hiragana_set = get_object_or_404(KanjiHiraganaSet, pk=pk)
        kanji_hiragana_set.delete()
        return redirect('management:kanji_regist')

class Ad(SuperUserCheck, View):
    template_name = 'management/ad.html'

    def get(self, request, *args, **kwargs):
        ads = Posts.objects.filter(poster__is_advertiser=True)

        # 平均滞在時間を計算し、広告とともにコンテキストに追加
        ads_with_avg_duration = []
        for ad in ads:
            view_durations = ViewDurations.objects.filter(post=ad)
            total_duration = sum(duration.duration for duration in view_durations)
            avg_duration = total_duration / view_durations.count() if view_durations.count() > 0 else 0
            ads_with_avg_duration.append((ad, avg_duration))

        context = {'ads_with_avg_duration': ads_with_avg_duration}
        return render(request, self.template_name, context)

class PosterWaiterList(SuperUserCheck, ListView):
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

class AddToPosterGroup(SuperUserCheck, View):
    def get(self, request, user_id):
        user = get_object_or_404(Users, id=user_id)
        
        is_real_str = request.GET.get('is_real')  # クエリパラメータからis_realを取得
        if is_real_str:
            user.is_real = is_real_str.lower() == 'true'  # 'true' なら True, それ以外なら False
            
        user.poster_waiter = False
        group, created = Group.objects.get_or_create(name='Poster')
        group.user_set.add(user)
        
        user.save()
        return redirect('management:poster_waiter_list')

class RemoveFromWaitList(SuperUserCheck, View):
    def get(self, request, user_id):
        user = get_object_or_404(Users, id=user_id)
        user.poster_waiter= False
        user.save()
        return redirect('management:poster_waiter_list')

@method_decorator(ensure_csrf_cookie, name='dispatch')
@method_decorator(require_POST, name='dispatch')
class ClickCountView(View):
    def post(self, request, name):
        try:
            click_count, created = ClickCount.objects.get_or_create(name=name)
            click_count.count = F('count') + 1
            click_count.save()
            click_count.refresh_from_db()
            return JsonResponse({"count": click_count.count})
        except Exception as e:
            # 実際のプロダクション環境では、エラー内容をロギングするなどの対応が必要です。
            print(f"Error processing RUClickCount for {name}: {e}")
            return JsonResponse({"error": "Unable to process request."}, status=500)