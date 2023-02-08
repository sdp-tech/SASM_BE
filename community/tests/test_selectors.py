import unittest
from unittest.mock import patch

from django.test import TestCase
from django.core.exceptions import ValidationError

from community.models import Board, Post
from community.selectors import PostCommentPhotoSelector


class PostCommentPhotoSelectorTests(TestCase):

    #test-level setup
    @classmethod
    def setUp(cls):
        cls.board_supports_all = Board.objects.create(name="test board 1", supports_hashtags=True, supports_post_photos=True, supports_post_comment_photos=True, supports_post_comments=True)
        cls.board_not_supports_all = Board.objects.create(name="test board 2", supports_hashtags=False, supports_post_photos=False, supports_post_comment_photos=False, supports_post_comments=False)
        cls.post_in_board_supports_all = Post.objects.create(title="test post 1", content="this is a test post", board=cls.board_supports_all)
        cls.post_in_board_not_supports_all = Post.objects.create(title="test post 2", content="this is a test post", board=cls.board_not_supports_all)


    def test_is_post_comment_photo_available(self):
        post_id = self.post_in_board_not_supports_all.id
        selector = PostCommentPhotoSelector()
        expected_false = selector.isPostCommentPhotoAvailable(post_id=post_id)

        self.assertFalse(expected_false)