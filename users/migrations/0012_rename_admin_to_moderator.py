# Generated by Django 4.2.7 on 2025-06-16 05:05

from django.db import migrations, models


def rename_admin_to_moderator(apps, schema_editor):
    """Переименовываем существующие записи с admin на moderator"""
    User = apps.get_model('users', 'User')
    User.objects.filter(role='admin').update(role='moderator')


def reverse_rename_admin_to_moderator(apps, schema_editor):
    """Обратная операция: moderator -> admin"""
    User = apps.get_model('users', 'User')
    User.objects.filter(role='moderator').update(role='admin')


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0011_add_role_icon"),
    ]

    operations = [
        migrations.AlterField(
            model_name="user",
            name="role",
            field=models.CharField(
                choices=[
                    ("owner", "Владелец платформы"),
                    ("moderator", "Модератор платформы"),
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
        # Добавляем миграцию данных
        migrations.RunPython(
            rename_admin_to_moderator,
            reverse_rename_admin_to_moderator,
        ),
    ]
