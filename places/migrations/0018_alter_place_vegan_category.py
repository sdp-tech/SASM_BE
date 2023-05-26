# Generated by Django 4.0 on 2023-05-22 14:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('places', '0017_alter_place_vegan_category'),
    ]

    operations = [
        migrations.AlterField(
            model_name='place',
            name='vegan_category',
            field=models.CharField(blank=True, choices=[('비건', '비건'), ('락토', '락토'), ('오보', '오보'), ('페스코', '페스코'), ('폴로', '폴로'), ('그 외', '그 외'), (None, 'None')], max_length=10, null=True),
        ),
    ]