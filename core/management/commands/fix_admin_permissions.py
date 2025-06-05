from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from users.models import User
from magicbeans_store.models import (
    SeedBank, Strain, StockItem, Order, OrderStatus,
    Promotion, Coupon, ShippingMethod, PaymentMethod
)


class Command(BaseCommand):
    help = 'Исправляет права доступа для администраторов магазина'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            help='Имя пользователя для назначения прав (по умолчанию все store_admin)',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🔧 Исправление прав доступа для администраторов магазина...'))

        try:
            with transaction.atomic():
                # Определяем пользователей для обновления
                if options['username']:
                    users = User.objects.filter(username=options['username'])
                    if not users.exists():
                        raise CommandError(f'Пользователь {options["username"]} не найден')
                else:
                    users = User.objects.filter(role='store_admin')

                if not users.exists():
                    self.stdout.write(self.style.WARNING('❌ Не найдено пользователей с ролью store_admin'))
                    return

                # Модели магазина для которых нужны права
                store_models = [
                    SeedBank, Strain, StockItem, Order, OrderStatus,
                    Promotion, Coupon, ShippingMethod, PaymentMethod
                ]

                # Собираем все необходимые права
                permissions_to_add = []

                for model in store_models:
                    content_type = ContentType.objects.get_for_model(model)

                    # Базовые права: view, add, change (delete не даем для ограничений)
                    permission_codenames = [
                        f'view_{model._meta.model_name}',
                        f'add_{model._meta.model_name}',
                        f'change_{model._meta.model_name}',
                    ]

                    for codename in permission_codenames:
                        try:
                            permission = Permission.objects.get(
                                content_type=content_type,
                                codename=codename
                            )
                            permissions_to_add.append(permission)
                            self.stdout.write(f'  ✅ Найдено право: {permission.name}')
                        except Permission.DoesNotExist:
                            self.stdout.write(f'  ⚠️ Право не найдено: {codename}')

                # Назначаем права пользователям
                for user in users:
                    self.stdout.write(f'\n👤 Обновляем права для пользователя: {user.username} (роль: {user.role})')

                    # Проверяем, что пользователь is_staff
                    if not user.is_staff:
                        user.is_staff = True
                        user.save()
                        self.stdout.write('  🔧 Установлен флаг is_staff = True')

                    # Добавляем все права
                    user.user_permissions.add(*permissions_to_add)
                    self.stdout.write(f'  ✅ Добавлено {len(permissions_to_add)} прав доступа')

                self.stdout.write(self.style.SUCCESS('\n🎉 Права доступа успешно обновлены!'))
                self.print_summary(users, permissions_to_add)

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Ошибка при обновлении прав: {e}'))
            raise CommandError(f'Не удалось обновить права доступа: {e}')

    def print_summary(self, users, permissions):
        self.stdout.write('\n📊 СВОДКА ОБНОВЛЕНИЯ ПРАВ:')
        self.stdout.write(f'  👥 Обновлено пользователей: {users.count()}')
        for user in users:
            self.stdout.write(f'    - {user.username} ({user.get_role_display()})')

        self.stdout.write(f'  🔐 Назначено прав: {len(permissions)}')
        self.stdout.write('  📋 Права включают:')
        self.stdout.write('    - 👀 Просмотр всех моделей магазина')
        self.stdout.write('    - ➕ Добавление новых записей')
        self.stdout.write('    - ✏️ Редактирование существующих')
        self.stdout.write('    - ❌ БЕЗ права удаления (для безопасности)')

        self.stdout.write('\n🚀 Теперь администраторы магазина могут работать с админкой!')
