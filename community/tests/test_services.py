import unittest
from unittest.mock import patch

from django.test import TestCase
from django.core.exceptions import ValidationError

from users.models import User
from community.models import Board, Post, PostContentStyle, PostHashtag, PostPhoto, PostComment, PostCommentPhoto
from community.services import PostService, PostHashtagService, PostCoordinatorService
from community.selectors import PostCommentSelector, PostCommentPhotoSelector


class PostCoordinatorServiceTests(TestCase):
 
    @classmethod
    def setUp(cls):
        cls.user = User.objects.create(email='test@test.test', nickname='test', password='test')
        cls.board_supports_only_hashtags = Board.objects.create(name="test board 1", supports_hashtags=True, supports_post_photos=False, supports_post_comment_photos=False, supports_post_comments=False)
        cls.board_supports_only_post_photos = Board.objects.create(name="test board 2", supports_hashtags=False, supports_post_photos=False, supports_post_comment_photos=True, supports_post_comments=False)
        # cls.post_in_board_supports_all = Post.objects.create(title="test post 1", content="this is a test post", board=cls.board_supports_all)
        # cls.post_in_board_not_supports_all = Post.objects.create(title="test post 2", content="this is a test post", board=cls.board_not_supports_all)


    def test_post_hashtags_can_be_created_only_if_board_supports_hashtags(self):
        post_service = PostCoordinatorService(user=self.user)

        post = post_service.create(
                        board_id=self.board_supports_only_post_photos.id,
                        title='test post',
                        content='test content',
                        hashtag_names=['hashtag1', 'hashtag2', 'hashtag3'],
                        image_files=['image1', 'image2', 'image3']
                        )

        expected_false = PostHashtag.objects.filter(id=post.id).exists()
        self.assertFalse(expected_false)


    def test_post_photos_can_be_created_only_if_board_supports_post_photos(self):
        post_service = PostCoordinatorService(user=self.user)

        post = post_service.create(
                        board_id=self.board_supports_only_hashtags.id,
                        title='test post',
                        content='test content',
                        hashtag_names=['hashtag1', 'hashtag2', 'hashtag3'],
                        image_files=['image1', 'image2', 'image3']
                        )

        expected_false = PostPhoto.objects.filter(post=post.id).exists()
        self.assertFalse(expected_false)  


class PostServiceTests(TestCase):
    # Mocking a function in a different module - https://stackoverflow.com/questions/16134281/python-mocking-a-function-from-an-imported-module
    # PostService.create 내에서 실행되는 get_board_from_name은 services 모듈에서 import된 함수이므로 아래와 같이 경로를 작성해주어야한다(community.selectors.get_board_from_name이 아님)
    # @patch('community.services.get_board_from_name')
    # def test_post_title_length_should_be_longer_than_zero_without_white_spaces(self, get_board_from_name_mock):
    #     """
    #     Since we already have tests for `get_board_from_name`,
    #     we can safely mock it here and give it a proper return value.
    #     """
    #     user = User(
    #         email='test@test.test',
    #         nickname='test'
    #     )
    #     board = Board(
    #         name='Test Board',
    #         supports_hashtags=True,
    #         supports_post_photos=True,
    #         supports_post_comment_photos=True,
    #         supports_post_comments=True
    #     )

    #     get_board_from_name_mock.return_value = board

    #     service = PostService(user=user)
    #     with self.assertRaises(ValidationError):
    #         service.create(title='       ',
    #                        content='test content',
    #                        board_name='Test Board')


    #class-level setup
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create(email='test@test.test', nickname='test', password='test')
        cls.board = Board.objects.create(name="test board", supports_hashtags=True, supports_post_photos=True, supports_post_comment_photos=True, supports_post_comments=True)
        cls.post = Post.objects.create(title="test post", content="this is a test post", board=cls.board)
        # cls.post_comment = PostComment.objects.create(post=cls.post, content="this is a test post comment", isParent=True)
        # cls.post_comment_photo = PostCommentPhoto.objects.create(image="temp_image", post_comment=cls.post_comment)


    def test_post_title_length_should_be_longer_than_zero_without_white_spaces(self):
        service = PostService()

        with self.assertRaises(ValidationError):
            service.create(title='       ',
                           content='Test content',
                           board=self.board,
                           writer=self.user)


    def test_post_content_length_should_be_longer_than_zero_without_white_spaces(self):
        service = PostService()

        with self.assertRaises(ValidationError):
            service.create(title='Test title',
                           content='       ',
                           board=self.board,
                           writer=self.user)   


class PostHashtagServiceTests(TestCase):

    #class-level setup
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create(email='test@test.test', nickname='test', password='test')
        cls.board = Board.objects.create(name="test board", supports_hashtags=True, supports_post_photos=True, supports_post_comment_photos=True, supports_post_comments=True)
        cls.post = Post.objects.create(title="test post", content="this is a test post", board=cls.board)
        # cls.post_comment = PostComment.objects.create(post=cls.post, content="this is a test post comment", isParent=True)
        # cls.post_comment_photo = PostCommentPhoto.objects.create(image="temp_image", post_comment=cls.post_comment)


    def test_post_hashtags_length_should_be_longer_than_zero_without_white_spaces(self):
        service = PostHashtagService(post=self.post)

        with self.assertRaises(ValidationError):
            service.create(names= ['       ', 'hashtag2', 'hashtag3'])      



    # def test_post_can_be_updated_only_by_writer():
    # def test_post_can_be_deleted_only_by_writer():
    # def test_post_hashtags_can_be_updated_if_board_supports_hashtags():
    # def test_post_photos_can_be_updated_if_board_supports_post_photos():
