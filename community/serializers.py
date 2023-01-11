import io
import time
import datetime
from django.contrib.auth import get_user_model
from django.core.files.images import ImageFile
from rest_framework import serializers
from community.models import Board, Post, PostComment, PostCommentPhoto, PostReport, PostCommentReport
from users.models import User


class PostCommentSerializer(serializers.ModelSerializer):
    nickname = serializers.SerializerMethodField()
    email = serializers.SerializerMethodField()

    class Meta:
        model = PostComment
        ordering = ['id']
        fields = [
            'id',
            'post',
            'content',
            'isParent',
            'parent',
            'writer',
            'mention',
            'nickname',
            'email',
        ]

    def get_nickname(self, obj):
        return obj.writer.nickname

    def get_email(self, obj):
        return obj.writer.email
    
    def validate(self, data):
        if 'parent' in data:
            parent = data['parent']

            # child comment를 parent로 설정 시 reject
            if parent and not parent.isParent:
                raise serializers.ValidationError(
                    'can not set the child comment as parent comment')
            # parent가 null이 아닌데(자신이 child), isParent가 true인 경우 reject
            if parent is not None and data['isParent']:
                raise serializers.ValidationError(
                    'child comment has isParent value be false')
            # parent가 null인데(자신이 parent), isParent가 false인 경우 reject
            if data['parent'] is None and not data['isParent']:
                raise serializers.ValidationError(
                    'parent comment has isParent value be true')
        return data


class PostCommentPhotoSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = PostCommentPhoto
        fields = [
            'image'
        ]


class PostCommentCreateSerializer(PostCommentSerializer):
    photos = PostCommentPhotoSerializer(many=True, read_only=True)

    class Meta:
        model = PostComment
        ordering = ['id']
        fields = [
            'id',
            'post',
            'content',
            'isParent',
            'parent',
            'mention',
            'photos'
        ]
    
    def create(self, validated_data):
        comment = PostComment(**validated_data)
        comment.writer = self.context['request'].user
        comment.save()

        """ 사진 저장 """
        # 최대 장수 3장으로 가정
        photo_data = self.context['request'].FILES
        photos = photo_data.getlist('photo')

        if (len(photos) > 3):
            raise serializers.ValidationError()
        for photo in photos:
            ext = photo.name.split(".")[-1]
            file_path = '{}/{}.{}'.format(
                    comment.id,photos.index(photo)+1,ext)
            image = ImageFile(io.BytesIO(photo.read()), name=file_path)
            PostCommentPhoto.objects.create(comment=comment, image=image)
        return comment


class PostCommentUpdateSerializer(PostCommentSerializer):
    photos = PostCommentPhotoSerializer(many=True, read_only=True)

    class Meta:
        model = PostComment
        ordering = ['id']
        fields = [
            'id',
            'post',
            'content',
            'isParent',
            'parent',
            'mention',
            'photos'
        ]


class PostReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostReport
        ordering = ['id']
        fields = [
            'id',
            'post',
            'user',
            'category'           
        ]

    def create(self, validated_data):
        user = self.context['request'].user
        report = PostReport.objects.create(**validated_data, user=user)
        return report


class PostCommentReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostCommentReport
        ordering = ['id']
        fields = [
            'id',
            'comment',
            'user',
            'category'           
        ]