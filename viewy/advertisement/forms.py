from django import forms
from .models import AdCampaigns, AdInfos
from posts.models import Posts

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