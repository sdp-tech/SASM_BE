# Generated by Django 4.0 on 2022-11-26 05:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('places', '0008_alter_placephoto_image'),
    ]

    operations = [
        migrations.AlterField(
            model_name='place',
            name='category',
            field=models.CharField(blank=True, choices=[('식당 및 카페', '식당 및 카페'), ('전시 및 체험공간', '전시 및 체험공간'), ('제로웨이스트 샵', '제로웨이스트 샵'), ('도시 재생 및 친환경 건출물', '도시 재생 및 친환경 건축물'), ('복합 문화 공간', '복합 문화 공간'), ('녹색 공간', '녹색 공간'), ('그 외', '그 외')], max_length=30),
        ),
    ]
