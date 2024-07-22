import boto3
import json
from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from django.utils import timezone
from django.conf import settings

# Configure Boto3
s3 = boto3.client(
  's3',
  aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
  aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
  region_name=settings.AWS_S3_REGION_NAME
)
BUCKET_NAME = settings.AWS_LOGIN_LOG_BUCKET_NAME

@receiver(user_logged_in)
def log_login(sender, request, user, **kwargs):
    log_entry = {
        'email': user.email,
        'timestamp': timezone.now().isoformat(),
        'ip_address': request.META.get('REMOTE_ADDR'),
        'user_agent': request.META.get('HTTP_USER_AGENT')
    }
    log_data = json.dumps(log_entry)
    
    file_name = f"login-logs/{user.email}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    s3.put_object(
        Bucket=BUCKET_NAME,
        Key=file_name,
        Body=log_data,
        ContentType='application/json'
    )
