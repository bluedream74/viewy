# Python standard library
from django.core.mail import send_mail
from django.http import HttpResponse, HttpResponseRedirect ,JsonResponse

# Third-party Django
from django import forms
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
import datetime
from django.views.generic.base import TemplateView, View
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, FormView, DeleteView
from django.views.generic.list import ListView

# Local application/library specific
from .forms import EditPrfForm, RegistForm, UserLoginForm, VerifyForm
from .models import Follows, Messages, Users
from management.models import UserStats
from .utils import send_email_ses, generate_verification_code


import os
from .models import Users

from django.http import JsonResponse
from .models import SearchHistorys
import json

from posts.models import Posts


class HomeView(TemplateView):
  template_name = 'home.html'
  
class CheckAgeView(TemplateView):
    template_name = 'check_age.html'

    def get(self, request, *args, **kwargs):
        if request.COOKIES.get('is_over_18'):
            return redirect('posts:postlist')
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        next_url = request.GET.get('next', 'posts:postlist') # クエリパラメータから戻り先のURLを取得
        response = redirect(next_url)
        response.set_cookie('is_over_18', 'true', max_age=60*60*24*3)  # このクッキーは３日間続く
        return response
    
class AboutViewyView(TemplateView):
    template_name = 'about_viewy.html'    
    
class ForInvitedView(TemplateView):
    template_name = 'for_invited.html'    

class GuideView(TemplateView):
    template_name = 'guide.html'
    
class GuideLineView(TemplateView):
    template_name = 'guideline.html'
    
class TermsView(TemplateView):
    template_name = 'terms.html'

class PolicyView(TemplateView):
    template_name = 'policy.html'

class RegistUserView(SuccessMessageMixin, CreateView):
    template_name = 'regist.html'
    form_class = RegistForm
    success_url = reverse_lazy('accounts:verify')

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
        mail_sent = send_email_ses(
            to_email=form.instance.email,
            subject='あなたの認証コードです',
            body=f'あなたの認証コードは {form.instance.verification_code}です。このコードの有効期間は５分です。'
        )
        
        if mail_sent:
            print("Mail sent successfully!")
        else:
            print("There was an error while sending the mail.")

        return response

class InvitedRegistUserView(SuccessMessageMixin, CreateView):
    template_name = 'regist.html'  
    form_class = RegistForm
    success_url = reverse_lazy('accounts:verify')  

    def form_valid(self, form):
        # Save form
        response = super().form_valid(form)
        
        # 招待されたユーザーであることをセッションに保存
        self.request.session['is_special_user'] = True
        
        # Generate a new verification code
        form.instance.verification_code = generate_verification_code()
        form.instance.verification_code_generated_at = timezone.now()
        

        #poster_waiterをTrueにする
        form.instance.poster_waiter = True

        form.instance.save()

        # Save email to session
        self.request.session['email'] = form.instance.email

        # Send verification code to user's email using Amazon SES
        mail_sent = send_email_ses(
            to_email=form.instance.email,
            subject='あなたの特別な認証コードです',
            body=f'あなたの認証コードは {form.instance.verification_code}です。このコードの有効期間は５分です。'
        )
        
        if mail_sent:
            print("Special mail sent successfully!")
        else:
            print("There was an error while sending the special mail.")

        return response
  

class VerifyView(FormView):
    template_name = 'verify.html'
    form_class = VerifyForm
    success_url = reverse_lazy('accounts:user_login')

    def form_valid(self, form):
        user = Users.objects.get(email=self.request.session['email'])

        # Combine the 5 input fields into one code
        code = form.cleaned_data['input1'] + form.cleaned_data['input2'] + form.cleaned_data['input3'] + form.cleaned_data['input4'] + form.cleaned_data['input5']

        # Check if the verification code has expired
        if user.verification_code_generated_at + datetime.timedelta(minutes=5) < timezone.now():
            form.add_error(None, 'Your verification code has expired.')
            return self.form_invalid(form)

        if user.verification_code == code:
            user.is_active = True
            user.verification_code = None
            user.save()

            # Add a success message
            messages.success(self.request, 'ユーザー登録が完了しました')

            # Record total users
            today = timezone.now().date()
            total_users = Users.objects.filter(is_active=True).count()
            print(f'Total users: {total_users}')  # <--- This line is new

            record, created = UserStats.objects.get_or_create(date=today)

            if not created:
                record.total_users = total_users
                record.save()
        else:
            messages.error(self.request, '認証コードが正しくありません。もう一度入力してください。')
            return self.form_invalid(form)

        return super().form_valid(form)  # Call parent form_valid


          
  
class UserLoginView(FormView):
    template_name = 'user_login.html'
    form_class = UserLoginForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Check if user is special user
        if self.request.session.get('is_special_user', False):
            context['is_special_user'] = True

        return context

    def form_valid(self, form):
        user = Users.objects.get(email=form.cleaned_data['email'])

        # Check if user is active
        if not user.is_active:
            # Generate a new verification code
            user.verification_code = generate_verification_code()  # replace with your code generation function
            user.verification_code_generated_at = timezone.now()  # update the time when the code was generated
            user.save()

            # Send the verification code by email
            send_email_ses(
                to_email=user.email,
                subject='あなたの認証コードです',
                body=f'あなたの認証コードは {user.verification_code}です'
            )

            # Save email to session
            self.request.session['email'] = user.email

            # Redirect to verification page
            return redirect('accounts:verify')

        # If user is active, log in and redirect to postlist
        login(self.request, user)

        # セッションからInvitedのフラグを削除
        if 'is_special_user' in self.request.session:
            del self.request.session['is_special_user']

        return redirect('posts:postlist')


    

class UserLogoutView(View):
  
  def get(self, request, *args, **kwargs):
    logout(request)
    return redirect('accounts:user_login')
  
class PostListView(TemplateView):
  template_name = 'posts/postlist.html'
  
  
  
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
      poster = get_object_or_404(Users, pk=kwargs['pk'])
      follow, created = Follows.objects.get_or_create(user=request.user, poster=poster)
      if not created:
          follow.delete()
      poster.follow_count = poster.follow.count()
      poster.save()
      data = {'follow_count': poster.follow_count}
      return JsonResponse(data)
  
  
  
class MessageListView(ListView):
    template_name = 'posts/message_list.html'
    context_object_name = 'messages'

    def get_queryset(self):
        User = get_user_model()
        current_user = User.objects.get(id=self.request.user.id)
        
        universal_user = User.objects.get(id=1) #ID＝1に送られたメッセージは全員への一斉送信として扱う

        return Messages.objects.filter(
            Q(recipient=current_user) | Q(recipient=universal_user)
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