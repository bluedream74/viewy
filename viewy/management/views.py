import json
import math
import re
import pytz
import random
from datetime import datetime, timedelta
from django.core.cache import cache

from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib import messages
from django.core import serializers
from django.urls import reverse
from django.db.models import (Avg, Case, CharField, Count, F, FloatField, Q, F, Sum, Value, When, OuterRef, Subquery, Min)
from django.db.models.functions import Concat, TruncMonth, TruncDate, TruncHour
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.views.decorators.http import require_POST
from django.views.generic.edit import FormView, CreateView
from django.http import HttpResponse


from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import redirect, render, get_object_or_404
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import ListView, DeleteView
from django.views.generic.base import TemplateView
from django.views.generic.edit import FormView

from accounts.models import Users, SearchHistorys, FreezeNotification
from posts.models import Ads, WideAds, Favorites, HotHashtags, Posts, KanjiHiraganaSet, RecommendedUser, ViewDurations, Videos
from .forms import HashTagSearchForm, RecommendedUserForm, BoostTypeForm, AffiliateForm, AffiliateInfoForm, AnalyzeDateForm
from .models import UserStats, ClickCount, DailyVisitorCount
from advertisement.models import MonthlyBilling, AdInfos, AdCampaigns

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
        
        # 性別別のユーザー数を取得
        male_users = Users.objects.filter(gender='male', is_active=True).count()
        female_users = Users.objects.filter(gender='female', is_active=True).count()
        other_gender_users = Users.objects.filter(gender='other', is_active=True).count()

        context['male_users'] = male_users
        context['female_users'] = female_users
        context['other_gender_users'] = other_gender_users
        
        # 性別別のユーザー数のパーセンテージを計算
        if total_users > 0:
            male_users_percentage = (male_users / total_users) * 100
            female_users_percentage = (female_users / total_users) * 100
            other_gender_users_percentage = (other_gender_users / total_users) * 100
        else:
            male_users_percentage = female_users_percentage = other_gender_users_percentage = 0
        
        # コンテキストに追加
        context['male_users_percentage'] = male_users_percentage
        context['female_users_percentage'] = female_users_percentage
        context['other_gender_users_percentage'] = other_gender_users_percentage


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
    
    
    
class UserAnalytics(TemplateView):
    template_name = 'management/user_analytics.html'
  
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # 日本のタイムゾーンを取得
        jp_timezone = pytz.timezone('Asia/Tokyo')

        # 30日前の日時を取得
        start_date = timezone.now().astimezone(jp_timezone).date() - timedelta(days=30)
        end_date = timezone.now().astimezone(jp_timezone).date()

        # DailyVisitorCountモデルから過去30日間のデータを取得
        visitor_data = DailyVisitorCount.objects.filter(date__range=(start_date, end_date))

        dates = [item.date.strftime('%Y-%m-%d') for item in visitor_data]
        total_users_list = [item.total_users for item in visitor_data]
        new_users_list = [item.new_users for item in visitor_data]
        repeat_users_list = [item.repeat_users for item in visitor_data]

        context = {
            'daily_users_labels': dates,
            'daily_users_values': total_users_list,
            'daily_new_users_values': new_users_list,  # ここを追加
            'daily_repeat_users_values': repeat_users_list,
        }
        
        # 全ユーザーの中で視聴履歴が1日以上のユーザーを取得
        one_day_viewed_users = ViewDurations.objects.values('user').annotate(viewed_days=Count('viewed_at__date', distinct=True)).filter(viewed_days__gte=1).count()
        context['one_day_viewed_users'] = one_day_viewed_users

        # 全ユーザーの中で視聴履歴が2日以上のユーザーを取得
        two_day_viewed_users = ViewDurations.objects.values('user').annotate(viewed_days=Count('viewed_at__date', distinct=True)).filter(viewed_days__gte=2).count()
        context['two_day_viewed_users'] = two_day_viewed_users

        # 全ユーザーの中で視聴履歴が5日以上のユーザーを取得
        five_day_viewed_users = ViewDurations.objects.values('user').annotate(viewed_days=Count('viewed_at__date', distinct=True)).filter(viewed_days__gte=5).count()
        context['five_day_viewed_users'] = five_day_viewed_users

        # DailyVisitorCountモデルから全ての日のtotal_usersを取得し、それを合計
        total_visitors = DailyVisitorCount.objects.aggregate(sum=Sum('total_users'))['sum']
        context['total_visitors'] = total_visitors


        return context
    

def update_daily_user_analytics(target_date):
    start_time = target_date
    end_time = start_time + timedelta(days=1)

    # 当日訪問したユーザーのIDを取得
    today_users = set(ViewDurations.objects.filter(viewed_at__range=(start_time, end_time)).values_list('user_id', flat=True))

    # それまでの日にViewDurationsが存在しないユーザーを取得
    previous_viewed_users = set(ViewDurations.objects.filter(viewed_at__lt=start_time).values_list('user_id', flat=True))

    # 新規ユーザーの取得
    new_users = today_users - previous_viewed_users

    # リピーターユーザーの取得
    repeat_users = today_users & previous_viewed_users  # 積集合を取ることでリピーターを取得

    # DailyUserAnalyticsモデルに保存
    DailyVisitorCount.objects.update_or_create(
        date=target_date,
        defaults={
            'total_users': len(today_users),
            'new_users': len(new_users),
            'repeat_users': len(repeat_users)
        }
    )
  
    
class DailyVisitorCountView(View):
    template_name = 'management/analyze_visitor.html'
    form_class = AnalyzeDateForm

    def get(self, request, *args, **kwargs):
        form = self.form_class()
        return render(request, self.template_name, {'form': form})
    

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():
            target_date = form.cleaned_data['analyze_date']
            update_daily_user_analytics(target_date)  # 更新関数を実行
            return redirect('/management/analyze/') # 成功ページや任意のページにリダイレクト
        return render(request, self.template_name, {'form': form})
    

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
        poster_users = poster_group.user_set.all()
        
        # コンテキストに poster_users_count を追加
        context['poster_users_count'] = poster_users.count()
        
        # is_realがTrueのユーザーとFalseのユーザーの数を計算
        real_users_count = poster_users.filter(is_real=True).count()
        not_real_users_count = poster_users.filter(is_real=False).count()

        # 1週間前の日時を計算
        one_week_ago = datetime.now() - timedelta(days=7)

        # 上記の期間にViewDurationsモデルにエントリがあるPosterグループのユーザーを取得
        active_posters = poster_users.filter(viewed_user__viewed_at__gte=one_week_ago).distinct()

        context['active_posters'] = active_posters
        context['active_posters_count'] = active_posters.count()
        
        # コンテキストに real_users_count と not_real_users_count を追加
        context['real_posters_count'] = real_users_count
        context['not_real_posters_count'] = not_real_users_count
        
        users = Users.objects.filter(id__in=poster_users).annotate(
            total_posts=Count('posted_posts'),
            avg_qp=Avg('posted_posts__qp'),
            total_views=Sum('posted_posts__views_count'),
            total_support_views=Sum('posted_posts__support_views_count')
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
                initial_data[f"user{i}"] = recommended_user.user.username  # Here, change from user object to username string
            context['form'] = RecommendedUserForm(initial=initial_data)

        return context

# おすすめユーザーをランダムに選んでくれる機能    
class RandomRecommendedUsers(SuperUserCheck, View):
    def get(self, request, *args, **kwargs):
        # 平均QPが上位の30人のユーザーを取得
        users = Users.objects.annotate(avg_qp=Avg('posted_posts__qp')).order_by('-avg_qp')[:30]
        
        # 上位の30人のユーザーからランダムで12人を選択
        selected_users = random.sample(list(users), 12)
        
        # 選択したユーザーのusernameをリストとして作成
        usernames = [{'username': user.username} for user in selected_users]
        
        return JsonResponse({'users': usernames})

# 各パートナーのブースト状態をその場で変更できる機能    
class UpdateBoostTypeView(SuperUserCheck, View):
    def post(self, request, *args, **kwargs):
        user_id = kwargs.get('user_id')
        user = get_object_or_404(Users, id=user_id)
        form = BoostTypeForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            return JsonResponse({'status': 'success'})
        else:
            return JsonResponse({'status': 'error', 'errors': form.errors})
    
    
class Post(SuperUserCheck, View):
    template_name = 'management/post.html'

    def get(self, request, *args, **kwargs):
        # Posts と関連する Users をプリフェッチし、QPが高い投稿順に上位から60投稿だけ取得
        posts = Posts.objects.all().prefetch_related('poster').order_by('-qp')[:60]

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

class PostSearch(SuperUserCheck, ListView):
    template_name = 'management/post_search.html'
    context_object_name = 'posts'
    model = Posts

    def get_queryset(self):
        query = self.request.GET.get('q')  # 検索クエリを取得

        if query:  # クエリが存在する場合にのみ検索を実行
            # ユーザーネームまたはdisplaynameで完全一致のユーザーを検索
            users = Users.objects.filter(Q(username=query) | Q(displayname=query))
            
            # 該当するユーザーの投稿をすべて取得
            return self.model.objects.filter(poster__in=users)
        
        return self.model.objects.none()  # クエリが存在しない場合は空のクエリセットを返す

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        query = self.request.GET.get('q')
        if query and not context['posts']:  # クエリが存在し、投稿がない場合
            context['error_message'] = 'ユーザーが見つかりません'

        return context

class TogglePostHiddenStatus(SuperUserCheck, View):
    def get(self, request, post_id):
        post = get_object_or_404(Posts, id=post_id)
        post.is_hidden = not post.is_hidden 
        post.save()
        query = request.GET.get('q', '')  # 検索クエリを取得
        url = reverse('management:post_search')  # PostSearchビューへのURLを生成
        if query:  # クエリがある場合、URLにクエリを追加
            url += f'?q={query}'
        
        return HttpResponseRedirect(url) 
    

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

        context = {'ads': ads}
        return render(request, self.template_name, context)
    
class AffiliateCreateView(SuperUserCheck, CreateView):
    template_name = 'management/affiliate_create.html'
    
    def get(self, request, *args, **kwargs):
        affiliate_form = AffiliateForm()
        adinfo_form = AffiliateInfoForm()  # user引数の渡し方を削除
        return render(request, self.template_name, {
            'affiliate_form': affiliate_form,
            'adinfo_form': adinfo_form,
        })
    
    def post(self, request, *args, **kwargs):
        affiliate_form = AffiliateForm(request.POST)
        adinfo_form = AffiliateInfoForm(request.POST)  # user引数の渡し方を削除
        
        if affiliate_form.is_valid() and adinfo_form.is_valid():
            affiliate_instance = affiliate_form.save(commit=False) 
            
            # affiliate@gmail.comのメールアドレスのユーザーを取得
            poster_user = Users.objects.get(email='affiliate@gmail.com')
            affiliate_instance.poster = poster_user  # そのユーザーをposterに設定
            
            affiliate_instance.save()  # 保存

            adinfo_instance = adinfo_form.save(commit=False)
            adinfo_instance.post = affiliate_instance
            adinfo_instance.save()

            return redirect(reverse_lazy('management:affiliate_create'))

        return render(request, self.template_name, {
            'affiliate_form': affiliate_form,
            'adinfo_form': adinfo_form,
        })
        
        
class PosterWaiterList(SuperUserCheck, ListView):
    template_name = 'management/poster_waiter.html'
    context_object_name = 'users'
    model = Users

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.filter(poster_waiter=True)        
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

        # マイアカウントページのキャッシュをクリア
        cache_key_poster = f"is_poster_{user_id}"  # キャッシュキーを作成
        cache.delete(cache_key_poster)  # キャッシュを削除

        # 分岐してリダイレクト
        if 'redirect_to' in request.GET and request.GET['redirect_to'] == 'search_user':
            return redirect('management:search_user')
        else:
            return redirect('management:poster_waiter_list')

class RemoveFromWaitList(SuperUserCheck, View):
    def get(self, request, user_id):
        user = get_object_or_404(Users, id=user_id)
        user.poster_waiter= False
        user.save()
        return redirect('management:poster_waiter_list')


class SearchEmailandAddPoster(SuperUserCheck, View):
    template_name = 'management/search_user.html'
    
    def get(self, request):
        users = []
        email_query = request.GET.get('email')
        if email_query:
            users = Users.objects.filter(email__exact=email_query)
            for user in users:
                user.is_poster = user.groups.filter(name='Poster').exists() 
        return render(request, self.template_name, {'users': users})
    

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
        

class FreezeNotificationApproveView(View):
    template_name = 'management/freeze_notification_approve.html'

    def get(self, request, *args, **kwargs):
        # 未承認の凍結通知を取得
        unapproved_notifications = FreezeNotification.objects.filter(approve=False)
        return render(request, self.template_name, {'unapproved_notifications': unapproved_notifications})

    def post(self, request, *args, **kwargs):
        try:
            notification_id = request.POST.get('notification_id')
            notification = FreezeNotification.objects.get(id=notification_id)
            notification.approve = True
            notification.save()
            messages.success(request, "承認が完了しました。")
        except FreezeNotification.DoesNotExist:
            messages.error(request, "該当する通知が見つかりません。")
        return redirect('/management/freeze_notification_approve/')
    

class DeleteFreezeNotificationView(View):

    def post(self, request, *args, **kwargs):
        notification_id = request.POST.get('notification_id')
        try:
            notification = FreezeNotification.objects.get(id=notification_id)
            notification.delete()
            messages.success(request, "通知を削除しました。")
        except FreezeNotification.DoesNotExist:
            messages.error(request, "該当する通知が見つかりません。")
        return redirect('management:freeze_notification_approve') 
    
    
class VideoListView(ListView):
    model = Videos
    context_object_name = 'videos'
    template_name = 'management/video_list.html'

    def get_queryset(self):
        only_fields = ['id', 'encoding_done', 'post__title']
        # hls_pathが空文字列もしくはNULLであるレコードをフィルタリング
        return Videos.objects.filter(Q(hls_path='') | Q(hls_path__isnull=True)).select_related('post').only(*only_fields)
    

from django.views.decorators.csrf import csrf_protect    
class ToggleEncodingStatusView(View):
    @method_decorator(csrf_protect)
    def post(self, request, *args, **kwargs):
        video_id = request.POST.get('video_id')
        status = request.POST.get('status') == 'true'
        video = Videos.objects.get(id=video_id)
        video.encoding_done = status
        video.save()
        return JsonResponse({'status': 'success'})

class CalculateMonthlyBilling(SuperUserCheck, View):

    template_name = 'management/monthly_billing.html'
    
    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)
    
    def post(self, request, *args, **kwargs):
        print('月末広告計算開始')
        billing_date_str = request.POST.get('billing_date')
        billing_date = datetime.strptime(billing_date_str, "%Y-%m-%dT%H:%M") if billing_date_str else None
        MonthlyBilling.calculate_monthly_billing(now=billing_date)
        messages.success(request, '計算は正常に実行されました')
        return redirect('management:calculate_monthly_billing') 