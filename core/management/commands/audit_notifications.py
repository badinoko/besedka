from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import models
from datetime import timedelta
import json
from pathlib import Path

from users.models import Notification


class Command(BaseCommand):
    help = (
        "Собирает сводные сведения о состоянии системы уведомлений для всех пользователей "
        "и формирует отчёт audit_reports/notifications_audit.json."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--days",
            type=int,
            default=30,
            help="Сколько дней считать \"давними\" непрочитанные уведомлениями (default: 30)",
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("📊 Запуск аудита системы уведомлений…"))

        days_threshold = options["days"]
        threshold_date = timezone.now() - timedelta(days=days_threshold)

        User = get_user_model()
        users_qs = User.objects.filter(is_active=True)

        report_data = {
            "generated_at": timezone.now().isoformat(),
            "days_threshold": days_threshold,
            "users": [],
        }

        total_notifications = 0
        total_unread = 0
        stale_unread_total = 0

        for user in users_qs.iterator():
            user_notifications = Notification.objects.filter(recipient=user)
            unread_qs = user_notifications.filter(is_read=False)
            stale_unread_qs = unread_qs.filter(created_at__lte=threshold_date)

            breakdown = (
                user_notifications.values("notification_type")
                .order_by()
                .annotate(count=models.Count("id"))
            )

            user_entry = {
                "id": user.id,
                "username": user.username,
                "role": getattr(user, "role", "unknown"),
                "total": int(user_notifications.count()),
                "unread": int(unread_qs.count()),
                "stale_unread": int(stale_unread_qs.count()),
                "by_type": {item["notification_type"]: item["count"] for item in breakdown},
            }

            report_data["users"].append(user_entry)

            total_notifications += int(user_entry["total"])
            total_unread += int(user_entry["unread"])
            stale_unread_total += int(user_entry["stale_unread"])

        report_data["summary"] = {
            "total_notifications": total_notifications,
            "total_unread": total_unread,
            "stale_unread_total": stale_unread_total,
        }

        output_path = Path("audit_reports/notifications_audit.json")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", encoding="utf-8") as fh:
            json.dump(report_data, fh, ensure_ascii=False, indent=2)

        self.stdout.write(
            self.style.SUCCESS(
                f"✅ Аудит завершён. Итог: уведомлений {total_notifications}, непрочитанных {total_unread}, "
                f"залежавшихся (>{days_threshold} дн.) {stale_unread_total}. Отчёт: {output_path}"
            )
        )
