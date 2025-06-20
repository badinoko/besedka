# Generated by Django 4.2.21 on 2025-06-16 20:55

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("chat", "0002_vipchatmembership_vipchatroom_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="ChatReaction",
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
                    "reaction_type",
                    models.CharField(
                        choices=[("like", "👍 Like"), ("dislike", "👎 Dislike")],
                        max_length=7,
                        verbose_name="Тип реакции",
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True, verbose_name="Создано"),
                ),
                (
                    "message",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="reactions",
                        to="chat.message",
                        verbose_name="Сообщение",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Пользователь",
                    ),
                ),
            ],
            options={
                "verbose_name": "Реакция сообщения",
                "verbose_name_plural": "Реакции сообщений",
                "indexes": [
                    models.Index(
                        fields=["message", "reaction_type"],
                        name="chat_chatre_message_698f56_idx",
                    )
                ],
                "unique_together": {("message", "user")},
            },
        ),
    ]
