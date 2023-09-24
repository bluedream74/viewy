from django.contrib.auth.mixins import UserPassesTestMixin
from django.urls import reverse_lazy

# Advertiserかチェックする
class GroupOrSuperuserRequired(UserPassesTestMixin):
    group_name = None

    def test_func(self):
        # ユーザーがスーパーユーザーかチェック
        if self.request.user.is_superuser:
            return True

        # そうでなければ、ユーザーが指定したグループに属しているかチェック
        if self.group_name:
            return self.request.user.groups.filter(name=self.group_name).exists()
        
        return False

    def get_login_url(self):
        return reverse_lazy('accounts:user_login') 