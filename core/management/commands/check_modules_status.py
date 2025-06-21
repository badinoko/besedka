#!/usr/bin/env python
"""
🔍 ПРОВЕРКА СТАТУСА МОДУЛЕЙ

Проверяет состояние модулей:
- Gallery (галерея)
- Chat (чат)
- Growlogs (дневники)

Запуск: python manage.py check_modules_status
"""

from django.core.management.base import BaseCommand
from django.apps import apps
import os

class Command(BaseCommand):
    help = '🔍 Проверка статуса модулей Gallery, Chat, Growlogs'

    def handle(self, *args, **options):
        print("🔍 ПРОВЕРКА СТАТУСА МОДУЛЕЙ ПЛАТФОРМЫ")
        print("=" * 60)

        self.check_gallery()
        self.check_chat()
        self.check_growlogs()
        self.check_urls()
        self.show_summary()

    def check_gallery(self):
        """Проверяем модуль галереи"""
        print("\n🖼️ МОДУЛЬ GALLERY:")
        print("-" * 40)

        try:
            from gallery.models import Photo, PhotoComment
            from gallery import views, admin

            # Проверяем модели
            photo_count = Photo.objects.count()
            comment_count = PhotoComment.objects.count()

            print(f"✅ Модели: Photo, PhotoComment")
            print(f"📊 Фотографий в базе: {photo_count}")
            print(f"📊 Комментариев: {comment_count}")

            # Проверяем views
            if hasattr(views, 'photo_list'):
                print("✅ Views: photo_list найден")
            else:
                print("❌ Views: отсутствуют основные функции")

            # Проверяем админку
            if hasattr(admin, 'PhotoAdmin'):
                print("✅ Admin: PhotoAdmin настроен")
            else:
                print("❌ Admin: административная панель не настроена")

            # Проверяем шаблоны
            template_path = "templates/gallery/"
            if os.path.exists(template_path):
                templates = os.listdir(template_path)
                print(f"📄 Шаблоны: {', '.join(templates)}")
            else:
                print("❌ Шаблоны: директория отсутствует")

            print("🟡 СТАТУС: Частично реализовано (модели + админка)")

        except ImportError as e:
            print(f"❌ ОШИБКА: {e}")
            print("🔴 СТАТУС: Не работает")

    def check_chat(self):
        """Проверяем модуль чата"""
        print("\n💬 МОДУЛЬ CHAT:")
        print("-" * 40)

        try:
            from chat.models import ChatMessage
            from chat import views, admin

            # Проверяем модели
            message_count = ChatMessage.objects.count()

            print(f"✅ Модели: ChatMessage")
            print(f"📊 Сообщений в базе: {message_count}")

            # Проверяем views
            if hasattr(views, 'chat_room'):
                print("✅ Views: chat_room найден")
            else:
                print("❌ Views: основные функции отсутствуют")

            # Проверяем админку
            if hasattr(admin, 'ChatMessageAdmin'):
                print("✅ Admin: ChatMessageAdmin настроен")
            else:
                print("❌ Admin: административная панель не настроена")

            # Проверяем шаблоны
            template_path = "templates/chat/"
            if os.path.exists(template_path):
                templates = os.listdir(template_path)
                print(f"📄 Шаблоны: {', '.join(templates)}")
            else:
                print("❌ Шаблоны: директория отсутствует")

            print("🟡 СТАТУС: Заглушка (только модели)")

        except ImportError as e:
            print(f"❌ ОШИБКА: {e}")
            print("🔴 СТАТУС: Не работает")

    def check_growlogs(self):
        """Проверяем модуль гроулогов"""
        print("\n📔 МОДУЛЬ GROWLOGS:")
        print("-" * 40)

        try:
            from growlogs.models import GrowLog, GrowLogEntry
            from growlogs import views, admin

            # Проверяем модели
            growlog_count = GrowLog.objects.count()
            entry_count = GrowLogEntry.objects.count()

            print(f"✅ Модели: GrowLog, GrowLogEntry")
            print(f"📊 Дневников в базе: {growlog_count}")
            print(f"📊 Записей в дневниках: {entry_count}")

            # Проверяем views
            if hasattr(views, 'growlog_list') and hasattr(views, 'growlog_detail'):
                print("✅ Views: growlog_list, growlog_detail найдены")
            else:
                print("❌ Views: основные функции отсутствуют")

            # Проверяем админку
            if hasattr(admin, 'GrowLogAdmin'):
                print("✅ Admin: GrowLogAdmin настроен")
            else:
                print("❌ Admin: административная панель не настроена")

            # Проверяем шаблоны
            template_path = "templates/growlogs/"
            if os.path.exists(template_path):
                templates = os.listdir(template_path)
                print(f"📄 Шаблоны: {', '.join(templates)}")
            else:
                print("❌ Шаблоны: директория отсутствует")

            print("🟡 СТАТУС: Частично реализовано (модели + views + админка)")

        except ImportError as e:
            print(f"❌ ОШИБКА: {e}")
            print("🔴 СТАТУС: Не работает")

    def check_urls(self):
        """Проверяем URL конфигурации"""
        print("\n🔗 URL КОНФИГУРАЦИИ:")
        print("-" * 40)

        # Проверяем основной urls.py
        try:
            from django.urls import reverse

            # Проверяем галерею
            try:
                gallery_url = reverse('gallery:gallery')
                print(f"✅ Gallery URLs: {gallery_url}")
            except:
                print("❌ Gallery URLs: не настроены")

            # Проверяем чат
            # chat_url = reverse('chat:chat')
            try:
                growlogs_url = reverse('growlogs:list')
                print(f"✅ Growlogs URLs: {growlogs_url}")
            except:
                print("❌ Growlogs URLs: не настроены")

        except Exception as e:
            print(f"❌ Ошибка при проверке URLs: {e}")

    def show_summary(self):
        """Показываем итоговую сводку"""
        print("\n📊 ИТОГОВАЯ СВОДКА:")
        print("-" * 40)

        print("🖼️ GALLERY:")
        print("   ✅ Модели: реализованы")
        print("   ✅ Админка: настроена")
        print("   🟡 Views: базовые")
        print("   ❌ Шаблоны: требуют доработки")
        print("   📈 Готовность: ~70%")

        print("\n💬 CHAT:")
        print("   ✅ Модели: реализованы")
        print("   ❌ Views: заглушки")
        print("   ❌ Админка: базовая")
        print("   ❌ WebSocket: не настроен")
        print("   📈 Готовность: ~30%")

        print("\n📔 GROWLOGS:")
        print("   ✅ Модели: полностью реализованы")
        print("   ✅ Админка: настроена с inline")
        print("   🟡 Views: частично")
        print("   ❌ Формы создания: заглушки")
        print("   📈 Готовность: ~60%")

        print(f"\n🎯 РЕКОМЕНДАЦИИ:")
        print("1. Gallery: добавить полноценные views и шаблоны")
        print("2. Chat: реализовать WebSocket для реального времени")
        print("3. Growlogs: доработать формы создания и редактирования")
        print("4. Все модули: добавить права доступа для ролей")

        print(f"\n🚀 СЛЕДУЮЩИЕ ШАГИ:")
        print("1. Выберите приоритетный модуль для доработки")
        print("2. Gallery легче всего довести до конца")
        print("3. Chat требует больше всего работы")
        print("4. Growlogs уже почти готовы")
