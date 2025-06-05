from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

User = get_user_model()

class Command(BaseCommand):
    help = _('Отладка конкретного пользователя для диагностики проблем с доступом')

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='Имя пользователя для отладки')

    def handle(self, *args, **options):
        username = options['username']

        try:
            user = User.objects.get(username=username)

            self.stdout.write(self.style.SUCCESS(f'\n🔍 ОТЛАДКА ПОЛЬЗОВАТЕЛЯ: {username}'))
            self.stdout.write('=' * 50)

            # Основная информация
            self.stdout.write(f'👤 Username: {user.username}')
            self.stdout.write(f'📧 Email: {user.email}')
            self.stdout.write(f'🎭 Role: {getattr(user, "role", "НЕТ АТРИБУТА ROLE!")}')
            self.stdout.write(f'⚙️ is_staff: {user.is_staff}')
            self.stdout.write(f'👑 is_superuser: {user.is_superuser}')
            self.stdout.write(f'✅ is_active: {user.is_active}')

            # Проверяем все атрибуты пользователя
            self.stdout.write('\n📊 ВСЕ АТРИБУТЫ ПОЛЬЗОВАТЕЛЯ:')
            for attr in dir(user):
                if not attr.startswith('_') and not callable(getattr(user, attr)):
                    try:
                        value = getattr(user, attr)
                        self.stdout.write(f'   {attr}: {value}')
                    except:
                        pass

            # Логика перенаправления
            self.stdout.write('\n🎯 ЛОГИКА ПЕРЕНАПРАВЛЕНИЯ:')

            if not user.is_staff:
                self.stdout.write(self.style.ERROR('   ❌ НЕТ ПРАВ STAFF → ОТКАЗ В ДОСТУПЕ'))
            elif user.is_superuser:
                self.stdout.write(self.style.WARNING('   🏛️ SUPERUSER → /standard-admin/'))
            elif getattr(user, 'role', None) in ['owner', 'admin']:
                self.stdout.write(self.style.SUCCESS('   👑 ВЛАДЕЛЕЦ/АДМИН ПЛАТФОРМЫ → /owner-admin/'))
            elif getattr(user, 'role', None) in ['store_owner', 'store_admin']:
                self.stdout.write(self.style.SUCCESS('   🛍️ ВЛАДЕЛЕЦ/АДМИН МАГАЗИНА → /store-admin/'))
            elif user.is_staff:
                self.stdout.write(self.style.HTTP_INFO('   ⚙️ STAFF БЕЗ РОЛИ → /admin-selector/'))
            else:
                self.stdout.write(self.style.ERROR('   ❌ НЕ ПОДХОДИТ НИ ОДИН ВАРИАНТ'))

        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'❌ Пользователь {username} не найден'))
