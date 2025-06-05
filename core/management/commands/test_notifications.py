from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from core.notification_service import NotificationService, AdminAlertService

User = get_user_model()


class Command(BaseCommand):
    help = 'Тестирует систему уведомлений администраторов'

    def add_arguments(self, parser):
        parser.add_argument(
            '--mode',
            type=str,
            default='basic',
            choices=['basic', 'security', 'performance', 'all'],
            help='Режим тестирования: basic, security, performance, all'
        )

    def handle(self, *args, **options):
        mode = options['mode']

        self.stdout.write(
            self.style.SUCCESS(f'🧪 Тестирование системы уведомлений (режим: {mode})')
        )

        # Проверяем наличие администраторов
        admin_count = User.objects.filter(
            role__in=['owner', 'admin', 'store_owner', 'store_admin'],
            is_active=True
        ).count()

        if admin_count == 0:
            self.stdout.write(
                self.style.WARNING('⚠️ Нет активных администраторов для отправки уведомлений!')
            )
            return

        self.stdout.write(
            self.style.SUCCESS(f'✅ Найдено {admin_count} активных администраторов')
        )

        if mode in ['basic', 'all']:
            self._test_basic_notifications()

        if mode in ['security', 'all']:
            self._test_security_alerts()

        if mode in ['performance', 'all']:
            self._test_performance_alerts()

        self.stdout.write(
            self.style.SUCCESS('🎉 Тестирование завершено!')
        )

    def _test_basic_notifications(self):
        self.stdout.write('\n📮 Тестирование базовых уведомлений...')

        # Тест системного уведомления
        result = NotificationService.test_notification_system()
        self.stdout.write(f'  ✅ {result}')

        # Тест уведомления для администраторов магазина
        count = NotificationService.notify_store_admins(
            title="🏪 Тест уведомлений магазина",
            message="Это тестовое уведомление для администраторов магазина"
        )
        self.stdout.write(f'  ✅ Уведомление магазина отправлено {count} администраторам')

        # Тест уведомления для администраторов платформы
        count = NotificationService.notify_platform_admins(
            title="⚙️ Тест уведомлений платформы",
            message="Это тестовое уведомление для администраторов платформы"
        )
        self.stdout.write(f'  ✅ Уведомление платформы отправлено {count} администраторам')

    def _test_security_alerts(self):
        self.stdout.write('\n🔒 Тестирование оповещений безопасности...')

        # Тест оповещений разного уровня
        severities = ['low', 'medium', 'high', 'critical']

        for severity in severities:
            count = AdminAlertService.security_alert(
                message=f"Тестовое оповещение безопасности уровня {severity}",
                severity=severity
            )
            self.stdout.write(f'  ✅ Оповещение {severity} отправлено {count} администраторам')

    def _test_performance_alerts(self):
        self.stdout.write('\n📊 Тестирование оповещений производительности...')

        # Тест различных метрик
        test_metrics = [
            ("CPU Usage", "85%", "80%"),
            ("Memory Usage", "92%", "90%"),
            ("Database Response Time", "2.5s", "2.0s"),
            ("API Response Time", "1.8s", "1.5s"),
        ]

        for metric, value, threshold in test_metrics:
            count = AdminAlertService.performance_alert(metric, value, threshold)
            self.stdout.write(f'  ✅ Оповещение "{metric}" отправлено {count} администраторам')

        # Тест системной ошибки
        count = AdminAlertService.system_error_alert(
            error_details="Тестовая ошибка базы данных",
            component="Database"
        )
        self.stdout.write(f'  ✅ Оповещение об ошибке отправлено {count} администраторам')
