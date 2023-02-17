import unittest
from unittest.mock import patch

from django.test import TestCase
from django.core.exceptions import ValidationError

from community.models import Board, Post, PostContentStyle, PostHashtag, PostPhoto, PostComment, PostCommentPhoto, get_post_photo_upload_path, get_comment_photo_upload_path

class BoardTests(TestCase):
    def test_board_name_length_should_be_longer_than_zero_without_white_spaces(self):
        post_comment = Board(name='       ')

        with self.assertRaises(ValidationError):
            post_comment.full_clean()


class PostContentStyleTests(TestCase):
    def test_post_content_style_name_length_should_be_longer_than_zero_without_white_spaces(self):
        post_content_style = PostContentStyle(name='       ', styled_content='abcd')

        with self.assertRaises(ValidationError):
            post_content_style.full_clean()
        
    def test_post_content_style_content_length_should_be_longer_than_zero_without_white_spaces(self):
        post_content_style = PostContentStyle(name='abcd', styled_content='       ')

        with self.assertRaises(ValidationError):
            post_content_style.full_clean()


class PostTests(TestCase):
    def test_post_title_length_should_be_longer_than_zero_without_white_spaces(self):
        post = Post(title='       ', content='abcd')

        with self.assertRaises(ValidationError):
            post.full_clean()

    def test_post_content_length_should_be_longer_than_zero_without_white_spaces(self):
        post = Post(title='abcd', content='       ')

        with self.assertRaises(ValidationError):
            post.full_clean()


class PostHashtagTests(TestCase):
    def test_post_hashtag_name_length_should_be_longer_than_zero_without_white_spaces(self):
        hashtag = PostHashtag(name='       ')

        with self.assertRaises(ValidationError):
            hashtag.full_clean()


class PostPhotoTests(TestCase):
    # ForeignKey Field를 가지는 Model test를 위해 setUpTestData 설정
    # ref. https://stackoverflow.com/questions/44604686/how-to-test-a-model-that-has-a-foreign-key-in-django    
    @classmethod
    def setUpTestData(cls):
        cls.board = Board.objects.create(name="test board", supports_hashtags=True, supports_post_photos=True, supports_post_comment_photos=True, supports_post_comments=True)
        cls.post = Post.objects.create(title="test post", content="this is a test post", board=cls.board)
        cls.post_photo = PostPhoto.objects.create(image="temp_image", post=cls.post)

    def test_get_post_photo_upload_path(self):
        actual = get_post_photo_upload_path(instance=self.post_photo, filename='test_file')
        expected = 'community/post/test_file'

        self.assertEqual(actual, expected)


class PostCommentTests(TestCase):
    def test_post_comment_content_length_should_be_longer_than_zero_without_white_spaces(self):
        post_comment = PostComment(content='       ')

        with self.assertRaises(ValidationError):
            post_comment.full_clean()


class PostCommentPhotoTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.board = Board.objects.create(name="test board", supports_hashtags=True, supports_post_photos=True, supports_post_comment_photos=True, supports_post_comments=True)
        cls.post = Post.objects.create(title="test post", content="this is a test post", board=cls.board)
        cls.post_comment = PostComment.objects.create(post=cls.post, content="this is a test post comment", isParent=True)
        cls.post_comment_photo = PostCommentPhoto.objects.create(image="temp_image", post_comment=cls.post_comment)
    
    def test_get_comment_photo_upload_path(self):
        actual = get_comment_photo_upload_path(instance=self.post_comment_photo, filename='test_file')
        expected = 'community/post_comment/test_file'

        self.assertEqual(actual, expected)