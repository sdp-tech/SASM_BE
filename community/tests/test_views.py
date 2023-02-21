import re
import unittest
from unittest.mock import patch

from django.test import TestCase, Client
from django.urls import reverse
from django.test.client import MULTIPART_CONTENT, encode_multipart, BOUNDARY

from rest_framework import status

from users.models import User
from community.models import Board, Post, PostComment, PostHashtag, PostPhoto
from community.factories import BoardFactory, BoardSupportingAllFunctionsFactory, PostFactory, PostCommentFactory, UserDictFactory, CreatePostHavingOnlyRequiredFieldsDictFactory, CreatePostHavingOptionalFieldsDictFactory, CreatePostLackingRequiredFieldsDictFactory, PostListDictFactory, UpdatePostHavingOptionalFieldsDictFactory, PostCommentHavingOnlyRequiredFieldsDictFactory, PostCommentLackingRequiredFieldsDictFactory


class PostApiTests(TestCase):
    client = Client()

    @classmethod
    def setUpTestData(cls):

        # create superuser
        test_user_data = UserDictFactory()
        cls.test_user = User.objects.create_superuser(
            email = test_user_data['email'],
            password = test_user_data['password'],
            nickname = test_user_data['nickname']
        )

        cls.board = BoardSupportingAllFunctionsFactory()
        cls.post = PostFactory(writer=cls.test_user, board=cls.board)


    def test_post_create_api(self):

        obj_cnt_before = Post.objects.count()
        
        path = reverse('post_create')
        self.client.force_login(user=self.test_user)
        data = CreatePostHavingOptionalFieldsDictFactory()
        response = self.client.post(path, data)
        
        obj_cnt_after = Post.objects.count()

        # 응답코드
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # 생성
        self.assertEqual(obj_cnt_after, obj_cnt_before + 1)

        # 내용 일치
        created_post = Post.objects.order_by('-created').first()
        board = Board.objects.get(id=data['board'])
        self.assertEqual(created_post.board, board)
        self.assertEqual(created_post.title, data['title'])
        self.assertEqual(created_post.content, data['content'])

        # Optional field 저장 확인
        if data['hashtagList']:
            hashtags_in_db = []
            for i in PostHashtag.objects.filter(post=created_post).values('name'):
                hashtags_in_db.append(i['name'])

            for j in data['hashtagList']:
                self.assertTrue(j in hashtags_in_db)

        if data['imageList']:
            images_in_db = []
            for i in PostPhoto.objects.filter(post=created_post).values('image'):
                images_in_db.append(re.split('[.]', i['image'])[2]) # image name 추출
        
            for j in data['imageList']:
                self.assertTrue(j.name in images_in_db)


    def test_post_create_api_errors(self):

        # 필수 필드 누락
        path = reverse('post_create')
        self.client.force_login(user=self.test_user)
        data = CreatePostLackingRequiredFieldsDictFactory()
        response = self.client.post(path, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


    def test_post_update_api(self):

        obj_cnt_before = Post.objects.count()

        # get a post created by superuser
        post_id = Post.objects.get(writer_id=1).id
        path = reverse('post_update', kwargs={'post_id': post_id})
        data = UpdatePostHavingOptionalFieldsDictFactory()
        self.client.force_login(user=self.test_user) # isWriter
        response = self.client.put(path,
                                    data = encode_multipart(data = data, boundary=BOUNDARY),
                                    content_type= MULTIPART_CONTENT)
        
        obj_cnt_after = Post.objects.count()
        
        # 응답코드
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # row count 유지
        self.assertEqual(obj_cnt_after, obj_cnt_before)

        # 내용 일치
        updated_post = Post.objects.order_by('-updated').first()
        self.assertEqual(updated_post.title, data['title'])
        self.assertEqual(updated_post.content, data['content'])

        # Optional field 저장 확인
        if data['hashtagList']:
            hashtags_in_db = []
            for i in PostHashtag.objects.filter(post=updated_post).values('name'):
                hashtags_in_db.append(i['name'])

            for j in data['hashtagList']:
                self.assertTrue(j in hashtags_in_db)

        if data['imageList']:
            images_in_db = []
            for i in PostPhoto.objects.filter(post=updated_post).values('image'):
                images_in_db.append(re.split('[.]', i['image'])[2]) # image name 추출
        
            for j in data['imageList']:
                self.assertTrue(j.name in images_in_db)


    def test_post_delete_api(self):

        obj_cnt_before = Post.objects.count()

        # get a post created by superuser
        post_id = Post.objects.get(writer_id=1).id
        path = reverse('post_delete', kwargs={'post_id': post_id})
        self.client.force_login(user=self.test_user) # isWriter
        response = self.client.delete(path, content_type='application/json')

        obj_cnt_after = Post.objects.count()

        # 응답코드
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 삭제
        self.assertEqual(obj_cnt_after, obj_cnt_before - 1)


    def test_post_list_api(self):

        path = reverse('post_list')
        data = PostListDictFactory()
        board = Board.objects.get(id=1) # TODO : set random board using Faker
        PostFactory.create_batch(5, board=board) # board 1에 post 5개 생성
        self.client.force_login(user=self.test_user)
        response = self.client.get(path, data)

        # 응답코드
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 조회 건수와 DB post 개수 일치 확인
        posts_cnt = Post.objects.filter(board=board).count()
        self.assertEqual(response.data['data']['count'], posts_cnt)


    def test_post_detail_api(self):

        path = reverse('post_detail', kwargs={'post_id':1}) # TODO : set random post_id
        self.client.force_login(user=self.test_user)
        response = self.client.get(path)

        # 응답코드
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 내용 일치
        post = Post.objects.get(id=1)
        self.assertEqual(response.data['title'], post.title)
        self.assertEqual(response.data['content'], post.content)
        self.assertEqual(response.data['board'], post.board_id)
        self.assertEqual(User.objects.get(email=response.data['email']).id, post.writer_id)
        self.assertEqual(response.data['likeCount'], post.like_cnt)
        self.assertEqual(response.data['viewCount'], post.view_cnt)


class PostCommentApiTests(TestCase):
    client = Client()

    @classmethod
    def setUpTestData(cls):

        # create superuser
        test_user_data = UserDictFactory()
        cls.test_user = User.objects.create_superuser(
            email = test_user_data['email'],
            password = test_user_data['password'],
            nickname = test_user_data['nickname']
        )
        
        cls.board = BoardSupportingAllFunctionsFactory()
        cls.post = PostFactory(writer=cls.test_user, board=cls.board)
        cls.post_comment = PostCommentFactory(writer=cls.test_user, post=cls.post)


    def test_post_comment_get_api(self):

        post = Post.objects.get(id=1) # TODO : set random post using Faker
        PostCommentFactory.create_batch(5, post=post) # post 1에 comment 5개 생성

        path = reverse('post_comment_list')
        self.client.force_login(user=self.test_user)
        response = self.client.get(path+'?post=1')

        # 응답코드
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 조회 건수와 DB post 개수 일치 확인
        post_comments_cnt = PostComment.objects.filter(post=post).count()
        self.assertEqual(response.data['data']['count'], post_comments_cnt)


    def test_post_comment_create_api(self):
        
        obj_cnt_before = PostComment.objects.count()

        path = reverse('post_comment_create')
        data = PostCommentHavingOnlyRequiredFieldsDictFactory()
        self.client.force_login(user=self.test_user)
        response = self.client.post(path, data)
        obj_cnt_after = PostComment.objects.count()

        # 응답코드
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # 생성
        self.assertEqual(obj_cnt_after, obj_cnt_before + 1)

        # 내용 일치
        created_post_comment = PostComment.objects.order_by('-created').first()
        post = Post.objects.get(id=1)
        self.assertEqual(created_post_comment.post, post)
        self.assertEqual(created_post_comment.content, data['content'])
        self.assertEqual(created_post_comment.isParent, data['isParent'])


    def test_post_comment_create_api_errors(self):

        # 필수 필드 누락
        path = reverse('post_comment_create')
        self.client.force_login(user=self.test_user)
        data = PostCommentLackingRequiredFieldsDictFactory()
        response = self.client.post(path, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


    def test_post_comment_update_api(self):

        obj_cnt_before = PostComment.objects.count()

        # get a post comment created by superuser
        post_comment_id = PostComment.objects.get(writer_id=1).id
        path = reverse('post_comment_update', kwargs={'post_comment_id': post_comment_id})
        data = PostCommentHavingOnlyRequiredFieldsDictFactory()
        self.client.force_login(user=self.test_user) # isWriter
        response = self.client.put(path, data, content_type='application/json')
        obj_cnt_after = PostComment.objects.count()


        # 응답코드 확인
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # row count 유지
        self.assertEqual(obj_cnt_after, obj_cnt_before)

        # 내용 일치
        updated_post_comment = PostComment.objects.order_by('-updated').first()
        self.assertEqual(updated_post_comment.content, data['content'])


    def test_post_comment_delete_api(self):

        obj_cnt_before = PostComment.objects.count()

        # get a post comment created by superuser
        post_comment_id = PostComment.objects.get(writer_id=1).id
        path = reverse('post_comment_delete', kwargs={'post_comment_id': post_comment_id})
        self.client.force_login(user=self.test_user) # isWriter
        response = self.client.delete(path, content_type='application/json')

        obj_cnt_after = PostComment.objects.count()

        # 응답코드 확인
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 삭제
        self.assertEqual(obj_cnt_after, obj_cnt_before - 1)