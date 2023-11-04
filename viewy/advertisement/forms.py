from django import forms
from .models import AdCampaigns, AdInfos, RequestDocument, SetMeeting
from posts.models import Posts
from django.shortcuts import render
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import datetime, date

class AdCampaignForm(forms.ModelForm):
    PRICING_MODEL_CHOICES = [('CPC', 'CPC'), ('CPM', 'CPM')]

    pricing_model = forms.ChoiceField(
        choices=PRICING_MODEL_CHOICES,
        widget=forms.RadioSelect,  # ラジオボタンを使用
        label='Pricing Model'
    )

    target_views = forms.IntegerField(required=False)
    target_clicks = forms.IntegerField(required=False)


    end_date = forms.DateField(
        required=False,  # 必須ではなくする
        widget=forms.DateInput(attrs={
            'type': 'date', 
            'id': 'end-date-input'
        })
    )
    # budget = forms.DecimalField(
    # required=False,  # 初めては必須ではないと設定
    # widget=forms.NumberInput(attrs={
    #     'id': 'budget_input',
    #     'placeholder': '予算を入力してください',
    #     'min': '10000',
    #     'step': '10000',
    # })
    # )
    class Meta:
        model = AdCampaigns
        fields = ['title', 
        'start_date', 
        'end_date', 
        'andfeatures', 
        'pricing_model']
        widgets = {
            'start_date': forms.DateInput(attrs={
                'type': 'date', 
                'id': 'start-date-input',
                'min': date.today()  # 今日の日付をmin属性として設定
            }),
            'target_views': forms.NumberInput(attrs={
                'min': '10000',
                'step': '10000',
                'placeholder': '目標表示回数を入力'
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        title = cleaned_data.get('title')
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        pricing_model = cleaned_data.get('pricing_model')
        target_views = cleaned_data.get('target_views')
        target_clicks = cleaned_data.get('target_clicks')


        if pricing_model == 'CPC':
            if not target_clicks:
                self.add_error('target_clicks', ValidationError('CPCモデルの場合、クリック目標数は必須です'))
        elif pricing_model == 'CPM':
            if not target_views:
                self.add_error('target_views', ValidationError('CPMモデルの場合、表示目標数は必須です'))

        # Title validation
        if not title:
            self.add_error('title', ValidationError('キャンペーン名は必須です'))

        if start_date:
            # Ensure start_date is a date object for comparison
            start_date_as_date = start_date.date() if hasattr(start_date, 'date') else start_date
            if start_date_as_date < date.today(): 
                self.add_error('start_date', ValidationError('正しく開始日時を設定してください'))

        if end_date and start_date:
            # Ensure both dates are date objects for comparison
            end_date_as_date = end_date.date() if hasattr(end_date, 'date') else end_date
            start_date_as_date = start_date.date() if hasattr(start_date, 'date') else start_date
            if end_date_as_date <= start_date_as_date:
                self.add_error('end_date', ValidationError('正しく終了日時を設定してください'))

        # Target views validation
        if target_views and target_views <= 0:
            self.add_error('target_views', ValidationError('目標表示回数は正の値です'))

        return cleaned_data



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
            self.fields['ad_campaign'].queryset = AdCampaigns.objects.filter(created_by=self.user, is_hidden=False)

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
                
                
