# Generated by Django 4.0 on 2022-07-08 10:32

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('places', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='place',
            name='place_likeuser_set',
            field=models.ManyToManyField(blank=True, related_name='PlaceLikeUser', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='place',
            name='sns_type',
            field=models.ManyToManyField(related_name='sns', to='places.SNSType'),
        ),
        migrations.AddField(
            model_name='photo',
            name='place',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='places.place'),
        ),
    ]
