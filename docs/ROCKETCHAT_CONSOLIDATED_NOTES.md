# 📚 Консолидированный справочник по Rocket.Chat и серверной инфраструктуре

> Обновлено: 19 июня 2025

---

## 🪄 МАГИЧЕСКАЯ ПРОЦЕДУРА ПЕРЕЗАПУСКА (РЕШАЕТ ВСЕ ПРОБЛЕМЫ!)

### ⚡ СУПЕР-ПРОСТАЯ КОМАНДА (РЕКОМЕНДУЕТСЯ):
```bash
python scripts/magic_restart.py
```
**Это всё!** Скрипт автоматически:
- ✅ Безопасно перезапускает систему БЕЗ потери данных
- ✅ Автоматически настраивает Rocket.Chat 
- ✅ Проверяет что все работает
- ✅ **БОЛЬШЕ НЕ НУЖНО НАСТРАИВАТЬ ВРУЧНУЮ 16 РАЗ!**

### 🛠️ Ручная процедура (если нужна диагностика):

1. Полностью остановить все запущенные Python-процессы:
   ```bash
   taskkill /f /im python.exe
   ```
2. Перезапустить контейнеры (*web-1 должен быть УБИТ перед запуском!*):
   ```bash
   docker-compose -f docker-compose.local.yml stop web   # гарантируем, что web-1 не держит старый код
   docker-compose -f docker-compose.local.yml up -d postgres redis mongo rocketchat  # БЕЗ web!
   docker ps | cat                                       # проверяем, что работают postgres, redis, mongo, rocketchat
   ```
3. Запустить Django ТОЛЬКО через Daphne:
   ```bash
   daphne -b 127.0.0.1 -p 8001 config.asgi:application
   ```
4. Автоматическая настройка Rocket.Chat:
   ```bash
   python scripts/auto_rocketchat.py
   ```

---

## 🐳 Ключевые контейнеры Docker

| Контейнер        | Назначение           | Порт |
|------------------|----------------------|------|
| postgres         | База данных Django   | 5432 |
| redis            | Кэш / Celery broker  | 6379 |
| mongo            | База Rocket.Chat     | 27017|
| rocketchat       | Сам Rocket.Chat      | 3000 |
| web-1            | 🔥 **НЕ должен быть запущен** во время миграции (конфликт кода) |

> Если `web-1` автоматически поднимается, **сразу** выполнить `docker-compose -f docker-compose.local.yml stop web`.

---

## 🌐 Базовые URL окружения

| Сервис                | URL                                    |
|-----------------------|----------------------------------------|
| Django-сайт           | http://127.0.0.1:8001/                 |
| Rocket.Chat UI        | http://127.0.0.1:3000/                 |
| Rocket.Chat iframe    | встраивается на страницах Django       |
| Изолированный тест    | http://127.0.0.1:8001/chat/test/        |
| Интегрированный чат   | http://127.0.0.1:8001/chat/ (старый)   |

---

## 🔑 Унифицированные учётные данные

| Роль / сервис         | Логин              | Пароль               |
|-----------------------|--------------------|----------------------|
| Django Owner          | `owner`            | `owner123secure`     |
| Django Moderator      | `admin`            | `admin123secure`     |
| Django Store Owner    | `store_owner`      | `storeowner123secure`|
| Django Store Admin    | `store_admin`      | `storeadmin123secure`|
| Django Test User      | `test_user`        | `user123secure`      |
| Rocket.Chat Admin     | `owner`            | `owner123secure`     |

> **Никогда** не создаём дубликаты ключевых ролей. Для временных тестов используем `temp_*`.

---

## 🔐 OAuth «Besedka» (Custom provider в Rocket.Chat)

| Параметр              | Значение                                               |
|-----------------------|--------------------------------------------------------|
| Unique Name           | `besedka`                                              |
| URL                   | `http://127.0.0.1:8001`                                |
| Client ID             | `BesedkaRocketChat2025`                                |
| Client Secret         | `SecureSecretKey2025BesedkaRocketChatSSO`              |
| Authorize Path        | `/o/authorize/`                                        |
| Token Path            | `/o/token/`                                            |
| Identity Path         | `/api/v1/auth/rocket/`                                 |
| Scope                 | `read`                                                 |
| Param name token      | `access_token`                                         |
| Login Style           | `redirect`                                             |
| Button label          | «Войти через Беседку»                                  |
| Merge users           | `true`                                                 |
| Show button           | `true`                                                 |

### Роли → группы (JSON для поля mapping)
```json
{
  "owner": "admin,vip",
  "moderator": "admin",
  "user": "user"
}
```

---

## ⚙️ Настройки Rocket.Chat, обязательные для iframe/SSO

1. Administration → Settings → General → `Restrict access inside any Iframe` → **False**
2. Accounts → `Require password confirmation` → **Disabled**
3. Accounts → Two Factor Authentication → **Disabled** (TOTP off)
4. OAuth provider «Besedka» → `Enable` = **On**

> Без пункта 1 чат не загрузится во встраиваемый iframe на сайте.

---

## 📈 Текущее состояние интеграции (19 июня 2025)

- Rocket.Chat работает, аккаунт `owner` активен.
- Провайдер OAuth «Besedka» создан, но поля URL/paths **пока пустые** — требуется заполнить таблицей выше.
- Страница `/chat/rocketchat_integrated.html` ранее показывала три канала в iframe; сейчас выводит чистую страницу, т.к. шаблон был удалён при очистке.
- Отправка сообщений внутри Rocket.Chat (через прямой UI) функционирует — подтверждено скриншотом.
- Требуется восстановить интегрированный iframe-вид на стороне Django и повторно протестировать SSO.

---

## 📌 Что делать дальше

1. Заполнить все поля провайдера «Besedka» в Rocket.Chat как в таблице OAuth.
2. Проверить пункт *Restrict access inside any Iframe* = False.
3. Перезапустить **только** контейнер `rocketchat` (если меняли настройки через UI, не нужен полный down/up).
4. На Django-стороне открыть `/chat/test/` — авторизация через SSO должна пройти автоматически (без кнопки).
5. Если всё работает — вернуть (или создать) шаблон `rocketchat_integrated.html` и подключить на основную кнопку «Чат» сайта.

---

## 🛠️ Полезные команды

```bash
# Быстрый рестарт только rocketchat контейнера
docker-compose -f docker-compose.local.yml restart rocketchat

# Просмотр логов Rocket.Chat
docker-compose -f docker-compose.local.yml logs -f --tail=100 rocketchat | cat

# Проверка доступности сервисов
curl -I http://127.0.0.1:8001 | cat     # Django
curl -I http://127.0.0.1:3000 | cat     # Rocket.Chat
```

---

## 🔄 Ссылки на детальный План и Прогресс

- **План миграции:** `docs/ROCKETCHAT_MIGRATION_PLAN_V3.md` (последняя актуальная версия)
- **Журнал прогресса:** `docs/ROCKETCHAT_MIGRATION_PROGRESS.md`

> Все новые изменения фиксируем **только** в этих двух файлах, чтобы избежать хаоса.

---

## 📝 Источник сведений

Информация собрана из:
- `BESEDKA_MASTER_DOCUMENTATION.md`
- `BESEDKA_UI_STANDARDS.md`
- `BESEDKA_USER_SYSTEM.md`
- `CHANGELOG.md`
- `docs/ROCKETCHAT_*.md`

---

> **Важно:** Этот файл служит личным «шпаргалкой» для разработчика и не является частью официальной пользовательской документации. Держите его актуальным, но избегайте излишних деталей — только критически важные команды, логины и параметры. 

---

## 🔧 СОЗДАНИЕ КАНАЛОВ VIP И MODERATORS (20 июня 2025)

**Статус:** Скрипты готовы к запуску после настройки OAuth

### Команды для создания каналов:
```bash
# Через Python скрипт (рекомендуется)
python scripts/create_channels.py

# Предварительно установить pymongo:
pip install pymongo
```

### Создаваемые каналы:
- **#vip** — Приватный VIP чат для премиум пользователей  
- **#moderators** — Приватный канал для модераторов и администраторов
- **#general** — Настройка как канал по умолчанию

---

## 🚫 УСТРАНЕНИЕ КНОПКИ "JOIN THE CHANNEL" (20 июня 2025)

**Проблема:** При входе в канал появляется промежуточная кнопка "Join the Channel"

**Решение включено в скрипт:** `python scripts/create_channels.py`

**Или через UI Rocket.Chat:**
1. Administration → Settings → Accounts
2. Default User Preferences → Join Default Channels: **True**
3. Default User Preferences → Join Default Channels Silenced: **False**  
4. Сохранить изменения

**Дополнительно:** В поле "Открыть канал после авторизации" указать `general`

---

## 🛠️ ИСПРАВЛЕНИЯ 20 ИЮНЯ 2025

### ✅ Исправлен API endpoint для аутентификации:
- **Путь:** `/chat/api/auth/` (вместо `/api/chat/auth/`)
- **View:** `RocketChatAuthAPIView` создан в `chat/views.py`
- **Результат:** Устранены ошибки 404 в логах Django

### ✅ Обновлены данные для репозиториев:
- **BESEDKA_COPY** — только по указанию пользователя
- **БЕСЕДКА** — в полное распоряжение ИИ-ассистентов

---
