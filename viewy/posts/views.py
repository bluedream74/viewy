# Python standard library
from datetime import datetime
import os
import random

# Third-party Django
from django import forms
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.models import Group
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
from .models import Favorites, Posts, Report, Users, Videos, Visuals, Ads



class BasePostListView(ListView):
    model = Posts
    template_name = 'posts/postlist.html'
   
    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.prefetch_related('visuals', 'videos')
        if self.request.user.is_authenticated:
            reports = Report.objects.filter(reporter=self.request.user, post=OuterRef('pk'))
            queryset = queryset.annotate(reported_by_user=Exists(reports))
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        posts = self.get_queryset()
        for post in posts:
            post.visuals_list = post.visuals.all()
            post.videos_list = post.videos.all()
        context['posts'] = posts
        return context

class PostListView(BasePostListView):
    def get_queryset(self):
        posts = super().get_queryset().filter(is_hidden=False)
        post_ids = list(posts.values_list('id', flat=True))
        random_ids = random.sample(post_ids, min(len(post_ids), 9))  # ここを9に変更

        # ランダムな順序で投稿を取得するためのCase文を作成
        ordering = Case(*[When(id=id, then=pos) for pos, id in enumerate(random_ids)])
        return posts.filter(id__in=random_ids).order_by(ordering)

    def get_ad(self):
        # 広告を1つランダムに取得
        return Ads.objects.order_by('?').first()
        
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['ad'] = self.get_ad()
        return context
    
    
class GetMorePostsView(PostListView):
    def get(self, request, *args, **kwargs):
        # セッションIDとユーザー名をログに出力
        print(f"Session ID: {request.session.session_key}")
        print(f"User: {request.user}")
        print(request.user.is_authenticated)
        
        # 基底クラスのget_querysetメソッドを使用して、９個の投稿と１個の広告を取得
        queryset = super().get_queryset()
        for post in queryset:
            post.visuals_list = post.visuals.all()
            post.videos_list = post.videos.all()
        # 投稿をHTMLフラグメントとしてレンダリング
        # print(queryset)
        for post in queryset:
            visuals = post.visuals_list.all()  
            videos = post.videos_list.all()

        html = render_to_string('posts/get_more_posts.html', {'posts': queryset, 'user': request.user}, request=request)
        
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
        self.poster = get_object_or_404(Users, pk=self.kwargs['pk'])
        return Posts.objects.filter(poster=self.poster, is_hidden=False).order_by('-posted_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['about_poster'] = self.poster
        return context



class PosterPostListView(BasePostListView):
    template_name = os.path.join('posts', 'poster_post_list.html')

    def get_queryset(self):
        # URLから'post_id'パラメータを取得
        selected_post_id = int(self.request.GET.get('post_id', 0))

        # ポスターが投稿した全ての投稿を取得
        self.poster = get_object_or_404(Users, pk=self.kwargs['pk'])
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
            return Posts.objects.none()  # Return an empty queryset if no pk is provided

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
        hashtag = self.kwargs['hashtag']   # この一行が重要
        return (Posts.objects.filter(hashtag1=hashtag, is_hidden=False) | 
                Posts.objects.filter(hashtag2=hashtag, is_hidden=False) | 
                Posts.objects.filter(hashtag3=hashtag, is_hidden=False)).order_by('-posted_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['hashtag'] = self.kwargs['hashtag']
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
        context['visual_form'] = self.second_form_class()
        return context

    def form_valid(self, form):
        form.instance.ismanga = True
        response = super().form_valid(form)
        visual_form = self.second_form_class(self.request.POST, self.request.FILES)
        if visual_form.is_valid() and 'visuals' in self.request.FILES:
            for visual_file in self.request.FILES.getlist('visuals'):
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

    def form_valid(self, form):
        video_form = self.get_context_data()['video_form']
        if video_form.is_valid():
            form.instance.poster = self.request.user
            form.instance.posted_at = datetime.now()
            form.instance.ismanga = False
            form.save()
            video_file = video_form.cleaned_data.get('video')
            video = Videos(post=form.instance)
            video.video.save(video_file.name, video_file, save=True)
            return super().form_valid(form)
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
            post.save()
            data = {'favorite_count': post.favorite_count}
        except Exception as e:
            return JsonResponse({'error': str(e)})
        
        return JsonResponse(data)


# フォロー
class FollowListView(LoginRequiredMixin, ListView):
    model = Follows
    context_object_name = 'follow_posters'
    template_name = os.path.join('posts', 'follow_list.html')
    
    def get_queryset(self):
        user = self.request.user
        follows = Follows.objects.filter(user=user).select_related('poster')
        follow_posters = [f.poster for f in follows]
        return follow_posters
    
    
# 戻るボタン（未完成）
class BackView(RedirectView):
    def get_redirect_url(self, *args, **kwargs):
        return self.request.META.get('HTTP_REFERER') or reverse('posts:postlist')
    
    
# 視聴カウント
class ViewCountView(View):
    def post(self, request):
        if request.is_ajax():
            post_id = request.POST.get('post_id')

            # ポストが視聴履歴に含まれているかチェック
            user_profile = request.user
            post = Posts.objects.get(id=post_id)
            if post.viewed_by.filter(id=user_profile.id).exists():
                return JsonResponse({'exceeded_limit': False})

            # viewed_byフィールドにユーザーを追加
            post.viewed_by.add(user_profile)

            # view_post_countフィールドを1増やす
            user_profile.view_post_count += 1
            user_profile.save()

            # ユーザーが視聴した投稿の数を取得
            viewed_post_count = user_profile.view_post_count

            # 視聴した投稿の数が50を超えたかどうかを判定して返す
            if viewed_post_count > 50:
                return JsonResponse({'exceeded_limit': True})
            else:
                return JsonResponse({'exceeded_limit': False})
        
        return JsonResponse({'error': 'Invalid request'})
    
  
# マイアカウントページ
class MyAccountView(TemplateView):
    template_name = os.path.join('posts', 'my_account.html')
#   ポスターグループかどうか判断。継承して他のクラスにも適応できそう
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        is_poster = user.groups.filter(name='Poster').exists()
        context['is_poster'] = is_poster
        return context
  
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



  
# 検索候補表示
class AutoCorrectView(View):
    @staticmethod
    def get(request):
        query = request.GET.get('search_text', None)

        # Use set to keep hashtags unique
        hashtags_set = set()

        hashtag_results = Posts.objects.filter(Q(hashtag1__icontains=query) | Q(hashtag2__icontains=query) | Q(hashtag3__icontains=query))
        for post in hashtag_results:
            for hashtag in [post.hashtag1, post.hashtag2, post.hashtag3]:
                if hashtag and query.lower() in hashtag.lower():
                    hashtags_set.add(hashtag)

        # Prepare data for JsonResponse
        data = [{"type": "hashtag", "value": hashtag} for hashtag in hashtags_set]

        data = data[:10]  # Limit to first 10 results

        return JsonResponse(data, safe=False)

  
# パートナー催促ページ
class BePartnerPageView(TemplateView):
    template_name = os.path.join('posts', 'be_partner.html')


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
