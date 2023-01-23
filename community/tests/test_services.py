import unittest
from unittest.mock import patch

from django.test import TestCase
from django.core.exceptions import ValidationError

from users.models import User
from community.models import Board
from community.services import PostService


class PostServiceTests(TestCase):
    # Mocking a function in a different module - https://stackoverflow.com/questions/16134281/python-mocking-a-function-from-an-imported-module
    # PostService.create 내에서 실행되는 get_board_from_name은 services 모듈에서 import된 함수이므로 아래와 같이 경로를 작성해주어야한다(community.selectors.get_board_from_name이 아님)
    @patch('community.services.get_board_from_name')
    def test_post_title_length_should_be_longer_than_zero_without_white_spaces(self, get_board_from_name_mock):
        """
        Since we already have tests for `get_board_from_name`,
        we can safely mock it here and give it a proper return value.
        """
        user = User(
            email='test@test.test',
            nickname='test'
        )
        board = Board(
            name='Test Board',
            supports_hashtags=True,
            supports_post_photos=True,
            supports_post_comment_photos=True,
            supports_post_comments=True
        )

        get_board_from_name_mock.return_value = board

        service = PostService(user=user)
        with self.assertRaises(ValidationError):
            service.create(title='       ',
                           content='test content',
                           board_name='Test Board')
