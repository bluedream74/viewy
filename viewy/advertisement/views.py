import os, json
from moviepy.editor import VideoFileClip
from django.db.models import F
from django.views import View
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView
from .mixins import GroupOrSuperuserRequired
from django.db.models import Prefetch, Count
from django.urls import reverse, reverse_lazy
from django.views.generic.edit import FormView, CreateView
from django.http import HttpResponseRedirect, JsonResponse, HttpResponseForbidden
from django.contrib.messages.views import SuccessMessageMixin
from django.views.generic.base import ContextMixin
from tempfile import NamedTemporaryFile
from django.http import HttpResponseRedirect, Http404
from django.forms.models import model_to_dict
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.db.models.functions import Concat
from django.db.models import CharField

from posts.models import Posts, Users, Videos, Visuals
from .models import AdInfos, AndFeatures
from accounts.models import Features

from .forms import AdCampaignForm, AdInfoForm
from posts.forms import PostForm, VisualForm, VideoForm
from django.forms import formset_factory

from django.shortcuts import get_object_or_404, render, redirect
from .models import AdCampaigns

# is_advertiserかチェック
class AdvertiserCheckView(GroupOrSuperuserRequired, TemplateView):  pass

class AdCampaignsListView(AdvertiserCheckView, View):
    template_name = 'advertisement/ad_campaigns_list.html'

    def get(self, request, *args, **kwargs):
        # リクエストユーザーが作成したキャンペーンを取得
        campaigns = AdCampaigns.objects.filter(created_by=request.user)

        # 各キャンペーンの視聴回数の合計を更新
        for campaign in campaigns:
            campaign.update_total_views()

            # 期限チェック
            now = timezone.now()
            if now <= campaign.end_date:
                # キャンペーンに紐づくAdInfosを確認
                has_public_post = any(not ad_info.post.is_hidden for ad_info in campaign.ad_infos.all())
                
                # 少なくとも1つ以上の公開中のポストがあればキャンペーンも公開状態にする
                campaign.is_hidden = not has_public_post
                
            else:
                # 期限が切れている場合は必ず非公開にする
                campaign.is_hidden = True

            campaign.save()

        context = {
            'campaigns': campaigns
        }

        return render(request, self.template_name, context)


class AdCampaignDetailView(AdvertiserCheckView, View):
    template_name = 'advertisement/ad_campaign_detail.html'

    def get(self, request, campaign_id, *args, **kwargs):
        # リクエストユーザーが作成したキャンペーンを取得
        campaign = get_object_or_404(AdCampaigns, id=campaign_id, created_by=request.user)

        # そのキャンペーンに関連するAdInfosを取得
        ad_infos = (campaign.ad_infos.all()
                    .select_related('post')
                    .prefetch_related(Prefetch('post__visuals'))
                    .prefetch_related('post__videos'))
        for ad_info in ad_infos:
            ad_info.calculated_click_through_rate = ad_info.click_through_rate()
            
        # キャンペーンに関連する広告がない場合のメッセージ
        no_ad_message = None
        if not ad_infos.exists():
            no_ad_message = "このキャンペーンには関連する広告がありません。"

        # キャンペーンに関連するAndFeaturesを取得（is_allがTrueのものは除外）
        andfeatures = campaign.andfeatures.filter(is_all=False)

        context = {
            'ad_infos': ad_infos,
            'campaign': campaign,
            'no_ad_message': no_ad_message,
            'andfeatures': andfeatures,
        }
        return render(request, self.template_name, context)


class CampaignFormView(AdvertiserCheckView, View):
    template_name = 'advertisement/ad_campaign_create.html'
        
    def get_andfeature_by_orfeatures_name(self, name_ja):
        return AndFeatures.objects.filter(is_all=True, orfeatures__name_ja=name_ja).distinct().first()

    def get(self, request, *args, **kwargs):
        form = AdCampaignForm()
        sex = self.get_andfeature_by_orfeatures_name("男性")
        dimension = self.get_andfeature_by_orfeatures_name("３次元好き")
        print(sex)
        print(dimension)
        return render(request, self.template_name, {'form': form, 'sex': sex, 'dimension': dimension})

    def post(self, request, *args, **kwargs):
        form = AdCampaignForm(request.POST)
        if form.is_valid():
            adcampaign = form.save(commit=False)
            adcampaign.created_by = request.user
            adcampaign.save()
            
            sex = self.get_andfeature_by_orfeatures_name("男性")
            dimension = self.get_andfeature_by_orfeatures_name("３次元好き")

            selected_orfeatures_sex = request.POST.getlist('sex_orfeatures')
            selected_orfeatures_dimension = request.POST.getlist('dimension_orfeatures')

            all_sex_orfeatures_ids = [o.id for o in sex.orfeatures.all()]
            all_dimension_orfeatures_ids = [o.id for o in dimension.orfeatures.all()]

            def find_or_create_andfeature(selected_orfeatures, all_orfeatures_ids):
                if not selected_orfeatures:
                    return None
                if 'all' in selected_orfeatures:
                    return AndFeatures.objects.filter(is_all=True, orfeatures__in=all_orfeatures_ids).first()

                matching_andfeatures = AndFeatures.objects.annotate(
                    num_orfeatures=Count('orfeatures')
                ).filter(
                    orfeatures__id__in=selected_orfeatures,
                    num_orfeatures=len(selected_orfeatures)
                )

                if matching_andfeatures.exists():
                    return matching_andfeatures.first()
                else:
                    new_andfeature = AndFeatures.objects.create()
                    new_andfeature.orfeatures.set(selected_orfeatures)
                    return new_andfeature

            sex_andfeature = find_or_create_andfeature(selected_orfeatures_sex, all_sex_orfeatures_ids)
            if sex_andfeature:
                adcampaign.andfeatures.add(sex_andfeature)

            dimension_andfeature = find_or_create_andfeature(selected_orfeatures_dimension, all_dimension_orfeatures_ids)
            if dimension_andfeature:
                adcampaign.andfeatures.add(dimension_andfeature)

            return redirect(reverse('advertisement:ad_campaigns_list'))

        return render(request, self.template_name, {'form': form, 'sex': self.get_andfeature_by_orfeatures_name("男性"), 'dimension': self.get_andfeature_by_orfeatures_name("３次元好き")})


class BaseAdCreateView(AdvertiserCheckView, CreateView):
    form_class = AdInfoForm
    post_form_class = PostForm  # 新しく追加
    second_form_class = None  # VisualForm または VideoForm
    success_url = reverse_lazy('advertisement:ad_campaigns_list')
    success_message = "広告が成功しました。"

    def get_context_data(self, **kwargs):
        self.object = None
        context = super().get_context_data(**kwargs)
        if not context:
            context = {}

        if 'post_form' not in context:
            context['post_form'] = self.post_form_class(self.request.POST or None, self.request.FILES or None)
        if 'second_form' not in context and self.second_form_class:
            context['second_form'] = self.second_form_class(self.request.POST or None, self.request.FILES or None)
        context['user'] = self.request.user 
        return context

    def form_valid(self, form):
        # form.instance.poster = self.request.user
        context_data = self.get_context_data()
        post_form = context_data['post_form']
        
        if post_form.is_valid():
            # 二次元、三次元の処理やいつPostがうまれたか、などの情報はここで追加して保存する(BasePostCreateViewを参考に、、、)
            post = post_form.save(commit=False)  # まだデータベースに保存しない
            print("Postフォームのインスタンス内容：", post)
            post.poster = self.request.user  # ここでposterを設定します
            post.save() 
            print("保存されたPostのID：", post.id)
            form.instance.post = post # AdInfo の post フィールドに Post インスタンスを関連付け
            
            # 追加：ここではVideoやVisualの処理は行わない。サブクラスでの処理を想定
            response = super().form_valid(form)
            print("基本のform_valid処理完了。")

            return response
        else:
            print("Postフォームが無効です。")
            return self.form_invalid(form)

    def get_form_kwargs(self):
        kwargs = super(BaseAdCreateView, self).get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def test_func(self):
        return self.request.user.is_advertiser

    def handle_no_permission(self):
        return HttpResponseForbidden("広告投稿の権限がありません。")

    def form_invalid(self, form):
        context = self.get_context_data(form=form)
        return self.render_to_response(context)




class AdMangaCreateView(BaseAdCreateView):
    template_name = 'advertisement/ad_manga_create.html'
    second_form_class = VisualForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # second_formの代わりに、visual_formをcontextに追加する。
        if 'visual_form' not in context:
            context['visual_form'] = context.get('second_form')

        return context

    def form_valid(self, form):
        # まず、親クラスのform_validを実行して、AdInfosとPostが関連付けられ、両方がデータベースに保存されるようにします。
        response = super().form_valid(form)

        # post フィールドがセットされているか確認
        if not hasattr(form.instance, 'post'):
            # エラーメッセージを表示して処理を中止する。
            return self.form_invalid(form)

        # 次に、form.instance.postでPostオブジェクトを取得し、その属性を設定して保存します。
        post_instance = form.instance.post
        post_instance.ismanga = True

        # VisualFormのインスタンスを作成
        visual_form = self.get_context_data()['visual_form']

        # VisualFormのバリデーションを行う(画像サイズが５MBを超えている、または'visuals'がアップロードされていない場合)
        if not visual_form.is_valid() or 'visuals' not in self.request.FILES:
            # バリデーションに失敗した場合、エラーメッセージを含めて再度フォームを表示
            return self.form_invalid(form)

        # 画像の枚数が4ページ以下の場合は、content_lengthを20秒に設定
        image_files = self.request.FILES.getlist('visuals')
        if len(image_files) <= 4:
            post_instance.content_length = 20
        else:
            # 画像の枚数に5を掛けて秒数を計算
            post_instance.content_length = len(image_files) * 5

        post_instance.save()  # ismangaとcontent_lengthを保存します。
        
        # 最後に、画像ファイルを保存します。
        for visual_file in image_files:
            visual = Visuals(post=post_instance)  
            visual.visual.save(visual_file.name, visual_file, save=True)
            print("保存されたVisualのID：", visual.id)
        
        return response

class AdVideoCreateView(BaseAdCreateView):
    template_name = 'advertisement/ad_video_create.html'
    second_form_class = VideoForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # second_formの代わりに、video_formをcontextに追加する。
        if 'video_form' not in context:
            context['video_form'] = context.get('second_form')
        return context

    def get_temporary_file_path(self, uploaded_file):
        if hasattr(uploaded_file, 'temporary_file_path'):
            return uploaded_file.temporary_file_path()

        temp_file = NamedTemporaryFile(suffix=".mp4", delete=False)
        for chunk in uploaded_file.chunks():
            temp_file.write(chunk)
        temp_file.flush()
        path = temp_file.name
        temp_file.close()
        print("一時ファイルへの保存完了:", path)
        return path

    def form_valid(self, form):
        print("form_valid開始")
        # まず、親クラスのform_validを実行(Postオブジェクトの生成・保存)
        response = super().form_valid(form)

        # post フィールドがセットされているか確認
        if not hasattr(form.instance, 'post'):
            # エラーメッセージを表示して処理を中止する。
            return self.form_invalid(form)

        # 次に、form.instance.postでPostオブジェクトを取得し、その属性を設定して保存します。
        post_instance = form.instance.post
        post_instance.is_manga = False 
        print("Postインスタンス取得完了")

        # VideoFormのバリデーションとビデオ保存の処理
        video_form = self.get_context_data()['video_form']

        if video_form.is_valid(): #ここでVideoFormのバリデーション
            print("VideoFormのバリデーション成功")
            video_file = video_form.cleaned_data.get('video')
            print(type(video_file))  # video_file の型を表示
            print(video_file)  # video_file の内容を表示           
            temp_file_path = self.get_temporary_file_path(video_file)
            try:
                with VideoFileClip(temp_file_path) as clip:
                    post_instance.content_length = int(clip.duration)
                    post_instance.save()
                    print("Postインスタンスの内容更新完了")
                
                video = Videos(post=post_instance)#新しい Videos インスタンスの作成,保存
                video.video.save(video_file.name, video_file, save=True)#Videos モデルのsave メソッドが実行
                print("Videoの保存完了")
                
                return response
            except Exception as e:
                print(f"エラー発生：{str(e)}")
                form.add_error(None, str(e))
                return self.form_invalid(form)
            finally:
                if not hasattr(video_file, 'temporary_file_path'):
                    os.remove(temp_file_path)
        else:
            print("VideoFormのバリデーション失敗")
            return self.form_invalid(form)

    def form_invalid(self, form):
        print("form_invalid開始")
        return self.render_to_response(self.get_context_data(form=form))


class IsHiddenToggle(AdvertiserCheckView, View):
    def post(self, request, *args, **kwargs):
        body_unicode = request.body.decode('utf-8')
        body_data = json.loads(body_unicode)
        post_id = body_data.get('post_id')

        post = get_object_or_404(Posts, id=post_id)

        # AdInfosからAdCampaignを取得
        ad_info = get_object_or_404(AdInfos, post=post)
        campaign = ad_info.ad_campaign
        print(campaign.is_hidden)

        # キャンペーンが進行中かどうか確認
        if campaign.is_ongoing():
            # キャンペーンが進行中なら、キャンペーンのis_hidden状態に合わせる
            post.is_hidden = not post.is_hidden
        else:
            # キャンペーンが期限切れなら、必ず非公開にする
            post.is_hidden = True
        print(campaign.is_hidden)

        post.save(update_fields=['is_hidden'])

        return JsonResponse({'is_hidden': post.is_hidden})


class AdViewButton(AdvertiserCheckView, View):
    def get(self, request, post_id, *args, **kwargs):
        post = get_object_or_404(Posts, id=post_id)
        
        # モデルを辞書に変換（posterを除外）
        post_dict = model_to_dict(post, exclude=["visuals", "videos", "poster", "favorite"])
        
        # visuals と videos を手動でJSONシリアライズ可能な形に変換
        post_dict["visuals"] = [{"url": visual.visual.url} for visual in post.visuals.all()]
        post_dict["videos"] = [{"url": video.video.url, "thumbnail_url": video.thumbnail.url if video.thumbnail else None} for video in post.videos.all()]
        
        return JsonResponse({'post': post_dict})

class EditAdCampaignView(AdvertiserCheckView, View):
    template_name = 'advertisement/edit_ad_campaign.html'

    def get(self, request, campaign_id):
        campaign = get_object_or_404(AdCampaigns, id=campaign_id)
        form = AdCampaignForm(instance=campaign)
        # キャンペーンに関連するAndFeaturesを取得（is_allがTrueのものは除外）
        andfeatures = campaign.andfeatures.filter(is_all=False)
        start_date = campaign.start_date
        return render(request, self.template_name, {'form': form, 'andfeatures': andfeatures})

    def post(self, request, campaign_id):
        campaign = get_object_or_404(AdCampaigns, id=campaign_id)
        original_andfeatures = list(campaign.andfeatures.values_list('id', flat=True))
        form = AdCampaignForm(request.POST, instance=campaign)
        if form.is_valid():
            instance = form.save(commit=False)
            instance.andfeatures.set(original_andfeatures)
            instance.save()
            # 成功した場合のリダイレクト（例）
            return redirect(reverse('advertisement:ad_campaign_detail', kwargs={'campaign_id': campaign_id}))
        return render(request, self.template_name, {'form': form})

class AdCampaignStatusView(AdvertiserCheckView, View):
    
    def post(self, request, campaign_id):
        campaign = AdCampaigns.objects.filter(id=campaign_id).first()
        
        if not campaign:
            raise Http404("Campaign not found")
        print(campaign.is_hidden)

        # is_ongoing メソッドで現在進行中か確認
        if campaign.is_ongoing():
            # 進行中の場合、手動で状態をトグル可能
            campaign.is_hidden = not campaign.is_hidden
        else:
            # 期限切れの場合、必ず非公開（is_hidden=True）にする
            campaign.is_hidden = True

        campaign.save()
        print(campaign.is_hidden)

        # そのキャンペーンに紐づくすべてのAdInfosとPostsの状態を更新
        for ad_info in campaign.ad_infos.all():
            post = ad_info.post
            post.is_hidden = campaign.is_hidden
            post.save()
        
        return redirect(reverse_lazy('advertisement:ad_campaigns_list'))

class AdInfoDelete(AdvertiserCheckView, View):
    def post(self, request, ad_info_id):
        ad_info = get_object_or_404(AdInfos, id=ad_info_id)
        
        # 削除する前に、関連するAdCampaignのIDを取得
        campaign_id = ad_info.ad_campaign.id

        # AdInfoの削除 (関連するAdCampaignは削除しない)
        ad_info.delete()

        redirect_url = reverse('advertisement:ad_campaign_detail', kwargs={'campaign_id': campaign_id})
        return JsonResponse({'success': True, 'redirect_url': redirect_url})

class AdCampaignDelete(AdvertiserCheckView, View):
    def post(self, request, campaign_id):
        campaign = get_object_or_404(AdCampaigns, id=campaign_id)
        campaign.ad_infos.all().delete()
        campaign.delete()
        redirect_url = reverse('advertisement:ad_campaigns_list')  # 遷移先のURL
        return JsonResponse({'success': True, 'redirect_url': redirect_url})


class AdClickCountView(AdvertiserCheckView, View):

    @method_decorator(login_required)
    def post(self, request, post_id):
        try:
            ad_info = AdInfos.objects.get(post_id=post_id)
        except AdInfos.DoesNotExist:
            return JsonResponse({"status": "error", "message": "Advertisement not found"}, status=404)

        # F()式を使用して、clicks_countフィールドをデータベースレベルでインクリメント
        AdInfos.objects.filter(post_id=post_id).update(clicks_count=F('clicks_count') + 1)

        # もし、インクリメント後の値を取得する必要がある場合は、オブジェクトを再取得
        ad_info.refresh_from_db()
        print(ad_info.clicks_count)

        return JsonResponse({"status": "success"})