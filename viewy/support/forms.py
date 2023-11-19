from django import forms
from .models import NormalInquiry, CorporateInquiry

class BaseInquiryForm(forms.Form):
    name = forms.CharField(max_length=100, label="氏名")
    email = forms.EmailField(label="メールアドレス")
    INQUIRY_CHOICES = [
        ('normal', '一般'),
        ('corporate', '法人'),
    ]
    inquiry_type = forms.ChoiceField(widget=forms.RadioSelect, choices=INQUIRY_CHOICES, label="お問い合わせ種類")

class NormalInquiryForm(forms.ModelForm):
    class Meta:
        model = NormalInquiry
        fields = ['subject', 'occurrence_date', 'occurrence_url', 'device', 'browser', 'content']

class CorporateInquiryForm(forms.ModelForm):
    class Meta:
        model = CorporateInquiry
        fields = ['company_name', 'department_name', 'subject', 'content']