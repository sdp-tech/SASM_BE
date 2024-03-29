# Generated by Django 4.0 on 2023-04-10 21:23

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('stories', '0012_story_place'),
        ('curations', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='curation',
            name='rep_pic',
        ),
        migrations.RemoveField(
            model_name='curation',
            name='show_viewcount',
        ),
        migrations.RemoveField(
            model_name='curation',
            name='story_likeuser_set',
        ),
        migrations.RemoveField(
            model_name='curation',
            name='supports_comments',
        ),
        migrations.RemoveField(
            model_name='curation',
            name='tags',
        ),
        migrations.RemoveField(
            model_name='curation',
            name='view_cnt',
        ),
        migrations.AddField(
            model_name='curation',
            name='contents',
            field=models.CharField(default='', max_length=200),
        ),
        migrations.AddField(
            model_name='curation',
            name='likeuser_set',
            field=models.ManyToManyField(blank=True, related_name='liked_curations', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='curationphoto',
            name='curation',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='photos', to='curations.curation'),
        ),
        migrations.AlterField(
            model_name='curation_story',
            name='curation',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='short_curations', to='curations.curation'),
        ),
        migrations.AlterField(
            model_name='curation_story',
            name='story',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='short_curations', to='stories.story'),
        ),
    ]
