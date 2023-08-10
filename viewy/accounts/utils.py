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
        'regist@viewy.net',  # From
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
