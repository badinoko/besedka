#!/usr/bin/env python3
"""
Проверка рендера страницы с аутентификацией
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
django.setup()

from django.test import Client
from users.models import User
from bs4 import BeautifulSoup
import re

def main():
    print("🔍 ПРОВЕРКА РЕНДЕРА СТРАНИЦЫ С АУТЕНТИФИКАЦИЕЙ")
    print("=" * 50)

    client = Client()

    # Логинимся как owner
    try:
        owner = User.objects.get(username='owner')
        client.force_login(owner)
        print(f"✅ Залогинились как: {owner.username}")
    except User.DoesNotExist:
        print("❌ Пользователь owner не найден!")
        return

    # Запрашиваем главную страницу
    response = client.get('/')
    print(f"📄 Запросили главную страницу: {response.status_code}")

    # Проверяем контекст
    if hasattr(response, 'context') and response.context:
        unread_count = response.context.get('unread_notifications_count', 'НЕ НАЙДЕНО')
        print(f"🔧 Из контекста: unread_notifications_count = {unread_count}")

    # Проверяем HTML
    html = response.content.decode('utf-8')

    # Ищем счетчик уведомлений
    soup = BeautifulSoup(html, 'html.parser')

    # Поиск notifications-badge
    badge = soup.find(class_='notifications-badge')
    if badge:
        print(f"✅ Найден notifications-badge: {badge}")
        print(f"   Текст в бейдже: '{badge.get_text().strip()}'")
        print(f"   Стили: {badge.get('style', 'нет стилей')}")
    else:
        print("❌ notifications-badge не найден")

    # Ищем в HTML напрямую по тексту
    pattern = r'notifications-badge[^>]*>([^<]*)'
    matches = re.findall(pattern, html)
    if matches:
        print(f"🔍 Найдены совпадения в HTML: {matches}")

    # Проверяем общий контекст переменных в HTML
    if 'unread_notifications_count' in html:
        print("✅ Переменная unread_notifications_count найдена в HTML")
        # Извлекаем её значение
        pattern = r'unread_notifications_count[^}]*?(\d+)'
        matches = re.findall(pattern, html)
        if matches:
            print(f"   Значения: {matches}")
    else:
        print("❌ Переменная unread_notifications_count НЕ найдена в HTML")

    # Сохраняем кусок HTML для анализа
    start_pos = html.find('notifications-badge')
    if start_pos != -1:
        snippet = html[max(0, start_pos-200):start_pos+200]
        print(f"\n📝 ФРАГМЕНТ HTML (±200 символов):")
        print(snippet)

    print(f"\n" + "=" * 50)
    print("✅ Проверка завершена!")

if __name__ == '__main__':
    main()
