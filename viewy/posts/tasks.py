import time
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
    from .models import Videos  # ここに入れることで循環インポートを解決
    print("async_encode_video task started for video ID:", video_id)
    
    video = Videos.objects.get(id=video_id)
    
    video.encode_video()
    print("Video encoding completed for video ID:", video_id)
    
    video.create_thumbnail()
    print("Thumbnail creation completed for video ID:", video_id)
    
    video.encoding_done = True
    video.save()
    print("Video saved with encoding flag updated for video ID:", video_id)