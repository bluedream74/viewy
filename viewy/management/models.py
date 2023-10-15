from django.db import models
import datetime


class UserStats(models.Model):
    date = models.DateField()
    total_users = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.date.strftime('%Y-%m-%d') + '  :  ' + str(self.total_users)

    def save(self, *args, **kwargs):
        # If this is a new record...
        if not self.pk:
            # Try to get the record from yesterday
            yesterday = self.date - datetime.timedelta(days=1)
            try:
                yesterday_record = UserStats.objects.get(date=yesterday)
                self.total_users = yesterday_record.total_users
            except UserStats.DoesNotExist:
                pass  # If there is no record from yesterday, we will use the default value (0)

        super().save(*args, **kwargs)  # Call the "real" save() method
        

class ClickCount(models.Model):
    name = models.CharField(max_length=200, unique=True)
    count = models.IntegerField(default=0)

    def __str__(self):
        return self.name
    

class SupportRate(models.Model):
    name = models.CharField(max_length=255)  # 変数名を保存するためのフィールド
    value = models.DecimalField(max_digits=10, decimal_places=3)  # 小数点を保存するためのフィールド

    def __str__(self):
        return f"{self.name}: {self.value}"