import re
from django import forms
from .models import Users
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.contrib.auth import authenticate
from django.shortcuts import redirect
from django.utils.safestring import mark_safe
from .utils import generate_verification_code
from django.contrib.auth.password_validation import validate_password, MinimumLengthValidator, NumericPasswordValidator, CommonPasswordValidator, UserAttributeSimilarityValidator




# ユーザー登録処理
class RegistForm(forms.ModelForm):
  username = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'ユーザーネーム（英数字と_のみ）'}))
  email = forms.EmailField(widget=forms.TextInput(attrs={'placeholder': 'メールアドレス'}))
  password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'パスワード'}))
  password_confirm = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'パスワード（確認）'}))  # 新しいフィールド

  class Meta:
      model = Users
      fields = ['username', 'email', 'password', 'password_confirm']  # 新しいフィールドを追加

  def __init__(self, *args, **kwargs):
      super().__init__(*args, **kwargs)
      self.fields['email'].error_messages = {'invalid': '有効なメールアドレスを入力してください。'}
      self.fields['username'].error_messages = {'unique': 'このユーザーネームは既に使用されています。別のユーザーネームを入力してください。'}

  def clean(self):
      cleaned_data = super().clean()
      password = cleaned_data.get('password')
      password_confirm = cleaned_data.get('password_confirm')

      if password != password_confirm:  # パスワードと確認用パスワードが一致するかチェック
          self.add_error('password_confirm', 'パスワードが一致しません。')  # 一致しない場合はエラーメッセージを表示

      return cleaned_data
  
  def clean_username(self):
      username = self.cleaned_data.get('username')
      if username and not re.match(r'^[a-zA-Z0-9]+$', username):
          raise forms.ValidationError("ユーザーネームは英数字のみが使用可能です。")
      return username

  def clean_email(self):
      email = self.cleaned_data.get('email')
      if email and Users.objects.filter(email=email).exists():
          raise forms.ValidationError("このメールアドレスは既に使用されています。別のメールアドレスを入力してください。")
      return email
  
  def clean_password(self):
        password = self.cleaned_data.get('password')
        email = self.cleaned_data.get('email')
        if password and email:
            errors = []
            validators = [
                {"validator": MinimumLengthValidator(8), "message": "パスワードは8文字以上でなければなりません。"},
                {"validator": NumericPasswordValidator(), "message": "パスワードは数字だけではいけません。"},
                {"validator": CommonPasswordValidator(), "message": "一般的すぎるパスワードは使用できません。"},
                {"validator": UserAttributeSimilarityValidator(user_attributes=["email"]), "message": "パスワードがメールアドレスと似すぎています。"},
            ]
            user = self._meta.model(email=email)  # Create a temporary user instance to validate password.
            for v in validators:
                try:
                    if isinstance(v["validator"], UserAttributeSimilarityValidator):
                        v["validator"].validate(password, user)
                    else:
                        v["validator"].validate(password)
                except forms.ValidationError:
                    errors.append(forms.ValidationError(v["message"], code='invalid'))
            if errors:
                raise forms.ValidationError(errors)
        return password
  
  def save(self, commit=True):  # commit=Trueをデフォルトにする
        # もともと備わっているセーブ機能を一回止めるたのち、ハッシュ化する処理
        user = super().save(commit=False)
        validate_password(self.cleaned_data['password'], user) # パスワードのバリデーションをより詳しく行う
        user.set_password(self.cleaned_data['password']) # パスワードのハッシュ化
        user.verification_code = generate_verification_code()   # 認証コードを生成
        if commit:
            user.save()
        return user
    # この修正により、 RegistForm.save メソッドが呼び出されるときに commit=False が指定されていると、ユーザーはデータベースに保存されず、 RegistUserView の form_valid メソッド内の super().form_valid(form) によって保存されるようになります。


# 認証コードを入力するためのフォーム
class VerifyForm(forms.Form):
    input1 = forms.CharField(max_length=1, widget=forms.TextInput(attrs={'maxlength': '1'}))
    input2 = forms.CharField(max_length=1, widget=forms.TextInput(attrs={'maxlength': '1'}))
    input3 = forms.CharField(max_length=1, widget=forms.TextInput(attrs={'maxlength': '1'}))
    input4 = forms.CharField(max_length=1, widget=forms.TextInput(attrs={'maxlength': '1'}))
    input5 = forms.CharField(max_length=1, widget=forms.TextInput(attrs={'maxlength': '1'}))
  
  
class UserLoginForm(forms.Form):
    email = forms.EmailField(widget=forms.TextInput(attrs={'placeholder': 'メールアドレス'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'パスワード'}))

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get("email")
        password = cleaned_data.get("password")

        # Try to get the user
        try:
            user = Users.objects.get(email=email)
        except Users.DoesNotExist:
            # If user does not exist, raise error
            self.add_error(None, mark_safe('メールアドレスかパスワードが間違っています。<br>再度入力してください。'))
            return cleaned_data

        # If user is not active, allow form to pass and handle in the view
        if not user.is_active:
            return cleaned_data

        # If user is active, authenticate
        user = authenticate(email=email, password=password)
        if not user:
            self.add_error(None, mark_safe('メールアドレスかパスワードが間違っています。<br>再度入力してください。'))

        return cleaned_data
  
  
class EditPrfForm(forms.ModelForm):
    displayname = forms.CharField(max_length=30, required=False, widget=forms.TextInput(attrs={'placeholder': '表示名'})) 
    caption = forms.CharField(required=False, widget=forms.Textarea(attrs={'placeholder': 'キャプション(最大120字)', 'rows': 8}), initial='',     error_messages={'max_length': "キャプションは最大120字までです。",})
    url1 = forms.URLField(required=False, widget=forms.URLInput(attrs={'placeholder': 'URL'}), initial='',  error_messages={'invalid': "正しいURLを入力してください。"})
    url2 = forms.URLField(required=False, widget=forms.URLInput(attrs={'placeholder': 'URL'}), initial='',  error_messages={'invalid': "正しいURLを入力してください。"})
    url3 = forms.URLField(required=False, widget=forms.URLInput(attrs={'placeholder': 'URL'}), initial='',  error_messages={'invalid': "正しいURLを入力してください。"})
    url4 = forms.URLField(required=False, widget=forms.URLInput(attrs={'placeholder': 'URL'}), initial='',  error_messages={'invalid': "正しいURLを入力してください。"})
    url5 = forms.URLField(required=False, widget=forms.URLInput(attrs={'placeholder': 'URL'}), initial='',  error_messages={'invalid': "正しいURLを入力してください。"})
  
  
    class Meta:
        model = Users
        fields = ['displayname','prf_img', 'caption','url1', 'url2', 'url3', 'url4', 'url5']
