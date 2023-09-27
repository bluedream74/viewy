# Python standard library
import os
import random
import string
from django.core.mail import send_mail
from django.http import HttpResponse, HttpResponseRedirect ,JsonResponse

# Third-party Django
from django import forms
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.models import Group
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
import datetime
from django.views import generic
from django.views.generic.base import TemplateView, View
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, FormView, DeleteView
from django.views.generic.list import ListView
from django.contrib.auth.views import LoginView

# Local application/library specific
from .forms import EditPrfForm, RegistForm, InvitedRegistForm, UserLoginForm, VerifyForm, PasswordResetForm, SetPasswordForm, DeleteRequestForm
from .models import Follows, Messages, Users, DeleteRequest, Features, Surveys, SurveyResults
from management.models import UserStats
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth import get_user_model
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.template.loader import render_to_string
from accounts.models import Users

from django.contrib.auth.tokens import PasswordResetTokenGenerator
import random
import string
from .utils import send_delete_request_notification

from django.utils.safestring import mark_safe




from .models import Users

from django.http import JsonResponse
from .models import SearchHistorys
import json

from posts.models import Posts

from django.conf import settings

BASE_URL = settings.BASE_URL


class CustomPasswordResetTokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, user, timestamp):
        return super()._make_hash_value(user, timestamp) + str(int(timestamp) + 60 * 60)  # １時間の有効期限

custom_token_generator = CustomPasswordResetTokenGenerator()

# ユーザー登録時にランダムな5桁の認証コードを生成
def generate_verification_code():
    return ''.join(random.choices(string.digits, k=5))

def send_email_ses(to_email, subject, verification_code):
    body = render_to_string('regist_email.html', {
        'subject': subject,
        'verification_code': verification_code
    })

    send_mail(
        subject,
        body,
        'regist@viewy.net',  # From
        [to_email],  # To
        fail_silently=False,
    )



class HomeView(TemplateView):
  template_name = 'home.html'
  
class CheckAgeView(TemplateView):
    template_name = 'check_age.html'

    def get(self, request, *args, **kwargs):
        if request.COOKIES.get('is_over_18'):
            return redirect('posts:visitor_postlist')
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        next_url = request.GET.get('next', 'posts:visitor_postlist') # クエリパラメータから戻り先のURLを取得
        response = redirect(next_url)
        response.set_cookie('is_over_18', 'true', max_age=60*60*24*3)  # このクッキーは３日間続く
        return response
    
class AboutViewyView(TemplateView):
    template_name = 'about_viewy.html'    
    
# パートナー申請解説ページ
class PartnerApplicationGuideView(TemplateView):
    template_name = 'partner_application_guide.html'    
    
class ForInvitedView(TemplateView):
    template_name = 'for_invited.html'    
    
class ForAdvertiserView(TemplateView):
    template_name = 'for_advertiser.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # 'Poster' グループを取得
        poster_group = Group.objects.get(name='Poster')
        
        # 'Poster' グループのメンバーを取得
        poster_users = poster_group.user_set.filter(is_active=True)
        
        # ランダムにユーザーを選び、そのプロフィール画像を取得
        selected_users = random.sample(list(poster_users), min(30, len(poster_users)))
        
        # プロフィール画像を15個ずつに分ける
        poster_imgs1 = [user.prf_img.url for user in selected_users[:15] if user.prf_img]
        poster_imgs2 = [user.prf_img.url for user in selected_users[15:30] if user.prf_img]
        
        # コンテキストにプロフィール画像のリストを追加
        context['poster_imgs1'] = poster_imgs1
        context['poster_imgs2'] = poster_imgs2
        return context

class GuideView(TemplateView):
    template_name = 'guide.html'
    
class GuideLineView(TemplateView):
    template_name = 'guideline.html'
    
class TermsView(TemplateView):
    template_name = 'terms.html'

class PolicyView(TemplateView):
    template_name = 'policy.html'
    
# ユーザー登録の基盤クラス    
class BaseRegistUserView(SuccessMessageMixin, CreateView):
    def form_valid(self, form):
        # Save form
        response = super().form_valid(form)
        
        # Generate a new verification code
        form.instance.verification_code = generate_verification_code()
        form.instance.verification_code_generated_at = timezone.now()
        form.instance.save()

        # Save email to session
        self.request.session['email'] = form.instance.email

        # Send verification code to user's email using Amazon SES
        mail_sent = self.send_verification_email(form)
        
        if mail_sent:
            print("Mail sent successfully!")
        else:
            print("There was an error while sending the mail.")

        return response

    def send_verification_email(self, form):
        return send_email_ses(
            to_email=form.instance.email,
            subject='【Viewy】認証コード',
            verification_code=form.instance.verification_code
        )    
 
    
# 通常のユーザー登録
class RegistUserView(BaseRegistUserView):
    template_name = 'regist.html'
    form_class = RegistForm
    success_url = reverse_lazy('accounts:verify')


# 招待者用のユーザー登録
class InvitedRegistUserView(BaseRegistUserView):
    template_name = 'invited_regist.html'
    form_class = InvitedRegistForm
    success_url = reverse_lazy('accounts:verify')

    def form_valid(self, form):
        # 招待されたユーザーであることをセッションに保存
        self.request.session['is_special_user'] = True
        
        # poster_waiterをTrueにする
        form.instance.poster_waiter = True

        return super().form_valid(form)


# 広告主用のユーザー登録
class RegistAdvertiserView(BaseRegistUserView):
    template_name = 'regist_advertiser.html'
    form_class = InvitedRegistForm
    success_url = reverse_lazy('accounts:verify')

    def form_valid(self, form):
        # ユーザーのis_advertiserフィールドをTrueにセット
        form.instance.is_advertiser = True
        
        # ユーザーが広告主として登録されたことを示すセッション変数をセット
        self.request.session['registered_as_advertiser'] = True

        return super().form_valid(form)
  

class VerifyView(FormView):
    template_name = 'verify.html'
    form_class = VerifyForm
    success_url = reverse_lazy('posts:postlist')

    def form_valid(self, form):
        user = Users.objects.get(email=self.request.session['email'])

        # Combine the 5 input fields into one code
        code = form.cleaned_data['input1'] + form.cleaned_data['input2'] + form.cleaned_data['input3'] + form.cleaned_data['input4'] + form.cleaned_data['input5']

        # Check if the verification code has expired
        if user.verification_code_generated_at + datetime.timedelta(minutes=60) < timezone.now():
            form.add_error(None, 'Your verification code has expired.')
            return self.form_invalid(form)

        if user.verification_code == code:
            user.is_active = True
            user.verification_code = None
            user.save()

            # ユーザーをログインさせる
            login(self.request, user, backend='django.contrib.auth.backends.ModelBackend')


            # Add a success message
            messages.success(self.request, 'ユーザー登録が完了しました')

            # Record total users
            today = timezone.now().date()
            total_users = Users.objects.filter(is_active=True).count()
            print(f'Total users: {total_users}')

            record, created = UserStats.objects.get_or_create(date=today)

            if not created:
                record.total_users = total_users
                record.save()
                
            # セッションから広告主として登録されたかの情報を取得し、セッションからその情報を削除
            registered_as_advertiser = self.request.session.pop('registered_as_advertiser', False)
            
            # セッションからリダイレクト先URLを取得し、セッションからその情報を削除
            next_url = self.request.session.pop('return_to', None)
            if registered_as_advertiser:
                # ここで広告主用のリダイレクト先URLにとばす
                return redirect('advertisement:ad_campaigns_list')
            elif next_url:
                return redirect(next_url)  # 元のページにリダイレクト
            return redirect(self.success_url)  # デフォルトのリダイレクト先に移動
        else:
            messages.error(self.request, '認証コードが正しくありません。もう一度入力してください。')
            return self.form_invalid(form)


class ResendVerificationCodeView(View):
    def get(self, request, *args, **kwargs):
        email = request.session['email']
        user = Users.objects.get(email=email)

        # Generate a new verification code
        user.verification_code = generate_verification_code()
        user.verification_code_generated_at = timezone.now()
        user.save()

        # Send verification code to user's email using Amazon SES
        send_email_ses(
            to_email=user.email,
            subject='【Viewy】認証コードの再送信',
            verification_code=user.verification_code,
        )

        # Add a success message
        messages.success(request, '認証コードを再送しました。')

        return HttpResponseRedirect(reverse('accounts:verify'))
          
  
class UserLoginView(LoginView):
    template_name = 'user_login.html'
    form_class = UserLoginForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Check if user is special user
        if self.request.session.get('is_special_user', False):
            context['is_special_user'] = True

        return context
    
    def get(self, request, *args, **kwargs):
        # nextパラメータが存在する場合、セッションに保存
        if 'next' in request.GET:
            request.session['return_to'] = request.GET['next']
            print(f"Received return_to URL: {request.GET['next']}")  # ここでURLを出力
        return super().get(request, *args, **kwargs)

    def form_valid(self, form):
        email = form.cleaned_data['email']
        password = form.cleaned_data['password']

        user = authenticate(request=self.request, username=email, password=password)

        # 認証失敗時
        if user is None:
            try:
                existing_user = Users.objects.get(email=email)
                if not existing_user.is_active:
                    # is_activeがFalseの場合の処理

                    # 新しい確認コードを生成する
                    existing_user.verification_code = generate_verification_code()
                    existing_user.verification_code_generated_at = timezone.now()
                    existing_user.save()

                    # 確認コードをメールで送信する
                    send_email_ses(
                        to_email=existing_user.email,
                        subject='【Viewy】認証コード',
                        verification_code=existing_user.verification_code,
                    )

                    # メールアドレスをセッションに保存する
                    self.request.session['email'] = existing_user.email

                    # 確認ページへリダイレクトする
                    return redirect('accounts:verify')
                
                # メールアドレスは正しいがパスワードが間違っている場合
                else:
                    form.add_error(None, mark_safe('メールアドレスまたはパスワードが間違っています。'))
                    return self.form_invalid(form)

            # メールアドレスが存在しない場合
            except Users.DoesNotExist:
                form.add_error(None, mark_safe('メールアドレスまたはパスワードが間違っています。'))
                return self.form_invalid(form)

        # If user is active, log in and redirect to postlist
        login(self.request, user)
        messages.success(self.request, 'ログインしました')  # メッセージを追加


        # セッションからInvitedのフラグを削除
        if 'is_special_user' in self.request.session:
            del self.request.session['is_special_user']
            
        # セッションからリダイレクト先URLを取得し、セッションからその情報を削除
        next_url = self.request.session.pop('return_to', None) or 'posts:postlist'
        return redirect(next_url)

        

class UserLogoutView(View):
  
  def get(self, request, *args, **kwargs):
    logout(request)
    messages.success(request, 'ログアウトしました')  # メッセージを追加
    return redirect('posts:visitor_postlist')
  
# class PostListView(TemplateView):
#   template_name = 'posts/postlist.html'


# パスワードリセット関連


def send_password_reset_email(email):
    user = Users.objects.get(email=email)
    uid = force_str(urlsafe_base64_encode(force_bytes(user.pk)))
    token = custom_token_generator.make_token(user)
    reset_url = reverse('accounts:password_reset_confirm', kwargs={'uidb64': uid, 'token': token})
    full_reset_url = f'{BASE_URL}{reset_url}'
    subject = '【Viewy】パスワード再設定のご案内'
    message = render_to_string('password_reset_email.html',{'password_reset_link': full_reset_url, 'user': user}) # userをコンテキストに追加
    send_mail(subject, message, 'regist@viewy.net', [email], fail_silently=False)

class PasswordResetView(FormView):
    template_name = 'password_reset.html'
    form_class = PasswordResetForm
    success_url = reverse_lazy('accounts:password_reset_send')

    def form_valid(self, form):
        email = form.cleaned_data['email']
        send_password_reset_email(email)
        return super().form_valid(form)
    

class PasswordResetSendView(TemplateView):
    template_name = 'password_reset_send.html'

class PasswordResetConfirmView(FormView):
    template_name = 'password_reset_confirm.html'
    form_class = SetPasswordForm
    success_url = reverse_lazy('accounts:password_reset_complete')

    def dispatch(self, *args, **kwargs):
        self.user = self.get_user(kwargs['uidb64'])
        self.validlink = False
        if self.user:
            self.validlink = custom_token_generator.check_token(self.user, kwargs['token']) # カスタムジェネレータを使用
            if not self.validlink:
                print("トークンが無効です。期限切れの可能性があります。")
        else:
            print("User not found")
        return super().dispatch(*args, **kwargs)

    def get_user(self, uidb64):
        User = get_user_model()
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            return User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist) as e:
            print("Error retrieving user:", e)
            return None

    def form_valid(self, form):
        if self.validlink:
            password = form.cleaned_data['new_password1']
            self.user.set_password(password)
            self.user.save()
        else:
            print("無効なlinkだよん, passwordはアップデートされませんでした") # リンク無効、パスワード未更新
        return super().form_valid(form)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['validlink'] = self.validlink
        return context

class PasswordResetCompleteView(TemplateView):
    template_name = 'password_reset_complete.html'
  
  
class EditPrfView(View):
    def get(self, request):
        form = EditPrfForm(instance=request.user)
        return render(request, 'posts/edit_prf.html', {'form': form})
    
    def post(self, request):
        form = EditPrfForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('posts:my_account')
        else:
            # form.errors contains the error messages
            # You can pass it to the template to display them
            return render(request, 'posts/edit_prf.html', {'form': form})
            
            
        
class FollowView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        # only()メソッドを使用して、必要なフィールドのみを取得
        poster = get_object_or_404(Users.objects.only('id', 'follow_count', 'prf_img'), pk=kwargs['pk'])
        follow, created = Follows.objects.get_or_create(user=request.user, poster=poster)
        if not created:
          follow.delete()
        poster.follow_count = poster.follow.count()
        poster.save(update_fields=['follow_count'])  # 保存時にも特定のフィールドのみを更新
        data = {'follow_count': poster.follow_count}
        return JsonResponse(data)
  
  
  
class MessageListView(ListView):
    template_name = 'posts/message_list.html'
    context_object_name = 'messages'

    def get_queryset(self):
        return Messages.objects.filter(
            Q(recipient_id=self.request.user.id) | Q(recipient_id=1)
        ).order_by('-sent_at')
        
        
class MessageDetailView(DetailView):
    template_name = 'posts/message_detail.html'
    context_object_name = 'message'
    model = Messages

    def get_object(self):
        obj = super().get_object()
        if not obj.is_read:
            obj.is_read = True
            obj.save()
        return obj
    
    


class MessageDeleteView(DeleteView):
    model = Messages
    success_url = reverse_lazy('accounts:message_list')  # メッセージ削除後にリダイレクトするURLを指定します。

    def get_queryset(self):
        User = get_user_model()
        current_user = User.objects.get(id=self.request.user.id)
        universal_user = User.objects.get(id=1)  # ID＝1に送られたメッセージは全員への一斉送信として扱う
        return Messages.objects.filter(
            Q(recipient=current_user) | Q(recipient=universal_user)
        )

    def get(self, *args, **kwargs):
        response = self.delete(*args, **kwargs)
        return HttpResponseRedirect(self.success_url)


class SearchHistoryView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        user = request.user
        # visible=Trueの検索履歴のみを取得
        history = SearchHistorys.objects.filter(user=user, visible=True).order_by('-searched_at')[:5]  # 最新の5件
        return JsonResponse({'history': list(history.values())})

class SearchHistorySaveView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        user = request.user
        query = request.POST.get("query")

        # この関数でハッシュタグが実際に存在するかを確認
        # 存在しなかったら、400を返す
        if not self.hashtag_exists(query):
            return JsonResponse({"status": "error", "message": "Hashtag does not exist."}, status=400)

        # 既存の検索履歴を確認
        history, created = SearchHistorys.objects.get_or_create(user=user, query=query)

        if created:
            # 新しい検索履歴の場合、初期設定を行う
            history.search_count = 1
            history.visible = True
        else:
            # すでに存在する検索履歴の場合、visibleをTrueにし、search_countを増やす
            history.visible = True
            history.search_count += 1

        # searched_at を現在の日時に更新
        history.searched_at = timezone.now()
            
        history.save()
        return JsonResponse({"status": "success"})
   
    
    def hashtag_exists(self, query):

        return Posts.objects.filter(
            Q(hashtag1=query) | 
            Q(hashtag2=query) | 
            Q(hashtag3=query)
            ).exists()

# ×ボタンで表示されているすべての検索履歴を非表示にする
class HideSearchHistoriesView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        try:
            ## ユーザーの全ての検索履歴を取得
            histories = SearchHistorys.objects.filter(user=request.user, visible=True)

            if not histories.exists():
                return JsonResponse({"status": "error: No histories found."}, status=400)
            
            # 取得した検索履歴を非表示にする
            histories.update(visible=False)
                
            return JsonResponse({"status": "success"})

        except Exception as e:
            print(f"Exception: {str(e)}")
            return JsonResponse({"status": f"error: {str(e)}"}, status=500)
        
        
class DeleteUserView(LoginRequiredMixin, DeleteView):
    model = Users
    success_url = reverse_lazy('accounts:user_login')
    template_name = os.path.join('posts', 'delete_user.html')
    
    def get_object(self, queryset=None):
        return self.request.user

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Your account has been deleted successfully.')
        return super().delete(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        delete_confirmation = request.POST.get('delete_confirmation', '')
        if "cancel" in request.POST:
            url = reverse_lazy('posts:setting')
            return redirect(url)
        elif delete_confirmation.lower() == '削除':
            return super().post(request, *args, **kwargs)
        else:
            messages.error(request, '削除するためには"削除"と入力する必要があります。')
            return redirect('accounts:delete_user')
        
        
class DeleteRequestView(generic.CreateView):
    model = DeleteRequest
    form_class = DeleteRequestForm
    template_name = 'delete_request.html'
    success_url = reverse_lazy('delete_request_success')  # 'terms'はurls.pyで定義するURL名です。

    def form_valid(self, form):
        response = super().form_valid(form)
        send_delete_request_notification(self.object)  # メール通知の送信
        return response
    
class DeleteRequestSuccessView(TemplateView):
  template_name = 'delete_request_success.html'
  
  
# 次元変更を担うビュー
@method_decorator(login_required, name='dispatch')
@method_decorator(csrf_exempt, name='dispatch')
class ChangeDimensionView(View):

    def post(self, request, *args, **kwargs):

        try:
            data = json.loads(request.body)
            new_dimension = float(data.get('dimension'))

            request.user.dimension = new_dimension

            # 次元に応じた特徴を追加する
            feature_2d = get_object_or_404(Features, name="love 2D")
            feature_3d = get_object_or_404(Features, name="love 3D")

            if new_dimension == 3.0:
                request.user.features.remove(feature_2d)  # love 2D を削除
                request.user.features.add(feature_3d)  # love 3D を追加

            elif new_dimension == 2.0:
                request.user.features.remove(feature_3d)  # love 3D を削除
                request.user.features.add(feature_2d)  # love 2D を追加

            elif new_dimension == 2.5:
                request.user.features.add(feature_2d, feature_3d)  # love 2D と love 3D の両方を追加

            request.user.save()

            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
        
        
@method_decorator(csrf_exempt, name='dispatch')
class FirstSettingView(View):

    def post(self, request, *args, **kwargs):
        try:
            gender = request.POST.get('gender')
            dimension = float(request.POST.get('dimension'))

            request.user.gender = gender
            request.user.dimension = dimension

            # 性別に応じた特徴を追加する
            gender_features = {
                'male': 'male',
                'female': 'female',
                'other': 'other-gender',
            }
            if gender in gender_features:
                feature = get_object_or_404(Features, name=gender_features[gender])
                request.user.features.add(feature)

            # 次元に応じた特徴を追加する
            if dimension == 3.0:
                feature = get_object_or_404(Features, name='love 3D')
                request.user.features.add(feature)
            elif dimension == 2.0:
                feature = get_object_or_404(Features, name='love 2D')
                request.user.features.add(feature)
            elif dimension == 2.5:
                feature_2d = get_object_or_404(Features, name='love 2D')
                feature_3d = get_object_or_404(Features, name='love 3D')
                request.user.features.add(feature_2d, feature_3d)

            request.user.save()
            
            messages.success(request, '初期設定が完了しました。')
            return JsonResponse({'status': 'success'})

        except Exception as e:
            return JsonResponse({'status': 'error', 'error': str(e)})

    def get(self, request, *args, **kwargs):
        return JsonResponse({'status': 'error'})

@method_decorator(ensure_csrf_cookie, name='dispatch')
class SurveyAnswerView(View):
    def post(self, request, selected_option_id):
        user = request.user
        if user.is_authenticated:
            try:
                # selected_option_id,はURLから渡されます。
                selected_option = Features.objects.get(pk=selected_option_id)

                # ユーザーのfeaturesに選択した特性を追加
                user.features.add(selected_option)
                user.save()  # 必要に応じてユーザーオブジェクトを保存
                
                return JsonResponse({'status': 'success', 'message': 'Answer saved'})
            
            except Features.DoesNotExist:
                return JsonResponse({'status': 'error', 'message': 'Invalid option'}, status=400)
            except Surveys.DoesNotExist:
                return JsonResponse({'status': 'error', 'message': 'Invalid survey'}, status=400)
        else:
            return JsonResponse({'status': 'error', 'message': 'Not authenticated'}, status=401)