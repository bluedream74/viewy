from django.db.models.signals import pre_delete
from django.dispatch import receiver
from django.core.files.storage import default_storage as storage
from .models import Videos
from .models import Visuals

@receiver(pre_delete, sender=Videos)
def delete_video_and_thumbnail_on_delete(sender, instance, **kwargs):
    if instance.video:
        storage.delete(instance.video.name)
    if instance.thumbnail:
        storage.delete(instance.thumbnail.name)
        
        
@receiver(pre_delete, sender=Visuals)
def delete_visual_on_delete(sender, instance, **kwargs):
    if instance.visual:
        storage.delete(instance.visual.name)
