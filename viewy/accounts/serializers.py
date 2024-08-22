from rest_framework import serializers
from .models import Users, GENDER_CHOICES

class RegisterSerializer(serializers.ModelSerializer):
  username = serializers.CharField(required=True)
  email = serializers.EmailField(required=True)
  password = serializers.CharField(required=True, min_length=8)
  gender = serializers.ChoiceField(choices=GENDER_CHOICES, required=True)

  class Meta:
    model = Users
    fields = '__all__'

  