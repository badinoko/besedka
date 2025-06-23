#!/usr/bin/env python
"""
Сохранение содержимого страницы входа для анализа
"""

import requests

try:
    print("🔍 Получение страницы входа...")
    response = requests.get("http://127.0.0.1:8001/accounts/login/")

    print(f"Статус: {response.status_code}")
    print(f"Размер: {len(response.text)} символов")

    # Сохраняем содержимое
    with open("login_page_content.html", "w", encoding='utf-8') as f:
        f.write(response.text)

    print("✅ Содержимое сохранено в login_page_content.html")

    # Показываем первые 1000 символов
    print("\n📄 Первые 1000 символов:")
    print("-" * 50)
    print(response.text[:1000])
    print("-" * 50)

    # Ищем ключевые слова
    keywords = ['<form', 'login', 'username', 'password', 'csrf', 'allauth', 'auth']
    print(f"\n🔍 Поиск ключевых слов:")

    for keyword in keywords:
        count = response.text.lower().count(keyword.lower())
        if count > 0:
            print(f"   {keyword}: найдено {count} раз")
        else:
            print(f"   {keyword}: НЕ найдено")

except Exception as e:
    print(f"❌ Ошибка: {e}")
