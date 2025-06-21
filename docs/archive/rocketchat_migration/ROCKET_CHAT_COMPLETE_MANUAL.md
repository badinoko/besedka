# 🎯 ПОЛНАЯ ИНСТРУКЦИЯ ROCKET.CHAT OAUTH - ВСЕ ПОЛЯ!

**Дата:** 21 июня 2025 г.  
**Источник:** Реальные скриншоты пользователя + Django база данных  
**Статус:** ИСЧЕРПЫВАЮЩАЯ ИНСТРУКЦИЯ  

---

## 🏃‍♂️ БЫСТРЫЙ СТАРТ - АВТОМАТИЧЕСКИЙ СКРИПТ

```bash
# Запустите этот скрипт для автоматической настройки:
python scripts/rocket_chat_full_oauth_setup.py
```

**Если скрипт не работает - используйте ручную настройку ниже!**

---

## 🛠️ РУЧНАЯ НАСТРОЙКА - ПОЛНАЯ ИНСТРУКЦИЯ

### ОТКРЫТЬ АДМИНКУ ROCKET.CHAT:
1. http://127.0.0.1:3000
2. Логин: `owner` / Пароль: `owner123secure`
3. Administration → Settings → OAuth → Add Custom OAuth

---

## 📋 ВСЕ ПОЛЯ OAUTH НАСТРОЕК (ПОЛНАЯ ТАБЛИЦА)

### 🔧 ОСНОВНЫЕ НАСТРОЙКИ

| Поле | Значение | Обязательно |
|------|----------|-------------|
| **Unique Name** | `besedka` | ✅ ДА |
| **Enable** | ✅ ON | ✅ ДА |
| **URL** | `http://127.0.0.1:8001` | ✅ ДА |
| **Token Path** | `/o/token/` | ✅ ДА |
| **Token Sent Via** | `Header` | ⚪ AUTO |
| **Identity Token Sent Via** | `Default` | ⚪ AUTO |
| **Identity Path** | `/api/v1/auth/rocket/` | ✅ ДА |
| **Authorize Path** | `/o/authorize/` | ✅ ДА |
| **Scope** | `read` | ✅ ДА |
| **Access Token Param** | `access_token` | ✅ ДА |
| **Id** | `BesedkaRocketChat2025` | ✅ ДА |
| **Secret** | `SecureSecretKey2025BesedkaRocketChatSSO` | ✅ ДА |

### 🎨 ВНЕШНИЙ ВИД КНОПКИ

| Поле | Значение | Обязательно |
|------|----------|-------------|
| **Login Style** | `redirect` | ✅ ДА |
| **Button Text** | `Войти через Беседку` | ✅ ДА |
| **Button Color** | `#1d74f5` | ⚪ НЕТ |
| **Button Text Color** | `#FFFFFF` | ⚪ НЕТ |

### 👤 ПОЛЯ ПОЛЬЗОВАТЕЛЯ

| Поле | Значение | Обязательно |
|------|----------|-------------|
| **Username field** | `username` | ✅ ДА |
| **Email field** | `email` | ✅ ДА |
| **Name field** | `full_name` | ✅ ДА |
| **Avatar field** | `avatar_url` | ⚪ НЕТ |

### 🔐 РОЛИ И ГРУППЫ

| Поле | Значение | Обязательно |
|------|----------|-------------|
| **Roles field** | `roles` | ✅ ДА |
| **Groups field** | `groups` | ✅ ДА |
| **Roles to sync** | `admin,moderator,vip,user` | ✅ ДА |

### 🎯 МАППИНГ ГРУПП И КАНАЛОВ

| Поле | Значение | Описание |
|------|----------|----------|
| **Channel/Group mapping** | `{"owner":"admin,vip","moderator":"admin","user":"user"}` | JSON маппинг ролей |

**Пример заполнения поля "Сопоставление групп и каналов OAuth":**
```json
{
  "owner": "admin,vip",
  "moderator": "admin", 
  "user": "user"
}
```

### ⚙️ ПЕРЕКЛЮЧАТЕЛИ (ВСЕ ВКЛЮЧИТЬ!)

| Настройка | Значение | Критично |
|-----------|----------|----------|
| **Merge users** | ✅ ON | ✅ ДА |
| **Show Button** | ✅ ON | ✅ ДА |
| **Map Channels** | ✅ ON | ✅ ДА |
| **Merge Roles** | ✅ ON | ✅ ДА |

---

## 🔧 ДОПОЛНИТЕЛЬНЫЕ НАСТРОЙКИ ROCKET.CHAT

### 1. IFRAME ПОДДЕРЖКА (КРИТИЧЕСКИ ВАЖНО!)
```
Administration → Settings → General
Restrict access inside any Iframe → ❌ OFF
```

### 2. ОТКЛЮЧИТЬ 2FA
```
Administration → Settings → Accounts
Require password confirmation → ❌ OFF
Two Factor Authentication → ❌ OFF
```

### 3. АВТОМАТИЧЕСКОЕ ПРИСОЕДИНЕНИЕ К КАНАЛАМ
```
Administration → Settings → Accounts
Join Default Channels → ✅ ON
Join Default Channels Silenced → ❌ OFF
```

---

## 🧪 ТЕСТИРОВАНИЕ

### ПРОВЕРКА №1: КНОПКА ОТОБРАЖАЕТСЯ
1. Открыть http://127.0.0.1:3000/login
2. ✅ Должна быть кнопка "Войти через Беседку"

### ПРОВЕРКА №2: ИНТЕГРАЦИЯ РАБОТАЕТ
1. Открыть http://127.0.0.1:8001/chat/integrated/
2. Войти как `owner` / `owner123secure`
3. Нажать "Войти через Беседку" в Rocket.Chat
4. ✅ Должно произойти автоматическое перенаправление и вход

---

## ⚠️ ВАЖНЫЕ ЗАМЕТКИ

- **НЕ ОСТАВЛЯЙТЕ поля пустыми** - заполните ВСЕ обязательные поля
- **ПРОВЕРЬТЕ JSON** - скопируйте маппинг точно как указано
- **ВКЛЮЧИТЕ ВСЕ переключатели** - Map Channels, Merge Users, Merge Roles, Show Button
- **НЕ ЗАБУДЬТЕ iframe настройки** - без этого интеграция не работает

---

## 🚀 ЕСЛИ ВСЕ РАБОТАЕТ:

После успешной настройки вы должны увидеть:
1. ✅ Кнопку "Войти через Беседку" на http://127.0.0.1:3000/login
2. ✅ Автоматический вход пользователей Django в Rocket.Chat
3. ✅ Правильное присвоение ролей и доступ к каналам

**УДАЧИ! 🎉** 
