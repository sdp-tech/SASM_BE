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
        available_photo_key = ['photo1', 'photo2', 'photo3']
        all_photos = self.context['request'].FILES
        photo_key = all_photos.keys()

        for p in available_photo_key:
            if p in photo_key:
                # photo key가 중복으로 들어올 때 첫번째 파일만 취급
                photo_file = all_photos.getlist(p)[0]
                ext = photo_file.name.split(".")[-1]
                file_path = '{}/{}.{}'.format(comment.id,p.strip()[-1],ext)
                image = ImageFile(io.BytesIO(photo_file.read()), name=file_path)
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
    
    def update(self, instance, validated_data):
        """ 사진 수정 """
        # 최대 장수 3장으로 가정
        available_photo_key = ['photo1', 'photo2', 'photo3']
        all_photos = self.context['request'].FILES
        photo_key = all_photos.keys()

        for p in available_photo_key:
            if p in photo_key:
                # photo key가 중복으로 들어올 때 첫번째 파일만 취급
                photo_file = all_photos.getlist(p)[0]
                ext = photo_file.name.split(".")[-1]
                file_path = '{}/{}.{}'.format(instance.id,p.strip()[-1],ext)
                image = ImageFile(io.BytesIO(photo_file.read()), name=file_path)
                PostCommentPhoto.objects.create(comment=instance, image=image)
        return instance


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


class PostReportCreateSerializer(serializers.ModelSerializer):
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


class PostCommentReportCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostCommentReport
        ordering = ['id']
        fields = [
            'id',
            'comment',
            'user',
            'category'           
        ]    
    def create(self, validated_data):
        reported_post_comment = PostCommentReport(**validated_data)
        reported_post_comment.user = self.context['request'].user
        reported_post_comment.save()
        return reported_post_comment