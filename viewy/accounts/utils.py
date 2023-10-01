from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.contrib.auth import get_user_model
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes, force_str
from django.template.loader import render_to_string
from django.urls import reverse
from django.core.mail import send_mail
from accounts.models import Users
import random
import string

class CustomPasswordResetTokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, user, timestamp):
        return super()._make_hash_value(user, timestamp) + str(int(timestamp) + 5 * 60)  # 5分の有効期限

custom_token_generator = CustomPasswordResetTokenGenerator()

# ユーザー登録時にランダムな5桁の認証コードを生成
def generate_verification_code():
    return ''.join(random.choices(string.digits, k=5))

def send_email_ses(to_email, subject, body):
    send_mail(
        subject,
        body,
        'Viewy <regist@viewy.net>',  # From
        [to_email],  # To
        fail_silently=False,
    )



#ユーザーがパスワードリセットをリクエストした際にメールを送信します
def send_password_reset_email(email):
    user = Users.objects.get(email=email)
    uid = force_str(urlsafe_base64_encode(force_bytes(user.pk)))
    token = custom_token_generator.make_token(user)  # カスタムジェネレータを使用
    if user:
        reset_url = reverse('accounts:password_reset_confirm', kwargs={'uidb64': uid, 'token': token})
        full_reset_url = f'http://127.0.0.1:8000{reset_url}'
        subject = 'パスワードのリセット'
        message = render_to_string('password_reset_email.html', {'password_reset_link': full_reset_url})
        send_mail(subject, message, 'regist@viewy.net', [email], fail_silently=False)
        
        
def send_delete_request_notification(delete_request):
    """
    削除依頼が送信された際に通知メールを送る関数。
    
    :param delete_request: DeleteRequestモデルのインスタンス。
    """
    subject = '削除依頼が送信されました'
    message = f"新しい削除依頼が送信されました。\n\n詳細:\n\n依頼者: {delete_request.email}\n対象パートナー: {delete_request.postername}\n対象の投稿のタイトル: {delete_request.post_title}\nケースの種類: {delete_request.case_type}\n詳細: {delete_request.details}"
    from_email = 'Viewy投稿削除依頼 <delete-request@viewy.net>'
    recipient_list = ['support@viewy.net']

    send_mail(subject, message, from_email, recipient_list)
