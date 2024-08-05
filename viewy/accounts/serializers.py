from rest_framework import serializers
from .models import Users

class RegisterSerializer(serializers.ModelSerializer):
  username = serializers.CharField(required=True, unique=True)
  email = serializers.EmailField(required=True, unique=True)
  password = serializers.CharField(required=True, min_length=8)
  gender = serializers.CharField(required=True)
  
  class Meta:
    model = Users
    fields = '__all__'

  