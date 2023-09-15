from django.db import models
from posts.models import Posts
from accounts.models import Features


class AndFeatures(models.Model):
    orfeatures = models.ManyToManyField(Features)
    
    def __str__(self):
        return self.orfeatures


class AdInfos(models.Model):
    post = models.OneToOneField(Posts, on_delete=models.CASCADE)
    andfeatures = models.ManyToManyField(AndFeatures)
    
    def __str__(self):
      return self.post

