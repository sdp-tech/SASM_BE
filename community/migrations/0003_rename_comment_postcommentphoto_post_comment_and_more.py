# Generated by Django 4.0 on 2023-01-29 05:42

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('community', '0002_posthashtag_post_can_have_hashtag_with_unique_name_constraint_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='postcommentphoto',
            old_name='comment',
            new_name='post_comment',
        ),
        migrations.RenameField(
            model_name='postcommentreport',
            old_name='user',
            new_name='reporter',
        ),
        migrations.RenameField(
            model_name='postreport',
            old_name='user',
            new_name='reporter',
        ),
    ]
