# Generated by Django 4.0 on 2022-05-18 06:52

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0003_user_is_active_user_is_admin_user_is_staff_and_more'),
    ]

    operations = [
        migrations.AlterModelManagers(
            name='user',
            managers=[
            ],
        ),
    ]