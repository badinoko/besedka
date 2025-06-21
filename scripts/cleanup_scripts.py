#!/usr/bin/env python3
"""
Скрипт для удаления мусорных файлов и оставления только рабочих
"""

import os
import glob

# РАБОЧИЕ СКРИПТЫ (НЕ УДАЛЯТЬ!)
working_scripts = {
    'WORKING_SOLUTION_FINAL.py',
    'auto_setup_after_wizard.py',
    'backup_rocketchat.py',
    'auto_rocketchat.py',
    'clean_duplicate_vip.js',
    'disable_join_button.js',
    'subscribe_to_general.js',
    'fix_user_subscriptions_final.js',
    'quick_backup.py',
    'cleanup_scripts.py',  # Этот скрипт тоже не удаляем
    'cleanup_scripts.bat'  # И батч файл тоже
}

def cleanup_scripts():
    """Удаляет все мусорные скрипты"""

    scripts_dir = 'scripts'
    if not os.path.exists(scripts_dir):
        print(f"❌ Папка {scripts_dir} не найдена!")
        return

    # Находим все JS и Python файлы
    all_files = []
    for ext in ['*.js', '*.py']:
        all_files.extend(glob.glob(os.path.join(scripts_dir, ext)))

    # Считаем файлы
    total_files = len(all_files)
    deleted_count = 0
    kept_count = 0

    print(f"🔍 Найдено файлов: {total_files}")
    print(f"📋 Рабочих скриптов (не удаляем): {len(working_scripts)}")
    print()

    # Удаляем мусорные файлы
    for file_path in all_files:
        filename = os.path.basename(file_path)

        if filename in working_scripts:
            print(f"✅ ОСТАВЛЯЮ: {filename}")
            kept_count += 1
        else:
            try:
                os.remove(file_path)
                print(f"🗑️  УДАЛЕН: {filename}")
                deleted_count += 1
            except Exception as e:
                print(f"❌ ОШИБКА при удалении {filename}: {e}")

    print()
    print(f"📊 ИТОГО:")
    print(f"   - Удалено: {deleted_count} мусорных файлов")
    print(f"   - Оставлено: {kept_count} рабочих файлов")
    print()
    print("🎉 ОЧИСТКА ЗАВЕРШЕНА!")

if __name__ == "__main__":
    cleanup_scripts()
