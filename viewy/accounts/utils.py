import boto3
from botocore.exceptions import BotoCoreError, ClientError
import random
import string

def send_email_ses(to_email, subject, body):
    client = boto3.client('ses', region_name="ap-northeast-1")  # リージョン名を東京のものに変更しました
    try:
        response = client.send_email(
            Source='regist@viewy.net',  # ここをviewy.netから送信する適切なメールアドレスに変更します
            Destination={
                'ToAddresses': [
                    to_email,
                ],
            },
            Message={
                'Subject': {
                    'Data': subject,
                    'Charset': 'UTF-8'
                },
                'Body': {
                    'Text': {
                        'Data': body,
                        'Charset': 'UTF-8'
                    },
                }
            }
        )
    except (BotoCoreError, ClientError) as error:
        print(error)
        return False

    return True


# ユーザー登録時にランダムな5桁の認証コードを生成
def generate_verification_code():
    return ''.join(random.choices(string.digits, k=5))
