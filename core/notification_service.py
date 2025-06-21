from django.utils import timezone
from django.contrib.auth import get_user_model
from users.models import Notification

User = get_user_model()


class NotificationService:
    """
    Сервис для отправки уведомлений администраторам платформы.
    """

    @staticmethod
    def notify_admins(title: str, message: str, notification_type: str = 'system', exclude_user=None):
        """
        Отправляет уведомление всем администраторам платформы.

        Args:
            title: Заголовок уведомления
            message: Текст уведомления
            notification_type: Тип уведомления (system, security, etc.)
            exclude_user: Исключить этого пользователя из рассылки
        """
        admin_roles = ['owner', 'moderator', 'store_owner', 'store_admin']
        admin_users = User.objects.filter(
            role__in=admin_roles,
            is_active=True
        )

        if exclude_user:
            admin_users = admin_users.exclude(id=exclude_user.id)

        notifications = []
        for admin in admin_users:
            notifications.append(
                Notification(
                    recipient=admin,
                    sender=None,  # Системное уведомление
                    notification_type=notification_type,
                    title=title,
                    message=message,
                    created_at=timezone.now()
                )
            )

        # Массовая вставка уведомлений
        Notification.objects.bulk_create(notifications)

        return len(notifications)

    @staticmethod
    def notify_store_admins(title: str, message: str, notification_type: str = 'system', exclude_user=None):
        """
        Отправляет уведомление только администраторам магазина.
        """
        store_admin_roles = ['owner', 'store_owner', 'store_admin']
        store_admins = User.objects.filter(
            role__in=store_admin_roles,
            is_active=True
        )

        if exclude_user:
            store_admins = store_admins.exclude(id=exclude_user.id)

        notifications = []
        for admin in store_admins:
            notifications.append(
                Notification(
                    recipient=admin,
                    sender=None,
                    notification_type=notification_type,
                    title=title,
                    message=message,
                    created_at=timezone.now()
                )
            )

        Notification.objects.bulk_create(notifications)
        return len(notifications)

    @staticmethod
    def notify_platform_admins(title: str, message: str, notification_type: str = 'system', exclude_user=None):
        """
        Отправляет уведомление только администраторам платформы (владелец + модераторы).
        """
        platform_admin_roles = ['owner', 'moderator']
        platform_admins = User.objects.filter(
            role__in=platform_admin_roles,
            is_active=True
        )

        if exclude_user:
            platform_admins = platform_admins.exclude(id=exclude_user.id)

        notifications = []
        for admin in platform_admins:
            notifications.append(
                Notification(
                    recipient=admin,
                    sender=None,
                    notification_type=notification_type,
                    title=title,
                    message=message,
                    created_at=timezone.now()
                )
            )

        Notification.objects.bulk_create(notifications)
        return len(notifications)

    @staticmethod
    def notify_user_action(user, action_type: str, details: str = ""):
        """
        Уведомляет администраторов о действиях пользователей.

        Args:
            user: Пользователь, выполнивший действие
            action_type: Тип действия ('login', 'register', 'ban', 'content_report', etc.)
            details: Дополнительная информация
        """
        action_titles = {
            'login': f"👤 Вход пользователя",
            'register': f"🆕 Новая регистрация",
            'ban_appeal': f"🚫 Жалоба на бан",
            'content_report': f"🚨 Жалоба на контент",
            'suspicious_activity': f"⚠️ Подозрительная активность",
            'payment_issue': f"💳 Проблема с оплатой",
        }

        title = action_titles.get(action_type, f"📋 Действие пользователя: {action_type}")

        # Форматируем сообщение
        user_display = f"{user.username} ({user.get_role_display()})"
        message = f"Пользователь {user_display}"

        if details:
            message += f"\n\nДетали: {details}"

        message += f"\n\nВремя: {timezone.now().strftime('%d.%m.%Y %H:%M')}"

        # Отправляем уведомление соответствующим администраторам
        if action_type in ['payment_issue', 'order_issue']:
            # Проблемы с заказами - уведомляем администраторов магазина
            return NotificationService.notify_store_admins(title, message, 'system', exclude_user=user)
        else:
            # Остальные проблемы - уведомляем администраторов платформы
            return NotificationService.notify_platform_admins(title, message, 'system', exclude_user=user)

    @staticmethod
    def test_notification_system():
        """
        Тестирует систему уведомлений, отправляя тестовое сообщение всем админам.
        """
        title = "🧪 Тест системы уведомлений"
        message = f"""Это тестовое уведомление для проверки работы системы.

Отправлено: {timezone.now().strftime('%d.%m.%Y %H:%M:%S')}

Если вы видите это сообщение, система уведомлений работает корректно!"""

        count = NotificationService.notify_admins(title, message, 'system')
        return f"Тестовое уведомление отправлено {count} администраторам"


class AdminAlertService:
    """
    Сервис для критических уведомлений администраторов.
    """

    @staticmethod
    def security_alert(message: str, severity: str = 'medium'):
        """
        Отправляет уведомление о проблемах безопасности.
        """
        severity_icons = {
            'low': '🟡',
            'medium': '🟠',
            'high': '🔴',
            'critical': '🚨'
        }

        icon = severity_icons.get(severity, '⚠️')
        title = f"{icon} Оповещение безопасности"

        full_message = f"""УРОВЕНЬ: {severity.upper()}

{message}

Время: {timezone.now().strftime('%d.%m.%Y %H:%M:%S')}

Требуется проверка и принятие мер."""

        return NotificationService.notify_platform_admins(title, full_message, 'system')

    @staticmethod
    def system_error_alert(error_details: str, component: str = 'Unknown'):
        """
        Уведомляет об ошибках системы.
        """
        title = f"💥 Системная ошибка: {component}"
        message = f"""Обнаружена системная ошибка в компоненте: {component}

Детали ошибки:
{error_details}

Время: {timezone.now().strftime('%d.%m.%Y %H:%M:%S')}

Рекомендуется немедленная проверка системы."""

        return NotificationService.notify_admins(title, message, 'system')

    @staticmethod
    def performance_alert(metric: str, value: str, threshold: str):
        """
        Уведомляет о проблемах производительности.
        """
        title = f"📊 Превышение лимитов производительности"
        message = f"""Метрика: {metric}
Текущее значение: {value}
Пороговое значение: {threshold}

Время: {timezone.now().strftime('%d.%m.%Y %H:%M:%S')}

Рекомендуется проверить состояние системы."""

        return NotificationService.notify_admins(title, message, 'system')
