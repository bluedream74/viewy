from django import forms
from .models import Posts, Videos
from django.core.exceptions import ValidationError

class PostForm(forms.ModelForm):
    title = forms.CharField(label='タイトル', widget=forms.TextInput(attrs={'placeholder': 'タイトル'}))
    hashtag1 = forms.CharField(required=False, label='ハッシュタグ１', widget=forms.TextInput(attrs={'placeholder': 'タグ'}), error_messages={'max_length': "ハッシュタグは最大30字までです。",})
    hashtag2 = forms.CharField(required=False, label='ハッシュタグ２', widget=forms.TextInput(attrs={'placeholder': ''}), error_messages={'max_length': "ハッシュタグは最大30字までです。",})
    hashtag3 = forms.CharField(required=False, label='ハッシュタグ３', widget=forms.TextInput(attrs={'placeholder': ''}), error_messages={'max_length': "ハッシュタグは最大30字までです。",})
    caption = forms.CharField(required=False, label='説明欄', widget=forms.Textarea(attrs={'placeholder': 'キャプション'}))
    url = forms.URLField(required=False, widget=forms.TextInput(attrs={'placeholder': 'URL'}), error_messages={'invalid': '有効なURLを入力してください。',})

    class Meta:
        model = Posts
        fields = ['title', 'hashtag1', 'hashtag2', 'hashtag3', 'caption', 'url']
        
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

    
class VisualForm(forms.Form):
    visuals = forms.ImageField(
        label="マンガ",
        widget=forms.ClearableFileInput(attrs={"allow_multiple_selected": True}), required=False
        )
    
    def clean_visuals(self):
        visuals = self.cleaned_data.get('visuals')
        # ここで任意のバリデーションを追加
        # 例えば、画像サイズが大きすぎる場合はエラー
        if visuals and visuals.size > 5 * 1024 * 1024:  # 5MBを超えるサイズはエラー
            raise ValidationError("Image file too large ( > 5mb )")
        return visuals


    
    
class VideoForm(forms.Form):
    video = forms.FileField(
        label="動画",
        widget=forms.ClearableFileInput(),
        # error_messages={
        #     'invalid': '動画を選択してください。',
        #     'missing': '動画を選択してください。',
        #     'empty': '動画を選択してください。',
        # }
        )

    class Meta:
        model = Videos
        fields = ['video']

    def clean_video(self):
        video = self.cleaned_data.get('video')
        # ここで任意のバリデーションを追加
        # ファイルのMIMEタイプをチェック
        main_type = video.content_type.split('/')[0]
        if not main_type == 'video':
            raise ValidationError("動画ファイルを選択してください。")
        # if video and video.duration > 60:  # 1分を超える長さはエラー
        #     raise ValidationError("動画は最大１分です")
        return video
    
    
    
class SearchForm(forms.Form):
    query = forms.CharField(
        max_length=100, 
        widget=forms.TextInput(attrs={'placeholder': '検索する', 'id': 'search'}),
        label=False,  # ラベルを非表示にする
        )
    