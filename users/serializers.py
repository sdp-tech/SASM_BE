from django.contrib.auth import get_user_model
from rest_framework import serializers
from .models import User
from .utils import (
    email_isvalid, 
    username_isvalid,
)
class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "password",
            "gender",
            "nickname",
            "birthdate",
            "email",
            "address",
        )
        read_only_fields = ("id",)

    def validate_email(self, obj):
        if email_isvalid(obj):
            return obj
        raise serializers.ValidationError('메일 형식이 올바르지 않습니다.')


    def validate_username(self, obj):
        if username_isvalid(obj):
            return obj
        raise serializers.ValidationError('닉네임은 한 글자 이상이어야 합니다.')

    def create(self, validated_data):
        #password = validated_data.get("password")
        user = super().create(validated_data)
        user.set_password(validated_data["password"])
        user.save()
        return user