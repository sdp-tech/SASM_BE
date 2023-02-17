import unittest
from unittest.mock import patch

from django.test import TestCase, Client
from django.urls import reverse

from rest_framework import status

from users.models import User
from community.models import Board, Post, PostComment
from community.factories import BoardFactory, PostFactory, PostCommentFactory


class PostApiTests(TestCase):
    client = Client()

    @classmethod
    def setUpTestData(cls):

        # cls.test_user = UserFactory()
        cls.test_user = User.objects.create_superuser(
            email='test@test.com',
            nickname='test',
            password='test')
        
        cls.board = BoardFactory()
        cls.post = PostFactory(writer=cls.test_user)


    def test_post_create_api(self):
        obj_cnt_before = Post.objects.count()
        
        path = reverse('post_create')
        data = {
            'board': 1,
            'title': 'Test Title',
            'content': 'Test Content'
        }
        self.client.force_login(user=self.test_user)
        response = self.client.post(path, data)
        
        obj_cnt_after = Post.objects.count()


        # 응답코드
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # 생성
        self.assertEqual(obj_cnt_after, obj_cnt_before + 1)

        # 필요한 필드 포함
        created_post = Post.objects.order_by('-created').first()
        created_post_qs = Post.objects.filter(id=created_post.id)
        created_post_field_list = list(created_post_qs.values()[0].keys())
        required_fields = ['title',
                           'content',
                           'board_id',
                           'writer_id',
                           'like_cnt',
                           'view_cnt',
                           'comment_cnt']

        for field in required_fields:
            self.assertTrue(field in created_post_field_list)

        # 내용 일치
        selected_board = Board.objects.get(id=1)
        self.assertEqual(created_post.board, selected_board)
        self.assertEqual(created_post.title , 'Test Title')
        self.assertEqual(created_post.content, 'Test Content')


    def test_post_update_api(self):
        obj_cnt_before = Post.objects.count()

        path = reverse('post_update', kwargs={'post_id':1})
        data = {
            'title': 'Test Update Title',
            'content': 'Test Update Content'
        }
        self.client.force_login(user=self.test_user) # isWriter
        response = self.client.put(path, data, content_type='application/json')

        obj_cnt_after = Post.objects.count()

        # 응답코드
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # row count 유지
        self.assertEqual(obj_cnt_after, obj_cnt_before)

        # 필요한 필드 포함
        updated_post = Post.objects.order_by('-updated').first()
        updated_post_qs = Post.objects.filter(id=updated_post.id)
        updated_post_field_list = list(updated_post_qs.values()[0].keys())
        required_fields = ['title',
                           'content',
                           'board_id',
                           'writer_id',
                           'like_cnt',
                           'view_cnt',
                           'comment_cnt']

        for field in required_fields:
            self.assertTrue(field in updated_post_field_list)

        # 내용 일치
        self.assertEqual(updated_post.title, 'Test Update Title')
        self.assertEqual(updated_post.content, 'Test Update Content')


    def test_post_delete_api(self):

        obj_cnt_before = Post.objects.count()

        path = reverse('post_delete', kwargs={'post_id':1})
        self.client.force_login(user=self.test_user) # isWriter
        response = self.client.delete(path, content_type='application/json')

        obj_cnt_after = Post.objects.count()

        # 응답코드
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 삭제
        self.assertEqual(obj_cnt_after, obj_cnt_before - 1)


    def test_post_list_api(self):

        path = reverse('post_list')
        data = {
            'board': 1,
            'latest': True
        }
        selected_board = Board.objects.get(id=1)
        PostFactory.create_batch(5, board=selected_board) # board 1에 post 5개 생성
        self.client.force_login(user=self.test_user)
        response = self.client.get(path, data)

        # 응답코드
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 조회 건수와 DB post 개수 일치 확인
        posts_cnt = Post.objects.filter(board=selected_board).count()
        self.assertEqual(response.data['data']['count'], posts_cnt)


    def test_post_detail_api(self):

        path = reverse('post_detail', kwargs={'post_id':1})
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


class PostCommentListApiTests(TestCase):
    client = Client()

    @classmethod
    def setUpTestData(cls):

        # cls.test_user = UserFactory()
        cls.test_user = User.objects.create_superuser(
            email='test@test.com',
            nickname='test',
            password='test')
        
        cls.board = BoardFactory()
        cls.post = PostFactory(writer=cls.test_user)
        cls.post_comment = PostCommentFactory(writer=cls.test_user)


    def test_post_comment_get_api(self):

        selected_post = Post.objects.get(id=1)
        PostCommentFactory.create_batch(5, post=selected_post) # post 1에 comment 5개 생성

        path = reverse('post_comment_list')
        self.client.force_login(user=self.test_user)
        response = self.client.get(path+'?post=1')

        # 응답코드
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 조회 건수와 DB post 개수 일치 확인
        post_comments_cnt = PostComment.objects.filter(post=selected_post).count()
        self.assertEqual(response.data['data']['count'], post_comments_cnt)


    def test_post_comment_create_api(self):

        obj_cnt_before = PostComment.objects.count()

        path = reverse('post_comment_create')
        data = {
            'post': 1,
            'content': 'Test Content',
            'isParent': True
        }
        self.client.force_login(user=self.test_user)
        response = self.client.post(path, data)
        obj_cnt_after = PostComment.objects.count()

        # 응답코드
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # 생성
        self.assertEqual(obj_cnt_after, obj_cnt_before + 1)

        # 필요한 필드 포함
        created_post_comment = PostComment.objects.order_by('-created').first()
        created_post_comment_qs = PostComment.objects.filter(id=created_post_comment.id)
        created_post_comment_field_list = list(created_post_comment_qs.values()[0].keys())
        required_fields = ['post_id',
                           'content',
                           'isParent',
                           'parent_id',
                           'writer_id']

        for field in required_fields:
            self.assertTrue(field in created_post_comment_field_list)

        # 내용 일치
        post = Post.objects.get(id=1)
        self.assertEqual(created_post_comment.post, post)
        self.assertEqual(created_post_comment.content, 'Test Content')
        self.assertEqual(created_post_comment.isParent, True)


    def test_post_comment_update_api(self):

        obj_cnt_before = PostComment.objects.count()

        path = reverse('post_comment_update', kwargs={'post_comment_id':2})
        data = {
            'content': 'Test Update Content'
        }
        self.client.force_login(user=self.test_user) # isWriter
        response = self.client.put(path, data, content_type='application/json')

        obj_cnt_after = PostComment.objects.count()


        # 응답코드 확인
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # row count 유지
        self.assertEqual(obj_cnt_after, obj_cnt_before)

        # 필요한 필드 포함
        updated_post_comment = PostComment.objects.order_by('-updated').first()
        updated_post_comment_qs = PostComment.objects.filter(id=updated_post_comment.id)
        updated_post_comment_field_list = list(updated_post_comment_qs.values()[0].keys())
        required_fields = ['post_id',
                           'content',
                           'isParent',
                           'parent_id',
                           'writer_id']

        for field in required_fields:
            self.assertTrue(field in updated_post_comment_field_list)

        # 내용 일치
        self.assertEqual(updated_post_comment.content, 'Test Update Content')


    def test_post_comment_delete_api(self):

        obj_cnt_before = PostComment.objects.count()

        path = reverse('post_comment_delete', kwargs={'post_comment_id':2})
        self.client.force_login(user=self.test_user) # isWriter
        response = self.client.delete(path, content_type='application/json')

        obj_cnt_after = PostComment.objects.count()

        # 응답코드 확인
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 삭제
        self.assertEqual(obj_cnt_after, obj_cnt_before - 1)