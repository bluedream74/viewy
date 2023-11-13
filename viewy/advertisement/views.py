import os, json
from datetime import date, datetime
from decimal import Decimal, ROUND_UP
from django.utils import timezone
from datetime import timedelta
from moviepy.editor import VideoFileClip
from operator import itemgetter
from django.db import transaction
from django.db.models import F, Sum
from django import forms
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
from django.core.mail import send_mail

from posts.models import Posts, Users, Videos, Visuals
from .models import AdInfos, AndFeatures, MonthlyAdCost, MonthlyBilling, UserMonthlyBillingSummary
from accounts.models import Features
from django.views.generic import TemplateView
from django.template.loader import select_template

from .forms import AdCampaignForm, AdInfoForm, MonthSelectorForm
from posts.forms import PostForm, VisualForm, VideoForm
from accounts.forms import EditPrfForm
from django.forms import formset_factory

from django.shortcuts import get_object_or_404, render, redirect
from .models import AdCampaigns

# is_advertiserかチェック
class AdvertiserCheckView(GroupOrSuperuserRequired, TemplateView):  pass

class AdCampaignsListView(AdvertiserCheckView, TemplateView):
    template_name = 'advertisement/ad_campaigns_list.html'

    def get_queryset(self):
        # リクエストユーザーが作成したキャンペーンを取得
        return AdCampaigns.objects.filter(created_by=self.request.user).prefetch_related(
            Prefetch('ad_infos', queryset=AdInfos.objects.select_related('post'))
        ).annotate(
            adinfos_count=Count('ad_infos')
        ).order_by('-created_at')

    def get(self, request, *args, **kwargs):
        # リクエストユーザーが作成したキャンペーンを取得
        campaigns = AdCampaigns.objects.filter(created_by=request.user).prefetch_related(
            Prefetch('ad_infos', queryset=AdInfos.objects.select_related('post'))
        ).annotate(
            adinfos_count=Count('ad_infos')
        ).order_by('-created_at')

        today = timezone.now()

        with transaction.atomic():  
            campaigns_to_save = []
            ad_infos_to_save = []

            for campaign in campaigns:
                if campaign.status == 'running':
                    total_fee = 0 
                    total_views = 0
                    total_clicks = 0
                    
                    # Updating each AdInfo's fee
                    for ad_info in campaign.ad_infos.all(): 
                        ad_info.update_fee()
                        total_fee += ad_info.fee
                        total_views += ad_info.post.views_count   
                        total_clicks += ad_info.clicks_count
                        ad_infos_to_save.append(ad_info)

                    # Check if the fee or total_views_count has changed
                    if campaign.fee != total_fee or campaign.total_views_count != total_views or campaign.total_clicks_count != total_clicks:
                        campaign.fee = total_fee
                        campaign.total_views_count = total_views
                        campaign.total_clicks_count = total_clicks
                        campaigns_to_save.append(campaign)

            if campaigns_to_save:
                AdCampaigns.objects.bulk_update(campaigns_to_save, ['total_views_count', 'fee', 'total_clicks_count'])
            
            # Bulk update the ad_infos_to_save list if it is not empty
            if ad_infos_to_save:
                AdInfos.objects.bulk_update(ad_infos_to_save, ['fee'])

        ad_costs = self.get_ad_costs(request)
        context = {
            'campaigns': campaigns,
            **ad_costs,
        }

        return render(request, self.template_name, context)

    @staticmethod
    def get_ad_costs(request):
        today = timezone.now()
        year_month = date(today.year, today.month, 1)
        next_month_date = (today.replace(day=1) + timedelta(days=32)).replace(day=1)
        discount_rate = 0.9  # 10%の割引

        ad_costs = {
            'current_cpc': None,
            'current_cpm': None,
            'discounted_current_cpc': None,
            'discounted_current_cpm': None,
            'next_cpc': None,
            'next_cpm': None,
            'discounted_next_cpc': None,
            'discounted_next_cpm': None,
        }

        try:
            monthly_ad_cost = MonthlyAdCost.objects.get(year_month=year_month)
            ad_costs['current_cpc'] = monthly_ad_cost.cpc
            ad_costs['current_cpm'] = monthly_ad_cost.cpm

            # リクエストユーザーが特別広告主であるかどうかをチェック
            if request.user.is_specialadvertiser:
                ad_costs['discounted_current_cpc'] = monthly_ad_cost.cpc * discount_rate
                ad_costs['discounted_current_cpm'] = monthly_ad_cost.cpm * discount_rate
        except MonthlyAdCost.DoesNotExist:
            pass  # Values remain None

        try:
            next_monthly_ad_cost = MonthlyAdCost.objects.get(year_month=next_month_date)
            ad_costs['next_cpc'] = next_monthly_ad_cost.cpc
            ad_costs['next_cpm'] = next_monthly_ad_cost.cpm

            if request.user.is_specialadvertiser:
                ad_costs['discounted_next_cpc'] = next_monthly_ad_cost.cpc * discount_rate
                ad_costs['discounted_next_cpm'] = next_monthly_ad_cost.cpm * discount_rate
        except MonthlyAdCost.DoesNotExist:
            pass  # Values remain None

        return ad_costs


class FilteredAdCampaignsListView(AdCampaignsListView):

    def get_template_names(self):
        status = self.kwargs.get('status', None)
        templates = {
            'running': ['advertisement/running.html'],
            'pending': ['advertisement/pending.html'],
            'stopped': ['advertisement/stopped.html'],
            'expired': ['advertisement/expired.html'],
            'achieved': ['advertisement/achieved.html'],
            None: ['advertisement/ad_campaign_list.html']  # default
        }
        return templates.get(status)

    def get_queryset(self, status=None):
        # 親クラスのget_querysetメソッドを呼び出して、基本的なクエリセットを取得
        campaigns = super().get_queryset()

        if status:  # statusが指定されている場合のみフィルタリングを適用
            # ステータスに基づいてクエリセットをフィルタリング
            campaigns = campaigns.filter(status=status)
        
        return campaigns

    def get(self, request, *args, **kwargs):
        status = self.kwargs.get('status')  # URLからステータスを取得
        campaigns = self.get_queryset(status)  # クエリセットを更新し、campaignsに代入

        template_name = self.get_template_names()

        ad_costs = self.get_ad_costs(request)
        context = {
            'campaigns': campaigns,
            **ad_costs,
        }
        return render(request, template_name, context)

class CloseAdCampaignsListView(AdvertiserCheckView, View):
    template_name = 'advertisement/close.html' 

    def get_queryset(self, request):
        # ステータスがachieved、expired、またはstoppedのキャンペーンのみを取得
        return AdCampaigns.objects.filter(
            status__in=['achieved', 'expired', 'stopped'],
            created_by=request.user
        ).prefetch_related(
            Prefetch('ad_infos', queryset=AdInfos.objects.select_related('post'))
        ).annotate(
            adinfos_count=Count('ad_infos')  # ad_infosの数を注釈する
        ).order_by('-created_at')

    def get(self, request, *args, **kwargs):
        campaigns = self.get_queryset(request)  # 更新されたクエリセットを取得

        context = {
            'campaigns': campaigns,
            # ... (他のコンテキスト変数をここに追加)
        }

        return render(request, self.template_name, context)


class AdCampaignDetailView(AdvertiserCheckView, View):
    template_name = 'advertisement/ad_campaign_detail.html'

    def get(self, request, campaign_id, *args, **kwargs):
        # リクエストユーザーが作成したキャンペーンを取得
        campaign = get_object_or_404(AdCampaigns, id=campaign_id, created_by=request.user)

        # キャンペーンの開始日をチェックし、campaign.statusを設定
        today = timezone.now()
        if campaign.start_date > today:
            campaign.status = 'pending'

        # そのキャンペーンに関連するAdInfosを取得
        ad_infos = (campaign.ad_infos.all()
                    .select_related('post')
                    .prefetch_related(Prefetch('post__visuals'))
                    .prefetch_related('post__videos')
                    .order_by('-post__posted_at'))
        for ad_info in ad_infos:
            ad_info.calculated_click_through_rate = ad_info.click_through_rate()
            
        # キャンペーンに関連する広告がない場合のメッセージ
        no_ad_message = None
        if not ad_infos.exists():
            no_ad_message = "このキャンペーンには関連する広告がありません。"

        # キャンペーンに関連するAndFeaturesを取得（is_allがTrueのものは除外）
        andfeatures = campaign.andfeatures.filter(is_all=False)

        # MonthlyBillingオブジェクトを取得する
        monthly_billings = MonthlyBilling.objects.filter(ad_campaign_id=campaign_id).order_by('-month_year')

        context = {
            'ad_infos': ad_infos,
            'campaign': campaign,
            'monthly_billings': monthly_billings,
            'no_ad_message': no_ad_message,
            'andfeatures': andfeatures,
        }
        return render(request, self.template_name, context)

class BillingView(AdvertiserCheckView, TemplateView):
    template_name = 'advertisement/billings.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form = MonthSelectorForm(self.request.GET or None)

        now = timezone.now()
        if form.is_valid():
            month_year = form.cleaned_data['month_year']
            month_year = month_year.replace(day=1)
        else:
            # フォームが無効であれば、デフォルトで前月を表示
            first_day_of_last_month = now.replace(day=1) - timezone.timedelta(days=1)
            month_year = first_day_of_last_month.replace(day=1)
        
        campaigns = AdCampaigns.objects.filter(created_by=self.request.user)
        
        # 前月のデータのみをフィルタリング
        campaign_billings = [
            {
                'campaign_id': campaign.id,
                'campaign_title': campaign.title,
                'month_year': billing.month_year,
                'monthly_fee': billing.monthly_fee
            }
            for campaign in campaigns
            for billing in campaign.monthly_billings.filter(
                month_year=month_year
            )
        ]
        
        # 新しい順（降順）にソート
        campaign_billings_sorted = sorted(campaign_billings, key=itemgetter('month_year'), reverse=True)

        # ユーザーの月別の合計料金を取得
        user_monthly_billing_summary = UserMonthlyBillingSummary.objects.filter(
            user=self.request.user, 
            month_year=month_year
        ).first()
        
        # 合計料金と税込み合計料金をコンテキストに追加
        if user_monthly_billing_summary:
            context['total_fee'] = user_monthly_billing_summary.total_fee
            context['total_fee_with_tax'] = user_monthly_billing_summary.total_fee_with_tax
        else:
            context['total_fee'] = 0
            context['total_fee_with_tax'] = 0
            
        context['campaign_billings'] = campaign_billings_sorted
        context['form'] = form
        return context


class CampaignFormView(AdvertiserCheckView, View):
    template_name = 'advertisement/ad_campaign_create.html'
        
    def get_andfeature_by_orfeatures_name(self, name_ja):
        return AndFeatures.objects.filter(is_all=True, orfeatures__name_ja=name_ja).distinct().first()

    def get(self, request, *args, **kwargs):
        form = AdCampaignForm()
        sex = self.get_andfeature_by_orfeatures_name("男性")
        dimension = self.get_andfeature_by_orfeatures_name("三次元好き")

        ad_costs = AdCampaignsListView.get_ad_costs(request)

        return render(request, self.template_name, {
            'form': form,
            'sex': sex, 
            'dimension': dimension,
            **ad_costs,
            })

    def post(self, request, *args, **kwargs):
        form = AdCampaignForm(request.POST)
        # ad_cost_message の初期値を設定
        ad_cost_message = ""
        ad_costs = AdCampaignsListView.get_ad_costs(request)

        if form.is_valid():
            adcampaign = form.save(commit=False)

            # ここから見積金額の自動計算
            pricing_model = form.cleaned_data['pricing_model']

            # monthly_ad_cost の設定
            start_date = form.cleaned_data['start_date']
            target_month = start_date.replace(day=1)
            try:
                adcampaign.monthly_ad_cost = MonthlyAdCost.objects.get(year_month=target_month)
            except MonthlyAdCost.DoesNotExist:
                adcampaign.monthly_ad_cost = None
                # 日付をフォーマットしてメッセージを作成します。
                ad_cost_message = f"{target_month.strftime('%Y年%m月')} のCPC、CPMはまだ設定されていません"
            
            # adcampaign.monthly_ad_costがNoneの場合、エラーメッセージを表示してリターン
            if adcampaign.monthly_ad_cost is None:
                context = {
                    'form': form,
                    'sex': self.get_andfeature_by_orfeatures_name("男性"),
                    'dimension': self.get_andfeature_by_orfeatures_name("三次元好き"),
                    'ad_cost_message': ad_cost_message,
                    **ad_costs,
                }
                return render(request, self.template_name, context)

            # ステータスをpendingに設定
            adcampaign.status = 'pending'

            # 開始日が今日よりも前であれば、ステータスをrunningに設定する
            if start_date and start_date <= date.today():
                adcampaign.status = 'running'

            adcampaign.pricing_model = pricing_model

            # フォームから'end_date_option'の値を取得して適用
            end_date_option = form.cleaned_data.get('end_date_option')
            if end_date_option == 'none':
                adcampaign.end_date = None
            else:
                adcampaign.end_date = form.cleaned_data.get('end_date')

            # 初回限定キャンペーンの処理
            if 'first_time_campaign' in request.POST and not request.user.discount_applied:
                adcampaign.pricing_model = "CPM"
                adcampaign.target_views = 100000
                adcampaign.budget = 36000
                adcampaign.actual_cpc_or_cpm = Decimal(360)
                request.user.discount_applied = True
                adcampaign.title = f"{form.cleaned_data['title']} (初回限定価格)"
                request.user.save()

            else:
                # 通常の料金計算処理
                if pricing_model == "CPC":
                    adcampaign.target_clicks = form.cleaned_data.get('target_clicks')
                    adjusted_cpc = adcampaign.monthly_ad_cost.calculate_cpc(adcampaign.target_clicks, request.user)
                    adcampaign.budget = adcampaign.target_clicks * adjusted_cpc
                    adjusted_cpc = Decimal(adjusted_cpc).quantize(Decimal('0.1'), rounding=ROUND_UP)
                    adcampaign.actual_cpc_or_cpm = adjusted_cpc
                else:  # pricing_model == "CPM"
                    adcampaign.target_views = form.cleaned_data.get('target_views')
                    adjusted_cpm = adcampaign.monthly_ad_cost.calculate_cpm(adcampaign.target_views, request.user)
                    adcampaign.budget = adcampaign.target_views / 1000 * adjusted_cpm
                    adjusted_cpm = Decimal(adjusted_cpm).quantize(Decimal('0.1'), rounding=ROUND_UP)
                    adcampaign.actual_cpc_or_cpm = adjusted_cpm

            adcampaign.created_by = request.user
            adcampaign.save()
            
            sex = self.get_andfeature_by_orfeatures_name("男性")
            dimension = self.get_andfeature_by_orfeatures_name("三次元好き")

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
    
        context = {
            'form': form,
            'sex': self.get_andfeature_by_orfeatures_name("男性"),
            'dimension': self.get_andfeature_by_orfeatures_name("三次元好き"),
            'ad_cost_message': ad_cost_message,
            **ad_costs,
        }

        return render(request, self.template_name, context)


class BaseAdCreateView(AdvertiserCheckView, CreateView):
    form_class = AdInfoForm
    post_form_class = PostForm  # 新しく追加
    second_form_class = None  # VisualForm または VideoForm
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

            print("基本のform_valid処理完了。")

            # 成功した場合のリダイレクト先を設定する
            campaign_id = form.cleaned_data.get('ad_campaign').id  # 選択されたキャンペーンのIDを取得
            self.success_url = reverse('advertisement:ad_campaign_detail', args=[campaign_id]) 

            response = super().form_valid(form)

            return response
        else:
            print("Postフォームが無効です。")
            return self.form_invalid(form)

    def get_form_kwargs(self):
        kwargs = super(BaseAdCreateView, self).get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def send_ad_creation_notification(self, ad_instance):
        subject = '広告の審査をしてください'
        approval_url = 'https://www.viewy.net/management/approve_ad/'
        message = f'広告が作成されました。\n審査を行ってください。\n審査はこちら: {approval_url}'
        from_email = '広告審査 <adcreate@viewy.net>'
        recipient_list = ['support@viewy.net']
        try:
            result = send_mail(subject, message, from_email, recipient_list)
            if result:
                print("メールが正常に送信されました。")
            else:
                print("メール送信に失敗しました。")
        except Exception as e:
            print(f"メール送信中にエラーが発生しました: {e}")

    def test_func(self):
        return self.request.user.is_advertiser

    def handle_no_permission(self):
        return HttpResponseForbidden("広告投稿の権限がありません。")

    def form_invalid(self, form):
        context = self.get_context_data(form=form)
        return self.render_to_response(context)



class VisualFormValidationFailedException(Exception):
    """ VisualFormのバリデーション失敗のためのカスタム例外 """
    pass


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
        with transaction.atomic():
            # まず、親クラスのform_validを実行して、AdInfosとPostが関連付けられ、両方がデータベースに保存されるようにします。
            response = super().form_valid(form)

            # post フィールドがセットされているか確認
            if not hasattr(form.instance, 'post'):
                raise VisualFormValidationFailedException('Post field is not set')

            # 次に、form.instance.postでPostオブジェクトを取得し、その属性を設定して保存します。
            post_instance = form.instance.post
            post_instance.ismanga = True

            post_instance.is_hidden = True

            # VisualFormのインスタンスを作成
            visual_form = self.get_context_data()['visual_form']
            # VisualFormのバリデーションを行う(画像サイズが５MBを超えている、または'visuals'がアップロードされていない場合)
            if not visual_form.is_valid() or 'visuals' not in self.request.FILES:
                print('Visualのフォームバリに失敗')
                raise VisualFormValidationFailedException('画像ファイルを選択してください')

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
                # ファイルが画像でない場合は、例外を発生させます
                if not is_valid_image(visual_file):  # is_valid_image は適切な画像ファイルかどうかをチェックする関数
                    raise Exception('Not an image!!')
                visual = Visuals(post=post_instance)  
                visual.visual.save(visual_file.name, visual_file, save=True)
                print("保存されたVisualのID：", visual.id)

            # 全てのバリデーションと処理が成功した後にメール送信
            if form.is_valid():
                self.send_ad_creation_notification(form.instance)
        
        return response

    def post(self, request, *args, **kwargs):
        try:
            return super().post(request, *args, **kwargs)
        except VisualFormValidationFailedException as e:
            form = self.get_form()
            if hasattr(form.instance, 'post'):
                form.instance.post.delete()
            
            form.add_error(None, str(e))
            return self.form_invalid(form)

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
        # まず、親クラスのform_validを実行(Postオブジェクトの生成・保存)
        response = super().form_valid(form)

        # post フィールドがセットされているか確認
        if not hasattr(form.instance, 'post'):
            # エラーメッセージを表示して処理を中止する。
            return self.form_invalid(form)

        # 次に、form.instance.postでPostオブジェクトを取得し、その属性を設定して保存します。
        post_instance = form.instance.post
        post_instance.is_manga = False 
        post_instance.is_hidden = True

        # VideoFormのバリデーションとビデオ保存の処理
        video_form = self.get_context_data()['video_form']

        if video_form.is_valid(): #ここでVideoFormのバリデーション
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
                # ビデオ保存後、全てのバリデーションと処理が成功した場合にメール送信
                self.send_ad_creation_notification(form.instance)
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

        # ポストの表示状態をトグル
        post.is_hidden = not post.is_hidden

        post.save(update_fields=['is_hidden'])

        # キャンペーンの広告がすべて非表示か確認
        ads_in_campaign = AdInfos.objects.filter(ad_campaign=campaign)
        if all(ad.post.is_hidden for ad in ads_in_campaign):
            campaign.is_hidden = True
            campaign.status = 'stopped'  # ステータスをストップに
            campaign.end_date = timezone.now()  # 終了日を現在の日付に設定

            # 合計視聴回数と合計クリック数を計算
            total_views = sum(ad_info.post.views_count for ad_info in campaign.ad_infos.all())
            campaign.total_views_count = total_views

            total_clicks = AdInfos.objects.filter(ad_campaign=campaign).aggregate(total_clicks=Sum('clicks_count'))['total_clicks']
            campaign.total_clicks_count = total_clicks

            campaign.recalculate_campaign(request.user) # 料金を再計算し保存
        else:
            campaign.is_hidden = False
            campaign.status = 'running'  # ステータスを公開中に

        campaign.save()

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
        pricing_model = campaign.pricing_model
        # 'no_end_date' チェックボックスの状態を判定
        no_end_date_checked = 'checked' if campaign.end_date is None else ''

        actual_cpc_or_cpm_value = campaign.actual_cpc_or_cpm or 0
        total_views_count = campaign.total_views_count
        total_clicks_count = campaign.total_clicks_count
        status = campaign.status
        
        return render(request, self.template_name, {
            'form': form,
            'andfeatures': andfeatures,
            'pricing_model': pricing_model,
            'no_end_date_checked': no_end_date_checked,
            'actual_cpc_or_cpm': actual_cpc_or_cpm_value,
            'total_views_count': total_views_count,
            'total_clicks_count': total_clicks_count,
            'status': status
        })

    def post(self, request, campaign_id):
        campaign = get_object_or_404(AdCampaigns, id=campaign_id)
        original_andfeatures = list(campaign.andfeatures.values_list('id', flat=True))
        form = AdCampaignForm(request.POST, instance=campaign)
        if form.is_valid():
            adcampaign = form.save(commit=False)
            adcampaign.andfeatures.set(original_andfeatures)

            # 'no_end_date' チェックボックスの処理
            if 'no_end_date' in request.POST:
                adcampaign.end_date = None

            # 'end_date' の処理
            elif 'end_date' in request.POST and request.POST['end_date']:
                adcampaign.end_date = form.cleaned_data['end_date']

            # CPC または CPM の計算と保存
            if adcampaign.pricing_model == "CPC":
                adcampaign.target_clicks = form.cleaned_data.get('target_clicks')
                # target_clicks と actual_cpc_or_cpm を Decimal に変換
                target_clicks_decimal = Decimal(adcampaign.target_clicks)
                actual_cpc_or_cpm_decimal = Decimal(adcampaign.actual_cpc_or_cpm)
                # 計算を実行
                adcampaign.budget = target_clicks_decimal * actual_cpc_or_cpm_decimal
            else:
                adcampaign.target_views = form.cleaned_data.get('target_views')
                target_views_decimal = Decimal(adcampaign.target_views) / Decimal(1000)
                actual_cpc_or_cpm_decimal = Decimal(adcampaign.actual_cpc_or_cpm)
                # 計算を実行
                adcampaign.budget = target_views_decimal * actual_cpc_or_cpm_decimal

            adcampaign.save()
            # 成功した場合のリダイレクト（例）
            return redirect(reverse('advertisement:ad_campaign_detail', kwargs={'campaign_id': campaign_id}))
        else:
            # フォームにエラーがある場合、エラー情報をテンプレートに渡す
            print("Form errors:", form.errors)
            andfeatures = campaign.andfeatures.filter(is_all=False)
            pricing_model = campaign.pricing_model
            # 'no_end_date' チェックボックスの状態を判定
            no_end_date_checked = 'checked' if campaign.end_date is None else ''

            actual_cpc_or_cpm_value = campaign.actual_cpc_or_cpm or 0
            total_views_count = campaign.total_views_count
            total_clicks_count = campaign.total_clicks_count

            return render(request, self.template_name, {
                'form': form,
                'andfeatures': andfeatures,
                'pricing_model': pricing_model,
                'no_end_date_checked': no_end_date_checked,
                'actual_cpc_or_cpm': actual_cpc_or_cpm_value,
                'total_views_count': total_views_count,
                'total_clicks_count': total_clicks_count,
            })

class AdCampaignStatusView(AdvertiserCheckView, View):
    
    def post(self, request, campaign_id):
        with transaction.atomic():
            campaign = AdCampaigns.objects.filter(id=campaign_id).first()
            
            if not campaign:
                raise Http404("Campaign not found")

            # 合計視聴回数と合計クリック数を計算
            total_views = sum(ad_info.post.views_count for ad_info in campaign.ad_infos.all())
            campaign.total_views_count = total_views

            total_clicks = AdInfos.objects.filter(ad_campaign=campaign).aggregate(total_clicks=Sum('clicks_count'))['total_clicks']
            campaign.total_clicks_count = total_clicks

            campaign.is_hidden = True
            campaign.status = 'stopped'
            campaign.end_date = timezone.now()  # 終了日を現在の日付に設定
            campaign.recalculate_campaign(request.user) # 料金を再計算し保存
            campaign.save()

            # そのキャンペーンに紐づくすべてのAdInfosとPostsの状態を更新
            for ad_info in campaign.ad_infos.all():
                post = ad_info.post
                post.is_hidden = campaign.is_hidden
                post.save()
        
        # HTTPリファラから前のURLを取得
        referer_url = request.META.get('HTTP_REFERER')

        # リファラURLが存在する場合はそのURLにリダイレクト、存在しない場合はデフォルトのURLにリダイレクト
        return HttpResponseRedirect(referer_url if referer_url else reverse_lazy('advertisement:ad_campaigns_list'))

class AdInfoDelete(AdvertiserCheckView, View):
    def post(self, request, ad_info_id):
        ad_info = get_object_or_404(AdInfos, id=ad_info_id)
        
        # 削除する前に、関連するAdCampaignのIDを取得
        campaign_id = ad_info.ad_campaign.id

        # Delete the ad_info and its related Post object
        post_to_delete = ad_info.post
        ad_info.delete()
        post_to_delete.delete()

        return redirect('advertisement:ad_campaign_detail', campaign_id=campaign_id)

class AdCampaignDelete(AdvertiserCheckView, View):
    def post(self, request, campaign_id):
        campaign = get_object_or_404(AdCampaigns, id=campaign_id)

        # AdInfosに関連するPostsも一緒に削除
        for ad_info in campaign.ad_infos.all():
            ad_info.post.delete()

        campaign.ad_infos.all().delete()
        campaign.delete()
        # 遷移先のURL
        redirect_url = reverse('advertisement:ad_campaigns_list')  
        return HttpResponseRedirect(redirect_url)


class AdEditPrf(AdvertiserCheckView, View):
    def get(self, request):
        # 広告主用フォームインスタンスを作成し、特定のフィールドのみを表示する
        form = EditPrfForm(instance=request.user)
        # 'displayname' と 'prf_img' のみを表示するために、他のフィールドを隠す
        for field_name in ['caption', 'url1', 'url2', 'url3', 'url4', 'url5']:
            form.fields[field_name].widget = forms.HiddenInput()
        return render(request, 'advertisement/edit_prf.html', {'form': form})
    
    @transaction.atomic
    def post(self, request):
        # 送信されたデータとファイルからフォームを構築
        form = EditPrfForm(request.POST, request.FILES, instance=request.user)
        # フォームから特定のフィールドのみを保存する
        if form.is_valid():
            with transaction.atomic():
                user = form.save(commit=False)
                # 広告主として 'displayname' と 'prf_img' のみを更新する
                user.displayname = form.cleaned_data['displayname']
                user.prf_img = form.cleaned_data['prf_img']
                user.save()
            return redirect('advertisement:ad_edit_prf')
        else:
            # 有効でない場合は、エラーを含むフォームを再度表示する
            # ここでも 'displayname' と 'prf_img' 以外を隠す
            for field_name in ['caption', 'url1', 'url2', 'url3', 'url4', 'url5']:
                form.fields[field_name].widget = forms.HiddenInput()
            return render(request, 'advertisement/edit_prf.html', {'form': form})

class AdClickCountView(View):

    @method_decorator(login_required)
    def post(self, request, post_id):
        try:
            ad_info = AdInfos.objects.get(post_id=post_id)
        except AdInfos.DoesNotExist:
            print(f"Advertisement with post_id: {post_id} not found."); 
            return JsonResponse({"status": "error", "message": "Advertisement not found"}, status=404)

        # F()式を使用して、clicks_countフィールドをデータベースレベルでインクリメント
        AdInfos.objects.filter(post_id=post_id).update(clicks_count=F('clicks_count') + 1)

        # もし、インクリメント後の値を取得する必要がある場合は、オブジェクトを再取得
        ad_info.refresh_from_db()

        return JsonResponse({"status": "success"})