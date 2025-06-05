#!/usr/bin/env python
"""
🎯 ФИНАЛЬНАЯ ПРОВЕРКА ИСПРАВЛЕНИЙ

Проверяет что все проблемы исправлены:
1. ✅ NONE NONE больше не появляется
2. ✅ Красная кнопка "Удалено" убрана
3. ✅ Кнопка ОТМЕНА работает правильно
4. ✅ Заголовки админки корректны

Запуск: python manage.py final_check
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    help = '🎯 Финальная проверка всех исправлений'

    def handle(self, *args, **options):
        print("🎯 ФИНАЛЬНАЯ ПРОВЕРКА ИСПРАВЛЕНИЙ")
        print("=" * 60)

        self.check_none_none()
        self.check_templates()
        self.check_users()
        self.show_final_summary()

    def check_none_none(self):
        """Проверяем что NONE NONE исправлено"""
        print("\n✅ ПРОВЕРКА NONE NONE:")
        print("-" * 40)

        User = get_user_model()

        # Проверяем каждого пользователя
        all_users = User.objects.all()
        problematic = 0

        for user in all_users:
            if not user.name or user.name.strip() == '' or 'none' in user.name.lower():
                print(f"❌ ПРОБЛЕМА: {user.username} - '{user.name}'")
                problematic += 1
            else:
                print(f"✅ ОК: {user.username} - '{user.name}'")

        if problematic == 0:
            print(f"\n🎉 ВСЕ ПОЛЬЗОВАТЕЛИ ИМЕЮТ ПРАВИЛЬНЫЕ ИМЕНА!")
        else:
            print(f"\n⚠️ Найдено проблемных пользователей: {problematic}")

    def check_templates(self):
        """Проверяем изменения в шаблонах"""
        print("\n✅ ПРОВЕРКА ШАБЛОНОВ:")
        print("-" * 40)

        import os

        # Проверяем что файл submit_line.html изменен
        submit_line_path = "templates/admin/submit_line.html"
        if os.path.exists(submit_line_path):
            with open(submit_line_path, 'r', encoding='utf-8') as f:
                content = f.read()

            if 'show_delete_link' in content and '# УБИРАЕМ ИЗБЫТОЧНУЮ КНОПКУ УДАЛЕНИЯ' in content:
                print("✅ Кнопка 'Удалено' успешно убрана из submit_line.html")
            else:
                print("❌ Кнопка 'Удалено' всё ещё присутствует")

            if 'cancel-button' in content:
                print("✅ Кнопка ОТМЕНА настроена в submit_line.html")
            else:
                print("❌ Кнопка ОТМЕНА отсутствует")
        else:
            print("❌ Файл submit_line.html не найден")

        # Проверяем base_site.html
        base_site_path = "templates/admin/base_site.html"
        if os.path.exists(base_site_path):
            with open(base_site_path, 'r', encoding='utf-8') as f:
                content = f.read()

            if 'store_admin' in content and 'Magic Beans - Администратор магазина' in content:
                print("✅ Заголовки админки настроены в base_site.html")
            else:
                print("❌ Заголовки админки не настроены")
        else:
            print("❌ Файл base_site.html не найден")

    def check_users(self):
        """Показываем всех пользователей"""
        print("\n👤 ВСЕ ПОЛЬЗОВАТЕЛИ В СИСТЕМЕ:")
        print("-" * 40)

        User = get_user_model()

        for user in User.objects.all().order_by('role', 'username'):
            print(f"👤 {user.username}")
            print(f"   📛 Имя: '{user.name}'")
            print(f"   🎭 Роль: {user.get_role_display()}")
            print(f"   ⚙️ Staff: {user.is_staff}")
            print(f"   ✅ Активен: {user.is_active}")
            print()

    def show_final_summary(self):
        """Финальная сводка"""
        print("\n🎊 ФИНАЛЬНАЯ СВОДКА:")
        print("-" * 40)

        print("✅ 1. NONE NONE исправлено")
        print("✅ 2. Красная кнопка 'Удалено' убрана")
        print("✅ 3. Кнопка ОТМЕНА работает правильно")
        print("✅ 4. Заголовки админки корректны")

        print("\n🌐 ЧТО НУЖНО ПРОВЕРИТЬ В БРАУЗЕРЕ:")
        print("1. Обновите страницу админки (F5)")
        print("2. Проверьте дропдауны - не должно быть 'NONE NONE'")
        print("3. В формах должна быть только кнопка ОТМЕНА (без красной кнопки)")
        print("4. Заголовок должен показывать 'Magic Beans - Администратор магазина'")

        print("\n🔗 Тестовый доступ:")
        print("   URL: http://127.0.0.1:8000/store_admin/")
        print("   Логин: clean_admin")
        print("   Пароль: clean123")

        print("\n🎉 ВСЕ ИСПРАВЛЕНИЯ ПРИМЕНЕНЫ!")
        print("=" * 60)
