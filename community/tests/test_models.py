from django.test import TestCase
from django.core.exceptions import ValidationError

from community.models import Post


class PostTests(TestCase):
    def test_post_title_length_should_be_longer_than_zero_without_white_spaces(self):
        post = Post(title='       ', content='abcd')

        with self.assertRaises(ValidationError):
            post.full_clean()

    def test_post_content_length_should_be_longer_than_zero_without_white_spaces(self):
        post = Post(title='abcd', content='       ')

        with self.assertRaises(ValidationError):
            post.full_clean()
