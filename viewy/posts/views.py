# Python standard library
from datetime import datetime
import os
import random
from random import sample  

# Third-party Django
from django import forms
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.models import Group
from django.contrib.auth.decorators import login_required
from django.contrib.messages.views import SuccessMessageMixin
from django.core import serializers
from django.db.models import Case, Exists, OuterRef, Q, When, Sum, IntegerField
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
from accounts.models import Follows, SearchHistorys, Surveys
from advertisement.models import AdInfos, AndFeatures, AdCampaigns
from .forms import PostForm, SearchForm, VisualForm, VideoForm
from .models import Favorites, Posts, Report, Users, Videos, Visuals, Ads, WideAds, HotHashtags, KanjiHiraganaSet, RecommendedUser, ViewDurations, TomsTalk

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

from django.db.models import Count
from django.db.models import Case, When, F, CharField, Value
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

    def get_advertiser_users(self):
        # キャッシュキーを設定
        cache_key = "advertiser_users"
        
        # キャッシュからデータを取得
        advertiser_users = cache.get(cache_key)
        
        # キャッシュにデータが存在しない場合
        if not advertiser_users:
            advertiser_users = list(Group.objects.get(name='Advertiser').user_set.all())
            
            # データをキャッシュに保存。
            cache.set(cache_key, advertiser_users, 3600)
        
        return advertiser_users
    
    
    # SpecialAdvertiserグループに所属しているかをチェック
    def is_user_special_advertiser(self, user):
        return user.groups.filter(name='SpecialAdvertiser').exists()
    
    # AffiliateAdvertiserグループに所属しているかをチェック
    def is_user_affiliate_advertiser(self, user):
        return user.groups.filter(name='AffiliateAdvertiser').exists()

    def get_advertiser_posts(self, user, count=1):
        cache_key = f"advertiser_posts_for_user_{user.id}"
        cached_posts = cache.get(cache_key)

        if cached_posts:
            print(f"Cache HIT for user {user.id}")  # キャッシュがヒットした場合にログを表示
            return cached_posts
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
        ).filter(matched_andfeatures=F('total_andfeatures'))

        
        # 最後に、この条件を満たす AdCampaigns を持つ Posts をフィルタリング
        # Directly filter Posts based on matching AdCampaigns
        ad_posts = (Posts.objects.filter(
            Q(adinfos__ad_campaign__in=matching_adcampaigns) ,
            poster__in=advertiser_users
        )
        .select_related('poster', 'adinfos__post', 'adinfos__ad_campaign')
        .prefetch_related(
            'visuals',
            'adinfos__ad_campaign__andfeatures',
            'adinfos__ad_campaign__andfeatures__orfeatures'
        ))
        # 適切な広告をランダムに取得
        posts = ad_posts
        # 以下のコードは以前のものを変更せずにそのまま使用します。
        ad_post_ids = [post.id for post in posts]
        favorited_ads = Favorites.objects.filter(user=user, post_id__in=ad_post_ids).values_list('post', flat=True)
        favorited_ads_set = set(favorited_ads)

        followed_ad_posters_ids = [post.poster.id for post in posts]
        followed_ad_posters_set = self.get_followed_posters_set(user, followed_ad_posters_ids)

        for post in posts:
            post.favorited_by_user = post.id in favorited_ads_set
            post.followed_by_user = post.poster.id in followed_ad_posters_set
            post.is_advertisement = True
            post.is_by_specialadvertiser = self.is_user_special_advertiser(post.poster)  # SpecialAdvertiserチェックを追加
            post.is_by_affiliateadvertiser = self.is_user_affiliate_advertiser(post.poster)  # AffiliateAdvertiserチェックを追加
        
        
        # 結果をキャッシュに保存
        cache.set(cache_key, posts, 3600)  # 1時間キャッシュする
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

        return queryset 
    
    def exclude_advertiser_posts(self, queryset):
        # Advertiser グループのIDを取得します
        advertiser_group = Group.objects.get(name='Advertiser')  # Groupの名前が 'Advertiser' であることを仮定します
        # Advertiser グループに属するユーザーのIDを取得します
        advertiser_user_ids = advertiser_group.user_set.values_list('id', flat=True)
        # これらのユーザーによって作成された投稿を除外します
        return queryset.exclude(poster_id__in=advertiser_user_ids)

        
    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = self.exclude_advertiser_posts(queryset)  # Advertiserの投稿を除外
        queryset = queryset.select_related('poster')
        queryset = self.annotate_user_related_info(queryset)
        queryset = queryset.prefetch_related('visuals', 'videos')
        return queryset


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['posts'] = context['object_list']
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
    
    def get_combined_posts(self, posts, user):
    # 1. QP順でソート
        sorted_posts_by_qp = sorted(posts, key=lambda post: post.qp, reverse=True)

        # 投稿IDのリストを取得
        post_ids = [post.id for post in sorted_posts_by_qp]

        # このIDリストを使って閲覧数の辞書を取得
        viewed_count_dict = self.get_viewed_count_dict(user, post_ids)

        # 2. RPを計算
        followed_posters_set = set(user.follow.all().values_list('id', flat=True))
        for post in sorted_posts_by_qp:
            viewed_count = viewed_count_dict.get(post.id, 0)  # 辞書から閲覧数を取得。デフォルト値は0。
            post.rp = post.calculate_rp_for_user(user, followed_posters_set, viewed_count)

        # 3. RP順で再ソート
        sorted_posts_by_rp = sorted(sorted_posts_by_qp, key=lambda post: post.rp, reverse=True)
        first_4_by_rp = sorted_posts_by_rp[:4]
        next_2_by_rp = sorted_posts_by_rp[4:6]


        # 全ての広告からランダムに2つを選びます。
        advertiser_posts = self.get_random_ad_posts(user)

        # 最新の100個の投稿を取得して、dimensionフィルターを適用
        latest_100_posts = Posts.objects.all().order_by('-id')
        latest_100_posts = self.filter_by_dimension(latest_100_posts)[:100]

        # 最新の100件のIDを取得
        post_ids = list(latest_100_posts.values_list('id', flat=True))

        # 100件未満の場合、可能な限りの投稿を選択します。
        num_posts_to_select = min(2, len(post_ids))
        selected_ids = sample(post_ids, num_posts_to_select)

        # 選択したIDを使って投稿を取得
        random_two_posts = (Posts.objects.filter(id__in=selected_ids)
                    .select_related('poster')   # 仮定: PostsモデルにposterというForeignKeyがある場合
                    .prefetch_related('visuals')  # 仮定: Postsモデルと関連付けられた他のモデルの名前
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
        # ユーザーが回答したすべてのアンケートを取得
        answered_surveys = Surveys.objects.filter(surveyresults__user=user)
        
        # 未回答のアンケートを取得
        unanswered_surveys = Surveys.objects.exclude(id__in=answered_surveys.values_list('id'))
        
        return unanswered_surveys.first()  

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        if user.is_authenticated:
            posts = context['posts']
            context['posts'] = self.get_combined_posts(posts, user)
            # 未回答のアンケートを調べて、それをコンテキストに追加
            unanswered_survey = self.check_unanswered_surveys(user)
            # 10分の1の確率でアンケートを表示
            if random.random() < 1:
                context['unanswered_survey'] = unanswered_survey
            else:
                context['unanswered_survey'] = None
        else:
            context['posts'] = self.get_queryset().filter(is_hidden=False)

        return context
       

    
    
class GetMorePostsView(PostListView):

    def get(self, request, *args, **kwargs):
        # object_listの設定
        self.object_list = self.get_queryset()
        
        # PostListViewの処理を実行
        context = self.get_context_data(**kwargs)
        posts = context['posts']

        # 投稿をHTMLフラグメントとしてレンダリング
        html = render_to_string('posts/get_more_posts.html', {'posts': posts, 'user': request.user}, request=request)
        
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
        # まず、いいね数の多い順に並べる
        posts = super().get_queryset().order_by('-favorite_count')
        # 6-10番目を取得
        posts = posts[6:11]  

        return posts

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
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
        queryset = super().get_queryset().filter(id__in=post_ids, is_hidden=False)
        queryset = sorted(queryset, key=lambda post: post_ids.index(post.id))
        return queryset


class FavoritePostListView(BaseFavoriteView):
    template_name = os.path.join('posts', 'favorite_list.html')

    def get_queryset(self):
        # URLから'post_id'パラメータを取得
        selected_post_id = int(self.request.GET.get('post_id', 0))

        # ユーザーがお気に入りに追加した全ての投稿を取得 (BaseFavoriteView から取得)
        post_ids = self.get_user_favorite_post_ids()

        queryset = super().get_queryset().filter(id__in=post_ids, is_hidden=False)
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
        posts = Posts.objects.filter(poster=self.poster, is_hidden=False).order_by('-posted_at')
        cache.set(cache_key, posts, 300)  # キャッシュの有効期間を300秒（5分）に設定
        return posts

    def integrate_ads_to_queryset(self, queryset):

        # 現在のユーザーを取得
        user = self.request.user
        # 2つの広告ポストをランダムに取得
        ad_posts = self.get_random_ad_posts(user) 

        # 投稿リストに広告を組み込む
        return self.integrate_ads(queryset, iter(ad_posts))
    

class PosterPageView(BasePosterView):
    template_name = os.path.join('posts', 'poster_page.html')

    def get_queryset(self):
        self.set_poster_from_username()
        queryset = super().get_queryset().filter(poster=self.poster, is_hidden=False).order_by('-posted_at')
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # テンプレートでのクエリを避けるためのリストを作成
        followers_ids = self.poster.follow.all().values_list('id', flat=True)
        context['is_user_following'] = self.request.user.id in followers_ids
        # ユーザーがフォローしているかどうかの確認
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
        queryset = super().get_queryset().filter(id__in=post_ids, is_hidden=False)

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

        if last_post_id:
            try:
                last_poster_index = post_ids.index(last_post_id)
            except ValueError:
                return Posts.objects.none()

            next_post_ids = post_ids[last_poster_index+1:last_poster_index+9]
            queryset = super().get_queryset().filter(id__in=next_post_ids)
            queryset = sorted(queryset, key=lambda post: next_post_ids.index(post.id))
        else:
            return Posts.objects.none()  # 分岐が不要である場合、何も返さない

        # Use the integrate method from the BasePosterView
        final_queryset = self.integrate_ads_to_queryset(queryset)

        return final_queryset
    
    
class GetMorePreviousPosterPostsView(BasePosterView):

    def get_queryset(self):
        # POSTデータから最初の投稿IDを取得
        first_post_id = int(self.request.POST.get('first_post_id', 0))

        # Use the method from the BasePosterView to set the poster
        self.set_poster_from_pk()

        if not self.poster:
            return Posts.objects.none()

        # Use the get_filtered_posts method from the BasePosterView
        poster_posts = self.get_filtered_posts()
        post_ids = list(poster_posts.values_list('id', flat=True))

        if first_post_id:
            # 最初の投稿IDのインデックスを取得
            try:
                first_post_index = post_ids.index(first_post_id)
            except ValueError:
                return Posts.objects.none()
            
            # 最初の投稿より前の10個の投稿IDを取得
            prev_post_ids = post_ids[max(0, first_post_index - 8):first_post_index] 

            # querysetを取得し、投稿IDがprev_post_idsに含まれるものだけをフィルタリング
            queryset = super().get_queryset().filter(id__in=prev_post_ids)
            # querysetをprev_post_idsの順に並べ替え、順序を逆にする
            queryset = sorted(queryset, key=lambda post: prev_post_ids.index(post.id))  
        else:
            # 最初の投稿IDが存在しない場合、全ての投稿を取得
            queryset = super().get_queryset().filter(id__in=post_ids)

        # Use the integrate method from the BasePosterView
        return self.integrate_ads_to_queryset(queryset)
 
 
   
class BaseHashtagListView(BasePostListView):
    def get(self, request, *args, **kwargs):
        self.order = request.GET.get('order', 'posted_at')
        return super().get(request, *args, **kwargs)

    def filter_by_hashtag(self, queryset, hashtag):
        return queryset.filter(
            Q(hashtag1=hashtag, is_hidden=False) |
            Q(hashtag2=hashtag, is_hidden=False) |
            Q(hashtag3=hashtag, is_hidden=False)
        )

    def filter_by_dimension(self, queryset):
        if self.request.user.is_authenticated:
            filter_condition = self.get_user_filter_condition()
            return queryset.filter(**filter_condition)
        return queryset

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
    

class HashtagPageView(BaseHashtagListView):
    template_name = os.path.join('posts', 'hashtag_page.html')

    def get_queryset(self):
        queryset = super().get_queryset()
        hashtag = self.kwargs['hashtag']
        
        queryset = self.filter_by_dimension(queryset)
        queryset = self.filter_by_hashtag(queryset, hashtag)
        queryset = self.order_queryset(queryset)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
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

        # User Dimension Filter
        queryset = self.filter_by_dimension(queryset)

        # Order the posts
        queryset = self.order_queryset(queryset)

        post_ids = [post.id for post in queryset]

        base_queryset = super().get_queryset().filter(id__in=post_ids, is_hidden=False)

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

        # Apply user-specific filter
        queryset = self.filter_by_dimension(queryset)

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

        # Apply user-specific filter
        queryset = self.filter_by_dimension(queryset)

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
        return super().get_queryset().filter(poster=user).order_by('-posted_at')
    
class HiddenPostView(BasePostListView):
    template_name = os.path.join('posts', 'hidden_post.html')

    def get_queryset(self):
        queryset = super().get_queryset()
        post_id = self.request.GET.get('post_id')
        if post_id:
            queryset = queryset.filter(id=post_id)
        return queryset

    
    
class DeletePostView(View):
    def post(self, request, *args, **kwargs):
        post_id = request.POST.get('post_id')
        Posts.objects.filter(id=post_id).delete()
        return redirect('posts:my_posts')


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
        return super().form_valid(form)
    
    # Posterグループかどうか
    def test_func(self):
        return self.request.user.groups.filter(name='Poster').exists()
    
    # Posterじゃなかったとき
    def handle_no_permission(self):
        return HttpResponseForbidden("You are not allowed to access this page.")
        

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
        visual_form = self.second_form_class(self.request.POST, self.request.FILES)
        if not visual_form.is_valid() or 'visuals' not in self.request.FILES:
            # ビジュアルフォームが無効な場合、エラーメッセージを含めて再度フォームを表示
            return self.form_invalid(form)

        response = super().form_valid(form)
        image_files = self.request.FILES.getlist('visuals')

        # 画像の枚数が4ページ以下の場合は、content_lengthを20秒に設定
        if len(image_files) <= 4:
            form.instance.content_length = 20
        else:
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
                if not hasattr(video_file, 'temporary_file_path'):
                    os.remove(temp_file_path)
        else:
            # ビデオフォームが無効な場合、エラーメッセージを含めて再度フォームを表示
            return self.form_invalid(form)

    def form_invalid(self, form):
        return self.render_to_response(self.get_context_data(form=form))


# いいね（非同期）
class FavoriteView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        try:
            post_id = kwargs['pk']
            # 必要なフィールドだけを取得
            post = Posts.objects.only('id', 'favorite_count', 'views_count').get(pk=post_id)
            favorite, created = Favorites.objects.get_or_create(user=request.user, post=post)
            if not created:
                favorite.delete()
            post.favorite_count = post.favorite.count()
            post.update_favorite_rate()  # 更新
            post.save()
            data = {'favorite_count': post.favorite_count}
        except Exception as e:
            return JsonResponse({'error': str(e)})
        
        return JsonResponse(data)


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
        cached_posts = cache.get(cache_key)

        if cached_posts:
            print(f"Cache HIT for followed posts for user {self.request.user.id}")
            return cached_posts

        print(f"Cache MISS for followed posts for user {self.request.user.id}")
        queryset = super().get_queryset()
        followed_user_ids = self.get_followed_user_ids()
        queryset = queryset.filter(poster__id__in=followed_user_ids, is_hidden=False).order_by('-posted_at')
        cache.set(cache_key, queryset, 300)  # 5分間キャッシュ
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
    
    
  
# マイアカウントページ
class MyAccountView(TemplateView):
    template_name = os.path.join('posts', 'my_account.html')

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
        
        # Advertiser グループに関する処理
        cache_key_advertiser = f"is_advertiser_{user_id}"
        is_advertiser = cache.get(cache_key_advertiser)
        if is_advertiser is None:
            is_advertiser = user.groups.filter(name='Advertiser').exists()
            cache.set(cache_key_advertiser, is_advertiser, 600)  # 600 seconds = 10 minutes
        context['is_advertiser'] = is_advertiser

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
            'posted_at'
        ).filter(final_query, is_hidden=False).order_by('-posted_at').prefetch_related('visuals', 'videos')

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
            recent_searched_queries = list(SearchHistorys.objects.order_by('-searched_at').values_list('query', flat=True)[:1000])
            top_searched = (SearchHistorys.objects.filter(query__in=recent_searched_queries)
                            .values('query')
                            .annotate(search_count=Sum('search_count'))
                            .order_by('-search_count', '-searched_at')[:5])
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
    

# 単純な視聴回数カウント
class IncrementViewCount(View):
    def post(self, request, *args, **kwargs):
        post_id = kwargs.get('post_id')

        try:
            post = Posts.objects.get(id=post_id)
        except Posts.DoesNotExist:
            return JsonResponse({'error': 'Post not found'}, status=404)

        post.views_count += 1
        post.update_favorite_rate()  # いいね率を更新
        post.update_qp_if_necessary()  # 必要に応じてQPを更新
        post.save()

        return JsonResponse({'message': 'Successfully incremented view count'})
    
    
# 視聴履歴、滞在時間のデータを追加するビュー    
class ViewDurationView(View):
    
    def post(self, request, *args, **kwargs):
        try:
            user = request.user
            if not user.is_authenticated:
                return JsonResponse({"message": "User not authenticated"}, status=403)

            post_id = request.POST.get('post_id')
            if not post_id:
                return JsonResponse({"message": "post_id not provided"}, status=400)

            duration = request.POST.get('duration')
            if not duration:
                return JsonResponse({"message": "duration not provided"}, status=400)
            
            post = Posts.objects.get(pk=post_id)
            
            content_view = ViewDurations.objects.create(
                user=user,
                post=post,
                duration=duration
            )

            return JsonResponse({"message": "Success"}, status=200)
        except Posts.DoesNotExist:
            return JsonResponse({"message": "Post with ID: " + post_id + " does not exist"}, status=400)
        except Exception as e:
            return JsonResponse({"message": f"Unexpected Error: {str(e)}"}, status=500)
    
    def get(self, request, *args, **kwargs):
        return JsonResponse({"message": "Method not allowed"}, status=405)
    


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


# 報告処理
class SubmitReportView(View):
    @transaction.atomic
    def post(self, request):
        reporter = request.user
        post_id = request.POST.get('post_id')
        reason = request.POST.get('reason')

        post = get_object_or_404(Posts.objects.only('id'), id=post_id)

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
        Posts.objects.filter(id=post_id).update(report_count=F('report_count') + 1)

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

        post = get_object_or_404(Posts, id=post_id)

        emote_field = f"emote{emote_number}_count"
        
        # 属性の存在確認
        if not hasattr(post, emote_field):
            return JsonResponse({'success': False, 'error': 'Invalid emote number'})

        # Using F() expression to increment the count at the database level
        setattr(post, emote_field, F(emote_field) + click_count)
        post.emote_total_count = F('emote_total_count') + click_count
        post.save(update_fields=[emote_field, 'emote_total_count'])

        # データベースの実際の値を使用して返す前に、オブジェクトをリフレッシュします
        post.refresh_from_db()
        
        # Using the actual values from the database after refresh
        new_count = getattr(post, emote_field)
        new_total_count = post.emote_total_count
        print(new_total_count)

        return JsonResponse({'success': True, 'new_count': new_count, 'new_total_count': new_total_count})