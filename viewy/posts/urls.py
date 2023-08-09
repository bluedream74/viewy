from django.urls import path
from .views import (
 MangaCreateView, PostListView, VideoCreateView, FavoriteView, FavoritePostListView, PosterPageView, HashtagPostListView, HashtagPageView, FollowListView, FollowPageView, GetMoreFollowView, GetMorePreviousFollowView, BackView, PosterPostListView, MyAccountView, SettingView, DeletePostView, AddPostView, SearchPageView, HotHashtagView, FavoritePageView, BePartnerPageView, ViewCountView, SubmitReportView, MyPostView, AutoCorrectView, GetMorePostsView, GetMoreFavoriteView, GetMorePreviousFavoriteView, GetMorePosterPostsView, GetMorePreviousPosterPostsView, GetMoreHashtagView, GetMorePreviousHashtagView, IncrementViewCount, AdsViewCount, WideAdsViewCount, AdsClickCount, WideAdsClickCount, MyFollowListView

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
   path('posts/follow_list/', FollowListView.as_view(), name='follow_list'),
   path('follow_page/', FollowPageView.as_view(), name='follow_page'),
   path('get_more_follow/',  GetMoreFollowView.as_view(), name='get_more_follow'),
   path('get_more_previous_follow/',  GetMorePreviousFollowView.as_view(), name='get_more_previous_follow'),
   path('back/', BackView.as_view(), name='back'),
   path('poster_post_list/<int:pk>/', PosterPostListView.as_view(), name='poster_post_list'),
   path('get_more_poster_posts/',  GetMorePosterPostsView.as_view(), name='get_more_poster_posts'),
   path('get_more_previous_poster_posts/',  GetMorePreviousPosterPostsView.as_view(), name='get_more_previous_poster_posts'), 
   path('add_post/', AddPostView.as_view(), name='add_post'),
   path('my_account/', MyAccountView.as_view(), name='my_account'),   
   path('my_posts/', MyPostView.as_view(), name='my_posts'), 
   path('my_follow_list/', MyFollowListView.as_view(), name='my_follow_list'),
   path('delete_post/', DeletePostView.as_view(), name='delete_post'),
   path('setting/', SettingView.as_view(), name='setting'),   
   path('searchpage/', SearchPageView.as_view(), name='searchpage'),
   path('hothashtag/', HotHashtagView.as_view(), name='hothashtag'),
   path('auto_correct/', AutoCorrectView.as_view(), name='auto_correct'),
   path('be_partner/', BePartnerPageView.as_view(), name='be_partner'),
   path('increment_view_count/<int:post_id>', IncrementViewCount.as_view(), name='increment_view_count'),
   path('ads_view_count/<int:ad_id>', AdsViewCount.as_view(), name='ads_view_count'),
   path('wideads_view_count/<int:ad_id>', WideAdsViewCount.as_view(), name='wideads_view_count'),
   path('ads_click_count/<int:ad_id>', AdsClickCount.as_view(), name='ads_click_count'),
   path('wideads_click_count/<int:ad_id>', WideAdsClickCount.as_view(), name='Wideads_click_count'),
   path('view_count/', ViewCountView.as_view(), name='view_count'),
   path('report/', SubmitReportView.as_view(), name='report'),
]
