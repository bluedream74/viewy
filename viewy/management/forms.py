from django import forms
from django.core.exceptions import ValidationError
from accounts.models import Users
from posts.models import RecommendedUser, Posts
from advertisement.models import AdCampaigns, AdInfos

class HashTagSearchForm(forms.Form):
    hashtag1 = forms.CharField(max_length=30, label=False, widget=forms.TextInput(attrs={'placeholder': 'ハッシュタグ１'}))
    hashtag2 = forms.CharField(max_length=30, label=False, widget=forms.TextInput(attrs={'placeholder': 'ハッシュタグ２'}))
    hashtag3 = forms.CharField(max_length=30, label=False, widget=forms.TextInput(attrs={'placeholder': 'ハッシュタグ３'}))
    hashtag4 = forms.CharField(max_length=30, label=False, widget=forms.TextInput(attrs={'placeholder': 'ハッシュタグ４'}))

class RecommendedUserForm(forms.Form):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for i in range(1, 13):
            self.fields[f'user{i}'] = forms.CharField(label=str(i), max_length=255)  # Change to CharField

    def clean(self):
        cleaned_data = super().clean()
        user_list = [cleaned_data.get(f"user{i}") for i in range(1, 13)]

        if len(user_list) != len(set(user_list)):
            raise forms.ValidationError("同じユーザーネームを重複して選択することはできません。")

        # Check if each username exists in the database
        for i, username in enumerate(user_list, start=1):
            if not Users.objects.filter(username=username).exists():
                self.add_error(f'user{i}', f"ユーザーネーム '{username}' は存在しません。")
    # Add an error for non-existing usernames

        return cleaned_data
    
    
class BoostTypeForm(forms.ModelForm):
    class Meta:
        model = Users
        fields = ['boost_type']
        
        
class AffiliateInfoForm(forms.ModelForm):
    ad_campaign = forms.ModelChoiceField(queryset=AdCampaigns.objects.none(), label='Ad Campaign')

    class Meta:
        model = AdInfos
        fields = ['ad_campaign']

    def __init__(self, *args, **kwargs):
        super(AffiliateInfoForm, self).__init__(*args, **kwargs)
        
        # affiliate@gmail.comのユーザーを取得
        affiliate_user = Users.objects.get(email='affiliate@gmail.com')
        
        # そのユーザーが作成したキャンペーンのみをフィルタリングして選択できるように設定
        self.fields['ad_campaign'].queryset = AdCampaigns.objects.filter(created_by=affiliate_user)
        
        
class AffiliateForm(forms.ModelForm):
    title = forms.CharField(label='タイトル', widget=forms.TextInput(attrs={'placeholder': 'タイトル（最大30字）'}))
    hashtag1 = forms.CharField(required=False, label='ハッシュタグ１', widget=forms.TextInput(attrs={'placeholder': '（最大20字）'}), error_messages={'max_length': "ハッシュタグは最大20字までです。",})
    hashtag2 = forms.CharField(required=False, label='ハッシュタグ２', widget=forms.TextInput(attrs={'placeholder': ''}), error_messages={'max_length': "ハッシュタグは最大20字までです。",})
    hashtag3 = forms.CharField(required=False, label='ハッシュタグ３', widget=forms.TextInput(attrs={'placeholder': ''}), error_messages={'max_length': "ハッシュタグは最大20字までです。",})
    caption = forms.CharField(required=False, label='説明欄', widget=forms.Textarea(attrs={'placeholder': 'キャプション（最大100字）'}))
    affiliate_tag = forms.CharField(
        required=False, 
        label='アフィリエイトタグ', 
        widget=forms.Textarea(attrs={'placeholder': 'アフィリエイトタグを入力'})  # ここを変更
    )

    class Meta:
        model = Posts
        fields = ['title', 'hashtag1', 'hashtag2', 'hashtag3', 'caption', 'affiliate_tag']
        
    def clean(self):
        cleaned_data = super().clean()
        title = cleaned_data.get('title')
        caption = cleaned_data.get('caption')
        
        # タイトルとキャプションの内容が重複する場合はエラー
        if title == caption:
            raise ValidationError("タイトルとキャプションの内容は重複できません。")
        
        # タイトルが2文字以下の場合はエラー
        if len(title) < 2:
            raise ValidationError("タイトルは2文字以上で入力してください。")
        
        return cleaned_data