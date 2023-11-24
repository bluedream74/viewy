from django import forms
from .models import NormalInquiry, CorporateInquiry
from django.forms.widgets import DateTimeInput

class BaseInquiryForm(forms.Form):
    name = forms.CharField(max_length=100, label="氏名")
    email = forms.EmailField(label="メールアドレス")
    INQUIRY_CHOICES = [
        ('normal', 'Viewyに関して'),
        ('corporate', '法人様からのお問い合わせ'),
    ]
    inquiry_type = forms.ChoiceField(
        widget=forms.RadioSelect, 
        choices=INQUIRY_CHOICES, 
        label="お問い合わせ種類",
        initial='normal'
    )

class NormalInquiryForm(forms.ModelForm):
    normal_subject = forms.CharField(
        label="件名",
        max_length=100,
        widget=forms.TextInput(attrs={'id': 'normal_subject', 'name': 'normal_subject'})
    )
    normal_content = forms.CharField(
        label="お問い合わせ内容",
        widget=forms.Textarea(attrs={'id': 'normal_content', 'name': 'normal_content'}),
        max_length=2000
    )
    occurrence_date = forms.DateTimeField(
        input_formats=['%Y-%m-%d %H:%M'],
        label="お問い合わせ事項発生日時",
        widget=forms.DateTimeInput(attrs={
            'type': 'datetime-local', 
            'class': 'form-control' 
        })
    )

    DEVICE_CHOICES = [
        ('', '選択してください'),  # デフォルトの選択肢（空）
        ('windows', 'PC (Windows OS)'),
        ('mac', 'PC (Mac OS)'),
        ('iphone', 'スマートフォン (iPhone)'),
        ('android', 'スマートフォン (その他)'),
        ('ipad', 'タブレット (iPad)'),
        ('android_tablet', 'タブレット (その他)')
    ]

    device = forms.ChoiceField(
        choices=DEVICE_CHOICES,
        label="使用している端末",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    BROWSER_CHOICES = [
        ('', '選択してください'),  # デフォルトの選択肢（空）
        ('chrome', 'Google Chrome'),
        ('safari', 'Safari'),
        ('firefox', 'FireFox'),
        ('edge', 'Microsoft Edge'),
        ('other', 'その他')
    ]

    browser = forms.ChoiceField(
        choices=BROWSER_CHOICES,
        label="使用しているブラウザ",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        model = NormalInquiry
        fields = ['occurrence_date', 'occurrence_url', 'device', 'browser']

class CorporateInquiryForm(forms.ModelForm):
    corporate_subject = forms.CharField(
        label="件名", 
        max_length=100,
        widget=forms.TextInput(attrs={'id': 'corporate_subject', 'name': 'corporate_subject'})
    )
    corporate_content = forms.CharField(
        label="お問い合わせ内容", 
        max_length=2000,
        widget=forms.Textarea(attrs={'id': 'corporate_content', 'name': 'corporate_content'})
    )
    company_name = forms.CharField(
        label="会社名",
        max_length=100)
    department_name = forms.CharField(
        label="所属部署名",
        max_length=100, required=False)
    class Meta:
        model = CorporateInquiry
        fields = ['company_name', 'department_name']