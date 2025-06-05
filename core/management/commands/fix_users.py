from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

User = get_user_model()

class Command(BaseCommand):
    help = _('Исправляет роли и права пользователей в соответствии с архитектурой проекта')

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🔧 Начинаем исправление пользователей...'))

        # Исправляем владельца платформы
        try:
            owner = User.objects.get(username='owner')
            owner.role = 'owner'
            owner.is_staff = True
            owner.is_superuser = True
            owner.save()
            self.stdout.write(self.style.SUCCESS(f'✅ owner: role={owner.role}, staff={owner.is_staff}, super={owner.is_superuser}'))
        except User.DoesNotExist:
            self.stdout.write(self.style.WARNING('⚠️ Пользователь owner не найден'))

        # Исправляем администратора платформы
        try:
            admin = User.objects.get(username='admin')
            admin.role = 'admin'
            admin.is_staff = True
            admin.is_superuser = False
            admin.save()
            self.stdout.write(self.style.SUCCESS(f'✅ admin: role={admin.role}, staff={admin.is_staff}, super={admin.is_superuser}'))
        except User.DoesNotExist:
            self.stdout.write(self.style.WARNING('⚠️ Пользователь admin не найден'))

        # Исправляем владельца магазина
        try:
            store_owner = User.objects.get(username='store_owner')
            store_owner.role = 'store_owner'
            store_owner.is_staff = True
            store_owner.is_superuser = False
            store_owner.save()
            self.stdout.write(self.style.SUCCESS(f'✅ store_owner: role={store_owner.role}, staff={store_owner.is_staff}, super={store_owner.is_superuser}'))
        except User.DoesNotExist:
            self.stdout.write(self.style.WARNING('⚠️ Пользователь store_owner не найден'))

        # Исправляем второго владельца магазина (owner2)
        try:
            owner2 = User.objects.get(username='owner2')
            owner2.role = 'store_owner'
            owner2.is_staff = True
            owner2.is_superuser = False  # Убираем superuser статус!
            owner2.save()
            self.stdout.write(self.style.SUCCESS(f'✅ owner2: role={owner2.role}, staff={owner2.is_staff}, super={owner2.is_superuser}'))
        except User.DoesNotExist:
            self.stdout.write(self.style.WARNING('⚠️ Пользователь owner2 не найден'))

        # Исправляем администратора магазина
        try:
            store_admin = User.objects.get(username='store_admin')
            store_admin.role = 'store_admin'
            store_admin.is_staff = True
            store_admin.is_superuser = False
            store_admin.save()
            self.stdout.write(self.style.SUCCESS(f'✅ store_admin: role={store_admin.role}, staff={store_admin.is_staff}, super={store_admin.is_superuser}'))
        except User.DoesNotExist:
            self.stdout.write(self.style.WARNING('⚠️ Пользователь store_admin не найден'))

        self.stdout.write(self.style.SUCCESS('\n🎉 Исправление пользователей завершено!'))
        self.stdout.write(self.style.HTTP_INFO('\n📋 АРХИТЕКТУРА АДМИНОК:'))
        self.stdout.write('  👑 owner (владелец платформы) → /owner-admin/')
        self.stdout.write('  ⚙️ admin (админ платформы) → /owner-admin/')
        self.stdout.write('  🛍️ store_owner (владелец магазина) → /store-admin/ (склад + админы + статистика)')
        self.stdout.write('  🧑‍🌾 store_admin (админ магазина) → /store-admin/ (только склад)')
        self.stdout.write('\n🔗 Теперь /admin/ автоматически перенаправляет по ролям!')

        # Показываем итоговое состояние
        self.stdout.write(self.style.HTTP_INFO('\n📊 ИТОГОВОЕ СОСТОЯНИЕ ПОЛЬЗОВАТЕЛЕЙ:'))
        for user in User.objects.exclude(username__in=['testadmin', 'AnonymousUser']):
            self.stdout.write(f'  {user.username}: {user.role} (staff: {user.is_staff}, super: {user.is_superuser})')
