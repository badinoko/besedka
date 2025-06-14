#!/usr/bin/env python
import os
import django

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
django.setup()

from news.models import Post

# Проверяем все посты
posts = Post.objects.all()
print(f"Всего постов: {posts.count()}")

print("\nПосты с пустыми slug'ами:")
empty_slug_posts = []
for post in posts:
    if not post.slug or post.slug.strip() == '':
        empty_slug_posts.append(post)
        print(f"ID: {post.id}, Title: '{post.title}', Slug: '{post.slug}', Status: {post.status}")

if not empty_slug_posts:
    print("Постов с пустыми slug'ами не найдено")

print(f"\nВсего постов с пустыми slug'ами: {len(empty_slug_posts)}")

# Проверяем опубликованные посты
published_posts = Post.published.all()
print(f"\nОпубликованных постов: {published_posts.count()}")

print("\nПервые 5 опубликованных постов:")
for post in published_posts[:5]:
    print(f"ID: {post.id}, Title: '{post.title}', Slug: '{post.slug}'")
