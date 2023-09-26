from django import forms
from django.core.exceptions import ValidationError
from accounts.models import Users
from posts.models import RecommendedUser

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