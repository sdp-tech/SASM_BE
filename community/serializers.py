import io
import time
import datetime
from django.contrib.auth import get_user_model
from django.core.files.images import ImageFile
from rest_framework import serializers
from community.models import Board, Post, PostPhoto, PostHashtag, PostComment, PostCommentPhoto, PostReport, PostCommentReport
from users.models import User

class PostPhotoSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = PostPhoto
        fields = [
            'image'
        ]


class PostHashtagSerializer(serializers.ModelSerializer):

    class Meta:
        model = PostHashtag
        fields = [
            'name',
        ]


class BoardSerializer(serializers.ModelSerializer):
   
    class Meta:
        model = Board
        fields = [
            'name',
        ]

class PostListSerializer(serializers.ModelSerializer):
    nickname = serializers.SerializerMethodField()
    hashtag = PostHashtagSerializer(many=True, read_only=True)

    class Meta:
        model = Post
        fields = [
            'id',
            'title',
            'content',
            'like_cnt',
            'comment_cnt',
            'board',
            # 'post_like',
            'nickname',
            'hashtag',
            'created',
            'updated',
        ]
    
    def get_nickname(self, obj):
        return obj.writer.nickname
    
    def to_representation(self, instance):
        response = super().to_representation(instance)
        response['board'] = BoardSerializer(instance.board).data
        print('123', response)
        return response




class PostDetailSerializer(serializers.ModelSerializer):
    post_like = serializers.SerializerMethodField()
    nickname = serializers.SerializerMethodField()
    post_photos = PostPhotoSerializer(many=True, read_only=True)
    hashtag = PostHashtagSerializer(many=True, read_only=True)

    class Meta:
        model = Post
        fields = [
            'id',
            'title',
            'content',
            'board',
            'like_cnt',
            'view_cnt',
            'comment_cnt',
            'post_photos',
            'hashtag',
            'post_like',
            'nickname',
            'created',
            'updated',
        ]

    def get_nickname(self, obj):
        return obj.writer.nickname
    
    def to_representation(self, instance):
        response =  super().to_representation(instance)
        response['board'] = BoardSerializer(instance.board).data
        print(response)
        return response

    def get_post_like(self, obj):
        '''
            게시글의 좋아요 여부를 알려주기 위한 함수
        '''
        print("like")
        re_user = self.context['request'].user.id
        if obj.post_likeuser_set.filter(id=re_user).exists():
            return 'ok'
        else:
            return 'none'

    # 댓글 개수 세기 필요
    # def count_comment(self, comment)

    def create(self, validated_data):
        print('create')
        post = Post(**validated_data)
        post.writer = self.context['request'].user
        print(post.writer)
        post.save()

        #사진 최대 10개
        post_photos_data = self.context['request'].FILES
        post_photos = post_photos_data.getlist('post_photos')
        count_photo = len(post_photos)
        if (count_photo > 10):
            raise serializers.ValidationError()
        for post_photo_data in post_photos:
            # 파일 경로 설정
            ext = post_photo_data.name.split(".")[-1]
            file_path = '{}/{}.{}'.format(post.id, str(datetime.datetime.now()),ext)
            image = ImageFile(io.BytesIO(post_photo_data.read()), name=file_path)
            PostPhoto.objects.create(post=post, image=image)
            print(post_photos)

        #해시태그 최대 5개
        hashtags_data = self.context['request'].POST.getlist('hashtag')[0].split(' ')
        print(hashtags_data)
        count_hashtag = len(hashtags_data)
        print(count_hashtag)
        if (count_hashtag > 5):
            raise serializers.ValidationError()
        # for hashtag_data in 

        print(post)
        return post

    def update(self, instance, validated_data):
        print('update')
        # instance = Post(**validated_data)
        # instance.save()

        #사진 최대 10개
        post_photos_data = self.context['request'].FILES
        post_photos = post_photos_data.getlist('post_photos')
        count_photo = len(post_photos)
        if (count_photo > 10):
            raise serializers.ValidationError()
        for post_photo_data in post_photos:
            # 파일 경로 설정
            ext = post_photo_data.name.split(".")[-1]
            file_path = '{}/{}.{}'.format(instance.id, str(datetime.datetime.now()),ext)
            image = ImageFile(io.BytesIO(post_photo_data.read()), name=file_path)
            PostPhoto.objects.create(post=instance, image=image)
            print(post_photos)

        #해시태그 최대 5개
        hashtags_data = self.context['request'].POST.getlist('hashtag')[0].split(' ')
        print(hashtags_data)
        count_hashtag = len(hashtags_data)
        print(count_hashtag)
        if (count_hashtag > 5):
            raise serializers.ValidationError()

        return instance

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