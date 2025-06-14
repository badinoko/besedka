# Generated by Django 4.2.21 on 2025-05-28 03:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0002_alter_actionlog_action_type"),
    ]

    operations = [
        migrations.CreateModel(
            name="MaintenanceModeSetting",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "section_name",
                    models.CharField(
                        choices=[
                            ("chat", "Чат"),
                            ("gallery", "Галерея"),
                            ("growlogs", "Гроу-репорты"),
                            ("store", "Магазин"),
                        ],
                        help_text="Выберите раздел сайта.",
                        max_length=50,
                        unique=True,
                        verbose_name="Название раздела",
                    ),
                ),
                (
                    "is_enabled",
                    models.BooleanField(
                        default=False,
                        help_text="Включить/выключить режим технического обслуживания для этого раздела.",
                        verbose_name="Режим обслуживания включен",
                    ),
                ),
                (
                    "title",
                    models.CharField(
                        default="Техническое обслуживание",
                        help_text="Заголовок, который увидят пользователи (например, 'Чат временно недоступен').",
                        max_length=200,
                        verbose_name="Заголовок страницы обслуживания",
                    ),
                ),
                (
                    "message",
                    models.TextField(
                        default="Мы работаем над улучшением этого раздела. Пожалуйста, зайдите позже.",
                        help_text="Подробное сообщение для пользователей.",
                        verbose_name="Сообщение для пользователей",
                    ),
                ),
                (
                    "expected_recovery_time",
                    models.CharField(
                        blank=True,
                        default="В ближайшее время",
                        help_text="Например, 'В течение часа', 'До 15:00 МСК', 'В ближайшее время'.",
                        max_length=100,
                        null=True,
                        verbose_name="Ожидаемое время восстановления",
                    ),
                ),
                (
                    "color_scheme",
                    models.CharField(
                        choices=[
                            ("blue", "Синяя (информационная)"),
                            ("orange", "Оранжевая (предупреждение)"),
                            ("red", "Красная (критично/недоступно)"),
                        ],
                        default="blue",
                        help_text="Выберите цветовую схему для страницы обслуживания.",
                        max_length=20,
                        verbose_name="Цветовая схема страницы",
                    ),
                ),
            ],
            options={
                "verbose_name": "Настройка режима обслуживания",
                "verbose_name_plural": "Настройки режимов обслуживания",
                "ordering": ["section_name"],
            },
        ),
    ]
