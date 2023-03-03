# Generated by Django 4.0 on 2023-03-03 14:59

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0005_user_social_provider'),
        ('stories', '0009_storycomment'),
    ]

    operations = [
        migrations.AlterField(
            model_name='storycomment',
            name='mention',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='mentioned_story_comments', to='users.user'),
        ),
        migrations.AlterField(
            model_name='storycomment',
            name='parent',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='childs', to='stories.storycomment'),
        ),
        migrations.AlterField(
            model_name='storycomment',
            name='writer',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='story_comments', to='users.user'),
        ),
    ]
