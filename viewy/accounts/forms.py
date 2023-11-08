import re, uuid
from django import forms
from django.utils import timezone
from .models import Users, DeleteRequest
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.contrib.auth import authenticate
from django.shortcuts import redirect
from django.utils.safestring import mark_safe
from .utils import generate_verification_code
from django.contrib.auth.password_validation import validate_password, MinimumLengthValidator, NumericPasswordValidator, CommonPasswordValidator, UserAttributeSimilarityValidator

from django.contrib.auth.forms import PasswordResetForm as AuthPasswordResetForm
from django.contrib.auth.forms import SetPasswordForm as AuthSetPasswordForm
from axes.utils import reset
from axes.handlers.proxy import AxesProxyHandler

# ユーザー登録処理
class RegistForm(forms.ModelForm):
    username = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'ユーザーネーム（英数字と_のみ）'}))
    email = forms.EmailField(widget=forms.TextInput(attrs={'placeholder': 'メールアドレス'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'パスワード'}))
    password_confirm = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'パスワード（確認）'}))  # 新しいフィールド
    # 生年月のフィールドを追加
    birth_year = forms.TypedChoiceField(coerce=int, choices=[])
    birth_month = forms.TypedChoiceField(coerce=int, choices=[(i, i) for i in range(1, 13)])

    class Meta:
        model = Users
        fields = ['username', 'email', 'password', 'password_confirm']  # 新しいフィールドを追加

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].error_messages = {'invalid': '有効なメールアドレスを入力してください。'}
        self.fields['username'].error_messages = {'unique': 'このユーザーネームは既に使用されています。別のユーザーネームを入力してください。'}
        # 現在の年と月を取得
        current_year = timezone.now().year
        # 初期選択肢として「年を入力」を追加
        birth_year_choices = [('','------')] + [(year, year) for year in range(current_year - 17, 1919, -1)]
        self.fields['birth_year'].choices = birth_year_choices
        
        # 初期選択肢として「月を入力」を追加
        birth_month_choices = [('','----')] + [(month, month) for month in range(1, 13)]
        self.fields['birth_month'].choices = birth_month_choices

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')

        if password != password_confirm:  # パスワードと確認用パスワードが一致するかチェック
            self.add_error('password_confirm', 'パスワードが一致しません。')  # 一致しない場合はエラーメッセージを表示
            
        # 生年月のデータを取得
        birth_year = cleaned_data.get('birth_year')
        birth_month = cleaned_data.get('birth_month')
        
        # 現在の日付を取得
        today = timezone.now().date()
        
        # ユーザが18歳以上かどうかを確認する
        if birth_year and birth_month:
            if birth_year > today.year - 18 or (birth_year == today.year - 18 and birth_month > today.month):
                self.add_error('birth_year', 'You must be at least 18 years old.')

        return cleaned_data
  
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if username and not re.match(r'^[a-zA-Z0-9_]+$', username):
            raise forms.ValidationError("ユーザーネームは英数字と_のみが使用可能です。")
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
                {"validator": MinimumLengthValidator(4), "message": "パスワードは4文字以上である必要があります。"},
                # {"validator": NumericPasswordValidator(), "message": "パスワードは数字だけではいけません。"},
                # {"validator": CommonPasswordValidator(), "message": "一般的すぎるパスワードは使用できません。"},
                # {"validator": UserAttributeSimilarityValidator(user_attributes=["email"]), "message": "パスワードがメールアドレスと似すぎています。"},
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
    
    def clean_birth_year(self):
        birth_year = self.cleaned_data.get('birth_year')
        if birth_year == '':
            raise forms.ValidationError("生年月の年を入力してください。")
        return birth_year

    def clean_birth_month(self):
        birth_month = self.cleaned_data.get('birth_month')
        if birth_month == '':
            raise forms.ValidationError("生年月の月を入力してください。")
        return birth_month
  
    def save(self, commit=True):  # commit=Trueをデフォルトにする
        # もともと備わっているセーブ機能を一回止めるたのち、ハッシュ化する処理
        user = super().save(commit=False)
        validate_password(self.cleaned_data['password'], user) # パスワードのバリデーションをより詳しく行う
        user.set_password(self.cleaned_data['password']) # パスワードのハッシュ化
        user.verification_code = generate_verification_code()   # 認証コードを生成
        # 生年月を保存
        user.birth_year = self.cleaned_data.get('birth_year')
        user.birth_month = self.cleaned_data.get('birth_month')
        if not user.username:
            user.username = self.generate_unique_username()

        if commit:
            user.save()
        return user
    # この修正により、 RegistForm.save メソッドが呼び出されるときに commit=False が指定されていると、ユーザーはデータベースに保存されず、 RegistUserView の form_valid メソッド内の super().form_valid(form) によって保存されるようになります。

    def generate_unique_username(self):
        # 一意のユーザーネームを生成するまでループ
        while True:
            username = str(uuid.uuid4())[:8]
            if not Users.objects.filter(username=username).exists():
                return username


class InvitedRegistForm(RegistForm):
    username = forms.CharField(
        required=True, 
        widget=forms.TextInput(attrs={'placeholder': 'ユーザーネーム（英数字と_のみ）'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # InvitedRegistFormのときだけ生年月を必須ではなくする
        self.fields['birth_year'].required = False
        self.fields['birth_month'].required = False

    def clean_birth_year(self):
        # 必須でない場合はバリデーションをカスタマイズ
        birth_year = self.cleaned_data.get('birth_year')
        if not birth_year:
            return None  # 必須ではないのでNoneを返す
        return birth_year  # 他のバリデーションは親クラスに任せる

    def clean_birth_month(self):
        # 必須でない場合はバリデーションをカスタマイズ
        birth_month = self.cleaned_data.get('birth_month')
        if not birth_month:
            return None  # 必須ではないのでNoneを返す
        return birth_month  # 他のバリデーションは親クラスに任せる


# 認証コードを入力するためのフォーム
class VerifyForm(forms.Form):
    input1 = forms.CharField(max_length=1, widget=forms.TextInput(attrs={'maxlength': '1'}))
    input2 = forms.CharField(max_length=1, widget=forms.TextInput(attrs={'maxlength': '1'}))
    input3 = forms.CharField(max_length=1, widget=forms.TextInput(attrs={'maxlength': '1'}))
    input4 = forms.CharField(max_length=1, widget=forms.TextInput(attrs={'maxlength': '1'}))
    input5 = forms.CharField(max_length=1, widget=forms.TextInput(attrs={'maxlength': '1'}))
  
  
class UserLoginForm(forms.Form):
    email = forms.EmailField(widget=forms.TextInput(attrs={'placeholder': 'メールアドレス', 'autocomplete': 'email'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'パスワード', 'autocomplete': 'current-password'}))

    def __init__(self, *args, **kwargs):
        # Pop the 'request' argument if it is present
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get("email")
        password = cleaned_data.get("password")

        try:
            user = Users.objects.get(email=email)
        except Users.DoesNotExist:
            self._handle_login_failure(email, password, "User does not exist with the provided email.")
            return cleaned_data

        if not user.check_password(password):
            self._handle_login_failure(email, password, "Password mismatch for the provided email.")
        
        return cleaned_data

    def _handle_login_failure(self, email, password, debug_message):
        self.add_error(None, mark_safe('メールアドレスまたはパスワードが間違っています。<br>再度入力してください。'))
        AxesProxyHandler.user_login_failed(
            request=self.request,
            sender=self.__class__,
            credentials={'username': email, 'password': password}
        )

class PasswordResetForm(AuthPasswordResetForm):
    email = forms.EmailField(widget=forms.TextInput(attrs={'placeholder': 'メールアドレス'}))

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and not Users.objects.filter(email=email).exists():
            raise forms.ValidationError(mark_safe("このメールアドレスは登録されていません。<br>正しいメールアドレスを入力してください。"))
        return email

class SetPasswordForm(AuthSetPasswordForm):
    new_password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': '新しいパスワード'}),
    )
    new_password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': '新しいパスワード（確認）'}),
    )
  
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


class DeleteRequestForm(forms.ModelForm):
    email = forms.EmailField(widget=forms.EmailInput())
    postername = forms.CharField(widget=forms.TextInput(attrs={'placeholder': '正確でなくても結構です'}))
    post_title = forms.CharField(widget=forms.TextInput(attrs={'placeholder': '正確でなくても結構です'}))


    class Meta:
        model = DeleteRequest
        fields = ['email', 'postername', 'post_title', 'case_type', 'details']