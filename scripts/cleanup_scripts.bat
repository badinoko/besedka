@echo off
echo 🗑️ УДАЛЯЮ МУСОРНЫЕ СКРИПТЫ...

REM Удаляем мусорные JS скрипты
del /Q scripts\add_roles_mapping.js
del /Q scripts\add_user_to_channels.js
del /Q scripts\check_channel_display.js
del /Q scripts\check_channels_status.js
del /Q scripts\check_site_url.js
del /Q scripts\check_user_subscriptions.js
del /Q scripts\clean_vip_chat.js
del /Q scripts\complete_oauth_mapping.js
del /Q scripts\complete_oauth_setup.js
del /Q scripts\complete_rocketchat_setup.js
del /Q scripts\create_rocketchat_channels.js
del /Q scripts\create_vip_moderators_channels.js
del /Q scripts\final_oauth_setup.js
del /Q scripts\fix_channels_final.js
del /Q scripts\fix_channels_ids.js
del /Q scripts\fix_channels_mongo.js
del /Q scripts\fix_rocketchat_settings.js
del /Q scripts\fix_site_url.js
del /Q scripts\fix_subscriptions.js
del /Q scripts\link_oauth_user.js
del /Q scripts\setup_auto_join_general.js
del /Q scripts\simple_add_user.js
del /Q scripts\skip_setup_wizard.js
del /Q scripts\update_oauth_credentials.js

REM Удаляем мусорные Python скрипты
del /Q scripts\check_channels.py
del /Q scripts\check_fix_siteurl.py
del /Q scripts\check_user.py
del /Q scripts\check_view_counts.py
del /Q scripts\comprehensive_audit.py
del /Q scripts\create_all_users.py
del /Q scripts\create_channels.py
del /Q scripts\create_oauth_app_correct.py
del /Q scripts\create_oauth_app_fixed.py
del /Q scripts\create_oauth_app.py
del /Q scripts\create_rocket_oauth.py
del /Q scripts\create_superuser.py
del /Q scripts\create_test_chat_messages.py
del /Q scripts\disable_password_confirmation.py
del /Q scripts\disable_rocketchat_2fa.py
del /Q scripts\e2e_screenshot.py
del /Q scripts\final_test_data.py
del /Q scripts\find_totp_settings.py
del /Q scripts\fix_channels_final.py
del /Q scripts\fix_channels_quick.py
del /Q scripts\fix_moderators_channel.py
del /Q scripts\fix_rocketchat_settings_docker.py
del /Q scripts\fix_rocketchat_settings.py
del /Q scripts\functional_audit.py
del /Q scripts\magic_restart.py
del /Q scripts\rocket_chat_full_oauth_setup.py
del /Q scripts\rocketchat_full_auto_setup.py
del /Q scripts\safe_restart.py
del /Q scripts\setup_groups.py
del /Q scripts\setup_permissions.py
del /Q scripts\setup_rocketchat_oauth.py
del /Q scripts\simple_test_data.py
del /Q scripts\test_django_login.py
del /Q scripts\test_login.py
del /Q scripts\test_rocket_oauth.py
del /Q scripts\update_oauth_app.py
del /Q scripts\visual_audit.py

echo ✅ МУСОРНЫЕ СКРИПТЫ УДАЛЕНЫ!
echo.
echo 📋 ОСТАВЛЕНЫ ТОЛЬКО РАБОЧИЕ СКРИПТЫ:
echo - WORKING_SOLUTION_FINAL.py (главное решение)
echo - auto_setup_after_wizard.py (автонастройка)
echo - backup_rocketchat.py (бэкапы)
echo - auto_rocketchat.py (автоматизация)
echo - clean_duplicate_vip.js (очистка дублей)
echo - disable_join_button.js (отключение кнопки)
echo - subscribe_to_general.js (подписки)
echo - fix_user_subscriptions_final.js (исправление подписок)
echo - quick_backup.py (быстрые бэкапы)
echo.
pause
