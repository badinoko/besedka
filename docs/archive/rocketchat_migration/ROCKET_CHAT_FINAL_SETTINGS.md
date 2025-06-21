# 🎯 ТОЧНЫЕ НАСТРОЙКИ ROCKET.CHAT - ЕДИНСТВЕННЫЙ ИСТОЧНИК ПРАВДЫ

**Дата:** 21 июня 2025 г.  
**Статус:** ФИНАЛЬНЫЕ РАБОЧИЕ НАСТРОЙКИ  
**Источник:** Реальные данные из Django базы данных  

---

## 🔑 OAUTH ПРИЛОЖЕНИЕ В DJANGO (ГОТОВО)

✅ **Client ID:** `BesedkaRocketChat2025`  
✅ **Client Secret:** `SecureSecretKey2025BesedkaRocketChatSSO`  
✅ **Skip Authorization:** `True` (автоматическое одобрение)  
✅ **API Endpoint:** http://127.0.0.1:8001/api/v1/auth/rocket/ (HTTP 401 - требует авторизации)  

---

## 🛠️ НАСТРОЙКИ В ROCKET.CHAT АДМИНКЕ

### ШАГ 1: ЗАЙТИ В АДМИНКУ
1. Открыть http://127.0.0.1:3000
2. Войти как `owner` / `owner123secure`
3. Administration → Settings → OAuth → Add Custom OAuth

### ШАГ 2: ОСНОВНЫЕ НАСТРОЙКИ

| Поле | Значение |
|------|----------|
| **Unique Name** | `besedka` |
| **Enable** | ✅ ON |
| **URL** | `http://127.0.0.1:8001` |
| **Token Path** | `/o/token/` |
| **Identity Path** | `/api/v1/auth/rocket/` |
| **Authorize Path** | `/o/authorize/` |
| **Scope** | `read` |
| **Param name for token** | `access_token` |
| **Id** | `BesedkaRocketChat2025` |
| **Secret** | `SecureSecretKey2025BesedkaRocketChatSSO` |

### ШАГ 3: ВНЕШНИЙ ВИД КНОПКИ

| Поле | Значение |
|------|----------|
| **Login Style** | `redirect` |
| **Button Text** | `Войти через Беседку` |
| **Button Color** | `#1d74f5` |
| **Button Text Color** | `#FFFFFF` |

### ШАГ 4: ПОЛЯ ПОЛЬЗОВАТЕЛЯ

| Поле | Значение |
|------|----------|
| **Username field** | `username` |
| **Email field** | `email` |
| **Name field** | `full_name` |
| **Avatar field** | `avatar_url` |
| **Roles field** | `roles` |
| **Groups field** | `groups` |

### ШАГ 5: МАППИНГ РОЛЕЙ И ГРУПП

| Поле | Значение |
|------|----------|
| **Roles to sync** | `admin,moderator,vip,user` |
| **Channel/Group mapping** | `{"owner":"admin,vip","moderator":"admin","user":"user"}` |

### ШАГ 6: ПЕРЕКЛЮЧАТЕЛИ

| Настройка | Значение |
|-----------|----------|
| **Merge users** | ✅ ON |
| **Show Button** | ✅ ON |
| **Map Channels** | ✅ ON |
| **Merge Roles** | ✅ ON |

---

## 🔧 ДОПОЛНИТЕЛЬНЫЕ НАСТРОЙКИ ROCKET.CHAT

### IFRAME ПОДДЕРЖКА (КРИТИЧЕСКИ ВАЖНО!)
1. Administration → Settings → General
2. **Restrict access inside any Iframe** → ❌ OFF

### ОТКЛЮЧИТЬ 2FA (для простоты настройки)
1. Administration → Settings → Accounts
2. **Require password confirmation** → ❌ OFF
3. **Two Factor Authentication** → ❌ OFF

---

## 🧪 ТЕСТИРОВАНИЕ

### ПРОВЕРКА №1: КНОПКА ОТОБРАЖАЕТСЯ
1. Открыть http://127.0.0.1:3000/login
2. Должна быть кнопка "Войти через Беседку"

### ПРОВЕРКА №2: ИНТЕГРАЦИЯ РАБОТАЕТ
1. Открыть http://127.0.0.1:8001/chat/integrated/
2. Войти как `owner` / `owner123secure`
3. Нажать "Войти через Беседку" в Rocket.Chat
4. Должно произойти автоматическое перенаправление и вход

---

## ⚠️ ВАЖНЫЕ ЗАМЕТКИ

- **НЕ МЕНЯТЬ Client ID и Secret** - они синхронизированы с Django
- **НЕ СОЗДАВАТЬ новые OAuth провайдеры** - используйте только `besedka`
- **ПРОВЕРИТЬ iframe настройки** - без этого интеграция не работает
- **Все поля обязательны** - пустые поля = неработающая интеграция

---

## 🗑️ СТАРЫЕ ФАЙЛЫ (УДАЛИТЬ)

Следующие файлы содержат УСТАРЕВШИЕ настройки и создают путаницу:
- `rocket_chat_oauth_credentials.txt` (устарел)
- `nuclear_oauth_reset.js` (устарел)
- `hijack_ghost.js` (устарел)
- `fix_oauth_clean.js` (устарел)

**ИСПОЛЬЗУЙТЕ ТОЛЬКО ЭТОТ ФАЙЛ!** 
