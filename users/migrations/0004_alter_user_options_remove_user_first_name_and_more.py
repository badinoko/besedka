# Generated by Django 4.2.21 on 2025-05-22 01:23

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0003_update_user_roles"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="user",
            options={
                "verbose_name": "Пользователь",
                "verbose_name_plural": "Пользователи",
            },
        ),
        migrations.RemoveField(
            model_name="user",
            name="first_name",
        ),
        migrations.RemoveField(
            model_name="user",
            name="last_name",
        ),
        migrations.AddField(
            model_name="user",
            name="name",
            field=models.CharField(
                blank=True, max_length=255, verbose_name="Имя пользователя"
            ),
        ),
        migrations.AlterField(
            model_name="banrecord",
            name="banned_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="bans_given",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AlterField(
            model_name="user",
            name="avatar",
            field=models.ImageField(
                blank=True, null=True, upload_to="avatars/", verbose_name="Аватар"
            ),
        ),
        migrations.AlterField(
            model_name="user",
            name="bio",
            field=models.TextField(blank=True, verbose_name="О себе"),
        ),
        migrations.AlterField(
            model_name="user",
            name="is_banned",
            field=models.BooleanField(
                default=False,
                help_text="Забаненные пользователи не могут войти в систему",
                verbose_name="Забанен",
            ),
        ),
        migrations.AlterField(
            model_name="user",
            name="role",
            field=models.CharField(
                choices=[
                    ("owner", "Владелец платформы"),
                    ("admin", "Администратор платформы"),
                    ("store_owner", "Владелец магазина"),
                    ("store_admin", "Администратор магазина"),
                    ("user", "Пользователь"),
                    ("guest", "Гость"),
                ],
                default="user",
                max_length=20,
                verbose_name="Роль",
            ),
        ),
    ]
