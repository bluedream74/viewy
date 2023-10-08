from django import forms
from .models import AdCampaigns, AdInfos, RequestDocument, SetMeeting
from posts.models import Posts
from django.shortcuts import render
from django.core.exceptions import ValidationError


class AdCampaignForm(forms.ModelForm):
    class Meta:
        model = AdCampaigns
        fields = ['title', 'start_date', 'end_date', 'budget', 'andfeatures']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date', 'id': 'start-date-input'}),
            'end_date': forms.DateInput(attrs={'type': 'date', 'id': 'end-date-input'}),
            'budget': forms.NumberInput(attrs={
                'min': '1000', 
                'step': '1000', 
                'placeholder': '1000円単位で入力'}),
        }



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
            self.fields['ad_campaign'].queryset = AdCampaigns.objects.filter(created_by=self.user)

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
                
                
