# 🚨 ЭКСТРЕННОЕ ВОССТАНОВЛЕНИЕ ROCKET.CHAT

**Дата создания бэкапов:** 21 июня 2025, 02:24 MSK  
**Состояние:** Рабочий Rocket.Chat v7.7.1 с созданным workspace "besedka"

## 📦 СОЗДАННЫЕ БЭКАПЫ:

### 1. **MongoDB (Rocket.Chat данные):**
- `rocketchat_backups/rocketchat_backup_working_setup/` - полная база Rocket.Chat
- `rocketchat_backups/rocketchat_backup_20250621_022428/` - дублирующий бэкап

### 2. **PostgreSQL (Django данные):**
- `postgres_backup_working_setup.sql` - база Django со всеми пользователями
- `postgres_backup_20250621_022434.sql` - дублирующий бэкап

## 🛠️ КАК ВОССТАНОВИТЬ:

### MONGODB (если Rocket.Chat сломался):
```bash
# 1. Остановить Rocket.Chat
docker-compose -f docker-compose.local.yml stop rocketchat

# 2. Очистить MongoDB volume (ОСТОРОЖНО!)
docker volume rm magic_beans_new_mongo_data

# 3. Запустить MongoDB заново
docker-compose -f docker-compose.local.yml up -d mongo mongo-init-replica

# 4. Восстановить из бэкапа
docker cp rocketchat_backups/rocketchat_backup_working_setup mongo-container:/restore
docker exec mongo-container mongorestore /restore

# 5. Запустить Rocket.Chat
docker-compose -f docker-compose.local.yml up -d rocketchat
```

### POSTGRESQL (если Django сломался):
```bash
# 1. Остановить PostgreSQL
docker-compose -f docker-compose.local.yml stop postgres

# 2. Очистить PostgreSQL volume (ОСТОРОЖНО!)
docker volume rm magic_beans_new_postgres_data

# 3. Запустить PostgreSQL заново
docker-compose -f docker-compose.local.yml up -d postgres

# 4. Восстановить из бэкапа
docker exec -i postgres-container psql -U postgres < postgres_backup_working_setup.sql
```

## ⚡ БЫСТРЫЙ ЗАПУСК ПОСЛЕ ВОССТАНОВЛЕНИЯ:

```bash
# 1. Убить процессы Python
taskkill /f /im python.exe

# 2. Запустить контейнеры
docker-compose -f docker-compose.local.yml up -d

# 3. Остановить web
docker-compose -f docker-compose.local.yml stop web

# 4. Запустить Django
daphne -b 127.0.0.1 -p 8001 config.asgi:application
```

## 🎯 ЧТО РАБОТАЕТ В БЭКАПЕ:

✅ **Rocket.Chat v7.7.1**: Контейнер запускается  
✅ **Workspace "besedka"**: Создан с каналом #general  
✅ **Пользователь "owner"**: Создан через Setup Wizard  
✅ **Django**: Все данные пользователей и контент  
✅ **OAuth infrastructure**: API endpoints готовы  

## ❌ ЧТО НУЖНО НАСТРОИТЬ ЗАНОВО:

- OAuth провайдер в Rocket.Chat (вручную через админку)
- Создание VIP канала
- Отключение iframe ограничений

## 📝 ЛИЦЕНЗИЯ НА СПОКОЙСТВИЕ:

**Эти бэкапы созданы в момент СТАБИЛЬНОЙ РАБОТЫ системы!**  
Вы всегда можете вернуться к этому состоянию.

---
*Создано 21 июня 2025 в 02:30 MSK* 
