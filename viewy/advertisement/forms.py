from django import forms
from .models import AdCampaigns, AdInfos, RequestDocument, SetMeeting
from posts.models import Posts
from django.shortcuts import render
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import datetime, date, timedelta
import datetime
import calendar


class AdCampaignForm(forms.ModelForm):
    PRICING_MODEL_CHOICES = [ ('CPM', 'CPM'), ('CPC', 'CPC')]

    pricing_model = forms.ChoiceField(
        choices=PRICING_MODEL_CHOICES,
        widget=forms.RadioSelect,  # ラジオボタンを使用
        label='Pricing Model',
        initial='CPM' 
    )

    target_views = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={
            'min': 50000,
            'step': 10000,
            'placeholder': '目標表示回数を入力'
        })
    )
    target_clicks = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={
            'min': 1000,
            'step': 100,
            'placeholder': 'クリック目標数を入力'
        })
    )

    end_date_option = forms.ChoiceField(
        choices=[('none', '期限なし'), ('set', '期限を設定')],
        widget=forms.RadioSelect,
        label='終了期限オプション',
        initial='none'
    )

    end_date = forms.DateField(
        required=False,  # 必須ではなくする
        widget=forms.DateInput(attrs={
            'type': 'date', 
            'id': 'end-date-input'
        })
    )

    class Meta:
        model = AdCampaigns
        fields = ['title', 
        'start_date', 
        'andfeatures',]
        widgets = {
            'start_date': forms.DateInput(attrs={
                'type': 'date', 
                'id': 'start-date-input',
                # 今日の日付を min 属性として設定
                'min': date.today().isoformat(),  
                # 翌月末の日付を max 属性として設定
                'max': '',  # この値は後でセットします
            }),
        }


    def clean_start_date(self):
        start_date = self.cleaned_data.get('start_date')
        # 新規作成時のみ今日以降の日付を要求する
        # start_dateがdatetimeオブジェクトの場合、dateオブジェクトに変換
        if isinstance(start_date, datetime.datetime):
            start_date = start_date.date()
        
        # instanceがあるかどうかをチェックし、pkが設定されている場合は編集とみなす
        if not self.instance or not self.instance.pk:
            # start_dateが現在の日付より前かどうかをチェック
            if start_date < date.today():
                raise forms.ValidationError('開始日は今日以降の日付を選択してください。')
        return start_date

    def clean(self):
        cleaned_data = super().clean()
        title = cleaned_data.get('title')
        start_date = cleaned_data.get('start_date')
        end_date_option = cleaned_data.get('end_date_option')
        end_date = cleaned_data.get('end_date')
        target_views = cleaned_data.get('target_views')
        target_clicks = cleaned_data.get('target_clicks')

        # 既存インスタンスの場合は、pricing_model をインスタンスから取得
        if self.instance and self.instance.pk:
            pricing_model = self.instance.pricing_model
        else:
            pricing_model = cleaned_data.get('pricing_model')

        if pricing_model == 'CPC':
            if not target_clicks:
                self.add_error('target_clicks', ValidationError('CPCモデルの場合、クリック目標数は必須です'))
        elif pricing_model == 'CPM':
            if not target_views:
                self.add_error('target_views', ValidationError('CPMモデルの場合、表示目標数は必須です'))

        # Title validation
        if not title:
            self.add_error('title', ValidationError('キャンペーン名は必須です'))

        # 'none'が選択された場合、end_dateをクリアする
        if end_date_option == 'none':
            cleaned_data['end_date'] = None
        # 'set'が選択された場合、end_dateを検証する
        elif end_date_option == 'set' and not cleaned_data.get('end_date'):
            self.add_error('end_date', forms.ValidationError('終了日を選択してください。'))

        if end_date and start_date:
            # Ensure both dates are date objects for comparison
            end_date_as_date = end_date.date() if hasattr(end_date, 'date') else end_date
            start_date_as_date = start_date.date() if hasattr(start_date, 'date') else start_date
            if end_date_as_date <= start_date_as_date:
                self.add_error('end_date', ValidationError('正しく終了日時を設定してください'))

        target_views = cleaned_data.get('target_views')
        if target_views is not None:
            if target_views % 10000 != 0:
                self.add_error('target_views', ValidationError('目標表示回数は10000の単位で入力してください'))

        # Target clicks validation
        target_clicks = cleaned_data.get('target_clicks')
        if target_clicks is not None:
            if target_clicks % 100 != 0:
                self.add_error('target_clicks', ValidationError('クリック目標数は100の単位で入力してください'))

        # インスタンスが編集の場合にのみ特定のフィールドのチェックを行う
        if self.instance and self.instance.pk:
            original_target_views = self.instance.target_views
            original_target_clicks = self.instance.target_clicks

            # target_viewsのバリデーション
            if 'target_views' in cleaned_data:
                if cleaned_data['target_views'] is not None:
                    if cleaned_data['target_views'] < 200000 and original_target_views >= 200000:
                        self.add_error('target_views', ValidationError('目標表示回数は20万回未満に設定できません。'))

            # target_clicksのバリデーション
            if 'target_clicks' in cleaned_data:
                if cleaned_data['target_clicks'] is not None:
                    if cleaned_data['target_clicks'] < 2000 and original_target_clicks > 2000:
                        self.add_error('target_clicks', ValidationError('クリック目標数は2000回以下に設定できません。'))

        return cleaned_data

    def __init__(self, *args, **kwargs):
        # kwargsからinstanceを取得する
        instance = kwargs.get('instance', None)
        super(AdCampaignForm, self).__init__(*args, **kwargs)

        # 今日の日付を取得
        today = date.today()
        # 現在の年と月を取得
        year, month = today.year, today.month
        # 翌月を計算
        next_month = month + 1 if month < 12 else 1
        next_year = year if month < 12 else year + 1
        # 翌月末の日を計算
        last_day_of_next_month = calendar.monthrange(next_year, next_month)[1]
        # 翌月末の日付を作成
        last_date_of_next_month = date(next_year, next_month, last_day_of_next_month)
        # max 属性をセット
        self.fields['start_date'].widget.attrs['max'] = last_date_of_next_month.isoformat()

        # instanceが存在し、pkが設定されている場合は編集画面とみなす
        if instance and instance.pk:
            self.fields['end_date'].initial = timezone.localtime(instance.end_date) if instance.end_date else None
            self.fields['start_date'].widget.attrs['readonly'] = 'readonly'
            self.fields['target_views'].initial = instance.target_views
            self.fields['target_clicks'].initial = instance.target_clicks

            # Disable target_views if the current value is less than 200,000
            if instance.target_views < 200000:
                self.fields['target_views'].widget.attrs['readonly'] = 'readonly'
                self.fields['target_views'].disabled = True

            else:
                self.fields['target_views'].widget.attrs.update({'min': 200000})
            
            # Disable target_clicks if the current value is less than or equal to 2000
            if instance.target_clicks <= 2000:
                self.fields['target_clicks'].widget.attrs['readonly'] = 'readonly'
                self.fields['target_clicks'].disabled = True
            
            else:
                 self.fields['target_clicks'].widget.attrs.update({'min': 2000})

            # pricing_model を変更不可にし、バリデーションを必須ではないように設定
            self.fields['pricing_model'].disabled = True
            self.fields['pricing_model'].required = False
            self.fields['pricing_model'].initial = instance.pricing_model


class AdInfoForm(forms.ModelForm):
    ad_campaign = forms.ModelChoiceField(queryset=AdCampaigns.objects.none(), label='Ad Campaign')  # Set to none initially

    class Meta:
        model = AdInfos
        fields = ['ad_campaign']

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.ismanga = kwargs.pop('ismanga', None)
        super(AdInfoForm, self).__init__(*args, **kwargs)
        if self.user:
            self.fields['ad_campaign'].queryset = AdCampaigns.objects.filter(created_by=self.user, is_hidden=False).order_by('-created_at')

    def save(self, *args, **kwargs):
        return super().save(*args, **kwargs)
    


class RequestDocumentForm(forms.ModelForm):
    class Meta:
        model = RequestDocument
        fields = ['company_name', 'email', 'address', 'phone_number']
        widgets = {
            'company_name': forms.TextInput(attrs={'placeholder': '社名を入力してください'}),
            'email': forms.EmailInput(attrs={'placeholder': 'メールアドレスを入力してください'}),
            'address': forms.Textarea(attrs={'placeholder': '住所を入力してください', 'rows': 2}),
            'phone_number': forms.TextInput(attrs={'placeholder': '電話番号を入力してください'}),
        }
        

class SetMeetingForm(forms.ModelForm):
    meeting_type = forms.ChoiceField(
        choices=SetMeeting.MEETING_CHOICES,
        widget=forms.RadioSelect,
        required=True,
    )
    
    class Meta:
        model = SetMeeting
        fields = [
            'company_name', 'address', 'phone_number', 'meeting_type', 'date_time_1', 'date_time_2', 'date_time_3',
            'date_time_4', 'date_time_5', 'email', 'x_account',
        ]
        widgets = {
            'date_time_1': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'date_time_2': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'date_time_3': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'date_time_4': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'date_time_5': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'address': forms.Textarea(attrs={'rows': 2}),
        }

    def clean(self):
        cleaned_data = super().clean()

        meeting_type = cleaned_data.get('meeting_type')
        company_name = cleaned_data.get('company_name')
        address = cleaned_data.get('address')
        phone_number = cleaned_data.get('phone_number')
        email = cleaned_data.get('email')
        x_account = cleaned_data.get('x_account')
        date_times = [
            cleaned_data.get('date_time_1'),
            cleaned_data.get('date_time_2'),
            cleaned_data.get('date_time_3'),
            cleaned_data.get('date_time_4'),
            cleaned_data.get('date_time_5'),
        ]

        # 社名、住所、電話番号のバリデーション
        if not company_name:
            self.add_error('company_name', '社名を入力してください。')
        if not address:
            self.add_error('address', '住所を入力してください。')
        if not phone_number:
            self.add_error('phone_number', '電話番号を入力してください。')

        # ミーティングタイプに基づいたバリデーション
        if meeting_type == 'zoom' or meeting_type == 'email':
            if not email:
                self.add_error('email', 'メールアドレスを入力してください。')
            
            # Zoomの場合のみ候補日のバリデーション
            if meeting_type == 'zoom':
                count_valid_dates = sum([1 for date_time in date_times if date_time])
                if count_valid_dates < 3:
                    self.add_error(None, '候補日は３つ以上設定してください。')
                    
        elif meeting_type == 'chat':
            if not x_account:
                self.add_error('x_account', 'IDを入力してください。')
                
class MonthSelectorForm(forms.Form):
    month_year = forms.DateField(
        label='年月を選択',
        widget=forms.SelectDateWidget(
            years=range(timezone.now().year - 5, timezone.now().year + 1),
            empty_label=("年を選択", "月を選択", None),
        )
    )
    
    def __init__(self, *args, **kwargs):
        super(MonthSelectorForm, self).__init__(*args, **kwargs)
        # 現在の日付を取得し、1日に設定
        initial_date = timezone.now().date().replace(day=1)
        # 先月に設定するために1日引く
        initial_date -= timezone.timedelta(days=1)
        # その後、再び1日に設定して先月の初日にする
        initial_date = initial_date.replace(day=1)
        
        # フォームの初期値を設定
        self.initial['month_year'] = initial_date
        self.fields['month_year'].widget = forms.SelectDateWidget(
            years=range(timezone.now().year - 1, timezone.now().year + 1),
            empty_label=("年を選択", "月を選択", None),
        )
