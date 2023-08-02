from django import forms

class HashTagSearchForm(forms.Form):
    hashtag1 = forms.CharField(max_length=30, label=False, widget=forms.TextInput(attrs={'placeholder': 'ハッシュタグ１'}))
    hashtag2 = forms.CharField(max_length=30, label=False, widget=forms.TextInput(attrs={'placeholder': 'ハッシュタグ２'}))
    hashtag3 = forms.CharField(max_length=30, label=False, widget=forms.TextInput(attrs={'placeholder': 'ハッシュタグ３'}))
    hashtag4 = forms.CharField(max_length=30, label=False, widget=forms.TextInput(attrs={'placeholder': 'ハッシュタグ４'}))