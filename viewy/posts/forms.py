from django import forms
from .models import Posts, Videos
from django.core.exceptions import ValidationError
from moviepy.editor import VideoFileClip
from django.core.files.uploadedfile import InMemoryUploadedFile, TemporaryUploadedFile
import tempfile
from multiupload.fields import MultiFileField

from moviepy.editor import VideoFileClip
from django.core.files.uploadedfile import InMemoryUploadedFile, TemporaryUploadedFile
import tempfile



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
    visuals = MultiFileField(
        min_num=1, 
        max_num=31, 
        max_file_size=1024*1024*5,  # 5MBを超えるサイズはエラー
        label="マンガ",
        required=False
    )
    
    def clean_visuals(self):
        visuals = self.cleaned_data.get('visuals')

        if visuals:
            for visual in visuals:
                if visual.size > 5 * 1024 * 1024:  # 5MBを超えるサイズはエラー
                    raise forms.ValidationError("Image file too large ( > 5mb )")
        return visuals


    
    
class VideoForm(forms.Form):
    video = forms.FileField(
        label="動画",
        widget=forms.ClearableFileInput(attrs={'accept': 'video/*'}),
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

        # 動画の長さをチェック
        # InMemoryUploadedFileかTemporaryUploadedFileか判別する
        # InMemoryUploadedFileは通常VideoFileClipを利用できないから変換
        if isinstance(video, InMemoryUploadedFile):
        # メモリ上のファイルの場合、一時的なファイルにデータを書き出す
            tmp_file = tempfile.NamedTemporaryFile(delete=False)  # delete=False を追加
            for chunk in video.chunks():
                tmp_file.write(chunk)
            tmp_file.close()  # ファイルをクローズ
            clip_path = tmp_file.name
        elif isinstance(video, TemporaryUploadedFile):
            clip_path = video.temporary_file_path()

        with VideoFileClip(clip_path) as clip:
            if clip.duration > 120:  # 動画が120秒より長い場合
                raise ValidationError('動画の最長の長さは2分までです。')
                
        if isinstance(video, InMemoryUploadedFile):
            tmp_file.close()

        return video
    
    
class SearchForm(forms.Form):
    query = forms.CharField(
        max_length=100, 
        widget=forms.TextInput(attrs={'placeholder': '検索する', 'id': 'search'}),
        label=False,  # ラベルを非表示にする
        )
    
    
# Masterユーザー用
class HashTagSearchForm(forms.Form):
    hashtag1 = forms.CharField(max_length=30, label=False, widget=forms.TextInput(attrs={'placeholder': 'ハッシュタグ１'}))
    hashtag2 = forms.CharField(max_length=30, label=False, widget=forms.TextInput(attrs={'placeholder': 'ハッシュタグ２'}))
    hashtag3 = forms.CharField(max_length=30, label=False, widget=forms.TextInput(attrs={'placeholder': 'ハッシュタグ３'}))
    hashtag4 = forms.CharField(max_length=30, label=False, widget=forms.TextInput(attrs={'placeholder': 'ハッシュタグ４'}))