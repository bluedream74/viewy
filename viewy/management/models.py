from django.db import models


class UserStats(models.Model):
    date = models.DateField()
    total_users = models.PositiveIntegerField()
 
    def __str__(self):
      return self.date.strftime('%Y-%m-%d') + '  :  ' + str(self.total_users)
