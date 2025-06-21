# 🚀 БОЛЬШЕ НИКОГДА НЕ НАСТРАИВАТЬ ROCKET.CHAT ЗАНОВО!

## 🆘 Если видите Setup Wizard (в 17-й, 18-й или N-й раз):

### Шаг 1: Пройдите Setup Wizard один последний раз
- Username: `owner`
- Email: любой (например, `owner@test.com`)
- Password: `owner123`

### Шаг 2: Сразу после создания пользователя запустите:
```bash
python scripts/auto_setup_after_wizard.py
```

Этот скрипт:
- ✅ Настроит OAuth автоматически
- ✅ Создаст VIP канал и модераторский канал
- ✅ Отключит iframe ограничения
- ✅ Уберет кнопку "Join the Channel"
- ✅ Исправит раздражающие уведомления про порты
- ✅ **СОЗДАСТ РЕЗЕРВНУЮ КОПИЮ!**

### 📋 Полные настройки OAuth (если нужно настроить вручную):

**Administration → Settings → OAuth → Add Custom OAuth:**

**Основные настройки:**
- Enable: ✅ On
- URL: `http://127.0.0.1:8001`
- Token Path: `/o/token/`
- Identity Path: `/api/v1/auth/rocket/`
- Authorize Path: `/o/authorize/`
- Scope: `read`
- Param Name for Token: `access_token`
- Id: `OhyXGbFxYqzOIFgSvdZqgfbFqoXqRHOqKdxArWwp`
- Secret: `z0nI7QezCmekBMtoKXDdxzxVz6FxNvQfkv4kESZGP1XWYXGHFvEcVbIZU1TorncflOQEBfpXgYLJh4yffVQ8ha7RVjo0VE4h6DPlYhMYrb85WRt3GMdp4LWSsR5jiV0y`

**Дополнительные настройки:**
- Login Style: `redirect`
- Button Text: `Войти через Беседку`
- Button Color: `#1d74f5`
- Button Text Color: `#FFFFFF`
- Username field: `username`
- Email field: `email`
- Name field: `full_name`
- Avatar field: `avatar_url`
- Roles/Groups field mapping: `{"owner": "admin,vip", "moderator": "admin", "user": "user"}`
- Merge users: ✅ On
- Show Button: ✅ On

## 🔄 В СЛЕДУЮЩИЙ РАЗ (когда снова увидите Setup Wizard):

Просто запустите:
```bash
python scripts/backup_rocketchat.py restore
```

И все настройки восстановятся за 10 секунд!

## 📋 Правила, чтобы не терять настройки:

### ✅ ДЕЛАЙТЕ:
- `docker-compose stop` (НЕ down!)
- `docker-compose start` или `up -d`
- Создавайте резервные копии после важных изменений:
  ```bash
  python scripts/backup_rocketchat.py backup
  ```

### ❌ НЕ ДЕЛАЙТЕ:
- `docker-compose down` (удаляет контейнеры)
- `docker-compose down -v` (удаляет volumes с данными!)
- Не перезагружайте компьютер без остановки Docker

## 🎯 Автоматизация для ленивых:

Добавьте в ваш `.bashrc` или PowerShell профиль:
```bash
alias rcbackup='python scripts/backup_rocketchat.py backup'
alias rcrestore='python scripts/backup_rocketchat.py restore'
```

Теперь просто:
- `rcbackup` - создать резервную копию
- `rcrestore` - восстановить

## 💡 Почему это происходит?

MongoDB в Docker иногда теряет данные при:
- Неправильной остановке контейнеров
- Обновлении Docker Desktop
- Перезагрузке Windows
- Использовании `docker-compose down`

Но с резервными копиями это больше не проблема!

---

**P.S.** Если все-таки что-то пойдет не так, резервные копии хранятся в папке `rocketchat_backups/` с датой и временем. 
