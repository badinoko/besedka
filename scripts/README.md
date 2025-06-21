# 📂 Скрипты автоматизации Rocket.Chat

## 🚀 Основные скрипты

### 🪄 Универсальные решения:
| Скрипт | Описание | Использование |
|--------|----------|---------------|
| `magic_restart.py` | Решает ВСЕ проблемы одной командой | `python scripts/magic_restart.py` |
| `auto_setup_after_wizard.py` | Полная автоматическая настройка после Setup Wizard | `python scripts/auto_setup_after_wizard.py` |
| `backup_rocketchat.py` | Создание и восстановление резервных копий | `python scripts/backup_rocketchat.py [backup|restore]` |

### 🔧 Специализированные скрипты:
| Скрипт | Описание | Использование |
|--------|----------|---------------|
| `fix_site_url.js` | Устраняет уведомление о несоответствии URL | `type scripts\fix_site_url.js \| docker exec -i magic_beans_new-mongo-1 mongosh rocketchat` |
| `create_vip_moderators_channels.js` | Создает VIP и Moderators каналы | `type scripts\create_vip_moderators_channels.js \| docker exec -i magic_beans_new-mongo-1 mongosh rocketchat` |
| `disable_join_button.js` | Отключает промежуточную кнопку "Join Channel" | `type scripts\disable_join_button.js \| docker exec -i magic_beans_new-mongo-1 mongosh rocketchat` |
| `auto_join_all_channels.js` | Подписывает пользователя на все каналы | `type scripts\auto_join_all_channels.js \| docker exec -i magic_beans_new-mongo-1 mongosh rocketchat` |

### 📊 Диагностические скрипты:
| Скрипт | Описание | Использование |
|--------|----------|---------------|
| `check_user_subscriptions.py` | Проверяет подписки пользователей | `python scripts/check_user_subscriptions.py` |
| `check_channels_info.js` | Выводит информацию о каналах | `type scripts\check_channels_info.js \| docker exec -i magic_beans_new-mongo-1 mongosh rocketchat` |
| `check_duplicate_channels.js` | Ищет дублирующиеся каналы | `type scripts\check_duplicate_channels.js \| docker exec -i magic_beans_new-mongo-1 mongosh rocketchat` |

### 🧹 Утилиты очистки:
| Скрипт | Описание | Использование |
|--------|----------|---------------|
| `cleanup_scripts.py` | Удаляет временные и устаревшие скрипты | `python scripts/cleanup_scripts.py` |
| `cleanup_scripts.bat` | Batch версия очистки для Windows | `scripts\cleanup_scripts.bat` |
| `clean_duplicate_vip.js` | Удаляет дублирующие VIP каналы | `type scripts\clean_duplicate_vip.js \| docker exec -i magic_beans_new-mongo-1 mongosh rocketchat` |

## 📝 Важные замечания

1. **Всегда используйте `magic_restart.py` в первую очередь** - он решает большинство проблем автоматически

2. **Перед экспериментами делайте бэкап:**
   ```bash
   python scripts/backup_rocketchat.py backup
   ```

3. **Для MongoDB скриптов на Windows используйте `type` вместо `cat`:**
   ```bash
   type scripts\script_name.js | docker exec -i magic_beans_new-mongo-1 mongosh rocketchat
   ```

4. **Проверяйте состояние контейнеров перед запуском:**
   ```bash
   docker ps
   ```

## 🚨 Критические правила

- **НИКОГДА** не используйте `docker-compose down -v` (удалит все данные)
- **ВСЕГДА** останавливайте Python процессы перед перезапуском: `taskkill /f /im python.exe`
- **ИСПОЛЬЗУЙТЕ** только `daphne` для запуска Django, НЕ `python manage.py runserver` 
