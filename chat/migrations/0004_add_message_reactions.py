# Generated by Django 4.2.21 on 2025-07-02 22:47

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import uuid


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("chat", "0003_add_message_pinning_fields"),
    ]

    operations = [
        migrations.CreateModel(
            name="MessageReaction",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "reaction_type",
                    models.CharField(
                        choices=[("like", "Лайк"), ("dislike", "Дизлайк")],
                        max_length=10,
                        verbose_name="Тип реакции",
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(
                        default=django.utils.timezone.now, verbose_name="Дата создания"
                    ),
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
                        related_name="chat_reactions",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Пользователь",
                    ),
                ),
            ],
            options={
                "verbose_name": "Реакция на сообщение",
                "verbose_name_plural": "Реакции на сообщения",
                "indexes": [
                    models.Index(
                        fields=["message", "reaction_type"],
                        name="chat_messag_message_b87cb7_idx",
                    ),
                    models.Index(
                        fields=["user", "created_at"],
                        name="chat_messag_user_id_e27d94_idx",
                    ),
                ],
                "unique_together": {("message", "user")},
            },
        ),
    ]
