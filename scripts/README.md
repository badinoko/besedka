# 📂 Scripts directory (June 2025)

Эта папка содержит **Только четыре** активных скрипта, управляющие Rocket.Chat-стеком проекта «Беседка».

| Файл | Назначение |
|------|------------|
| `FINAL_ROCKETCHAT_FIX.js` | Single-Source-of-Truth скрипт: приводит MongoDB RC к эталонному состоянию (пользователи, каналы, OAuth, кастомный CSS). |
| `magic_restart_real.py` | Полный безопасный перезапуск: останавливает Python-процессы, поднимает контейнеры, применяет FIX, запускает Daphne; включает auto-login. |
| `full_auto_restart.py` | Укороченный перезапуск (тонкая обёртка над «magic_restart_real» без бэкапов). |
| `backup_rocketchat.py` | Создание / восстановление горячих бэкапов Rocket.Chat. |

Все остальные исторические / утилитные скрипты перенесены в `scripts/archive/` и не участвуют в процессе CI.

Правила добавления / изменения смотрите в `SCRIPT_MANAGEMENT.md`. Nothing else should live here без апдейта того файла.

## 🚨 Критические правила

- **НИКОГДА** не используйте `docker-compose down -v` (удалит все данные)
- **ВСЕГДА** останавливайте Python процессы перед перезапуском: `taskkill /f /im python.exe`
- **ИСПОЛЬЗУЙТЕ** только `daphne` для запуска Django, НЕ `python manage.py runserver` 
