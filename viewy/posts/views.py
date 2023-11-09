# Python standard library
from datetime import datetime
import os
import random
import math
import time
from random import sample
from decimal import Decimal, ROUND_UP

# Third-party Django
from django import forms
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.models import Group
from django.contrib.auth.decorators import login_required
from django.contrib.messages.views import SuccessMessageMixin
from django.core.exceptions import ObjectDoesNotExist
from django.core import serializers
from django.db.models import Case, Exists, OuterRef, Q, When, Sum, IntegerField, Subquery
from django.http import HttpResponseForbidden, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.utils.dateparse import parse_datetime
from django.utils.decorators import method_decorator
from django.urls import reverse, reverse_lazy
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.views.generic import RedirectView
from django.views.generic.base import TemplateView, View
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, FormView
from django.views.generic.list import ListView

# Local application/library specific
from accounts.models import Follows, SearchHistorys, Surveys, Notification, FreezeNotification, FreezeNotificationView, NotificationView, Blocks
from advertisement.models import AdInfos, AndFeatures, AdCampaigns
from management.models import SupportRate
from .forms import PostForm, SearchForm, VisualForm, VideoForm, FreezeNotificationForm
from .models import Favorites, Collection, Collect, Posts, Report, Users, Videos, Visuals, Ads, WideAds, HotHashtags, KanjiHiraganaSet, RecommendedUser, ViewDurations, TomsTalk, Recommends, PinnedPost

from collections import defaultdict
import logging
logger = logging.getLogger(__name__)
from random import sample

import jaconv
import re
from moviepy.editor import VideoFileClip
from tempfile import NamedTemporaryFile

from django.db.models import Prefetch
from django.core.cache import cache

from django.db.models import Case, When, F, CharField, Value, Count
from django.db.models.query import QuerySet
import json
from itertools import chain
from django.utils.html import escape

from itertools import chain
from django.db import transaction


class BasePostListView(ListView):
    model = Posts
    template_name = 'posts/postlist.html'


    def get_user_filter_condition(self):
        if self.request.user.is_authenticated:  # ログインユーザーの場合のみdimensionを取得
            user_dimension = self.request.user.dimension
        else:
            return {}  # 非ログインユーザーの場合、空の辞書を返す

        filter_condition = {}
        if user_dimension == 2.0:
            filter_condition = {'poster__is_real': False}
        elif user_dimension == 3.0:
            filter_condition = {'poster__is_real': True}
        return filter_condition

    def filter_by_dimension(self, queryset):
        if self.request.user.is_authenticated:
            filter_condition = self.get_user_filter_condition()
            return queryset.filter(**filter_condition)
        return queryset
    

    def get_viewed_count_dict(self, user, post_ids):
        viewed_counts = ViewDurations.objects.filter(user=user, post_id__in=post_ids).values('post').annotate(post_count=Count('id')).values_list('post', 'post_count')
        return {item[0]: item[1] for item in viewed_counts}

    def get_followed_posters_set(self, user, poster_ids):
        followed_poster_ids = Follows.objects.filter(user_id=user.id, poster_id__in=poster_ids).values_list('poster_id', flat=True)
        return set(followed_poster_ids)
    
    # フォローしているパートナーがリコメンドしている投稿を取得する
    def get_followed_recommends_set(self, user, post_ids):
        # ユーザーがフォローしているポスターのIDを取得
        followed_poster_ids = Follows.objects.filter(user_id=user.id).values_list('poster_id', flat=True)

        # 自分がフォローしているポスターがリコメンドした投稿のIDを取得
        followed_recommends = Recommends.objects.filter(user_id__in=followed_poster_ids, post_id__in=post_ids).exclude(post__poster_id__in=followed_poster_ids).values_list('post_id', flat=True)
        return set(followed_recommends)
    
    def get_followed_recommends(self, user):
        # ユーザーがフォローしているポスターのIDを取得
        followed_poster_ids = Follows.objects.filter(user_id=user.id).values_list('poster_id', flat=True)

        # 上記のIDを使用して、そのポスターたちがリコメンドした投稿の詳細を取得
        followed_recommends = Recommends.objects.filter(user_id__in=followed_poster_ids).values('post_id', 'user__username', 'user__displayname')

        result = {}
        for item in followed_recommends:
            display_name_or_username = item['user__displayname'] if item['user__displayname'] else item['user__username']
            if item['post_id'] not in result:
                result[item['post_id']] = []
            result[item['post_id']].append(display_name_or_username)

        return result

    def get_advertiser_users(self):
        # キャッシュキーを設定
        cache_key = "advertiser_users"
        
        # キャッシュからデータを取得
        advertiser_users = cache.get(cache_key)
        
        # キャッシュにデータが存在しない場合
        if not advertiser_users:
            advertiser_users = list(Users.objects.filter(is_advertiser=True))
            
            # データをキャッシュに保存。
            cache.set(cache_key, advertiser_users, 3600)
        
        return advertiser_users


    def get_advertiser_posts(self, user, count=1):
        cache_key = f"advertiser_posts_for_user_{user.id}"
        cached_post_ids = cache.get(cache_key)

        if cached_post_ids:
            print(f"Cache HIT for user {user.id}")  # キャッシュがヒットした場合にログを表示
            return Posts.objects.filter(id__in=cached_post_ids)
        else:
            print(f"Cache MISS for user {user.id}")  # キャッシュがミスした場合にログを表示
        
        user_features = set(user.features.all())
        print(user_features)
        advertiser_users = self.get_advertiser_users()

        # まず、各 AndFeatures の中で、user_features と一致する orfeatures の数を計算
        matching_andfeatures = AndFeatures.objects.annotate(
            matched_orfeatures_count=Count(
                Case(
                    When(orfeatures__in=user_features, then=1),
                    output_field=IntegerField()
                )
            )
        ).filter(matched_orfeatures_count__gte=1)
        

        # 次に、これを使用して各 AdCampaigns で、全ての AndFeatures が上記の条件を満たすものをフィルタリング
        #andfeaturesを持っていないAdCampaignsは、total_andfeaturesは0になり、matched_andfeaturesも0になる（何もマッチしないため）
        matching_adcampaigns = AdCampaigns.objects.annotate(
            total_andfeatures=Count('andfeatures', distinct=True),
            matched_andfeatures=Count(
                Case(
                    When(andfeatures__in=matching_andfeatures, then=1),
                    output_field=IntegerField()
                )
            )
        ).filter(matched_andfeatures=F('total_andfeatures')) \
        .filter(Q(end_date__gte=timezone.now() - timedelta(hours=2)) | Q(end_date__isnull=True)) \
        .filter(start_date__lte=timezone.now()) \
        .filter(is_hidden=False)  # 終了日が現在時刻より未来のものまたはend_dateがNULLのものだけ取得(厳密に終了日を設定すると、終了日が過ぎたキャンペーンを取得できずステータスの更新ができないから、２時間前までに終了したキャンペーンを取得しステータスを必ず設定するようにした)
        # 開始期限が来てないものは除く
        # is_hidden=trueは除く


        # 全キャンペーンのIDリストを取得
        campaign_ids = matching_adcampaigns.values_list('id', flat=True)

        # 各キャンペーンに関連する広告情報から、表示回数の合計を集計
        aggregated_views = AdInfos.objects.filter(ad_campaign_id__in=campaign_ids).values('ad_campaign').annotate(total_views=Sum('post__views_count'))
        views_dict = {item['ad_campaign']: item['total_views'] for item in aggregated_views}

        # 各キャンペーンに関連する広告情報から、クリック数の合計を集計
        aggregated_clicks = AdInfos.objects.filter(ad_campaign_id__in=campaign_ids).values('ad_campaign_id').annotate(total_clicks=Sum('clicks_count'))
        clicks_dict = {item['ad_campaign_id']: item['total_clicks'] for item in aggregated_clicks}

        to_update = []
        for campaign in matching_adcampaigns:
            # 合計表示回数と合計クリック回数を更新
            campaign.total_views_count = views_dict.get(campaign.id, 0)
            campaign.total_clicks_count = clicks_dict.get(campaign.id, 0)

            # 状態がRunningでなければRunningに設定する
            if campaign.status != 'running':
                campaign.status = 'running'
            
            # campaignの終了日が現在日時を超えている場合
            if campaign.end_date and campaign.end_date < timezone.now():
                campaign.status = 'expired'  # 状態をExpiredに設定
                campaign.is_hidden = True
                
                # 実際の表示回数(total_views_count)でactual_cpc_or_cpm と fee の再計算し料金を確定
                if campaign.pricing_model == 'CPM':
                    campaign.actual_cpc_or_cpm = Decimal(campaign.monthly_ad_cost.calculate_cpm(campaign.total_views_count))
                    campaign.fee = Decimal(campaign.total_views_count / 1000) * campaign.actual_cpc_or_cpm
                elif campaign.pricing_model == 'CPC':
                    campaign.actual_cpc_or_cpm = Decimal(campaign.monthly_ad_cost.calculate_cpc(campaign.total_clicks_count))
                    campaign.fee = Decimal(campaign.total_clicks_count) * campaign.actual_cpc_or_cpm

                # 小数第一位まで保存し、それ以降は切り上げ
                campaign.actual_cpc_or_cpm = campaign.actual_cpc_or_cpm.quantize(Decimal('0.1'), rounding=ROUND_UP)
                campaign.fee = campaign.fee.quantize(Decimal('0.1'), rounding=ROUND_UP)

                campaign.save(update_fields=['fee', 'actual_cpc_or_cpm'])
            
            # 目標の表示回数やクリック数を超えていたら状態をachievedに設定
            if (campaign.pricing_model == 'CPC' and campaign.total_clicks_count >= campaign.target_clicks) or \
            (campaign.pricing_model == 'CPM' and campaign.total_views_count >= campaign.target_views):
                campaign.status = 'achieved'
                campaign.is_hidden = True
                campaign.end_date = timezone.now()
            
            to_update.append(campaign)

        # Save all updated campaigns in a single query
        if to_update:
            AdCampaigns.objects.bulk_update(to_update, ['total_views_count', 'total_clicks_count', 'is_hidden', 'status', 'end_date'])


        
        # 最後に、この条件を満たす AdCampaigns を持つ Posts をフィルタリング
        # Directly filter Posts based on matching AdCampaigns
        ad_posts = (Posts.objects.filter(
            Q(adinfos__ad_campaign__in=matching_adcampaigns) ,
            poster__in=advertiser_users,
            is_hidden=False
        )
        .select_related('poster', 'adinfos__post', 'adinfos__ad_campaign')
        .prefetch_related(
            'visuals',
            'adinfos__ad_campaign__andfeatures',
            'adinfos__ad_campaign__andfeatures__orfeatures'
        ))

        # QuerySetをリストに変換
        ad_posts_list = list(ad_posts)

        # 広告主ごとに広告リストを作成し、広告数をカウント
        advertiser_ad_count = defaultdict(int)
        ads_by_advertiser = defaultdict(list)

        for post in ad_posts_list:
            advertiser_id = post.poster.id
            advertiser_ad_count[advertiser_id] += 1
            ads_by_advertiser[advertiser_id].append(post)

        # 全体の広告数をカウント
        total_ads = len(ad_posts_list)

        # 各広告主の割合が上限を超えていないか確認し、超えていれば調整
        for advertiser_id, ads in list(ads_by_advertiser.items()):

            # 広告主の最大許容割合を取得
            max_ad_percentage = ads[0].poster.max_ad_per * 100

            # 現在の広告主の割合を計算
            current_percentage = (advertiser_ad_count[advertiser_id] / total_ads) * 100

            # 割合が上限を超えていれば、ランダムに広告を削除して調整
            while current_percentage > max_ad_percentage:
                # 広告主の広告からランダムに一つ選びリストから削除
                post_to_remove = random.choice(ads_by_advertiser[advertiser_id])
                ad_posts_list.remove(post_to_remove)
                ads_by_advertiser[advertiser_id].remove(post_to_remove)

                # 全広告数を更新
                total_ads -= 1

                # 広告主の広告数を更新
                advertiser_ad_count[advertiser_id] -= 1

                # 新しい割合を計算
                current_percentage = (advertiser_ad_count[advertiser_id] / total_ads) * 100

        # 適切な広告をランダムに取得
        posts = ad_posts_list
        # 以下のコードは以前のものを変更せずにそのまま使用します。
        ad_post_ids = [post.id for post in posts]
        favorited_ads = Favorites.objects.filter(user=user, post_id__in=ad_post_ids).values_list('post', flat=True)
        favorited_ads_set = set(favorited_ads)

        followed_ad_posters_ids = [post.poster.id for post in posts]
        followed_ad_posters_set = self.get_followed_posters_set(user, followed_ad_posters_ids)

        for post in posts:
            post.favorited_by_user = post.id in favorited_ads_set
            post.followed_by_user = post.poster.id in followed_ad_posters_set
        
        ad_post_ids = [post.id for post in posts]
        
        # 結果をキャッシュに保存
        cache.set(cache_key, ad_post_ids, 3600)  # 1時間キャッシュする
        print(f"Cache SET for user {user.id}")  # キャッシュにデータをセットした場合にログを表示
        print(posts)
        
        return posts
    
    def get_random_ad_posts(self, user): #二つの広告を取得するメソッド

        # キャッシュから全ての広告を取得
        all_advertiser_posts = list(self.get_advertiser_posts(user)) 

        return sample(all_advertiser_posts, min(2, len(all_advertiser_posts)))
    
    def integrate_ads(self, queryset, ad_posts_iterator):
        final_posts = []
        post_count = len(queryset)

        if post_count <= 4:  # 4つ以下の場合、広告を取得しない
            return queryset

        ad_insert_positions = [4, 9]  # 5番目と10番目の位置に広告を挿入

        for i, post in enumerate(queryset):
            if i in ad_insert_positions:
                try:
                    final_posts.append(next(ad_posts_iterator))
                except StopIteration:
                    pass
            final_posts.append(post)

        # すべての広告を使用したことを確認
        for ad_post in ad_posts_iterator:
            final_posts.append(ad_post)

        return final_posts

    def annotate_user_related_info(self, queryset):
        if not self.request.user.is_authenticated:
            return queryset

        # Annotate for reports
        reports = Report.objects.filter(reporter=self.request.user, post=OuterRef('pk'))
        queryset = queryset.annotate(reported_by_user=Exists(reports))

        # Annotate for favorites
        favorites = Favorites.objects.filter(user=self.request.user, post=OuterRef('pk'))
        queryset = queryset.annotate(favorited_by_user=Exists(favorites))

        # Annotate for follows
        follows = Follows.objects.filter(user=self.request.user, poster=OuterRef('poster_id'))
        queryset = queryset.annotate(followed_by_user=Exists(follows))
        
        # Annotate for recommends
        recommends = Recommends.objects.filter(user=self.request.user, post=OuterRef('pk'))
        queryset = queryset.annotate(recommended_by_user=Exists(recommends))

        return queryset 
    
    def exclude_advertiser_posts(self, queryset):
        # is_advertiser フィールドが True であるユーザーのIDを取得します
        advertiser_user_ids = Users.objects.filter(is_advertiser=True).values_list('id', flat=True)
        # これらのユーザーによって作成された投稿を除外します
        
        return queryset.exclude(poster_id__in=advertiser_user_ids)

    def exclude_blocked_posters(self, queryset):
        """ログインユーザーがブロックしたポスターの投稿を除外する"""
        user = self.request.user
        if user.is_authenticated:
            # BlocksモデルからブロックされたポスターのIDを取得
            blocked_posters_ids = Blocks.objects.filter(user=user).values_list('poster_id', flat=True)
            # それらのポスターによる投稿を除外
            queryset = queryset.exclude(poster_id__in=blocked_posters_ids)
        return queryset

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.filter(is_hidden=False)

        queryset = self.exclude_blocked_posters(queryset)  # ブロックされたポスターの投稿を除外
        queryset = self.exclude_advertiser_posts(queryset)  # Advertiserの投稿を除外
        queryset = queryset.select_related('poster')
        queryset = self.annotate_user_related_info(queryset)
        queryset = queryset.prefetch_related('visuals', 'videos')

        # is_mangaがFalseの場合に、関連するVideosのencoding_doneが全てTrueである投稿だけを含める
        videos = Videos.objects.filter(post=OuterRef('pk'), encoding_done=False)
        queryset = queryset.exclude(ismanga=False, videos__in=Subquery(videos.values('pk')))

        # 予約投稿日時が現在の日時より未来のものを除外
        now = timezone.now()
        queryset = queryset.exclude(scheduled_post_time__gt=now, scheduled_post_time__isnull=False)

        return queryset


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # ユーザー情報の取得
        user = self.request.user
        
        # ユーザー認証チェック
        if user.is_authenticated:
            # ユーザーが作成したコレクションの取得
            user_collections = Collection.objects.filter(user=user).order_by('-created_at')
            context['user_collections'] = user_collections
            
            # 新規コレクション作成の選択肢の追加
            collection_choices_with_ids = [('新規コレクション作成', None)] + list(user_collections.values_list('name', 'id'))
            context['collection_choices_with_ids'] = collection_choices_with_ids
        
        # ポスト情報の取得
        posts = context.get('object_list', [])
        context['posts'] = posts
        
        # 全てのpost_idを取得
        if isinstance(posts, QuerySet):
            # posts はクエリセットの場合
            post_ids = list(posts.values_list('id', flat=True))
        else:
            # posts はリスト（またはクエリセットでない何か）の場合
            post_ids = [post.id for post in posts]
        
        # collected_inの情報を取得

        collections_for_posts = Collect.objects.filter(post__id__in=post_ids).values_list('post_id', 'collection_id')
        
        # post_idをキーにしたcollection_idのリストを生成
        collections_map = {}
        for post_id, collection_id in collections_for_posts:
            collections_map.setdefault(post_id, []).append(collection_id)
        
        # already_added_collectionsの生成
        already_added_collections = set()
        for post_id, collection_ids in collections_map.items():
            already_added_collections.update(collection_ids)
        context['already_added_collections'] = list(already_added_collections)

        return context
    
    def post(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        more_posts = list(queryset)

        if more_posts:
            for post in more_posts:
                post.visuals_list = post.visuals.all()
                post.videos_list = post.videos.all()
                
            html = render_to_string('posts/get_more_posts.html', {'posts': more_posts}, request=request)
        else:
            html = ""

        return JsonResponse({'html': html})



class PostListView(BasePostListView):

    def dispatch(self, request, *args, **kwargs):
        # ユーザーがログインしていない場合、ログイン画面にリダイレクト
        if not request.user.is_authenticated:
            return redirect('accounts:user_login')
        
        # SupportRateからsupport_manga_rp_rateを事前に取得して保持する
        if not hasattr(self, 'manga_rate'):
            self.manga_rate = None
            try:
                self.manga_rate = float(SupportRate.objects.get(name='support_manga_rp_rate').value)
            except ObjectDoesNotExist:
                pass
        
        return super().dispatch(request, *args, **kwargs)

    # def apply_manga_rate_to_rp(self, post):
    #     if hasattr(post.poster, 'is_real') and not post.poster.is_real and self.manga_rate:
    #         post.rp *= self.manga_rate
            
    def get_followed_users_posts(self, user, posts):
        two_weeks_ago = timezone.now() - timedelta(weeks=2)
        # userがフォローしているユーザーのIDのリストを取得
        followed_user_ids = Follows.objects.filter(user=user).values_list('poster', flat=True)

        # フォローしているユーザーの投稿を取得
        followed_users_posts = posts.filter(poster__id__in=followed_user_ids, posted_at__gte=two_weeks_ago)
        return followed_users_posts

    def get_followed_users_recommended_posts(self, user, posts):
        two_weeks_ago = timezone.now() - timedelta(weeks=2)
        # userがフォローしているユーザーのIDのリストを取得
        followed_user_ids = Follows.objects.filter(user=user).values_list('poster', flat=True)

        # フォローしているユーザーがリコメンドした投稿を取得
        # ただし、そのユーザーが投稿した投稿は除外
        followed_users_post_ids = posts.filter(poster__id__in=followed_user_ids).values_list('id', flat=True)
        recommended_posts = Recommends.objects.filter(
            user__id__in=followed_user_ids,
            created_at__gte=two_weeks_ago,
            post__in=posts
        ).exclude(post__id__in=followed_users_post_ids).select_related('post')

        # 取得したリコメンドから投稿オブジェクトをリストとして取得
        recommended_posts_list = [recommend.post for recommend in recommended_posts]

        return recommended_posts_list

    def get_combined_posts(self, posts, user):

        # 1. 視聴回数の辞書を取得
        post_ids = list(posts.values_list('id', flat=True))
        viewed_counts = self.get_viewed_count_dict(user, post_ids)

        # 2. 視聴回数が最も少ない投稿を絞り込む
        sorted_viewed_counts = sorted(viewed_counts.items(), key=lambda x: x[1])
        least_viewed_posts = set()
        i = 0
        while len(least_viewed_posts) < 8 and i < len(sorted_viewed_counts):
            current_viewed_count = sorted_viewed_counts[i][1]
            post_ids_at_current_viewed_count = []
            while i < len(sorted_viewed_counts) and sorted_viewed_counts[i][1] == current_viewed_count:
                least_viewed_posts.add(sorted_viewed_counts[i][0])
                post_ids_at_current_viewed_count.append(sorted_viewed_counts[i][0])
                i += 1

        # QP順上位8位を取得
        posts_with_least_views = posts.filter(id__in=least_viewed_posts).order_by('-qp')[:8]

        # フォローしているユーザーの投稿を取得
        followed_users_posts = self.get_followed_users_posts(user, posts)

        # フォローしているユーザーがリコメンドした投稿を取得
        followed_users_recommended_posts = self.get_followed_users_recommended_posts(user, posts)

        # 投稿を統合
        all_posts = list(posts_with_least_views) + list(followed_users_posts) + followed_users_recommended_posts

        # IDがユニークな投稿のリストを作成
        unique_posts = []
        seen_ids = set()
        for post in all_posts:
            if post.id not in seen_ids:
                unique_posts.append(post)
                seen_ids.add(post.id)

        # ユニークな投稿のリストをall_postsに再代入
        posts_to_sort_by_rp = unique_posts

        # フォローしているユーザーの投稿のIDのセットを取得
        followed_users_posts_ids = set(followed_users_posts.values_list('id', flat=True))

        # フォローしているユーザーがリコメンドした投稿のIDのセットを取得
        followed_users_recommended_posts_ids = set(post.id for post in followed_users_recommended_posts)

        # RPを計算
        for post in posts_to_sort_by_rp:
            viewed_count = viewed_counts.get(post.id, 0)
            post.rp = post.calculate_rp_for_user(followed_users_posts_ids, viewed_count, followed_users_recommended_posts_ids)
            # self.apply_manga_rate_to_rp(post)

        # RP順でソート
        sorted_posts_by_rp = sorted(posts_to_sort_by_rp, key=lambda post: post.rp, reverse=True)


        # 最終結果を取得
        first_4_by_rp = sorted_posts_by_rp[:4]
        next_2_by_rp = sorted_posts_by_rp[4:6]


        # 全ての広告からランダムに2つを選びます。
        advertiser_posts = self.get_random_ad_posts(user)

        # 最新の100個の投稿を取得して、dimensionフィルターとexclude_blocked_posters, exclude_advertiser_postを適用
        latest_100_posts = Posts.objects.all().order_by('-id')
        latest_100_posts = self.exclude_advertiser_posts(latest_100_posts)  # 広告主の投稿を除外

        # 予約投稿日時が現在の日時より未来のものを除外
        now = timezone.now()
        latest_100_posts = latest_100_posts.exclude(scheduled_post_time__gt=now, scheduled_post_time__isnull=False)

        latest_100_posts = self.exclude_blocked_posters(latest_100_posts)
        latest_100_posts = self.filter_by_dimension(latest_100_posts)[:500]

        # 最新の100件のIDを取得
        post_ids = list(latest_100_posts.values_list('id', flat=True))

        # 100件未満の場合、可能な限りの投稿を選択します。
        num_posts_to_select = min(2, len(post_ids))
        selected_ids = sample(post_ids, num_posts_to_select)

        # 選択したIDを使って投稿を取得
        random_two_posts = (Posts.objects.filter(id__in=selected_ids)
                    .select_related('poster')
                    .prefetch_related('visuals', 'collected_in__collection')  # 'collected_in'とその'collection'を追加
                    .all())

        # 残りのフィルターとアノテーションを適用
        random_two_posts = self.filter_by_dimension(random_two_posts)
        random_two_posts = self.annotate_user_related_info(random_two_posts)
        random_two_posts = list(random_two_posts)

        combined = list(first_4_by_rp) + advertiser_posts[:1] + list(next_2_by_rp) + list(random_two_posts) + advertiser_posts[1:]

        return combined
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # 次元のフィルターはここで適応（いいねやフォローには適応したくないから）
        queryset = self.filter_by_dimension(queryset)
        
        return queryset
    
    def check_unanswered_surveys(self, user):
        # ユーザーがすでに選択した特性を取得
        selected_features = user.features.all()
        
        # 選択された特性に関連するアンケートを取得
        answered_surveys = Surveys.objects.filter(options__in=selected_features).distinct()
        
        # 未回答のアンケートを取得
        unanswered_surveys = Surveys.objects.exclude(id__in=answered_surveys.values_list('id'))

        return unanswered_surveys.first() 

    def get_context_data(self, **kwargs):
        
        # 親クラスのget_context_dataを実行
        context = super().get_context_data(**kwargs)
        
        # ユーザー情報の取得
        user = self.request.user
        
        if user.is_authenticated:
            # ポスト情報の取得と結合
            posts = context['posts']
            context['posts'] = self.get_combined_posts(posts, user)
            
            # フォローしているユーザーがリコメンドしている投稿の取得
            context['followed_recommends_details'] = self.get_followed_recommends(user)
   
            # 未回答のアンケートのチェック
            unanswered_survey = self.check_unanswered_surveys(user)
            if random.random() < 0.1:
                context['unanswered_survey'] = unanswered_survey
            else:
                context['unanswered_survey'] = None
            
            # 未読の通知の取得
            read_notifications = NotificationView.objects.filter(user=user).values_list('notification_id', flat=True)
            if user.groups.filter(name='Poster').exists():
                unread_notifications = Notification.objects.exclude(id__in=read_notifications)
            else:
                unread_notifications = Notification.objects.exclude(id__in=read_notifications).filter(only_partner=False)
            context['unread_notifications'] = unread_notifications
            
            # ユーザーがフォローしているposterのIDリストの取得
            followed_posters_ids = Follows.objects.filter(user=user).values_list('poster_id', flat=True)
            
            # 未読の凍結通知の取得
            read_freeze_notifications = FreezeNotificationView.objects.filter(user=user).values_list('freeze_notification_id', flat=True)
            unread_freeze_notifications = FreezeNotification.objects.exclude(id__in=read_freeze_notifications).filter(approve=True, poster_id__in=followed_posters_ids)
            context['unread_freeze_notifications'] = unread_freeze_notifications

        return context
       

    
    
class GetMorePostsView(PostListView):

    def get(self, request, *args, **kwargs):
        # object_listの設定
        self.object_list = self.get_queryset()
        
        # PostListViewの処理を実行
        context = self.get_context_data(**kwargs)
        posts = context['posts']
        followed_recommends_details = context['followed_recommends_details']

        # 投稿とその他のデータをHTMLフラグメントとしてレンダリング
        data_to_pass = {
            'posts': posts,
            'user': request.user,
            'followed_recommends_details': followed_recommends_details
        }
        html = render_to_string('posts/get_more_posts.html', data_to_pass, request=request)
        
        # HTMLフラグメントをJSONとして返す
        return JsonResponse({'html': html}, content_type='application/json')



class VisitorPostListView(BasePostListView):
    template_name = 'posts/visitor_postlist.html'

    def dispatch(self, request, *args, **kwargs):
        # ユーザーがログインしている場合、PostListViewにリダイレクト
        if request.user.is_authenticated:
            return redirect('posts:postlist')
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        # 親クラスのget_querysetを呼び出し
        base_query = super().get_queryset()

        # is_realがTrueのユーザーの投稿で、favorite_countが上位5件を取得
        real_user_posts = base_query.filter(poster__is_real=True).order_by('-favorite_count')[:5]

        # is_realがFalseのユーザーの投稿で、favorite_countが上位5件を取得
        not_real_user_posts = base_query.filter(poster__is_real=False).order_by('-favorite_count')[:5]

        # 上記の2つのクエリセットを結合
        combined_query = real_user_posts.union(not_real_user_posts).order_by('-favorite_count')[:10]

        # クエリを実行して結果をリストに変換
        combined_posts = list(combined_query)

        # 10件の投稿の中からランダムに5件を選択
        posts = random.sample(combined_posts, 5)
        
        return posts
    
    
# 好みページ
class StarView(TemplateView):
    template_name = os.path.join('posts', 'star.html')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = get_object_or_404(Users, pk=self.request.user.id)  # 仮定：現在のログインユーザーの情報を取得
        context['favorite_count'] = user.favorite_received.count()  # いいねの数
        context['collection_count'] = user.collections.count()      # コレクションの数
        context['follow_count'] = Follows.objects.filter(user=user).count()  # フォローしている人数
        return context
    

class BaseFavoriteView(BasePostListView):
    def get_user_favorite_post_ids(self):
        """お気に入りにした投稿のIDを取得"""
        cache_key = f'favorite_posts_for_user_{self.request.user.id}'
        cached_post_ids = cache.get(cache_key)

        if cached_post_ids:
            print(f"Cache HIT for favorite posts for user {self.request.user.id}")
            return cached_post_ids

        print(f"Cache MISS for favorite posts for user {self.request.user.id}")
        user_favorite_posts = Favorites.objects.filter(user=self.request.user).order_by('-created_at')
        post_ids = [favorite.post_id for favorite in user_favorite_posts]

        cache.set(cache_key, post_ids, 300)  # 5分間キャッシュ
        return post_ids



class FavoritePageView(BaseFavoriteView):
    template_name = os.path.join('posts', 'favorite_page.html')

    def get_queryset(self):
        post_ids = self.get_user_favorite_post_ids()
        queryset = super().get_queryset().filter(id__in=post_ids)
        queryset = sorted(queryset, key=lambda post: post_ids.index(post.id))
        return queryset


class FavoritePostListView(BaseFavoriteView):
    template_name = os.path.join('posts', 'favorite_list.html')

    def get_queryset(self):
        # URLから'post_id'パラメータを取得
        selected_post_id = int(self.request.GET.get('post_id', 0))

        # ユーザーがお気に入りに追加した全ての投稿を取得 (BaseFavoriteView から取得)
        post_ids = self.get_user_favorite_post_ids()

        queryset = super().get_queryset().filter(id__in=post_ids)
        if selected_post_id in post_ids:
            selected_post_index = post_ids.index(selected_post_id)
            selected_post_ids = post_ids[selected_post_index:selected_post_index+8]
            queryset = [post for post in queryset if post.id in selected_post_ids]
            queryset = sorted(queryset, key=lambda post: selected_post_ids.index(post.id))
   

        # 選択した投稿がリストの中にあるか確認
        if selected_post_id in post_ids:
            # 選択した投稿のインデックスを見つける
            selected_post_index = post_ids.index(selected_post_id)
            # 選択した投稿とそれに続く投稿のIDを取得
            selected_post_ids = post_ids[selected_post_index:selected_post_index+8]
            # querysetが選択した投稿とそれに続く投稿のみを含むようにフィルタリング
            queryset = [post for post in queryset if post.id in selected_post_ids]

        # querysetがselected_post_idsの順番と同じになるようにソート
        queryset = sorted(queryset, key=lambda post: selected_post_ids.index(post.id))

        # 現在のユーザーを取得
        user = self.request.user

        # 2つの広告ポストをランダムに取得
        ad_posts = self.get_random_ad_posts(user) 

        # 投稿リストに広告を組み込む
        return self.integrate_ads(queryset, iter(ad_posts))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context
    
    

class GetMoreFavoriteView(BaseFavoriteView):

    def get_queryset(self):
        last_post_id = int(self.request.POST.get('last_post_id', 0))

        # ユーザーがお気に入りに追加した全ての投稿を取得 (BaseFavoriteView から取得)
        post_ids = self.get_user_favorite_post_ids()

        if last_post_id:
            last_favorite_index = post_ids.index(last_post_id)
            next_post_ids = post_ids[last_favorite_index+1:last_favorite_index+8] 

            queryset = super().get_queryset().filter(id__in=next_post_ids)
            queryset = sorted(queryset, key=lambda post: next_post_ids.index(post.id))
        else:
            queryset = super().get_queryset().filter(id__in=post_ids)

        # 現在のユーザーを取得
        user = self.request.user

        # 2つの広告ポストをランダムに取得
        ad_posts = self.get_random_ad_posts(user) 

        # 投稿リストに広告を組み込む
        return self.integrate_ads(queryset, iter(ad_posts))

    

class GetMorePreviousFavoriteView(BaseFavoriteView):

    def get_queryset(self):
        first_post_id = int(self.request.POST.get('first_post_id', 0))

        # ユーザーがお気に入りに追加した全ての投稿を取得 (BaseFavoriteView から取得)
        post_ids = self.get_user_favorite_post_ids()

        if first_post_id:
            first_favorite_index = post_ids.index(first_post_id)
            prev_post_ids = post_ids[max(0, first_favorite_index - 8):first_favorite_index] 

            queryset = super().get_queryset().filter(id__in=prev_post_ids)
            queryset = sorted(queryset, key=lambda post: prev_post_ids.index(post.id))  
        else:
            queryset = super().get_queryset().filter(id__in=post_ids)

        # 現在のユーザーを取得
        user = self.request.user

        # 2つの広告ポストをランダムに取得
        ad_posts = self.get_random_ad_posts(user) 

        # 投稿リストに広告を組み込む
        return self.integrate_ads(queryset, iter(ad_posts))




class CollectionsMenuView(ListView):
    template_name = 'posts/collections_menu.html'
    context_object_name = 'collections'

    def get_queryset(self):
        return Collection.objects.filter(user=self.request.user).prefetch_related('collects__post').order_by('-created_at')


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        for collection in context['collections']:
            # Add the number of posts in the collection
            collection.post_count = collection.collects.count()

            latest_post = collection.collects.order_by('-added_at').first().post if collection.collects.exists() else None
            if latest_post:
                if latest_post.ismanga:
                    collection.latest_thumbnail = latest_post.visuals.first().visual.url if latest_post.visuals.exists() else None
                else:
                    video = latest_post.videos.first()
                    collection.latest_thumbnail = video.thumbnail.url if video and video.thumbnail else None
        return context


class BaseCollectionView(BasePostListView):  # BasePostListViewを継承
    def get_user_collection_post_ids(self, collection_id):
        """コレクションに含まれる投稿のIDを取得"""
        cache_key = f'collection_posts_for_user_{self.request.user.id}_collection_{collection_id}'
        cached_post_ids = cache.get(cache_key)

        if cached_post_ids:
            print(f"Cache HIT for collection posts for user {self.request.user.id}")
            return cached_post_ids

        print(f"Cache MISS for collection posts for user {self.request.user.id}")
        user_collection_posts = Collect.objects.filter(collection__id=collection_id).order_by('-added_at')
        post_ids = [collect.post_id for collect in user_collection_posts]

        cache.set(cache_key, post_ids, 300)  # 5分間キャッシュ
        return post_ids
    

class CollectionPageView(BaseCollectionView):
    template_name = os.path.join('posts', 'collection_page.html')

    def get_queryset(self):
        collection_id = self.kwargs['collection_id']  # URLからコレクションのIDを取得
        post_ids = self.get_user_collection_post_ids(collection_id)
        queryset = super().get_queryset().filter(id__in=post_ids)
        queryset = sorted(queryset, key=lambda post: post_ids.index(post.id))
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        collection_id = self.kwargs['collection_id']
        collection = get_object_or_404(Collection, id=collection_id)
        context['collection_name'] = collection.name
        context['collection_id'] = collection_id  # 追加
        return context
    
    
class CollectionPostListView(BaseCollectionView):
    template_name = os.path.join('posts', 'collection_list.html')

    def get_queryset(self):
        # URLから'post_id'パラメータを取得
        selected_post_id = int(self.request.GET.get('post_id', 0))

        # コレクションに含まれる全ての投稿を取得 (BaseCollectionView から取得)
        collection_id = self.kwargs['collection_id']  # URLからコレクションのIDを取得
        post_ids = self.get_user_collection_post_ids(collection_id)

        queryset = super().get_queryset().filter(id__in=post_ids)
        if selected_post_id in post_ids:
            selected_post_index = post_ids.index(selected_post_id)
            selected_post_ids = post_ids[selected_post_index:selected_post_index+8]
            queryset = [post for post in queryset if post.id in selected_post_ids]
            queryset = sorted(queryset, key=lambda post: selected_post_ids.index(post.id))

        # 現在のユーザーを取得
        user = self.request.user

        # 2つの広告ポストをランダムに取得 (注: この関数はFavoritePostListViewにのみ存在します。CollectionPostListViewにもこの機能が必要な場合は、対応する関数を追加するか、BasePostListViewに移動してください)
        ad_posts = self.get_random_ad_posts(user) 

        # 投稿リストに広告を組み込む
        return self.integrate_ads(queryset, iter(ad_posts))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        collection = get_object_or_404(Collection, id=self.kwargs['collection_id'])
        context['collection_name'] = collection.name
        context['collection_id'] = self.kwargs['collection_id']  # 追加: collection_id を context に設定
        return context

    
    
class GetMoreCollectionView(BaseCollectionView):

    def get_queryset(self):
        last_post_id = int(self.request.POST.get('last_post_id', 0))
        
        collection_id = self.request.POST.get('collection_id')
        post_ids = self.get_user_collection_post_ids(collection_id)

        if last_post_id:
            try:
                last_collection_index = post_ids.index(last_post_id)
            except ValueError:
                # last_post_idがpost_idsに存在しない場合のエラーハンドリング
                return []

            next_post_ids = post_ids[last_collection_index+1:last_collection_index+8]

            queryset = super().get_queryset().filter(id__in=next_post_ids)
            queryset = sorted(queryset, key=lambda post: next_post_ids.index(post.id))
        else:
            queryset = super().get_queryset().filter(id__in=post_ids)

        return queryset
    
    
class GetMorePreviousCollectionView(BaseCollectionView):

    def get_queryset(self):
        first_post_id = int(self.request.POST.get('first_post_id', 0))

        # URLからコレクションのIDを取得
        collection_id = self.request.POST.get('collection_id')
        post_ids = self.get_user_collection_post_ids(collection_id)

        if first_post_id:
            try:
                first_collection_index = post_ids.index(first_post_id)
            except ValueError:
                # first_post_idがpost_idsに存在しない場合のエラーハンドリング
                return []

            prev_post_ids = post_ids[max(0, first_collection_index - 8):first_collection_index]

            queryset = super().get_queryset().filter(id__in=prev_post_ids)
            queryset = sorted(queryset, key=lambda post: prev_post_ids.index(post.id))
        else:
            queryset = super().get_queryset().filter(id__in=post_ids)

        # 現在のユーザーを取得
        user = self.request.user

        # 2つの広告ポストをランダムに取得
        ad_posts = self.get_random_ad_posts(user)

        # 投稿リストに広告を組み込む
        return self.integrate_ads(queryset, iter(ad_posts))
    
    
class DeleteCollectionView(View):
    def post(self, request, *args, **kwargs):
        collection_id = kwargs.get('collection_id')
        try:
            collection = Collection.objects.get(pk=collection_id)
            collection.delete()
            return JsonResponse({'status': 'success', 'message': 'Collection deleted successfully.'})
        except Collection.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Collection not found.'})
        
        
@method_decorator(csrf_exempt, name='dispatch')
class RenameCollectionView(View):

    def post(self, request, collection_id):
        try:
            # リクエストボディからJSONとしてデータを取得
            data = json.loads(request.body.decode('utf-8'))
            new_name = data.get('newName')
            
            # DBから該当のコレクションを取得
            collection = Collection.objects.get(id=collection_id)
            collection.name = new_name  # コレクション名を更新
            collection.save()  # 変更を保存

            return JsonResponse({"status": "success", "message": "コレクション名を変更しました。"})
        
        except Collection.DoesNotExist:
            return JsonResponse({"status": "error", "message": "コレクションが存在しません。"})
        except Exception as e:
            return JsonResponse({"status": "error", "message": f"エラー: {str(e)}"})

    def get(self, request, collection_id):
        return JsonResponse({"status": "error", "message": "不正なリクエストです。"})
    
    
@method_decorator(csrf_exempt, name='dispatch')
class CreateNewCollection(View):
    
    def post(self, request):
        try:
            collection_name = request.POST.get('collectionName')
            # リクエストユーザーをCollectionのuserフィールドにセット
            new_collection = Collection(name=collection_name, user=request.user)
            new_collection.save()

            return JsonResponse({"status": "success", "message": "コレクションを作成しました。"})
        except Exception as e:
            return JsonResponse({"status": "error", "message": f"エラー: {str(e)}"})
    

class  BasePosterView(BasePostListView):
    def set_poster_from_username(self):
        self.poster = get_object_or_404(Users, username=self.kwargs['username'])

    def set_poster_from_pk(self):
        self.poster = get_object_or_404(Users, pk=self.request.POST.get('pk'))

    def get_filtered_posts(self):
        cache_key = f'filtered_posts_for_user_{self.poster.id}'
        cached_posts = cache.get(cache_key)

        if cached_posts:
            print(f"Cache HIT for user {self.poster.id}")
            return cached_posts

        print(f"Cache MISS for user {self.poster.id}")
        posts = Posts.objects.filter(poster=self.poster).order_by('-posted_at')
        cache.set(cache_key, posts, 300)  # キャッシュの有効期間を300秒（5分）に設定
        return posts

    def integrate_ads_to_queryset(self, queryset):

        # 現在のユーザーを取得
        user = self.request.user
        # 2つの広告ポストをランダムに取得
        ad_posts = self.get_random_ad_posts(user) 

        # 投稿リストに広告を組み込む
        return self.integrate_ads(queryset, iter(ad_posts))
    
    def get_pinned_posts(self):
        """
        投稿者がピン止めした投稿をorderフィールドの順番に返す。
        """
        # PinnedPostモデルを使用して、投稿者がピン止めした投稿を取得します。
        pinned_post_objects = PinnedPost.objects.filter(user=self.poster)
        
        # 取得したPinnedPostオブジェクトから実際の投稿を取り出します。
        pinned_posts = [pinned.post for pinned in pinned_post_objects]
        
        return pinned_posts
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # ユーザーが自身のページを見ている場合のみ、followed_recommends_detailsを追加
        if self.request.user == self.poster:
            context['followed_recommends_details'] = self.get_followed_recommends(self.request.user)

        return context
    
    def post(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        more_posts = list(queryset)

        if more_posts:
            for post in more_posts:
                post.visuals_list = post.visuals.all()
                post.videos_list = post.videos.all()
            
            context = {
                'posts': more_posts,
                'user': request.user
            }

            # ユーザーが自身のページを見ている場合のみ、followed_recommends_detailsを追加
            if request.user == self.poster:
                context['followed_recommends_details'] = self.get_followed_recommends(request.user)

            html = render_to_string('posts/get_more_posts.html', context, request=request)
        else:
            html = ""

        return JsonResponse({'html': html})
    

class PosterPageView(BasePosterView):
    template_name = os.path.join('posts', 'poster_page.html')

    def get_queryset(self):
        self.set_poster_from_username()

        # `get_pinned_posts`メソッドを使って、ピン止めされた投稿を取得
        pinned_posts = list(self.get_pinned_posts())
        pinned_post_ids = [post.id for post in pinned_posts]

        # 元のquerysetを取得し、ピン止めされた投稿を除外
        queryset = super().get_queryset().filter(poster=self.poster).exclude(id__in=pinned_post_ids).order_by('-posted_at')

        # ピン止めされた投稿を最初に追加して結果を返す
        return pinned_posts + list(queryset)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        if user.is_authenticated:  # ユーザーがログインしている場合のみ以下の処理を実行
            # テンプレートでのクエリを避けるためのリストを作成
            followers_ids = self.poster.follow.all().values_list('id', flat=True)
            context['is_user_following'] = user.id in followers_ids
            # ユーザーがフォローしているかどうかの確認
            context['is_user_blocking'] = Blocks.objects.filter(user=user, poster=self.poster).exists()

            # ピン止めされた投稿のIDを取得
            pinned_post_ids = PinnedPost.objects.filter(user=self.poster).values_list('post_id', flat=True)
            context['pinned_post_ids'] = pinned_post_ids

        else:
            context['is_user_following'] = False
            context['is_user_blocking'] = False

        context['about_poster'] = self.poster
        return context



class PosterPostListView(BasePosterView):
    template_name = os.path.join('posts', 'poster_post_list.html')

    def get_queryset(self):
        selected_post_id = int(self.request.GET.get('post_id', 0))

        # Use the method from the BasePosterView
        self.set_poster_from_username()
        poster_posts = self.get_filtered_posts()

        post_ids = [post.id for post in poster_posts]
        pinned_post_ids = [post.id for post in self.get_pinned_posts()]

        if selected_post_id in pinned_post_ids:
            pinned_post_index = pinned_post_ids.index(selected_post_id)

            # 残りのピン止め投稿
            remaining_pinned = pinned_post_ids[pinned_post_index:]

            # 残りの通常の投稿を取得
            remaining_posts = post_ids[:8 - len(remaining_pinned)]
            combined_ids = remaining_pinned + remaining_posts

            queryset = super().get_queryset().filter(id__in=combined_ids)
            queryset = sorted(queryset, key=lambda post: combined_ids.index(post.id))

        else:
            queryset = super().get_queryset().filter(id__in=post_ids)

            if selected_post_id in post_ids:
                selected_post_index = post_ids.index(selected_post_id)
                selected_post_ids = post_ids[selected_post_index:selected_post_index+8]
                queryset = [post for post in queryset if post.id in selected_post_ids]
                queryset = sorted(queryset, key=lambda post: selected_post_ids.index(post.id))
        
        # Use the integrate method from the BasePosterView
        return self.integrate_ads_to_queryset(queryset)



class GetMorePosterPostsView(BasePosterView):

    def get_queryset(self):
        last_post_id = int(self.request.POST.get('last_post_id', 0))

        # Use the method from the BasePosterView to set the poster
        self.set_poster_from_pk()

        if not self.poster:
            return Posts.objects.none()

        poster_posts = self.get_filtered_posts()
        post_ids = list(poster_posts.values_list('id', flat=True))

        # ピン止めされた投稿のIDを取得
        pinned_post_ids = [post.id for post in self.get_pinned_posts()]

        # ピン止めされた投稿を除外する
        post_ids = [post_id for post_id in post_ids if post_id not in pinned_post_ids]

        if last_post_id:
            try:
                last_poster_index = post_ids.index(last_post_id)
            except ValueError:
                return Posts.objects.none()

            next_post_ids = post_ids[last_poster_index+1:last_poster_index+9]
            queryset = super().get_queryset().filter(id__in=next_post_ids)
            queryset = sorted(queryset, key=lambda post: next_post_ids.index(post.id))
        else:
            return Posts.objects.none()

        # Use the integrate method from the BasePosterView
        return self.integrate_ads_to_queryset(queryset)
    
    
class GetMorePreviousPosterPostsView(BasePosterView):

    def get_queryset(self):
        # POSTデータから最初の投稿IDを取得
        first_post_id = int(self.request.POST.get('first_post_id', 0))

        # BasePosterViewのメソッドを使って、投稿者を設定
        self.set_poster_from_pk()

        if not self.poster:
            return Posts.objects.none()

        # BasePosterViewのget_pinned_postsメソッドを使ってピン止めされた投稿を取得
        pinned_posts = self.get_pinned_posts()
        pinned_post_ids = [post.id for post in pinned_posts]

        # BasePosterViewのget_filtered_postsメソッドを使って投稿を取得
        poster_posts = self.get_filtered_posts().exclude(id__in=pinned_post_ids)  # 既に取得したピン止め投稿を除外

        # ピン止めされた投稿と他の投稿を結合
        all_posts = pinned_posts + list(poster_posts)
        post_ids = [post.id for post in all_posts]

        # 最初の投稿IDのインデックスを取得
        try:
            first_post_index = post_ids.index(first_post_id)
        except ValueError:
            return Posts.objects.none()

        # 最初の投稿より前の投稿IDを取得するロジック
        prev_post_ids = post_ids[max(0, first_post_index - 8):first_post_index]

        # querysetを取得し、投稿IDがprev_post_idsに含まれるものだけをフィルタリング
        queryset = super().get_queryset().filter(id__in=prev_post_ids)
        # querysetをprev_post_idsの順に並べ替え
        queryset = sorted(queryset, key=lambda post: prev_post_ids.index(post.id))

        # BasePosterViewのintegrateメソッドを使って、クエリセットに広告を組み込む
        return self.integrate_ads_to_queryset(queryset)
 
   
class BaseHashtagListView(BasePostListView):
    def get(self, request, *args, **kwargs):
        self.order = request.GET.get('order', 'posted_at')
        return super().get(request, *args, **kwargs)

    def filter_by_hashtag(self, queryset, hashtag):
        return queryset.filter(
            Q(hashtag1=hashtag) |
            Q(hashtag2=hashtag) |
            Q(hashtag3=hashtag)
        )
        
    def filter_by_selected_dimension(self, queryset):
        # セッションから利用者の選択したdimensionを取得
        selected_dimension = self.request.session.get('selected_dimension', None)

        if selected_dimension is None:
            return queryset  # セッションからdimensionが取得できない場合、クエリセットをそのまま返す

        filter_condition = {}
        if selected_dimension == 2.0:  # セッションから取得した値は文字列なので注意
            filter_condition = {'poster__is_real': False}
        elif selected_dimension == 3.0:
            filter_condition = {'poster__is_real': True}

        return queryset.filter(**filter_condition)


    def order_queryset(self, queryset):
        if self.order == 'qp':
            return queryset.order_by('-qp')
        else:
            return queryset.order_by('-posted_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_order'] = self.order
        return context

    def get_hashtag(self):
        return self.kwargs.get('hashtag', self.request.POST.get('hashtag'))

    def post(self, request, *args, **kwargs):
        self.order = request.POST.get('order', 'posted_at')
        return super().post(request, *args, **kwargs)


class HashtagDimensionChangeView(View):
    def post(self, request, *args, **kwargs):
        dimension = request.POST.get('dimension')
        if dimension:
            try:
                dimension = float(dimension)
                request.session['selected_dimension'] = dimension
                
                # Print the set value to the console
                print('Set selected_dimension in session:', dimension)
                
                return JsonResponse({'status': 'success'})
            except ValueError:
                return JsonResponse({'status': 'error', 'message': 'Invalid dimension value'}, status=400)
        return JsonResponse({'status': 'error', 'message': 'Dimension is required'}, status=400)


class HashtagPageView(BaseHashtagListView):
    template_name = os.path.join('posts', 'hashtag_page.html')

    def get_queryset(self):
        queryset = super().get_queryset()
        hashtag = self.kwargs['hashtag']
        
        # 選択したdimensionによるフィルターをかける
        queryset = self.filter_by_selected_dimension(queryset)
        
        queryset = self.filter_by_hashtag(queryset, hashtag)
        queryset = self.order_queryset(queryset)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # セッションから選択されたdimensionを取得し、コンテキストに追加
        context['selected_dimension'] = self.request.session.get('selected_dimension', '2.5')
        
        context['current_dimension'] = getattr(self.request.user, 'dimension', 2.5)
        context['form'] = SearchForm()
        context['hashtag'] = self.kwargs['hashtag']
        
        return context
    

class HashtagPostListView(BaseHashtagListView):
    template_name = os.path.join('posts', 'hashtag_list.html')

    def get_queryset(self):
        selected_post_id = int(self.request.GET.get('post_id', 0))
        hashtag = self.kwargs['hashtag']

        queryset = Posts.objects.all()

        # Hashtag Filter
        queryset = self.filter_by_hashtag(queryset, hashtag)

        # 選択したdimensionによるフィルターをかける
        queryset = self.filter_by_selected_dimension(queryset)

        # Order the posts
        queryset = self.order_queryset(queryset)

        post_ids = [post.id for post in queryset]

        base_queryset = super().get_queryset().filter(id__in=post_ids)

        # 選択した投稿がリストの中にあるか確認
        if selected_post_id in post_ids:
            # 選択した投稿のインデックスを見つける
            selected_post_index = post_ids.index(selected_post_id)
            # 選択した投稿とそれに続く投稿のIDを取得
            selected_post_ids = post_ids[selected_post_index:selected_post_index+8]
            # base_querysetが選択した投稿とそれに続く投稿のみを含むようにフィルタリング
            base_queryset = [post for post in base_queryset if post.id in selected_post_ids]

        # base_querysetがselected_post_idsの順番と同じになるようにソート
        base_queryset = sorted(base_queryset, key=lambda post: post_ids.index(post.id))


        # 現在のユーザーを取得
        user = self.request.user
        # 2つの広告ポストをランダムに取得
        ad_posts = self.get_random_ad_posts(user) 

        # 投稿リストに広告を組み込む
        return self.integrate_ads(base_queryset, iter(ad_posts))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['hashtag'] = self.kwargs['hashtag']
        return context
    

class GetMoreHashtagView(BaseHashtagListView):
    
    def get_hashtag(self):
        return self.request.POST.get('hashtag')

    def get_queryset(self):
        print(self.request.POST)  # POSTデータをログに出力

        last_post_id = int(self.request.POST.get('last_post_id', 0))
        hashtag = self.get_hashtag()  # Use the method to get hashtag

        # Get the filtered queryset by hashtag
        queryset = Posts.objects.all()
        queryset = self.filter_by_hashtag(queryset, hashtag)

        # 選択したdimensionによるフィルターをかける
        queryset = self.filter_by_selected_dimension(queryset)

        # Apply the order to the queryset
        queryset = self.order_queryset(queryset)
        
        post_ids = list(queryset.values_list('id', flat=True))

        if last_post_id:
            last_poster_index = post_ids.index(last_post_id)
            next_post_ids = post_ids[last_poster_index+1:last_poster_index+9]

            queryset = super().get_queryset().filter(id__in=next_post_ids)
            queryset = sorted(queryset, key=lambda post: next_post_ids.index(post.id))
        else:
            queryset = super().get_queryset().filter(id__in=post_ids)

        # 現在のユーザーを取得
        user = self.request.user
        # 2つの広告ポストをランダムに取得
        ad_posts = self.get_random_ad_posts(user) 

        # 投稿リストに広告を組み込む
        return self.integrate_ads(queryset, iter(ad_posts))
    


class GetMorePreviousHashtagView(BaseHashtagListView):

    def get_hashtag(self):
        return self.request.POST.get('hashtag')

    def get_queryset(self):
        first_post_id = int(self.request.POST.get('first_post_id', 0))
        hashtag = self.get_hashtag()  # Use the method to get hashtag
        
        # Get the filtered queryset by hashtag
        queryset = Posts.objects.all()
        queryset = self.filter_by_hashtag(queryset, hashtag)

        # 選択したdimensionによるフィルターをかける
        queryset = self.filter_by_selected_dimension(queryset)

        # Apply the order to the queryset
        queryset = self.order_queryset(queryset)

        post_ids = list(queryset.values_list('id', flat=True))

        if first_post_id:
            first_post_index = post_ids.index(first_post_id)
            prev_post_ids = post_ids[max(0, first_post_index - 8):first_post_index] 

            queryset = super().get_queryset().filter(id__in=prev_post_ids)
            queryset = sorted(queryset, key=lambda post: prev_post_ids.index(post.id))
        else:
            queryset = super().get_queryset().filter(id__in=post_ids)

        # 現在のユーザーを取得
        user = self.request.user
        # 2つの広告ポストをランダムに取得
        ad_posts = self.get_random_ad_posts(user) 

        # 投稿リストに広告を組み込む
        return self.integrate_ads(queryset, iter(ad_posts))
    

class MyPostView(BasePostListView):
    template_name = os.path.join('posts', 'my_posts.html')

    def get_queryset(self):
        user = self.request.user
        
        # ピン止めされた投稿のIDを取得
        pinned_post_ids = list(PinnedPost.objects.filter(user=user).values_list('post_id', flat=True)[:3])
        
        # ピン止めされた投稿を直接取得
        pinned_posts = Posts.objects.filter(id__in=pinned_post_ids)
        
        # 通常の投稿を取得
        regular_posts = (Posts.objects.filter(poster=user)
                            .exclude(id__in=pinned_post_ids)  # ピン止めされた投稿を除外
                            .select_related('poster')
                            .prefetch_related('visuals', 'videos')
                            .order_by('-posted_at'))
         # ピン止めした投稿と通常の投稿を結合
        combined_posts = list(pinned_posts) + list(regular_posts)

        return combined_posts

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # ピン止めされている投稿のIDを取得
        user = self.request.user
        pinned_post_ids = list(PinnedPost.objects.filter(user=user).values_list('post_id', flat=True))
        
        # ピン止めされている投稿のIDをテンプレートに渡す
        context['pinned_post_ids'] = pinned_post_ids
        context['now'] = timezone.now()  # 現在の日時をコンテキストに追加

        return context 
      
    
class HiddenPostView(BasePostListView):
    template_name = os.path.join('posts', 'hidden_post.html')

    def get_queryset(self):
        post_id = self.request.GET.get('post_id')
        if post_id:
            queryset = Posts.objects.filter(id=post_id, is_hidden=True)
            queryset = queryset.select_related('poster')
            queryset = queryset.prefetch_related('visuals', 'videos')
            print(queryset)
            return queryset
        # post_idが指定されていない、または該当する投稿が存在しない場合は空のクエリセットを返す
        return Posts.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        posts = context['object_list']
        
        for post in posts:
            post.visuals_list = list(post.visuals.all())
            post.videos_list = list(post.videos.all())
            
        context['posts'] = posts
        return context
    

class UnpublishedPostView(BasePostListView):
    template_name = os.path.join('posts', 'unpublished_post.html')

    def get_queryset(self):
        user = self.request.user
        post_id = self.request.GET.get('post_id')
        
        if post_id:
            now = timezone.now()
            
            queryset = Posts.objects.filter(
                id=post_id, 
                poster=user,  # 現在のユーザーが投稿者であることを確認
                is_hidden=False,  # 隠されていることを確認
                scheduled_post_time__gt=now  # 予約投稿日時が未来であることを確認
            )
            
            queryset = queryset.select_related('poster')
            queryset = queryset.prefetch_related('visuals', 'videos')
            
            return queryset

        # post_idが指定されていない、または該当する投稿が存在しない場合は空のクエリセットを返す
        return Posts.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        posts = context['object_list']
        
        for post in posts:
            post.visuals_list = list(post.visuals.all())
            post.videos_list = list(post.videos.all())
            
        context['posts'] = posts
        return context
    
class UpdateScheduledTimeView(View):
    # POSTリクエストを処理するためのメソッド
    def post(self, request, *args, **kwargs):
        post_id = request.POST.get('post_id')
        action = request.POST.get('action')
        
        try:
            post = Posts.objects.get(id=post_id)
        except Posts.DoesNotExist:
            # ポストが存在しない場合、リダイレクト先を決定する
            return redirect(reverse_lazy('name_of_the_view_displaying_the_posts'))

        if action == "update":
            scheduled_time = request.POST.get('scheduled_time')
            post.scheduled_post_time = scheduled_time
            post.save()
        elif action == "publish_now":
            post.scheduled_post_time = None
            post.save()

        return redirect('posts:my_posts')
    
    
class PinPostView(View):
    def post(self, request, *args, **kwargs):
        post_id = request.POST.get('post_id')
        user = request.user

        # 既にピン留めされているかどうかを確認します
        pinned_post = PinnedPost.objects.filter(user=user, post_id=post_id).first()
        if pinned_post:
            # 既にピン留めされている場合は削除
            pinned_post.delete()
            return JsonResponse({'success': True, 'action': 'unpinned', 'message': 'Post unpinned successfully.'})
        
        # ユーザーによってピン留めされている投稿が3つの場合、最も古いものを削除
        if PinnedPost.objects.filter(user=user).count() >= 3:
            oldest_pinned = PinnedPost.objects.filter(user=user).last()
            oldest_pinned.delete()

        # 新しい投稿をピン留め
        PinnedPost.objects.create(user=user, post_id=post_id)
        return JsonResponse({'success': True, 'action': 'pinned', 'message': 'Post pinned successfully.'})
    
    
class DeletePostView(View):
    def post(self, request, *args, **kwargs):
        post_id = request.POST.get('post_id')
        try:
            Posts.objects.filter(id=post_id).delete()
            return JsonResponse({"success": True})
        except:
            return JsonResponse({"success": False})
        
        


# 投稿処理
class BasePostCreateView(UserPassesTestMixin, LoginRequiredMixin, SuccessMessageMixin, CreateView):
    form_class = PostForm
    success_url = reverse_lazy('posts:postlist')
    success_message = "投稿が成功しました。"

    def form_valid(self, form):
        form.instance.poster = self.request.user
        form.instance.is_real = self.request.user.is_real  # Set the is_real value of the post based on the user's is_real value
        form.instance.posted_at = datetime.now()
        form.save()
        response = super().form_valid(form)
        
        # 新しい投稿が保存された後にキャッシュをクリア
        self.clear_poster_cache(self.request.user)
        
        return response

    def clear_poster_cache(self, poster):
        """投稿者のキャッシュをクリアするメソッド"""
        cache_key = f'filtered_posts_for_user_{poster.id}'
        cache.delete(cache_key)
        print(f"Cache for user {poster.id} has been cleared.")
    
    # Posterグループかどうか
    def test_func(self):
        return self.request.user.groups.filter(name='Poster').exists() and not self.request.user.is_advertiser

        

class MangaCreateView(BasePostCreateView):
    template_name = 'posts/create_manga.html'
    second_form_class = VisualForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if 'visual_form' not in context:
            context['visual_form'] = self.second_form_class(self.request.POST or None, self.request.FILES or None)
        return context

    def form_valid(self, form):
        form.instance.ismanga = True
        form.instance.scheduled_post_time = form.cleaned_data['scheduled_post_time']  # 予約投稿日時を確実に保存
        visual_form = self.second_form_class(self.request.POST, self.request.FILES)
        if not visual_form.is_valid() or 'visuals' not in self.request.FILES:
            # ビジュアルフォームが無効な場合、エラーメッセージを含めて再度フォームを表示
            return self.form_invalid(form)

        response = super().form_valid(form)
        image_files = self.request.FILES.getlist('visuals')

        # 画像の枚数に5を掛けて秒数を計算
        form.instance.content_length = len(image_files) * 5

        form.save()

        for visual_file in image_files:
            visual = Visuals(post=form.instance)
            visual.visual.save(visual_file.name, visual_file, save=True)
        return response

    

class VideoCreateView(BasePostCreateView):
    template_name = 'posts/create_video.html'
    video_form_class = VideoForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['video_form'] = self.video_form_class(self.request.POST or None, self.request.FILES or None)
        return context

    def get_temporary_file_path(self, uploaded_file):
        if hasattr(uploaded_file, 'temporary_file_path'):
            return uploaded_file.temporary_file_path()

        temp_file = NamedTemporaryFile(suffix=".mp4", delete=False)
        for chunk in uploaded_file.chunks():
            temp_file.write(chunk)
        temp_file.flush()  # Ensure all data is written to the file
        path = temp_file.name
        temp_file.close()
        return path

    def form_valid(self, form):
        video_form = self.get_context_data()['video_form']
        if video_form.is_valid():
            form.instance.poster = self.request.user
            form.instance.posted_at = datetime.now()
            form.instance.ismanga = False
            form.instance.scheduled_post_time = form.cleaned_data['scheduled_post_time']  # 予約投稿日時を確実に保存
            
            # ここでscheduled_post_timeの値を出力
            print("Scheduled post time:", form.cleaned_data['scheduled_post_time'])
            
            video_file = video_form.cleaned_data.get('video')
            
            print(type(video_file))  # video_file の型を表示
            print(video_file)  # video_file の内容を表示
            
            temp_file_path = self.get_temporary_file_path(video_file)
            try:
                # Use moviepy to get the duration (length) of the video
                with VideoFileClip(temp_file_path) as clip:
                    form.instance.content_length = int(clip.duration)  # Save the video's length in seconds
                
                form.save()
                video = Videos(post=form.instance)
                video.video.save(video_file.name, video_file, save=True)
                return super().form_valid(form)
            except Exception as e:
                form.add_error(None, str(e))
                return self.form_invalid(form)
            finally:
                # Remove the temporary file if it was created
                if os.path.exists(temp_file_path):
                    os.remove(temp_file_path)
        else:
            # ビデオフォームが無効な場合、エラーメッセージを含めて再度フォームを表示
            return self.form_invalid(form)

    def form_invalid(self, form):
        return self.render_to_response(self.get_context_data(form=form))


# いいね（非同期）
class FavoriteView(LoginRequiredMixin, View):

    @staticmethod
    def clear_favorite_cache_for_user(user):
        """指定されたユーザーのお気に入りキャッシュをクリアする"""
        cache_key = f'favorite_posts_for_user_{user.id}'
        cache.delete(cache_key)
        
    def post(self, request, *args, **kwargs):
        try:
            post_id = kwargs['pk']
            # 必要なフィールドだけを取得
            post = Posts.objects.only('id', 'favorite_count', 'views_count').get(pk=post_id)
            favorite, created = Favorites.objects.get_or_create(user=request.user, post=post)
            if not created:
                favorite.delete()
                
            # キャッシュをクリア
            self.clear_favorite_cache_for_user(request.user)

            post.favorite_count = post.favorite.count()
            post.update_favorite_rate()  # 更新
            post.save()
            data = {'favorite_count': post.favorite_count}
        except Exception as e:
            return JsonResponse({'error': str(e)})
        
        return JsonResponse(data)
    
    
class RecommendPostView(View):
    
    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def post(self, request, *args, **kwargs):
        post_id = request.POST.get('post_id')
        recommend = request.POST.get('recommend') == 'true'
        user = request.user
        
        # For debugging
        print(f"User: {user}")
        print(f"Post ID: {post_id}")
        print(f"Recommend: {recommend}")
        
        # レコメンドを追加するロジック
        if recommend:
            # すでに同じレコメンドが存在しないか確認
            existing_recommend = Recommends.objects.filter(user=user, post_id=post_id).first()
            
            # For debugging
            print(f"Existing Recommend (for adding): {existing_recommend}")
            
            if not existing_recommend:
                # 新しいレコメンドを作成
                new_recommend = Recommends.objects.create(user=user, post_id=post_id)
                print(f"Newly Created Recommend: {new_recommend}")
                return JsonResponse({'success': True, 'action': 'added'})

        # レコメンドを削除するロジック
        else:
            existing_recommend = Recommends.objects.filter(user=user, post_id=post_id).first()
            
            # For debugging
            print(f"Existing Recommend (for removing): {existing_recommend}")
            
            if existing_recommend:
                existing_recommend.delete()
                return JsonResponse({'success': True, 'action': 'removed'})

        return JsonResponse({'success': False, 'error': 'Action not taken'})
    
class GetRecommendUsers(View):

    def get(self, request, post_id, *args, **kwargs):
        # この投稿をレコメンドしているユーザーを取得
        recommended_users = Recommends.objects.filter(post_id=post_id).select_related('user').order_by('-created_at')

        # リクエストユーザーが各ユーザーをフォローしているかどうかをチェック
        following_users_ids = Follows.objects.filter(user=request.user).values_list('poster', flat=True)

        users_data = []
        for recommend in recommended_users:
            user = recommend.user
            users_data.append({
                "id": user.id,
                "username": user.username,
                "display_name": user.displayname,  # 追加
                "follow_count": user.follow_count,  # 追加
                "support_follow_count": user.support_follow_count,  # 追加
                "prf_img_url": user.prf_img.url,
                'is_followed': user.id in following_users_ids
            })

        return JsonResponse(users_data, safe=False)


# フォロー
class BaseFollowListView(BasePostListView):
    
    def get_followed_user_ids(self):
        cache_key = f'followed_user_ids_for_user_{self.request.user.id}'
        cached_followed_ids = cache.get(cache_key)

        if cached_followed_ids:
            print(f"Cache HIT for followed user IDs for user {self.request.user.id}")
            return cached_followed_ids

        print(f"Cache MISS for followed user IDs for user {self.request.user.id}")
        follows = Follows.objects.filter(user=self.request.user).select_related('poster')
        followed_user_ids = [follow.poster.id for follow in follows]
        cache.set(cache_key, followed_user_ids, 300)  # 5分間キャッシュ
        return followed_user_ids

    def get_queryset(self):
        cache_key = f'followed_posts_for_user_{self.request.user.id}'
        cached_posts_data = cache.get(cache_key)

        queryset = super().get_queryset()
        followed_user_ids = self.get_followed_user_ids()

        if cached_posts_data:
            print(f"Cache HIT for followed posts for user {self.request.user.id}")
            queryset = queryset.filter(id__in=cached_posts_data)
        else:
            print(f"Cache MISS for followed posts for user {self.request.user.id}")
            queryset = queryset.filter(poster__id__in=followed_user_ids)
            posts_data = list(queryset.values_list('id', flat=True))
            cache.set(cache_key, posts_data, 300)  # キャッシュに保存

        # キャッシュの有無に関わらず共通のフィルターやソートを適用する
        queryset = queryset.order_by('-posted_at')
        return queryset

        



class FollowPageView(BaseFollowListView):
    template_name = os.path.join('posts', 'follow_page.html')
    
    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset



class FollowListView(BaseFollowListView):
    template_name = os.path.join('posts', 'follow_list.html')
    
    def get_queryset(self):
        queryset = super().get_queryset()

        # URLから'post_id'パラメータを取得
        selected_post_id = int(self.request.GET.get('post_id', 0))
        followed_user_ids = self.get_followed_user_ids()

        # 選択した投稿のユーザーIDがフォローリストの中にあるか確認
        selected_post = queryset.filter(id=selected_post_id).first()

        # 選択した投稿以降の投稿のみを含むようにフィルタリング
        if selected_post and selected_post.poster.id in followed_user_ids:
            # querysetからPythonのリストを作成
            post_list = list(queryset)
            # 選択した投稿のインデックスを見つける
            selected_post_index = post_list.index(selected_post)
            # 選択した投稿に続く9件の投稿を取得
            post_list = post_list[selected_post_index:selected_post_index+8]
            queryset = post_list

        # 2つの広告ポストをランダムに取得
        ad_posts = self.get_random_ad_posts(self.request.user) 

        # 投稿リストに広告を組み込む
        return self.integrate_ads(queryset, iter(ad_posts))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context
   

class GetMoreFollowView(BaseFollowListView):

    def get_queryset(self):
        queryset = super().get_queryset()
        
        last_post_id = int(self.request.POST.get('last_post_id', 0))

        if last_post_id:
            # last_post_id以降の投稿を取得
            post_ids = list(queryset.values_list('id', flat=True))
            last_post_index = post_ids.index(last_post_id)
            next_post_ids = post_ids[last_post_index+1:last_post_index+9]

            queryset = queryset.filter(id__in=next_post_ids)
            queryset = sorted(queryset, key=lambda post: next_post_ids.index(post.id))
        else:
            queryset = queryset.filter(id__in=post_ids)

        # 現在のユーザーを取得
        user = self.request.user

        # 2つの広告ポストをランダムに取得
        ad_posts = self.get_random_ad_posts(user) 

        # 投稿リストに広告を組み込む
        return self.integrate_ads(queryset, iter(ad_posts))


   
   
class GetMorePreviousFollowView(BaseFollowListView):

    def get_queryset(self):
        queryset = super().get_queryset()        
        
        first_post_id = int(self.request.POST.get('first_post_id', 0))

        if first_post_id:
            post_ids = list(queryset.values_list('id', flat=True))
            first_post_index = post_ids.index(first_post_id)
            prev_post_ids = post_ids[max(0, first_post_index - 8):first_post_index]

            queryset = queryset.filter(id__in=prev_post_ids)
            queryset = sorted(queryset, key=lambda post: prev_post_ids.index(post.id))  # reverse to maintain the correct order
        else:
            queryset = queryset.filter(id__in=post_ids)

        # 現在のユーザーを取得
        user = self.request.user

        # 2つの広告ポストをランダムに取得
        ad_posts = self.get_random_ad_posts(user) 

        # 投稿リストに広告を組み込む
        return self.integrate_ads(queryset, iter(ad_posts))


    
class MyFollowListView(LoginRequiredMixin, ListView):    # フォローしたアカウントのリスト
    model = Follows
    context_object_name = 'follow_posters'
    template_name = os.path.join('posts', 'my_follow_list.html')
    
    def get_queryset(self):
        user = self.request.user
        follows = Follows.objects.filter(user=user)\
            .select_related('poster')\
            .only('poster__username', 'poster__prf_img', 'poster__displayname', 'poster__follow_count')\
            .order_by('-created_at')
        follow_posters = [f.poster for f in follows]
        # 各posterが現在のユーザーにフォローされているかどうかの情報を取得
        followed_by_user_ids = set([f.poster_id for f in follows])
        
        for poster in follow_posters:
            poster.is_followed_by_current_user = poster.id in followed_by_user_ids

        return follow_posters
    

class MyBlockListView(LoginRequiredMixin, ListView):    
    model = Blocks
    context_object_name = 'blocked_posters'
    template_name = os.path.join('posts', 'block_list.html')
    
    def get_queryset(self):
        user = self.request.user
        blocks = Blocks.objects.filter(user=user)\
            .select_related('poster')\
            .only('poster__username', 'poster__prf_img', 'poster__displayname')\
            .order_by('-created_at')
        blocked_posters = [b.poster for b in blocks]
        
        return blocked_posters


class FreezeNotificationRequest(View):
    template_name = 'posts/freeze_notification_request.html'

    def get(self, request):
        form = FreezeNotificationForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = FreezeNotificationForm(request.POST)
        if form.is_valid():
            freeze_notification = form.save(commit=False)
            freeze_notification.poster = request.user
            freeze_notification.save()
            # ここで適切なメッセージを表示したり、他のページにリダイレクトすることも可能です
            return redirect('/posts/freeze_notification_request_success/')

        return render(request, self.template_name, {'form': form})
    

class FreezeNotificationRequestSuccessView(TemplateView):
    template_name = 'posts/freeze_notification_request_success.html'
    

class FreezeListView(TemplateView):
    template_name = 'posts/freeze_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # 現在の日時を取得
        now = timezone.now()

        # 3ヶ月前の日時を計算
        three_months_ago = now - timedelta(days=90)

        # ユーザーがフォローしているposterのIDリストを取得
        followed_posters_ids = Follows.objects.filter(user=self.request.user).values_list('poster_id', flat=True)

        # その中で最近凍結され、かつ3ヶ月以内に作成されたポスターのIDリストを取得
        recently_frozen_posters_ids = FreezeNotification.objects.filter(
            approve=True, 
            poster_id__in=followed_posters_ids, 
            created_at__gte=three_months_ago   # 3ヶ月以内に作成されたものに絞り込み
        ).values_list('poster_id', flat=True)
        
        # IDリストを使用して、Usersモデルから該当するポスターの情報を取得
        recently_frozen_posters = Users.objects.filter(id__in=recently_frozen_posters_ids)
        
        context['freeze_posters'] = recently_frozen_posters

        return context
    
  
# マイアカウントページ
class MyAccountView(LoginRequiredMixin, TemplateView):
    template_name = os.path.join('posts', 'my_account.html')
    login_url = '/accounts/user_login/'  # ユーザがログインしていない場合にリダイレクトされるURL。これはプロジェクトの設定に基づいて変更してください。
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        user = self.request.user
        user_id = user.id

        # Poster グループに関する処理
        cache_key_poster = f"is_poster_{user_id}"
        is_poster = cache.get(cache_key_poster)
        if is_poster is None:
            is_poster = user.groups.filter(name='Poster').exists()
            cache.set(cache_key_poster, is_poster, 600)  # 600 seconds = 10 minutes
        context['is_poster'] = is_poster

        # TomsTalkに関する処理
        tomstalk_list = TomsTalk.objects.all().annotate(repeat=F('display_rate')).values('id', 'repeat')
        expanded_list = []
        for item in tomstalk_list:
            expanded_list.extend([item['id']] * item['repeat'])
        selected_id = random.choice(expanded_list) if expanded_list else None
        context['tomstalk'] = TomsTalk.objects.get(pk=selected_id) if selected_id else None
        
        context['current_dimension'] = user.dimension

        return context
    
class SettingView(TemplateView):
    template_name = os.path.join('posts', 'setting.html')
    

  
# 投稿ページ
class AddPostView(TemplateView):
  template_name = os.path.join('posts', 'add_post.html')

# 検索ページ
class SearchPageView(FormView):
    template_name = os.path.join('posts', 'searchpage.html')
    form_class = SearchForm

    def form_valid(self, form):
        query = form.cleaned_data.get('query')
        url = reverse('posts:hashtag', kwargs={'hashtag': query})
        return HttpResponseRedirect(url)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = self.form_class()
        return context


# おすすめハッシュタグを検索ページに表示
class HotHashtagView(TemplateView):
    template_name = os.path.join('posts', 'searchpage.html')

    def dispatch(self, request, *args, **kwargs):
        # セッションの dimension を 2.5 に設定
        request.session['selected_dimension'] = 2.5
        print("The selected_dimension has been set to 2.5")
        return super().dispatch(request, *args, **kwargs)


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # 最新のHotHashtagsのエントリを取得
        latest_hot_hashtags = HotHashtags.objects.latest('created_at')

        # HotHashtagsエントリからハッシュタグを取得してリスト化
        hashtags = [
            latest_hot_hashtags.hashtag1,
            latest_hot_hashtags.hashtag2,
            latest_hot_hashtags.hashtag3,
            latest_hot_hashtags.hashtag4,
        ]
        hashtags = [hashtag for hashtag in hashtags if hashtag]  # 空のハッシュタグを除去

        # ハッシュタグに基づいてクエリセットを構築
        queries = [Q(hashtag1=hashtag) | Q(hashtag2=hashtag) | Q(hashtag3=hashtag) for hashtag in hashtags]
        final_query = queries.pop() if queries else Q()  # クエリがない場合は空のQオブジェクトを使用
        for query in queries:
            final_query |= query

        posts = Posts.objects.only(
            'ismanga',
            'title',
            'hashtag1',
            'hashtag2',
            'hashtag3',
            'favorite_count',
            'support_favorite_count',
            'posted_at'
        ).filter(final_query, is_hidden=False).order_by('-posted_at').prefetch_related('visuals', 'videos')
        
        # is_mangaがFalseの場合に、関連するVideosのencoding_doneが全てTrueである投稿だけを含める
        videos = Videos.objects.filter(post=OuterRef('pk'), encoding_done=False)
        posts = posts.exclude(ismanga=False, videos__in=Subquery(videos.values('pk')))

        if self.request.user.is_authenticated:
            reports = Report.objects.filter(reporter=self.request.user, post=OuterRef('pk'))
            posts = posts.annotate(reported_by_user=Exists(reports))

        # ハッシュタグに基づいて投稿を整理
        # Use a dictionary to keep track of posts by their hashtags
        # ハッシュタグに基づいて投稿を整理
        posts_by_hashtag = defaultdict(list)
        for post in posts:
            post.visuals_list = post.visuals.all()
            post.videos_list = post.videos.all()
            for hashtag in hashtags:
                if hashtag in [post.hashtag1, post.hashtag2, post.hashtag3]:
                    posts_by_hashtag[hashtag].append(post)

        # Sorting and limiting the posts
        for hashtag, posts_list in posts_by_hashtag.items():
            posts_by_hashtag[hashtag] = sorted(posts_list, key=lambda x: x.posted_at, reverse=True)[:9]  # 最新の9個だけを取得
        
        # HotHashtagsの順番に基づいて、posts_by_hashtagを順序付け
        ordered_posts_by_hashtag = {hashtag: posts_by_hashtag.get(hashtag, []) for hashtag in hashtags}

        # WideAdsからすべての広告を取得
        wide_ads = list(WideAds.objects.all())

        # 広告が存在する場合のみランダムに選ぶ
        context['random_ad2'] = random.choice(wide_ads) if wide_ads else None
        context['random_ad4'] = random.choice(wide_ads) if wide_ads else None

        # おすすめユーザーの取得（RecommendedUserモデルに基づいて取得）
        recommended_user_entries = RecommendedUser.objects.select_related('user').only(
            'user__username',
            'user__prf_img',
            'user__displayname'
        ).all()
        recommended_users = [entry.user for entry in recommended_user_entries]
        context['recommended_users'] = recommended_users
            
        context['posts_by_hashtag'] = ordered_posts_by_hashtag
        context['form'] = SearchForm()
        return context





  
# 検索候補表示
class AutoCorrectView(View):
    @staticmethod
    def get(request):
        query = request.GET.get('search_text', '').strip()

        # Check the query length and limit it to avoid misuse.
        MAX_QUERY_LENGTH = 30
        if len(query) > MAX_QUERY_LENGTH:
            return JsonResponse({"error": "Invalid query"}, status=400)

        # Escape the query to prevent XSS and other potential attacks.
        query = escape(query)

        # クエリが空もしくは空白のみの場合、最新の1000件の検索履歴から検索回数の多いハッシュタグ上位5つを返す
        if not query or query.isspace():
            top_searched = list(SearchHistorys.objects.all()
                                .values('query')
                                .annotate(total_search_count=Sum('search_count')))

            # Pythonでソートとフィルタリング
            top_searched = sorted(top_searched, key=lambda x: (-x['total_search_count'], x['query']))[:5]

            data = [{"type": "hashtag", "value": record['query']} for record in top_searched]
            return JsonResponse(data, safe=False)
        
        hiragana_query = jaconv.kata2hira(jaconv.z2h(query.lower()))
        katakana_query = jaconv.hira2kata(hiragana_query)
        
        hashtag_queries = [hiragana_query, katakana_query]

        # クエリがアルファベットの場合の処理
        if query.isalpha():
            hashtag_queries.extend([query.upper(), query.lower()])

        q_objects = Q()
        for search_query in hashtag_queries:
            q_objects |= Q(hashtag1__istartswith=search_query) 
            q_objects |= Q(hashtag2__istartswith=search_query) 
            q_objects |= Q(hashtag3__istartswith=search_query)

        hashtag_results = Posts.objects.filter(q_objects).values_list('hashtag1', 'hashtag2', 'hashtag3')

        hashtags_set = set()
        for post in hashtag_results:
            for search_query in hashtag_queries:
                hashtags_set.update([hashtag for hashtag in post if hashtag and hashtag.startswith(search_query)])

        kanji_mappings = KanjiHiraganaSet.objects.all()
        for mapping in kanji_mappings:
            hiragana_queries = mapping.hiragana.split(',')
            if hiragana_query in hiragana_queries:
                hashtags_set.add(mapping.kanji)

        data = [{"type": "hashtag", "value": hashtag} for hashtag in list(hashtags_set)[:10]]

        return JsonResponse(data, safe=False)
  
# パートナー催促ページ
class BePartnerPageView(TemplateView):
    template_name = os.path.join('posts', 'be_partner.html')
    
class ViewDurationCountView(View):

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        print("Received POST data:", request.POST)
        post_id = request.POST.get('post_id')
        duration = request.POST.get('duration')

        try:
            post = Posts.objects.only('views_count', 'poster', 'favorite_count', 'content_length', 'avg_duration', 'poster__boost_type','support_favorite_count','support_views_count','qp').select_related('poster').get(id=post_id)
        except Posts.DoesNotExist:
            return JsonResponse({'error': 'Post not found'}, status=404)

        # 滞在時間の更新
        post.update_avg_duration(int(duration))

        # 視聴回数のカウントアップ
        post.views_count += 1

        # データベースからmaster_denominatorの値を取得
        support_rate = SupportRate.objects.get(name="master_denominator")
        denominator = int(support_rate.value)  # valueを整数に変換

        # qpの値を少数第2位まで切り捨て
        qp_rounded = math.floor(post.qp * 100) / 100

        # qp_roundedの1.34乗を計算
        numerator = qp_rounded ** 1.34

        # 0からdenominatorの範囲でランダムな浮動小数点数を生成して、それがnumeratorより小さいか確認の前に、
        # サポートいいねの数と普通のいいねの数を確認し、条件に応じてnumeratorを調整
        if post.support_favorite_count > 3 * post.favorite_count:  # ここで普通のいいねの数を確認する仮定
            numerator /= 5  # numeratorの値を5分の1にします

        if random.uniform(0, denominator) < numerator:
            post.support_favorite_count += 1
            
            # QPに基づいてsupport_follow_countの増加確率を計算
            if post.qp >= 3:
                chance = 2/3  # 三分の二 (2/3)
            elif post.qp <= 1:
                chance = 1/5  # 五分の一 (1/5)
            else:  # 1 < post.qp < 3 の場合
                linear_interpolation = 1/5 + (2/3 - 1/5) * ((3 - post.qp) / 2)
                chance = linear_interpolation

            # qpとchanceの値を表示
            print(f"QP: {post.qp}, Chance: {chance}")

            # 計算された確率でposterのsupport_follow_countを増加させる
            if random.random() < chance:
                post.poster.support_follow_count += 1

        # 見られるごとにsupport_views_countを増やす
        additional_views = (numerator / denominator) * 125 * (qp_rounded + 1) ** -1.322
        incremented_views = math.floor(additional_views * 10) / 10  # 少数第2位を切り捨てて、少数第1位を残す
        post.support_views_count += incremented_views

        post.update_favorite_rate()
        post.update_qp_if_necessary()

        # すべての更新をデータベースに反映
        Posts.objects.filter(id=post_id).update(
            views_count=post.views_count,
            favorite_count=post.favorite_count,
            content_length=post.content_length,
            avg_duration=post.avg_duration,
            favorite_rate=post.favorite_rate,
            qp=post.qp,
            support_favorite_count=post.support_favorite_count,
            support_views_count=post.support_views_count  # これも追加
        )

        # 投稿者のsupport_follow_countをデータベースに反映
        Users.objects.filter(id=post.poster.id).update(
            support_follow_count=post.poster.support_follow_count
        )

        user_id = request.session.get('_auth_user_id')
        ViewDurations.objects.create(
            user_id=user_id,
            post_id=post_id,
            duration=duration
        )

        return JsonResponse({'message': 'Successfully updated post interactions'})
    


class AdViewCountBase(View):
    model = None  # 具体的なモデルは具象ビュークラスで指定

    def post(self, request, *args, **kwargs):
        ad_id = kwargs.get('ad_id')

        try:
            ad = self.model.objects.get(id=ad_id)
        except self.model.DoesNotExist:
            return JsonResponse({'error': 'Ad not found'}, status=404)

        ad.views_count += 1
        ad.update_click_rate()  # 更新
        ad.save()

        return JsonResponse({'message': 'Successfully ad view count'})

class AdClickCountBase(View):
    model = None

    def post(self, request, *args, **kwargs):
        ad_id = kwargs.get('ad_id')

        try:
            ad = self.model.objects.get(id=ad_id)
        except self.model.DoesNotExist:
            return JsonResponse({'error': 'Ad not found'}, status=404)

        ad.click_count += 1
        ad.update_click_rate()  # 更新
        ad.save()

        return JsonResponse({'message': 'Successfully ad click count'})

class AdsViewCount(AdViewCountBase):
    model = Ads

class WideAdsViewCount(AdViewCountBase):
    model = WideAds

class AdsClickCount(AdClickCountBase):
    model = Ads

class WideAdsClickCount(AdClickCountBase):
    model = WideAds
    
    
class AddToCollectionView(View):
    
    @transaction.atomic
    def post(self, request, *args, **kwargs):
        print("AddToCollectionView post method called")  # Called at the start of the post method

        collection_id = request.POST.get('collection_id')
        post_id = request.POST.get('post_id')

        print(f"Received collection_id: {collection_id}, post_id: {post_id}")  # Log the received IDs

        # 既に追加されているかチェック
        if Collect.objects.filter(collection_id=collection_id, post_id=post_id).exists():
            print("Post already added to collection")  # Log if post is already added
            return JsonResponse({'message': 'Already added'}, status=400)

        # ここで追加
        try:
            Collect.objects.create(collection_id=collection_id, post_id=post_id)
            print("Post added to collection successfully")  # Log successful addition
            return JsonResponse({'message': 'Added successfully'})
        except Exception as e:
            print(f"Error while adding post to collection: {e}")  # Log any error during addition
            return JsonResponse({'message': 'Error occurred'}, status=500)


class RemoveFromCollectionView(View):

    def post(self, request, *args, **kwargs):
        collection_id = request.POST.get('collection_id')
        post_id = request.POST.get('post_id')
        
        # 該当する Collect オブジェクトをすべて取得
        collect_objs = Collect.objects.filter(collection_id=collection_id, post_id=post_id)
        
        # 該当するオブジェクトがある場合、すべて削除
        if collect_objs.exists():
            collect_objs.delete()

            # 関連するコレクションのキャッシュを削除
            cache_key = f'collection_posts_for_user_{request.user.id}_collection_{collection_id}'
            cache.delete(cache_key)

            return JsonResponse({"message": "Removed successfully"})
        else:
            return JsonResponse({"message": "Relation not found between collection and post"}, status=400)
        

@method_decorator(csrf_exempt, name='dispatch')
class CreateCollectionAndAddPost(View):
    
    def post(self, request):
        try:
            collection_name = request.POST.get('collectionName')
            post_id = request.POST.get('postId')

            # コレクションの作成
            new_collection = Collection(name=collection_name, user=request.user)
            new_collection.save()

            # 投稿を新しいコレクションに追加
            post_to_add = Posts.objects.get(id=post_id)
            # 中間モデルを使用して、コレクションと投稿の関連付けレコードを作成
            Collect.objects.create(collection=new_collection, post=post_to_add)

            # 関連するコレクションのキャッシュを削除
            cache_key = f'collection_posts_for_user_{request.user.id}_collection_{new_collection.id}'
            cache.delete(cache_key)

            return JsonResponse({
                "status": "success",
                "message": "コレクションを作成し、投稿を追加しました。",
                "collection_id": new_collection.id,
                "collectionName": collection_name
            })
        except Exception as e:
            return JsonResponse({"status": "error", "message": f"エラー: {str(e)}"})
        

class CollectionsForPostView(View):
    def get(self, request, *args, **kwargs):
        post_id = kwargs.get('post_id')
        collects_for_post = Collect.objects.filter(post_id=post_id)
        collection_ids = list(collects_for_post.values_list('collection_id', flat=True))
        
        print("Post ID:", post_id)
        print("Collection IDs for the Post:", collection_ids)

        return JsonResponse({'collection_ids': collection_ids})

# 報告処理
class SubmitReportView(View):
    @transaction.atomic
    def post(self, request):
        reporter = request.user
        post_id = request.POST.get('post_id')
        reason = request.POST.get('reason')

        # Check if reason is provided
        if not reason:
            response_data = {
                'message': '報告の理由を入力してください。',
                'error': True
            }
            return JsonResponse(response_data, status=400)

        post = get_object_or_404(Posts.objects.only('id', 'report_count'), id=post_id)

        # 同一ユーザーからの同一投稿に対する報告が存在する場合はエラーを返す
        if Report.objects.filter(reporter=reporter, post=post).exists():
            response_data = {
                'message': 'すでにこの投稿を報告しています。',
                'already_reported': True
            }
            return JsonResponse(response_data)

        # 報告を作成して保存
        report = Report(reporter=reporter, post=post, reason=reason)
        report.save()
        
        # 投稿の報告回数をインクリメント (データベースレベルでの更新)
        updated_report_count = F('report_count') + 1
        
        # 現在の報告回数が49であれば、次の報告で50になる
        if post.report_count == 49:
            Posts.objects.filter(id=post_id).update(
                report_count=updated_report_count,
                is_hidden=True
            )
        else:
            Posts.objects.filter(id=post_id).update(
                report_count=updated_report_count
            )

        # ユーザーの報告回数をインクリメント (データベースレベルでの更新)
        reporter.report_count = F('report_count') + 1
        reporter.save(update_fields=['report_count'])

        # 応答データを作成
        response_data = {
            'message': '報告が正常に送信されました。'
        }
        return JsonResponse(response_data)

    def get(self, request):
        return JsonResponse({'error': 'GETメソッドは許可されていません'})


class EmoteCountView(View):
    @transaction.atomic
    def post(self, request, *args, **kwargs):
        post_id = self.kwargs.get('post_id')
        emote_number = self.kwargs.get('emote_number')

        # Get click count from the client
        body = json.loads(request.body)
        click_count = body.get('clicks', 1)

        emote_field = f"emote{emote_number}_count"
        
        # Using F() expression to increment the count at the database level
        updated_rows = Posts.objects.filter(id=post_id).update(
            **{emote_field: F(emote_field) + click_count, 
               'emote_total_count': F('emote_total_count') + click_count}
        )

        # Check if post exists
        if updated_rows == 0:
            return JsonResponse({'success': False, 'error': 'Post not found'})

        # Re-fetch the post object to get the updated counts
        post = Posts.objects.only('id', f'emote{emote_number}_count', 'emote_total_count').get(id=post_id)

        # Using the actual values from the database after refresh
        new_count = getattr(post, emote_field)
        new_total_count = post.emote_total_count

        return JsonResponse({'success': True, 'new_count': new_count, 'new_total_count': new_total_count})


from .tasks import delayed_message, another_delayed_message

class ShowMessageView(TemplateView):
    template_name = 'posts/show_message.html'

    def post(self, request, *args, **kwargs):
        print("View: POST request received...")

        input_str = request.POST.get('input_str', '')
        task_name = request.POST.get('task_name', 'delayed_message')
        print(f"View: Task Name: {task_name}")
        
        if input_str:
            print(f"View: Input String: {input_str}")

        if task_name == "delayed_message":
            print("View: Adding delayed_message task to queue...")
            task_result = delayed_message.delay()
        elif task_name == "another_delayed_message":
            print("View: Adding another_delayed_message task to queue...")
            task_result = another_delayed_message.delay(input_str)
        else:
            raise ValueError(f"Invalid task name: {task_name}")

        print("View: Waiting for task result...")
        self.message = task_result.get()
        print(f"View: Received message: {self.message}")
        return self.get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        print("View: Getting context data...")
        context = super().get_context_data(**kwargs)
        context['message'] = getattr(self, 'message', None)
        return context
    
    
class TestStreamingView(TemplateView):
    template_name = 'posts/test_streaming.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        video = Videos.objects.get(id=472)

        # videoオブジェクトをコンテキストに追加
        context['video'] = video

        AWS_S3_CUSTOM_DOMAIN = 'd26kmcll34ldze.cloudfront.net'

        if video.hls_path:
            context['hls_url'] = f'https://{AWS_S3_CUSTOM_DOMAIN}/{video.hls_path}'
        if video.dash_path:
            context['dash_url'] = f'https://{AWS_S3_CUSTOM_DOMAIN}/{video.dash_path}'

        return context