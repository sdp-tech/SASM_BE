import unittest
from unittest.mock import patch

from django.test import TestCase, Client
from django.urls import reverse

from rest_framework import status

from users.models import User
from community.models import Board, Post, PostComment


class PostApiTests(TestCase):
    client = Client()

    @classmethod
    def setUpTestData(cls):
        
        cls.test_user = User.objects.create_superuser(
            email='test@test.test',
            nickname='test',
            password='test')

        cls.board = Board.objects.create(
            name="test board",
            supports_hashtags=True,
            supports_post_photos=True,
            supports_post_comment_photos=True,
            supports_post_comments=True)

        # cls.board2 = Board.objects.create(
        #     name="test board2",
        #     supports_hashtags=False,
        #     supports_post_photos=False,
        #     supports_post_comment_photos=False,
        #     supports_post_comments=False)

        cls.post = Post.objects.create(
            title="test post",
            content="this is a test post",
            board=cls.board,
            writer=cls.test_user)


    def test_post_create_api(self):

        path = reverse('post_create')
        data = {
            'board': 1,
            'title': 'Test Title',
            'content': 'Test Content'
        }

        self.client.force_login(user=self.test_user)
        response = self.client.post(path, data)

        # 응답코드 확인
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # 입력내용과 DB 저장내용의 일치 확인
        created_post = Post.objects.get(title='Test Title')
        self.assertEqual(created_post.content, 'Test Content')

        selected_board = Board.objects.get(id=1)
        self.assertEqual(created_post.board, selected_board)


    def test_post_update_api(self):

        path = reverse('post_update', kwargs={'post_id':1})
        data = {
            'title': 'Test Update Title',
            'content': 'Test Update Content'
        }

        self.client.force_login(user=self.test_user) # isWriter
        response = self.client.put(path, data, content_type='application/json')

        # 응답코드 확인
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # 입력내용과 DB 저장내용의 일치 확인
        updated_post = Post.objects.get(title='Test Update Title')
        self.assertEqual(updated_post.content, 'Test Update Content')


    def test_post_delete_api(self):

        path = reverse('post_delete', kwargs={'post_id':1})

        self.client.force_login(user=self.test_user) # isWriter
        response = self.client.delete(path, content_type='application/json')

        # 응답코드 확인
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # DB에서 post 개수 0 확인
        posts_cnt = Post.objects.count()
        self.assertEqual(posts_cnt, 0)        


    def test_post_list_api(self):

        path = reverse('post_list')
        data = {
            'board': 1,
            'latest': True
        }

        self.client.force_login(user=self.test_user)
        response = self.client.get(path, data)

        # 응답코드 확인
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # DB에서 post 개수와 일치 확인
        posts_cnt = Post.objects.count()
        self.assertEqual(response.data['data']['count'], posts_cnt)


    def test_post_detail_api(self):

        path = reverse('post_detail', kwargs={'post_id':1})

        self.client.force_login(user=self.test_user)
        response = self.client.get(path)

        # 응답코드 확인
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # 해당 post와 정보일치 확인
        selected_post = Post.objects.get(id=1)
        self.assertEqual(response.data['content'], selected_post.content)


class PostCommentListApiTests(TestCase):
    client = Client()

    @classmethod
    def setUpTestData(cls):
        
        cls.test_user = User.objects.create_superuser(
            email='test@test.test',
            nickname='test',
            password='test')

        cls.board = Board.objects.create(
            name="test board",
            supports_hashtags=True,
            supports_post_photos=True,
            supports_post_comment_photos=True,
            supports_post_comments=True)

        cls.post = Post.objects.create(
            title="test post",
            content="this is a test post",
            board=cls.board)

        cls.post_comment = PostComment.objects.create(
            post=cls.post,
            content="this is a test post comment",
            isParent=True,
            writer=cls.test_user)


    def test_post_comment_get_api(self):

        path = reverse('post_comment_list')
        self.client.force_login(user=self.test_user)
        response = self.client.get(path+'?post=1')
        
        # 응답코드 확인
        self.assertEqual(response.status_code, status.HTTP_200_OK)


    def test_post_comment_create_api(self):

        path = reverse('post_comment_create')
        data = {
            'post': 1,
            'content': 'Test Content',
            'isParent': True
        }

        self.client.force_login(user=self.test_user)
        response = self.client.post(path, data)

        # 응답코드 확인
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # 입력내용과 DB 저장내용의 일치 확인
        created_post_comment = PostComment.objects.get(id=2)
        self.assertEqual(created_post_comment.content, 'Test Content')

        selected_post = Post.objects.get(id=1)
        self.assertEqual(created_post_comment.post, selected_post)     


    def test_post_comment_update_api(self):

        path = reverse('post_comment_update', kwargs={'post_comment_id':1})
        data = {
            'content': 'Test Update Content'
        }

        self.client.force_login(user=self.test_user) # isWriter
        response = self.client.put(path, data, content_type='application/json')

        # 응답코드 확인
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # 입력내용과 DB 저장내용의 일치 확인
        updated_post_comment = PostComment.objects.get(id=1)
        self.assertEqual(updated_post_comment.content, 'Test Update Content')


    def test_post_comment_delete_api(self):

        path = reverse('post_comment_delete', kwargs={'post_comment_id':1})

        self.client.force_login(user=self.test_user) # isWriter
        response = self.client.delete(path, content_type='application/json')

        # 응답코드 확인
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # DB에서 post 개수 0 확인
        post_comments_cnt = PostComment.objects.count()
        self.assertEqual(post_comments_cnt, 0)   