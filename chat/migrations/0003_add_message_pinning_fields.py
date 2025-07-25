# Generated by Django 4.2.21 on 2025-06-28 23:10

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("chat", "0002_add_extended_message_fields"),
    ]

    operations = [
        migrations.AddField(
            model_name="message",
            name="is_pinned",
            field=models.BooleanField(default=False, help_text="Сообщение закреплено"),
        ),
        migrations.AddField(
            model_name="message",
            name="pinned_at",
            field=models.DateTimeField(
                blank=True, help_text="Когда было закреплено", null=True
            ),
        ),
        migrations.AddField(
            model_name="message",
            name="pinned_by",
            field=models.ForeignKey(
                blank=True,
                help_text="Кто закрепил сообщение",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="pinned_messages",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
