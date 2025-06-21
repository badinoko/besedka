#!/usr/bin/env python3
"""
Скрипт для резервного копирования и восстановления настроек Rocket.Chat
Это решит проблему постоянной переустановки!
"""

import subprocess
import json
import os
from datetime import datetime

def run_command(cmd):
    """Выполняет команду и возвращает результат"""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.stdout.strip()

def backup_rocketchat():
    """Создает резервную копию всех настроек Rocket.Chat"""
    print("🔵 Создаю резервную копию настроек Rocket.Chat...")

    # Создаем директорию для бэкапов
    backup_dir = "rocketchat_backups"
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = f"{backup_dir}/rocketchat_backup_{timestamp}.json"

    # Экспортируем все коллекции MongoDB
    collections = [
        "rocketchat_settings",
        "users",
        "rocketchat_room",
        "rocketchat_oauth_apps"
    ]

    backup_data = {}

    for collection in collections:
        print(f"  📦 Экспортирую коллекцию {collection}...")
        cmd = f'docker exec magic_beans_new-mongo-1 mongosh rocketchat --quiet --eval "JSON.stringify(db.{collection}.find().toArray())"'
        data = run_command(cmd)
        if data:
            try:
                backup_data[collection] = json.loads(data)
                print(f"  ✅ Экспортировано {len(backup_data[collection])} записей из {collection}")
            except json.JSONDecodeError:
                print(f"  ⚠️ Не удалось экспортировать {collection}")

    # Сохраняем в файл
    with open(backup_file, 'w', encoding='utf-8') as f:
        json.dump(backup_data, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Резервная копия сохранена в: {backup_file}")

    # Также создаем последнюю копию для быстрого восстановления
    latest_file = f"{backup_dir}/rocketchat_latest.json"
    with open(latest_file, 'w', encoding='utf-8') as f:
        json.dump(backup_data, f, ensure_ascii=False, indent=2)

    return backup_file

def restore_rocketchat(backup_file=None):
    """Восстанавливает настройки Rocket.Chat из резервной копии"""
    if not backup_file:
        backup_file = "rocketchat_backups/rocketchat_latest.json"

    if not os.path.exists(backup_file):
        print(f"❌ Файл резервной копии не найден: {backup_file}")
        return False

    print(f"🔄 Восстанавливаю настройки из: {backup_file}")

    # Загружаем данные
    with open(backup_file, 'r', encoding='utf-8') as f:
        backup_data = json.load(f)

    # Создаем временный JS файл для восстановления
    restore_script = """
// Скрипт восстановления Rocket.Chat
const backup_data = %s;

// Восстанавливаем каждую коллекцию
Object.keys(backup_data).forEach(collection => {
    print(`Восстанавливаю ${collection}...`);
    const data = backup_data[collection];

    // Очищаем коллекцию
    db[collection].deleteMany({});

    // Вставляем данные
    if (data && data.length > 0) {
        // Преобразуем даты
        data.forEach(doc => {
            Object.keys(doc).forEach(key => {
                if (typeof doc[key] === 'string' && doc[key].match(/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}/)) {
                    doc[key] = new Date(doc[key]);
                }
            });
        });

        db[collection].insertMany(data);
        print(`✅ Восстановлено ${data.length} записей в ${collection}`);
    }
});

print('\\n✅ Восстановление завершено!');
""" % json.dumps(backup_data)

    # Сохраняем скрипт
    with open('restore_temp.js', 'w', encoding='utf-8') as f:
        f.write(restore_script)

    # Копируем в контейнер и выполняем
    run_command("docker cp restore_temp.js magic_beans_new-mongo-1:/tmp/")
    result = run_command("docker exec magic_beans_new-mongo-1 mongosh rocketchat /tmp/restore_temp.js")
    print(result)

    # Удаляем временный файл
    os.remove('restore_temp.js')

    # Перезапускаем Rocket.Chat
    print("\n🔄 Перезапускаю Rocket.Chat...")
    run_command("docker restart magic_beans_new-rocketchat-1")

    print("\n✅ Восстановление завершено! Rocket.Chat должен работать с сохраненными настройками.")
    return True

def main():
    """Главная функция"""
    import sys

    if len(sys.argv) > 1:
        if sys.argv[1] == "backup":
            backup_rocketchat()
        elif sys.argv[1] == "restore":
            restore_rocketchat()
        else:
            print("Использование:")
            print("  python scripts/backup_rocketchat.py backup   - создать резервную копию")
            print("  python scripts/backup_rocketchat.py restore  - восстановить из последней копии")
    else:
        # По умолчанию делаем бэкап
        backup_rocketchat()

if __name__ == "__main__":
    main()
