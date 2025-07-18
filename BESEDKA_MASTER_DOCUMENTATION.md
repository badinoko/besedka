# 🏗️ Проект "Беседка" - Мастер Документация

**Версия:** 13.0 – Переход на управляемую разработку чата (Июль 2025)
**Дата обновления:** 18 июля 2025 года
**Статус:** **Активная фаза разработки кастомного чата по "Чертежу" (Telegram-like)** 💬

---

## 📚 СТРУКТУРА ДОКУМЕНТАЦИИ

Это главный документ проекта. Ключевые документы:

- **[docs/TELEGRAM_CHAT_BLUEPRINT.md](docs/TELEGRAM_CHAT_BLUEPRINT.md)** — **(НОВЫЙ SSOT)** Технический и продуктовый чертеж для создания кастомного чата. **Это наш главный ориентир.**
- **[docs/CUSTOM_CHAT_DEVELOPMENT_ROADMAP.md](docs/CUSTOM_CHAT_DEVELOPMENT_ROADMAP.md)** — **(АКТУАЛЬНО)** Дорожная карта разработки чата, основанная на "Чертеже". **Здесь мы отслеживаем прогресс.**
- **[BESEDKA_USER_SYSTEM.md](BESEDKA_USER_SYSTEM.md)** — Эталонная система ролей, пользователей и прав доступа.
- **[BESEDKA_UI_STANDARDS.md](BESEDKA_UI_STANDARDS.md)** — Эталонные стандарты UI/UX, компоненты и цветовые схемы.

---

## 🌟 ОБЩЕЕ ОПИСАНИЕ ПРОЕКТА

"Беседка" - это комплексная веб-платформа, объединяющая:
- Интернет-магазин семян "Magic Beans".
- Социальную сеть для растениеводов.
- Систему гроу-репортов.
- Галерею сообщества с фотографиями.
- **Кастомный чат в реальном времени на Django Channels (в процессе полной переработки).**
- Новостной хаб с парсером.
- Инструменты для аналитики и отчетности.
- Прототип AI-ассистента для пользователей.

Проект создан с использованием современных веб-технологий и архитектурных принципов (таких как SSOT - Single Source of Truth) для обеспечения масштабируемости, безопасности и высокой производительности.

---

## 🚀 АРХИТЕКТУРА ПРОЕКТА

Проект "Беседка" разработан на основе модульной архитектуры с использованием следующих технологий и принципов:

- **Backend:** Django (Python), Django REST Framework, Django Channels.
- **Frontend:** HTML, CSS (Sass), JavaScript (ванильный JS, без тяжелых фреймворков).
- **База данных:** PostgreSQL.
- **Кэширование/Брокер сообщений:** Redis.
- **Развертывание:** Docker, Docker Compose.
- **Принципы:** SSOT, DRY (Don't Repeat Yourself), Clean Architecture.

---

## ⚙️ УСТАНОВКА И ЗАПУСК (Development)

Для запуска проекта в режиме разработки выполните следующие шаги:

1.  **Клонируйте репозиторий:**
    ```bash
    git clone [https://github.com/badinoko/besedka.git](https://github.com/badinoko/besedka.git)
    cd besedka
    ```

2.  **Настройте переменные окружения:**
    Создайте файл `.env` в корневой директории проекта и заполните его необходимыми переменными (примеры смотрите в `.env.example`):
    ```
    SECRET_KEY=your_secret_key
    DEBUG=True
    DATABASE_URL=postgres://user:password@db:5432/dbname
    REDIS_URL=redis://redis:6379/0
    # Дополнительные переменные, такие как настройки для email, сторонних API и т.д.
    ```

3.  **Соберите и запустите Docker-контейнеры:**
    Убедитесь, что Docker и Docker Compose установлены.
    ```bash
    docker-compose up --build
    ```
    Это запустит PostgreSQL, Redis и Django-приложение.

4.  **Выполните миграции базы данных:**
    ```bash
    docker-compose exec django python manage.py migrate
    ```

5.  **Создайте суперпользователя (по желанию):**
    ```bash
    docker-compose exec django python manage.py createsuperuser
    ```

6.  **Доступ к приложению:**
    Приложение будет доступно по адресу `http://localhost:8000`.

---

## 🎯 ДОСТИГНУТЫЕ ЦЕЛИ

**Проект "Беседка" успешно завершен и представляет собой:**

1.  **🏗️ Современную веб-платформу** с передовой SSOT-архитектурой
2.  **💎 Элегантный пользовательский интерфейс** с 3D-элементами и анимациями
3.  **🔒 Безопасную систему** с контролем доступа и защитой от манипуляций
4.  **⚡ Высокопроизводительное решение** с оптимизированными запросами
5.  **📱 Адаптивную платформу** для всех типов устройств
6.  **🚀 Готовый к масштабированию продукт** для коммерческого использования

**ПРОЕКТ ГОТОВ К РАЗВЕРТЫВАНИЮ В ПРОДАКШН!** 🎉

---

## 🗂️ Работа с Git-репозиториями

| Репозиторий | URL | Права push | Назначение |
| :---------- | :-- | :--------- | :--------- |
| **origin** | `https://github.com/badinoko/besedka` | ❌ ТОЛЬКО ПО КОМАНДЕ | Основной рабочий репозиторий проекта |
| **backup** | `https://github.com/badinoko/besedka_copy` | Только по прямой команде пользователя | Резервная копия, защищённая от случайных изменений |

### Стандартный workflow

```bash
# Проверить изменения
git status

# Добавить/обновить файлы
git add -A

# Коммит
git commit -m "Краткое описание изменений"

# Push в основной репозиторий (ТОЛЬКО по команде пользователя!)
# Это должно быть выполнено только после утверждения изменений
# git push origin main
```
