# 🌱 Беседка - Комплексная Платформа для Растениеводов

![Django](https://img.shields.io/badge/Django-4.2-092E20?style=for-the-badge&logo=django&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-DC382D?style=for-the-badge&logo=redis&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)

## 📖 Описание

**Беседка** - это инновационная веб-платформа, объединяющая социальную сеть для растениеводов и полнофункциональный интернет-магазин семян. Проект создан для сообщества энтузиастов выращивания растений, предоставляя им все необходимые инструменты для обмена опытом, ведения дневников роста и приобретения качественных семян.

## ✨ Основные Возможности

### 🏪 Интернет-магазин "Magic Beans"
- **Каталог семян** с детальными характеристиками сортов
- **Корзина и система заказов** с различными способами оплаты
- **Административная панель** для управления товарами и заказами
- **Система промокодов и скидок**
- **Отчеты по продажам и аналитика**

### 👥 Социальная Сеть
- **Профили пользователей** с настройками приватности
- **Система ролей**: Owner, Admin, Store Owner, Store Admin, User
- **Уведомления** о лайках, комментариях и других активностях
- **Безопасная авторизация** через Django Allauth + Telegram Login

### 📔 Гроу-Дневники (GrowLogs)
- **Создание дневников роста** с фотографиями и записями
- **Публичные и приватные дневники**
- **Лайки и комментарии** к записям
- **Система тегов** для категоризации

### 📸 Галерея Сообщества
- **Загрузка и демонстрация фотографий** растений
- **Система оценок и комментариев**
- **Фильтрация по категориям и тегам**

### 💬 Чат Сообщества
- **Общий чат** для всех пользователей
- **VIP-комнаты** для избранных участников
- **WebSocket соединения** для мгновенного обмена сообщениями
- **Модерация чата** с системой банов

### 📰 Новостной Модуль
- **Автоматический парсинг новостей** из различных источников
- **Система категорий и тегов**
- **Перевод новостей** с помощью AI

## 🚀 Технологии

### Backend
- **Django 4.2** - основной фреймворк
- **Python 3.12** - язык программирования
- **PostgreSQL** - основная база данных
- **Redis** - кеширование и сессии
- **Django Channels** - WebSocket поддержка
- **Celery** - асинхронные задачи

### Frontend
- **Bootstrap 5** - UI framework
- **JavaScript (ES6+)** - интерактивность
- **WebSocket API** - реальное время

### DevOps
- **Docker & Docker Compose** - контейнеризация
- **Nginx** - веб-сервер (в продакшене)
- **Gunicorn/Daphne** - WSGI/ASGI серверы

## 🏗️ Архитектура

Проект построен на модульной архитектуре Django с разделением на отдельные приложения:

```
besedka/
├── core/              # Основные компоненты и утилиты
├── users/             # Система пользователей и ролей
├── chat/              # Чат и WebSocket функциональность
├── gallery/           # Галерея изображений
├── growlogs/          # Дневники роста
├── news/              # Новостной модуль
├── magicbeans_store/  # Интернет-магазин
├── api/               # REST API
└── templates/         # Шаблоны HTML
```

## 📋 Требования

- Python 3.12+
- PostgreSQL 13+
- Redis 6+
- Docker & Docker Compose (опционально)

## 🛠️ Установка и Запуск

### С использованием Docker (рекомендуется)

```bash
# Клонирование репозитория
git clone https://github.com/badinoko/besedka.git
cd besedka

# Запуск с помощью Docker Compose
docker-compose -f docker-compose.local.yml up --build
```

### Локальная установка

```bash
# Клонирование репозитория
git clone https://github.com/badinoko/besedka.git
cd besedka

# Создание виртуального окружения
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# Установка зависимостей
pip install -r requirements/local.txt

# Настройка переменных окружения
cp .env.example .env
# Отредактируйте .env файл

# Миграции базы данных
python manage.py migrate

# Создание суперпользователя
python manage.py createsuperuser

# Запуск сервера разработки
python manage.py runserver
```

### WebSocket сервер (для чата)

WebSocket сервер автоматически запускается в Docker контейнере. Для локальной разработки без Docker:

```bash
# ТОЛЬКО для локальной разработки без Docker
daphne -p 8001 config.asgi:application
```

## 🔧 Настройка

### Переменные окружения

Создайте файл `.env` в корне проекта:

```env
# Database
DATABASE_URL=postgres://user:password@localhost:5432/besedka

# Redis
REDIS_URL=redis://localhost:6379/0

# Django
SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Email (опционально)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

## 👤 Система Ролей

| Роль | Описание | Возможности |
|------|----------|------------|
| **Owner** | Владелец платформы | Полный доступ ко всем функциям |
| **Admin** | Модератор платформы | Модерация контента, управление пользователями |
| **Store Owner** | Владелец магазина | Управление магазином и товарами |
| **Store Admin** | Администратор магазина | Обработка заказов, управление товарами |
| **User** | Обычный пользователь | Создание контента, покупки |

## 📚 API

Проект предоставляет REST API для интеграции с внешними сервисами:

- `GET /api/products/` - Список товаров
- `POST /api/orders/` - Создание заказа
- `GET /api/growlogs/` - Список дневников
- `POST /api/photos/` - Загрузка фотографий

Полная документация API доступна по адресу `/api/docs/`

## 🧪 Тестирование

```bash
# Запуск всех тестов
python manage.py test

# Запуск конкретного приложения
python manage.py test users

# Запуск с покрытием
coverage run --source='.' manage.py test
coverage report
```

## 📦 Развертывание

### Продакшн с Docker

```bash
# Сборка и запуск в продакшене
docker-compose -f docker-compose.production.yml up -d

# Применение миграций
docker-compose -f docker-compose.production.yml exec django python manage.py migrate

# Сбор статических файлов
docker-compose -f docker-compose.production.yml exec django python manage.py collectstatic --noinput
```

## 🤝 Участие в Разработке

1. Форкните репозиторий
2. Создайте ветку для новой функции (`git checkout -b feature/amazing-feature`)
3. Зафиксируйте изменения (`git commit -m 'Add amazing feature'`)
4. Отправьте изменения в ветку (`git push origin feature/amazing-feature`)
5. Откройте Pull Request

## 📄 Лицензия

Этот проект лицензирован под MIT License - см. файл [LICENSE](LICENSE) для деталей.

## 📞 Контакты

- **GitHub**: [@badinoko](https://github.com/badinoko)
- **Проект**: [besedka](https://github.com/badinoko/besedka)

## 🙏 Благодарности

- Django сообществу за отличный фреймворк
- Bootstrap команде за UI компоненты
- Всем участникам сообщества растениеводов

---

⭐ **Поставьте звездочку этому проекту, если он был полезен!**
