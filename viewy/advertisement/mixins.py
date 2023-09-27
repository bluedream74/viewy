from django.contrib.auth.mixins import UserPassesTestMixin
from django.urls import reverse_lazy

# is_advertiserかチェックする
class GroupOrSuperuserRequired(UserPassesTestMixin):
    group_name = None

    def test_func(self):
        # ユーザーがスーパーユーザーかチェック
        if self.request.user.is_superuser:
            return True

        # そうでなければ、ユーザーのis_advertiserであるかチェック
        return self.request.user.is_advertiser

    def get_login_url(self):
        return reverse_lazy('accounts:user_login') 