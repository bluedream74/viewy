# Python standard library
from datetime import datetime
import os
import random

# Third-party Django
from django import forms
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.models import Group
from django.contrib.auth.decorators import login_required
from django.contrib.messages.views import SuccessMessageMixin
from django.core import serializers
from django.db.models import Case, Exists, OuterRef, Q, When
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
from accounts.models import Follows
from .forms import PostForm, SearchForm, VisualForm, VideoForm
from .models import Favorites, Posts, Report, Users, Videos, Visuals, Ads, WideAds, HotHashtags, KanjiHiraganaSet, RecommendedUser, ViewDurations

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

class BasePostListView(ListView):
    model = Posts
    template_name = 'posts/postlist.html'
   
    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.select_related('poster').prefetch_related('visuals', 'videos')
        if self.request.user.is_authenticated:
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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        posts = context['object_list']
        context['posts'] = posts
        return context



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



class PostListView(BasePostListView):

    def get_ad(self):
        return Ads.objects.order_by('?').first()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        if user.is_authenticated:
            posts = context['posts']

            # すべてのpost_idsおよびposter_idsを取得
            post_ids = [post.id for post in posts]
            poster_ids = [post.poster.id for post in posts]

            # すべての投稿のviewed_countを計算
            viewed_counts = ViewDurations.objects.filter(user=user, post_id__in=post_ids).values('post').annotate(post_count=Count('id')).values_list('post', 'post_count')
            viewed_count_dict = {item[0]: item[1] for item in viewed_counts}

            # viewed_count_dictをターミナルに表示
            print("viewed_count_dict:", viewed_count_dict)

            # 現在のユーザーがフォローしている投稿者のリストを取得
            followed_poster_ids = Follows.objects.filter(user_id=user.id, poster_id__in=poster_ids).values_list('poster_id', flat=True)
            followed_posters_set = set(followed_poster_ids)

            # RPに基づいて投稿をソート
            sorted_posts_by_rp = sorted(posts, key=lambda post: post.calculate_rp_for_user(user, followed_posters_set, viewed_count_dict.get(post.id, 0)), reverse=True)

            # 最初の7つを取得
            top_posts_by_rp = sorted_posts_by_rp[:7]

            # 新着順で上位100の投稿を取得
            top_100_new_posts = Posts.objects.select_related('poster').prefetch_related('visuals', 'videos').order_by('-posted_at')[:100]
            random_two_from_top_100 = sample(list(top_100_new_posts), 2)

            # これらのリストを結合して結果としての9つの投稿を取得
            final_posts = top_posts_by_rp + random_two_from_top_100

            context['posts'] = final_posts
        else:
            # 認証されていない場合、デフォルトのクエリセットを返す
            context['posts'] = super().get_queryset().filter(is_hidden=False)

        # 広告をコンテキストに追加
        context['ad'] = self.get_ad()
        return context


    
    
class GetMorePostsView(PostListView):

    def get(self, request, *args, **kwargs):
        # セッションIDとユーザー名をログに出力
        print(f"Session ID: {request.session.session_key}")
        print(f"User: {request.user}")
        print(request.user.is_authenticated)

        user = request.user

        # 基底クラスのget_querysetメソッドを使用して投稿を取得
        posts = super().get_queryset()
        
        if user.is_authenticated:
            # すべてのpost_idsおよびposter_idsを取得
            post_ids = [post.id for post in posts]
            poster_ids = [post.poster.id for post in posts]

            # すべての投稿のviewed_countを計算
            viewed_counts = ViewDurations.objects.filter(user=user, post_id__in=post_ids).values('post').annotate(post_count=Count('id')).values_list('post', 'post_count')
            viewed_count_dict = {item[0]: item[1] for item in viewed_counts}

            # viewed_count_dictをターミナルに表示
            print("viewed_count_dict:", viewed_count_dict)

            # 現在のユーザーがフォローしている投稿者のリストを取得
            followed_poster_ids = Follows.objects.filter(user_id=user.id, poster_id__in=poster_ids).values_list('poster_id', flat=True)
            followed_posters_set = set(followed_poster_ids)

            # RPに基づいて投稿をソート
            sorted_posts = sorted(posts, key=lambda post: post.calculate_rp_for_user(user, followed_posters_set, viewed_count_dict.get(post.id, 0)), reverse=True)
            posts = sorted_posts[:9]
        else:
            # 認証されていない場合、デフォルトのクエリセットを返す
            posts = posts.filter(is_hidden=False)

        # 各投稿のビジュアルとビデオを取得
        for post in posts:
            post.visuals_list = post.visuals.all()
            post.videos_list = post.videos.all()

        ad = self.get_ad()  # 広告を取得

        # 投稿をHTMLフラグメントとしてレンダリング
        for post in posts:
            visuals = post.visuals_list.all()  
            videos = post.videos_list.all()

        html = render_to_string('posts/get_more_posts.html', {'posts': posts, 'user': request.user, 'ad': ad}, request=request)
        
        # HTMLフラグメントをJSONとして返す
        return JsonResponse({'html': html}, content_type='application/json')
    

class FavoritePageView(BasePostListView):
    template_name = os.path.join('posts', 'favorite_page.html')
    
    def get_queryset(self):
        user = self.request.user
        user_favorite_posts = Favorites.objects.filter(user=user).order_by('-created_at')
        post_ids = [favorite.post_id for favorite in user_favorite_posts]
        queryset = super().get_queryset().filter(id__in=post_ids, is_hidden=False)
        # Preserving the order of favorites.
        queryset = sorted(queryset, key=lambda post: post_ids.index(post.id))
        return queryset


class FavoritePostListView(BasePostListView):
    template_name = os.path.join('posts', 'favorite_list.html')

    def get_queryset(self):
        user = self.request.user
        # URLから'post_id'パラメータを取得
        selected_post_id = int(self.request.GET.get('post_id', 0))

        # ユーザーがお気に入りに追加した全ての投稿を取得
        user_favorite_posts = Favorites.objects.filter(user=user).order_by('-created_at')
        post_ids = [favorite.post_id for favorite in user_favorite_posts]
        queryset = super().get_queryset().filter(id__in=post_ids, is_hidden=False)

        # 選択した投稿がリストの中にあるか確認
        if selected_post_id in post_ids:
            # 選択した投稿のインデックスを見つける
            selected_post_index = post_ids.index(selected_post_id)
            # 選択した投稿とそれに続く投稿のIDを取得
            selected_post_ids = post_ids[selected_post_index:selected_post_index+9]
            # querysetが選択した投稿とそれに続く投稿のみを含むようにフィルタリング
            queryset = [post for post in queryset if post.id in selected_post_ids]

        # querysetがselected_post_idsの順番と同じになるようにソート
        queryset = sorted(queryset, key=lambda post: selected_post_ids.index(post.id))

        return queryset

    def get_ad(self):
        # ランダムに1つの広告を取得
        return Ads.objects.order_by('?').first()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # contextに広告を追加
        context['ad'] = self.get_ad()
        return context
    
    

class GetMoreFavoriteView(BasePostListView):
    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get_queryset(self):
        last_post_id = int(self.request.POST.get('last_post_id', 0))

        user_favorite_posts = Favorites.objects.filter(user=self.request.user).order_by('-created_at')
        post_ids = list(user_favorite_posts.values_list('post_id', flat=True))

        if last_post_id:
            last_favorite_index = post_ids.index(last_post_id)
            next_post_ids = post_ids[last_favorite_index+1:last_favorite_index+10]  # ここを10から9に変更

            queryset = super().get_queryset().filter(id__in=next_post_ids)
            queryset = sorted(queryset, key=lambda post: next_post_ids.index(post.id))
        else:
            queryset = super().get_queryset().filter(id__in=post_ids)

        return queryset[:9]  # ここを追加して、最初の9つの投稿だけを返す

    def get_ad(self):
        # 広告を1つランダムに取得
        return Ads.objects.order_by('?').first()

    def post(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        more_posts = list(queryset)
        if more_posts:  # 追加した投稿が存在する場合だけ広告を取得する
            for post in more_posts:
                post.visuals_list = post.visuals.all()
                post.videos_list = post.videos.all()

            ad = self.get_ad()  # 広告を取得

            # HTMLの生成部分を更新し、広告も送信
            html = render_to_string('posts/get_more_posts.html', {'posts': more_posts, 'ad': ad}, request=request)
        else:
            html = ""

        return JsonResponse({'html': html})
    

class GetMorePreviousFavoriteView(BasePostListView):
    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get_queryset(self):
        first_post_id = int(self.request.POST.get('first_post_id', 0))

        user_favorite_posts = Favorites.objects.filter(user=self.request.user).order_by('-created_at')  # order by created_at (ascending)
        post_ids = list(user_favorite_posts.values_list('post_id', flat=True))

        if first_post_id:
            first_favorite_index = post_ids.index(first_post_id)
            prev_post_ids = post_ids[max(0, first_favorite_index - 10):first_favorite_index]  # get previous 10 posts

            queryset = super().get_queryset().filter(id__in=prev_post_ids)
            queryset = sorted(queryset, key=lambda post: prev_post_ids.index(post.id), reverse=True)  # reverse to maintain the correct order
        else:
            queryset = super().get_queryset().filter(id__in=post_ids)

        # convert queryset to list and then reverse it
        return list(reversed(queryset[:9]))  # return first 9 posts only in reversed order
    
    def get_ad(self):
        # 広告を1つランダムに取得
        return Ads.objects.order_by('?').first()
    
    def post(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        more_posts = list(queryset)
        if more_posts:  # 追加した投稿が存在する場合だけ広告を取得する
            for post in more_posts:
                post.visuals_list = post.visuals.all()
                post.videos_list = post.videos.all()

            ad = self.get_ad()  # 広告を取得

            # HTMLの生成部分を更新し、広告も送信
            html = render_to_string('posts/get_more_posts.html', {'posts': more_posts, 'ad': ad}, request=request)
        else:
            html = ""

        return JsonResponse({'html': html})

    

class PosterPageView(BasePostListView):
    template_name = os.path.join('posts', 'poster_page.html')
    
    def get_queryset(self):
        # まず、BasePostListViewのget_querysetメソッドを呼び出します
        queryset = super().get_queryset()
        self.poster = get_object_or_404(Users, username=self.kwargs['username'])
         # その後、PosterPageViewの特定のフィルタリングを適用します
        queryset = queryset.filter(poster=self.poster, is_hidden=False).order_by('-posted_at')
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['followers'] = self.poster.follow.all()
        # ユーザーがフォローしているかどうかの確認
        context['about_poster'] = self.poster
        return context



class PosterPostListView(BasePostListView):
    template_name = os.path.join('posts', 'poster_post_list.html')

    def get_queryset(self):
        # URLから'post_id'パラメータを取得
        selected_post_id = int(self.request.GET.get('post_id', 0))

        # ポスターが投稿した全ての投稿を取得
        self.poster = get_object_or_404(Users, username=self.kwargs['username'])
        poster_posts = Posts.objects.filter(poster=self.poster, is_hidden=False).order_by('-posted_at')
        post_ids = [post.id for post in poster_posts]
        queryset = super().get_queryset().filter(id__in=post_ids, is_hidden=False)

        # 選択した投稿がリストの中にあるか確認
        if selected_post_id in post_ids:
            # 選択した投稿のインデックスを見つける
            selected_post_index = post_ids.index(selected_post_id)
            # 選択した投稿とそれに続く投稿のIDを取得
            selected_post_ids = post_ids[selected_post_index:selected_post_index+9]
            # querysetが選択した投稿とそれに続く投稿のみを含むようにフィルタリング
            queryset = [post for post in queryset if post.id in selected_post_ids]

        # querysetがselected_post_idsの順番と同じになるようにソート
        queryset = sorted(queryset, key=lambda post: selected_post_ids.index(post.id))

        return queryset

    def get_ad(self):
        # ランダムに1つの広告を取得
        return Ads.objects.order_by('?').first()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # contextに広告を追加
        context['ad'] = self.get_ad()
        return context


class GetMorePosterPostsView(BasePostListView):
    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get_queryset(self):
        last_post_id = int(self.request.POST.get('last_post_id', 0))

        # Get the pk from POST data
        poster_pk = self.request.POST.get('pk')
        if not poster_pk:
            return Posts.objects.none()

        # posterを設定
        self.poster = get_object_or_404(Users, pk=poster_pk)


        poster_posts = Posts.objects.filter(poster=self.poster, is_hidden=False).order_by('-posted_at')
        post_ids = list(poster_posts.values_list('id', flat=True))


        if last_post_id:
            last_poster_index = post_ids.index(last_post_id)
            next_post_ids = post_ids[last_poster_index+1:last_poster_index+10]  # ここを10から9に変更

            queryset = super().get_queryset().filter(id__in=next_post_ids)
            queryset = sorted(queryset, key=lambda post: next_post_ids.index(post.id))
        else:
            queryset = super().get_queryset().filter(id__in=post_ids)

        return queryset[:9]  # ここを追加して、最初の9つの投稿だけを返す

    def get_ad(self):
        # 広告を1つランダムに取得
        return Ads.objects.order_by('?').first()

    def post(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        more_posts = list(queryset)
        if more_posts:  # 追加した投稿が存在する場合だけ広告を取得する
            for post in more_posts:
                post.visuals_list = post.visuals.all()
                post.videos_list = post.videos.all()

            ad = self.get_ad()  # 広告を取得

            # HTMLの生成部分を更新し、広告も送信
            html = render_to_string('posts/get_more_posts.html', {'posts': more_posts, 'ad': ad}, request=request)
        else:
            html = ""

        return JsonResponse({'html': html})
    
    
    
    
class GetMorePreviousPosterPostsView(BasePostListView):
    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        # 親クラスのdispatchメソッドを呼び出す
        return super().dispatch(*args, **kwargs)

    def get_queryset(self):
        # POSTデータから最初の投稿IDを取得
        first_post_id = int(self.request.POST.get('first_post_id', 0))

        # POSTデータからpkを取得
        poster_pk = self.request.POST.get('pk')
        if not poster_pk:
            return Posts.objects.none()  # pkが提供されていない場合、空のクエリセットを返す

        # ポスターを設定
        self.poster = get_object_or_404(Users, pk=poster_pk)

        # ポスターの投稿を取得し、投稿日時で並べ替える
        poster_posts = Posts.objects.filter(poster=self.poster, is_hidden=False).order_by('-posted_at')
        post_ids = list(poster_posts.values_list('id', flat=True))

        if first_post_id:
            # 最初の投稿IDのインデックスを取得
            first_post_index = post_ids.index(first_post_id)
            # 最初の投稿より前の10個の投稿IDを取得
            prev_post_ids = post_ids[max(0, first_post_index - 10):first_post_index] 

            # querysetを取得し、投稿IDがprev_post_idsに含まれるものだけをフィルタリング
            queryset = super().get_queryset().filter(id__in=prev_post_ids)
            # querysetをprev_post_idsの順に並べ替え、順序を逆にする
            queryset = sorted(queryset, key=lambda post: prev_post_ids.index(post.id))  
        else:
            # 最初の投稿IDが存在しない場合、全ての投稿を取得
            queryset = super().get_queryset().filter(id__in=post_ids)

        return queryset[:9]  # 最初の9個の投稿だけを返す

    def get_ad(self):
        # ランダムな広告を取得
        return Ads.objects.order_by('?').first()

    def post(self, request, *args, **kwargs):
        # クエリセットを取得
        queryset = self.get_queryset()
        more_posts = list(queryset)
        if more_posts:  # 追加の投稿が存在する場合のみ広告を取得
            for post in more_posts:
                post.visuals_list = post.visuals.all()
                post.videos_list = post.videos.all()

            ad = self.get_ad()  # 広告を取得

            # HTML生成部分を更新し、広告も送信
            html = render_to_string('posts/get_more_posts.html', {'posts': more_posts, 'ad': ad}, request=request)
        else:
            html = ""

        return JsonResponse({'html': html})
   
    
    

class HashtagPageView(BasePostListView):
    template_name = os.path.join('posts', 'hashtag_page.html')
    
    def get_queryset(self):
        # BasePostListViewのget_querysetを呼び出す
        queryset = super().get_queryset()
        hashtag = self.kwargs['hashtag']

        # 既存のquerysetに特定のフィルタリングを適用
        queryset = (queryset.filter(hashtag1=hashtag, is_hidden=False) | 
                    queryset.filter(hashtag2=hashtag, is_hidden=False) | 
                    queryset.filter(hashtag3=hashtag, is_hidden=False)).order_by('-posted_at')
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['hashtag'] = self.kwargs['hashtag']
        context['form'] = SearchForm()  # 検索フォームを追加
        return context
    
    


class HashtagPostListView(BasePostListView):
    template_name = os.path.join('posts', 'hashtag_list.html')
    
    def get_queryset(self):
        # URLから'post_id'パラメータを取得
        selected_post_id = int(self.request.GET.get('post_id', 0))

        # 指定したハッシュタグが含まれる全ての投稿を取得
        hashtag = self.kwargs['hashtag']
        hashtag_posts = (Posts.objects.filter(hashtag1=hashtag, is_hidden=False) | 
                         Posts.objects.filter(hashtag2=hashtag, is_hidden=False) | 
                         Posts.objects.filter(hashtag3=hashtag, is_hidden=False)).order_by('-posted_at')
        post_ids = [post.id for post in hashtag_posts]
        queryset = super().get_queryset().filter(id__in=post_ids, is_hidden=False)

        # 選択した投稿がリストの中にあるか確認
        if selected_post_id in post_ids:
            # 選択した投稿のインデックスを見つける
            selected_post_index = post_ids.index(selected_post_id)
            # 選択した投稿とそれに続く投稿のIDを取得
            selected_post_ids = post_ids[selected_post_index:selected_post_index+9]
            # querysetが選択した投稿とそれに続く投稿のみを含むようにフィルタリング
            queryset = [post for post in queryset if post.id in selected_post_ids]

        # querysetがselected_post_idsの順番と同じになるようにソート
        queryset = sorted(queryset, key=lambda post: selected_post_ids.index(post.id))

        return queryset

    def get_ad(self):
        # ランダムに1つの広告を取得
        return Ads.objects.order_by('?').first()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # contextに広告を追加
        context['ad'] = self.get_ad()
        
        # 隠しコンテナにハッシュタグの値を渡す
        context['hashtag'] = self.kwargs['hashtag']
        return context
    

class GetMoreHashtagView(BasePostListView):
    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get_queryset(self):
        last_post_id = int(self.request.POST.get('last_post_id', 0))
        hashtag = self.request.POST.get('hashtag')  # Get the hashtag from POST data

        if not hashtag:
            return Posts.objects.none()  # Return an empty queryset if no hashtag is provided

        # Get all posts with the provided hashtag, ordered by date
        hashtag_posts = (Posts.objects.filter(hashtag1=hashtag, is_hidden=False) | 
                         Posts.objects.filter(hashtag2=hashtag, is_hidden=False) |
                         Posts.objects.filter(hashtag3=hashtag, is_hidden=False)).order_by('-posted_at')
        
        post_ids = list(hashtag_posts.values_list('id', flat=True))

        if last_post_id:
            last_poster_index = post_ids.index(last_post_id)
            next_post_ids = post_ids[last_poster_index+1:last_poster_index+10]

            queryset = super().get_queryset().filter(id__in=next_post_ids)
            queryset = sorted(queryset, key=lambda post: next_post_ids.index(post.id))
        else:
            queryset = super().get_queryset().filter(id__in=post_ids)

        return queryset[:9]

    def get_ad(self):
        # 広告を1つランダムに取得
        return Ads.objects.order_by('?').first()

    def post(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        more_posts = list(queryset)
        if more_posts:  # 追加した投稿が存在する場合だけ広告を取得する
            for post in more_posts:
                post.visuals_list = post.visuals.all()
                post.videos_list = post.videos.all()

            ad = self.get_ad()  # 広告を取得

            # HTMLの生成部分を更新し、広告も送信
            html = render_to_string('posts/get_more_posts.html', {'posts': more_posts, 'ad': ad}, request=request)
        else:
            html = ""

        return JsonResponse({'html': html})



class GetMorePreviousHashtagView(BasePostListView):
    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get_queryset(self):
        first_post_id = int(self.request.POST.get('first_post_id', 0))
        hashtag = self.request.POST.get('hashtag')  # Get the hashtag from POST data

        if not hashtag:
            return Posts.objects.none()  # Return an empty queryset if no hashtag is provided

        # Get all posts with the provided hashtag, ordered by date
        hashtag_posts = (Posts.objects.filter(hashtag1=hashtag, is_hidden=False) | 
                         Posts.objects.filter(hashtag2=hashtag, is_hidden=False) |
                         Posts.objects.filter(hashtag3=hashtag, is_hidden=False)).order_by('-posted_at')
        
        post_ids = list(hashtag_posts.values_list('id', flat=True))

        if first_post_id:
            first_post_index = post_ids.index(first_post_id)
            prev_post_ids = post_ids[max(0, first_post_index - 10):first_post_index] 

            queryset = super().get_queryset().filter(id__in=prev_post_ids)
            queryset = sorted(queryset, key=lambda post: prev_post_ids.index(post.id))
        else:
            queryset = super().get_queryset().filter(id__in=post_ids)

        return queryset[:9]

    def get_ad(self):
        # 広告を1つランダムに取得
        return Ads.objects.order_by('?').first()

    def post(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        more_posts = list(queryset)
        if more_posts:  # 追加した投稿が存在する場合だけ広告を取得する
            for post in more_posts:
                post.visuals_list = post.visuals.all()
                post.videos_list = post.videos.all()

            ad = self.get_ad()  # 広告を取得

            # HTMLの生成部分を更新し、広告も送信
            html = render_to_string('posts/get_more_posts.html', {'posts': more_posts, 'ad': ad}, request=request)
        else:
            html = ""

        return JsonResponse({'html': html})
    

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
            post = get_object_or_404(Posts, pk=kwargs['pk'])
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
class FollowPageView(BasePostListView):
    template_name = os.path.join('posts', 'follow_page.html')
    
    def get_queryset(self):
        user = self.request.user
        # ユーザーがフォローしている全てのユーザーを取得
        follows = Follows.objects.filter(user=user).select_related('poster')
        followed_user_ids = [follow.poster.id for follow in follows]

        # フォローしているユーザーの投稿を投稿日時の降順で取得
        queryset = super().get_queryset().filter(poster__id__in=followed_user_ids, is_hidden=False)
        queryset = queryset.order_by('-posted_at')

        return queryset



class FollowListView(BasePostListView):
    template_name = os.path.join('posts', 'follow_list.html')
    
    def get_queryset(self):
        user = self.request.user
        # URLから'post_id'パラメータを取得
        selected_post_id = int(self.request.GET.get('post_id', 0))

        # ユーザーがフォローしている全てのユーザーの投稿を取得
        follows = Follows.objects.filter(user=user).select_related('poster')
        followed_user_ids = [follow.poster.id for follow in follows]
        queryset = super().get_queryset().filter(poster__id__in=followed_user_ids, is_hidden=False)

        # querysetを投稿日時の降順に並び替え
        queryset = queryset.order_by('-posted_at')

        # 選択した投稿のユーザーIDがフォローリストの中にあるか確認
        selected_post = queryset.filter(id=selected_post_id).first()

        # 選択した投稿以降の投稿のみを含むようにフィルタリング
        if selected_post and selected_post.poster.id in followed_user_ids:
            # querysetからPythonのリストを作成
            post_list = list(queryset)
            # 選択した投稿のインデックスを見つける
            selected_post_index = post_list.index(selected_post)
            # 選択した投稿に続く9件の投稿を取得
            post_list = post_list[selected_post_index:selected_post_index+9]
            queryset = post_list

        return queryset

    def get_ad(self):
        # ランダムに1つの広告を取得
        return Ads.objects.order_by('?').first()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # contextに広告を追加
        context['ad'] = self.get_ad()
        return context
   

class GetMoreFollowView(BasePostListView):
    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get_queryset(self):
        last_post_id = int(self.request.POST.get('last_post_id', 0))

        # ユーザーがフォローしている全てのユーザーの投稿を取得
        follows = Follows.objects.filter(user=self.request.user).select_related('poster')
        followed_user_ids = [follow.poster.id for follow in follows]

        # フォローしているユーザーの投稿を取得
        queryset = super().get_queryset().filter(poster__id__in=followed_user_ids, is_hidden=False)

        # 投稿日時の降順に並び替え
        queryset = queryset.order_by('-posted_at')

        if last_post_id:
            # last_post_id以降の投稿を取得
            post_ids = list(queryset.values_list('id', flat=True))
            last_post_index = post_ids.index(last_post_id)
            next_post_ids = post_ids[last_post_index+1:last_post_index+10]

            queryset = queryset.filter(id__in=next_post_ids)
            queryset = sorted(queryset, key=lambda post: next_post_ids.index(post.id))
        else:
            queryset = queryset.filter(id__in=post_ids)

        return queryset[:9]  # 最初の9つの投稿だけを返す

    def get_ad(self):
        # 広告を1つランダムに取得
        return Ads.objects.order_by('?').first()

    def post(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        more_posts = list(queryset)
        if more_posts:  # 追加した投稿が存在する場合だけ広告を取得する
            for post in more_posts:
                post.visuals_list = post.visuals.all()
                post.videos_list = post.videos.all()

            ad = self.get_ad()  # 広告を取得

            # HTMLの生成部分を更新し、広告も送信
            html = render_to_string('posts/get_more_posts.html', {'posts': more_posts, 'ad': ad}, request=request)
        else:
            html = ""

        return JsonResponse({'html': html})   
   
   
class GetMorePreviousFollowView(BasePostListView):
    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get_queryset(self):
        first_post_id = int(self.request.POST.get('first_post_id', 0))

        # ユーザーがフォローしている全てのユーザーの投稿を取得
        follows = Follows.objects.filter(user=self.request.user).select_related('poster')
        followed_user_ids = [follow.poster.id for follow in follows]

        # フォローしているユーザーの投稿を取得
        queryset = super().get_queryset().filter(poster__id__in=followed_user_ids, is_hidden=False)

        # 投稿日時の降順に並び替え
        queryset = queryset.order_by('-posted_at')

        if first_post_id:
            post_ids = list(queryset.values_list('id', flat=True))
            first_post_index = post_ids.index(first_post_id)
            prev_post_ids = post_ids[max(0, first_post_index - 10):first_post_index]  # get previous 10 posts

            queryset = queryset.filter(id__in=prev_post_ids)
            queryset = sorted(queryset, key=lambda post: prev_post_ids.index(post.id), reverse=True)  # reverse to maintain the correct order
        else:
            queryset = queryset.filter(id__in=post_ids)

        return list(reversed(queryset[:9]))  # return first 9 posts only in reversed order

    def get_ad(self):
        # 広告を1つランダムに取得
        return Ads.objects.order_by('?').first()

    def post(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        more_posts = list(queryset)
        if more_posts:  # 追加した投稿が存在する場合だけ広告を取得する
            for post in more_posts:
                post.visuals_list = post.visuals.all()
                post.videos_list = post.videos.all()

            ad = self.get_ad()  # 広告を取得

            # HTMLの生成部分を更新し、広告も送信
            html = render_to_string('posts/get_more_posts.html', {'posts': more_posts, 'ad': ad}, request=request)
        else:
            html = ""

        return JsonResponse({'html': html})


    
class MyFollowListView(LoginRequiredMixin, ListView):    # フォローしたアカウントのリスト
    model = Follows
    context_object_name = 'follow_posters'
    template_name = os.path.join('posts', 'my_follow_list.html')
    
    def get_queryset(self):
        user = self.request.user
        follows = Follows.objects.filter(user=user).select_related('poster').order_by('-created_at')
        follow_posters = [f.poster for f in follows]
        # 各posterが現在のユーザーにフォローされているかどうかの情報を取得
        followed_by_user_ids = Follows.objects.filter(user=user).values_list('poster_id', flat=True)
        
        for poster in follow_posters:
            poster.is_followed_by_current_user = poster.id in followed_by_user_ids

        return follow_posters
    
# # 戻るボタン（未完成）
# class BackView(RedirectView):
#     def get_redirect_url(self, *args, **kwargs):
#         return self.request.META.get('HTTP_REFERER') or reverse('posts:postlist')
    
    
  
# マイアカウントページ
class MyAccountView(TemplateView):
    template_name = os.path.join('posts', 'my_account.html')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # 一度だけユーザーオブジェクトにアクセスする
        user = self.request.user
        user_id = user.id

        # キャッシュから情報を取得
        cache_key = f"is_poster_{user_id}"
        is_poster = cache.get(cache_key)

        # キャッシュに情報がなければデータベースから取得
        if is_poster is None:
            is_poster = self.request.user.groups.filter(name='Poster').exists()
            # キャッシュに情報を保存 (この例では10分間キャッシュ)
            cache.set(cache_key, is_poster, 600)  # 600 seconds = 10 minutes

        context['is_poster'] = is_poster
        context['current_dimension'] = self.request.user.dimension
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


# おすすめハッシュタグを検索ページに表示（一般ユーザーはいきなりこっちに入る）
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

        posts = Posts.objects.filter(final_query, is_hidden=False).prefetch_related('visuals', 'videos')

        if self.request.user.is_authenticated:
            reports = Report.objects.filter(reporter=self.request.user, post=OuterRef('pk'))
            posts = posts.annotate(reported_by_user=Exists(reports))

        # ハッシュタグに基づいて投稿を整理
        posts_by_hashtag = defaultdict(list)
        for post in posts:
            post.visuals_list = post.visuals.all()
            post.videos_list = post.videos.all()
            for hashtag in hashtags:
                if hashtag in [post.hashtag1, post.hashtag2, post.hashtag3]:
                    posts_by_hashtag[hashtag].append(post)

        # 新しい投稿順にソート
        for hashtag, posts in posts_by_hashtag.items():
            sorted_posts = sorted(posts, key=lambda x: x.posted_at, reverse=True)
            posts_by_hashtag[hashtag] = sorted_posts[:9]  # 最新の9個だけを取得
        
        # HotHashtagsの順番に基づいて、posts_by_hashtagを順序付け
        ordered_posts_by_hashtag = {hashtag: posts_by_hashtag.get(hashtag, []) for hashtag in hashtags}

        # WideAdsからすべての広告を取得
        wide_ads = list(WideAds.objects.all())

        # 広告が存在する場合のみランダムに選ぶ
        context['random_ad2'] = random.choice(wide_ads) if wide_ads else None
        context['random_ad4'] = random.choice(wide_ads) if wide_ads else None

        # おすすめユーザーの取得（RecommendedUserモデルに基づいて取得）
        recommended_user_entries = RecommendedUser.objects.select_related('user').all()
        recommended_users = [entry.user for entry in recommended_user_entries]
        context['recommended_users'] = recommended_users
            
        context['posts_by_hashtag'] = ordered_posts_by_hashtag
        context['form'] = SearchForm()
        return context





  
# 検索候補表示
class AutoCorrectView(View):
    @staticmethod
    def get(request):
        query = request.GET.get('search_text', None)

        # クエリが空もしくは空白のみの場合、何も返さない
        if not query or query.isspace():
            return JsonResponse([], safe=False)
        
        hiragana_query = jaconv.kata2hira(jaconv.z2h(query.lower()))
        katakana_query = jaconv.hira2kata(hiragana_query)
        
        hashtag_queries = [hiragana_query, katakana_query]

        # クエリがアルファベットの場合の処理
        if query.isalpha():
            hashtag_queries.append(query.upper())
            hashtag_queries.append(query.lower())

        hashtags_set = set()

        for search_query in hashtag_queries:
            hashtag_results = Posts.objects.filter(
                Q(hashtag1__istartswith=search_query) |
                Q(hashtag2__istartswith=search_query) |
                Q(hashtag3__istartswith=search_query))
            hashtags_set.update([hashtag for post in hashtag_results for hashtag in [post.hashtag1, post.hashtag2, post.hashtag3] if hashtag.startswith(search_query)])

        # 特定のひらがなクエリで対応する漢字を追加
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
    def post(self, request):
        reporter = request.user
        post_id = request.POST.get('post_id')
        reason = request.POST.get('reason')

        post = get_object_or_404(Posts, id=post_id)

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
        
        # 投稿の報告回数をインクリメント
        post.increment_report_count()

        # ユーザーの報告回数をインクリメント
        reporter.increment_report_count()

        # 応答データを作成
        response_data = {
            'message': '報告が正常に送信されました。'
        }
        return JsonResponse(response_data)

    def get(self, request):
        return JsonResponse({'error': 'GETメソッドは許可されていません'})
