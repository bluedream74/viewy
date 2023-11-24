from django.contrib import admin
from .models import (
  NormalInquiry, CorporateInquiry
)

admin.site.register(
  [NormalInquiry, CorporateInquiry]
)