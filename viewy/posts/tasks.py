import time
from django.core.files.storage import default_storage
from celery import shared_task

@shared_task
def delayed_message():
    time.sleep(10)  # 10秒待機
    return "Hello, no waiting this time!"

@shared_task
def another_delayed_message(input_str):
    time.sleep(10)  # 10秒待機
    reversed_str = input_str[::-1]
    return reversed_str

@shared_task
def async_encode_video(video_id):
    from .models import Videos
    print("async_encode_video task started for video ID:", video_id)
    
    video = Videos.objects.get(id=video_id)
    original_video_path = video.video.name  # エンコード前の動画パスを保存
    
    try:
        video.encode_video()
        print("Video encoding completed for video ID:", video_id)
        
        if not video.thumbnail:
            video.create_thumbnail()
            print("Thumbnail creation completed for video ID:", video_id)

        video.encoding_done = True
        video.save()
        print("Video saved with encoding flag updated for video ID:", video_id)

    finally:
        # エンコード前の動画をS3から削除
        if default_storage.exists(original_video_path):
            default_storage.delete(original_video_path)
            print(f"Original video deleted from S3: {original_video_path}")