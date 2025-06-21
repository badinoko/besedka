# 🎯 ФИНАЛЬНЫЕ ИНСТРУКЦИИ ROCKET.CHAT OAUTH

**⚠️ ИСПРАВЛЕНЫ ВСЕ ОШИБКИ!** ✅  
**Дата:** 21 июня 2025 г.  
**Основано на:** Скриншотах пользователя + реальных данных Django  

---

## 🚀 ДВА ВАРИАНТА НАСТРОЙКИ

### ВАРИАНТ 1: АВТОМАТИЧЕСКИЙ СКРИПТ
```bash
python scripts/rocket_chat_full_oauth_setup.py
```

### ВАРИАНТ 2: РУЧНАЯ НАСТРОЙКА (ГАРАНТИРОВАННО РАБОТАЕТ)

---

## 📋 РУЧНАЯ НАСТРОЙКА - ПОЛНАЯ ТАБЛИЦА

### ШАГ 1: ЗАЙТИ В ROCKET.CHAT АДМИНКУ
1. http://127.0.0.1:3000
2. Логин: `owner` / Пароль: `owner123secure` 
3. Administration → Settings → OAuth → Add Custom OAuth

### ШАГ 2: ЗАПОЛНИТЬ ВСЕ ПОЛЯ

| Поле | Точное значение | Критично |
|------|-----------------|----------|
| **Unique Name** | `besedka` | ✅ |
| **Enable** | ✅ ON | ✅ |
| **URL** | `http://127.0.0.1:8001` | ✅ |
| **Token Path** | `/o/token/` | ✅ |
| **Token Sent Via** | `Header` | ⚪ |
| **Identity Token Sent Via** | `Default` | ⚪ |
| **Identity Path** | `/api/v1/auth/rocket/` | ✅ |
| **Authorize Path** | `/o/authorize/` | ✅ |
| **Scope** | `read` | ✅ |
| **Access Token Param** | `access_token` | ✅ |
| **Id** | `BesedkaRocketChat2025` | ✅ |
| **Secret** | `SecureSecretKey2025BesedkaRocketChatSSO` | ✅ |
| **Login Style** | `redirect` | ✅ |
| **Button Text** | `Войти через Беседку` | ✅ |
| **Button Color** | `#1d74f5` | ⚪ |
| **Button Text Color** | `#FFFFFF` | ⚪ |
| **Username field** | `username` | ✅ |
| **Email field** | `email` | ✅ |
| **Name field** | `full_name` | ✅ |
| **Avatar field** | `avatar_url` | ⚪ |

### ⚠️ КРИТИЧЕСКИ ВАЖНО - РОЛИ И ГРУППЫ:

| Поле | Точное значение | ИСПРАВЛЕНО |
|------|-----------------|------------|
| **Имя поля Роли / Группы** | `roles` | ✅ (НЕ role!) |
| **Поле ролей/групп для сопоставления канала** | `groups` | ✅ |
| **Роли для синхронизации** | `admin,moderator,vip,user` | ✅ |

### 🎯 JSON МАППИНГ (СКОПИРОВАТЬ ТОЧНО ТАК):

**В поле "Сопоставление групп и каналов OAuth":**
```json
{
  "owner": "admin,vip",
  "moderator": "admin",
  "user": "user"
}
```

### ⚙️ ПЕРЕКЛЮЧАТЕЛИ (ВСЕ ВКЛЮЧИТЬ!):

| Переключатель | Значение |
|---------------|----------|
| **Merge users** | ✅ ON |
| **Show Button** | ✅ ON |
| **Map Channels** | ✅ ON |
| **Merge Roles** | ✅ ON |

---

## 🔧 ДОПОЛНИТЕЛЬНЫЕ НАСТРОЙКИ

### 1. IFRAME ПОДДЕРЖКА (ОБЯЗАТЕЛЬНО!)
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

---

## 🧪 ПРОВЕРКА РАБОТЫ

### 1. КНОПКА ДОЛЖНА ПОЯВИТЬСЯ:
- Откройте: http://127.0.0.1:3000/login
- ✅ Должна быть синяя кнопка "Войти через Беседку"

### 2. ИНТЕГРАЦИЯ ДОЛЖНА РАБОТАТЬ:
- Откройте: http://127.0.0.1:8001/chat/integrated/
- Войдите как `owner` / `owner123secure`
- Нажмите кнопку "Войти через Беседку" в Rocket.Chat
- ✅ Должен произойти автоматический вход

---

## 🎉 ЕСЛИ ВСЕ РАБОТАЕТ:

Вы увидите:
- ✅ Кнопку OAuth на странице логина Rocket.Chat
- ✅ Автоматический вход пользователей Django
- ✅ Правильные роли и доступ к каналам

**🏆 МИГРАЦИЯ НА ROCKET.CHAT ЗАВЕРШЕНА УСПЕШНО!**

---

## 📞 ПОДДЕРЖКА

Если что-то не работает:
1. Проверьте ВСЕ поля на точное соответствие таблице
2. Убедитесь что ALL переключатели включены
3. Проверьте JSON маппинг на корректность
4. Убедитесь что iframe настройки отключены

**ВСЕ ДАННЫЕ ПРОВЕРЕНЫ И ИСПРАВЛЕНЫ!** ✅ 
