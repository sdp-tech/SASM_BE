from django.contrib.auth import get_user_model
from rest_framework import serializers
from users import models as user_models
from .utils import (
    email_isvalid, 
    password_isvalid, 
    username_isvalid,
    hash_password,
    check_password,
)
class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    class Meta:
        model = user_models
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
        read_only_fields = ("id")

    def validate_email(self, obj):
        if email_isvalid(obj):
            return obj
        raise serializers.ValidationError('메일 형식이 올바르지 않습니다.')

    def validate_password(self, obj):
        if password_isvalid(obj):
            return hash_password(obj)
        raise serializers.ValidationError("비밀번호는 8 자리 이상이어야 합니다.")

    def validate_username(self, obj):
        if username_isvalid(obj):
            return obj
        raise serializers.ValidationError('닉네임은 한 글자 이상이어야 합니다.')

    def update(self, obj, validated_data):
        obj.email = validated_data.get('email', obj.email)
        obj.username = validated_data.get('username', obj.username)
        obj.password = hash_password(validated_data.get('password', obj.password))
        obj.save()
        return obj