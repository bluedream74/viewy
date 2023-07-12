# Python standard library
from django.core.mail import send_mail
from django.http import HttpResponse, JsonResponse

# Third-party Django
from django import forms
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views.generic.base import TemplateView, View
from django.views.generic.edit import CreateView, FormView
from django.views.generic.list import ListView

# Local application/library specific
from .forms import EditPrfForm, RegistForm, UserLoginForm, VerifyForm
from .models import Follows




import os
from .models import Users

class HomeView(TemplateView):
  template_name = 'home.html'
  
class CheckAgeView(TemplateView):
    template_name = 'check_age.html'

    def get(self, request, *args, **kwargs):
        if request.COOKIES.get('is_over_18'):
            return redirect('posts:postlist')
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        response = redirect('posts:postlist')
        response.set_cookie('is_over_18', 'true', max_age=60*60*24*3)  # このクッキーは３日間続く
        return response
  
class RegistUserView(SuccessMessageMixin, CreateView):
    template_name = 'regist.html'
    form_class = RegistForm
    success_message = 'ユーザー登録が完了しました'
    success_url = reverse_lazy('accounts:verify')

    def form_valid(self, form):
        # Save form
        response = super().form_valid(form)

        # Save email to session
        self.request.session['email'] = form.instance.email

        # Send verification code to user's email
        send_mail(
            'あなたの認証コードです',
            f'あなたの認証コードは {form.instance.verification_code}です',
            'yuuma0568@gmail.com',
            [form.instance.email],
            fail_silently=False,
        )

        return response

  

class VerifyView(FormView):
    template_name = 'verify.html'
    form_class = VerifyForm
    success_url = reverse_lazy('accounts:user_login')

    def form_valid(self, form):
        user = Users.objects.get(email=self.request.session['email'])

        # Combine the 5 input fields into one code
        code = form.cleaned_data['input1'] + form.cleaned_data['input2'] + form.cleaned_data['input3'] + form.cleaned_data['input4'] + form.cleaned_data['input5']

        if user.verification_code == code:
            user.is_active = True
            user.verification_code = None
            user.save()

        else:
            form.add_error(None, 'Invalid verification code.')
            return self.form_invalid(form)

        return super().form_valid(form)  # Call parent form_valid


          
  
class UserLoginView(FormView):
    template_name = 'user_login.html'
    form_class = UserLoginForm

    def form_valid(self, form):
        email = form.cleaned_data['email']
        password = form.cleaned_data['password']
        user = authenticate(email=email, password=password)

        if user is not None and user.is_active:
            login(self.request, user)
            return redirect('posts:postlist')
        else:
            messages.error(self.request, 'メールアドレスかパスワードが間違っています。再度入力してください。')
            return self.form_invalid(form)
    

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