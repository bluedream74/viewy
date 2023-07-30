from django.urls import path
from .views import (
 MangaCreateView, PostListView, VideoCreateView, FavoriteView, FavoritePostListView, PosterPageView, HashtagPostListView, HashtagPageView, FollowListView, BackView, PosterPostListView, MyAccountView,  DeletePostView, AddPostView, SearchPageView, HotHashtagView, SearchCustomView, FavoritePageView, BePartnerPageView, ViewCountView, SubmitReportView, MyPostView, AutoCorrectView, GetMorePostsView, GetMoreFavoriteView, GetMorePreviousFavoriteView, GetMorePosterPostsView, GetMorePreviousPosterPostsView, GetMoreHashtagView, GetMorePreviousHashtagView
)

app_name = 'posts'

urlpatterns = [
   path('manga_create/', MangaCreateView.as_view(), name='manga_create'),
   path('video_create/', VideoCreateView.as_view(), name='video_create'),
   path('postlist/', PostListView.as_view(), name='postlist'),
   path('get_more_posts/', GetMorePostsView.as_view(), name='get_more_posts'),
   path('favorite/<int:pk>/', FavoriteView.as_view(), name='favorite'),
   path('fovorite_page/', FavoritePageView.as_view(), name='favorite_page'),
   path('fovorite_list/', FavoritePostListView.as_view(), name='favorite_list'),
   path('get_more_favorite/',  GetMoreFavoriteView.as_view(), name='get_more_favorite'),
   path('get_more_previous_favorite/',  GetMorePreviousFavoriteView.as_view(), name='get_more_previous_favorite'),
   path('poster/<int:pk>/', PosterPageView.as_view(), name='poster_page'),
   path('hashtag/<str:hashtag>/', HashtagPageView.as_view(), name='hashtag'),
   path('hashtag_list/<str:hashtag>/', HashtagPostListView.as_view(), name='hashtag_list'),
   path('get_more_hashtag/', GetMoreHashtagView.as_view(), name='get_more_hashtag'),
   path('get_more_previous_hashtag/', GetMorePreviousHashtagView.as_view(), name='get_more_previous_hashtag'),
   path('follow_list/', FollowListView.as_view(), name='follow_list'),
   path('back/', BackView.as_view(), name='back'),
   path('poster_post_list/<int:pk>/', PosterPostListView.as_view(), name='poster_post_list'),
   path('get_more_poster_posts/',  GetMorePosterPostsView.as_view(), name='get_more_poster_posts'),
   path('get_more_previous_poster_posts/',  GetMorePreviousPosterPostsView.as_view(), name='get_more_previous_poster_posts'),
   # path('user_logout/', UserLogoutView.as_view(), name='user_logout'),
   path('my_account/', MyAccountView.as_view(), name='my_account'),   
   path('add_post/', AddPostView.as_view(), name='add_post'),
   path('my_account/', MyAccountView.as_view(), name='my_account'),   
   path('my_posts/', MyPostView.as_view(), name='my_posts'),   
   path('delete_post/', DeletePostView.as_view(), name='delete_post'),
   path('searchpage/', SearchPageView.as_view(), name='searchpage'),
   path('hothashtag/', HotHashtagView.as_view(), name='hothashtag'),
   path('searchcustom/', SearchCustomView.as_view(), name='searchcustom'),
   path('auto_correct/', AutoCorrectView.as_view(), name='auto_correct'),
   path('be_partner/', BePartnerPageView.as_view(), name='be_partner'),
   path('view_count/', ViewCountView.as_view(), name='view_count'),
   path('report/', SubmitReportView.as_view(), name='report'),
]
