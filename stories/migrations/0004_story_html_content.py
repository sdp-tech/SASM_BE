# Generated by Django 4.0 on 2022-09-07 08:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stories', '0003_story_rep_pic_alter_story_address'),
    ]

    operations = [
        migrations.AddField(
            model_name='story',
            name='html_content',
            field=models.TextField(default='p', max_length=50000),
            preserve_default=False,
        ),
    ]
