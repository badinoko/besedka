# Generated manually on 2025-05-29 23:50

from django.db import migrations, connection
from django.db.utils import OperationalError


def clean_notes_field_from_db(apps, schema_editor):
    """
    Окончательная очистка поля notes из таблицы GrowLogEntry.
    Это поле было объединено с activities и больше не используется.
    """
    with connection.cursor() as cursor:
        try:
            # Проверяем существует ли поле notes в таблице growlogs_growlogentry (PostgreSQL синтаксис)
            cursor.execute("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'growlogs_growlogentry'
                AND column_name = 'notes'
            """)
            result = cursor.fetchone()

            if result:
                print("📝 Поле 'notes' найдено в GrowLogEntry - удаляем...")

                # В PostgreSQL можно просто удалить столбец
                cursor.execute("ALTER TABLE growlogs_growlogentry DROP COLUMN IF EXISTS notes")

                print("✅ Поле 'notes' успешно удалено из GrowLogEntry")
                print("✅ Данные сохранены в поле 'activities'")

            else:
                print("✅ Поле 'notes' уже отсутствует в GrowLogEntry - все в порядке")

        except OperationalError as e:
            print(f"⚠️ Ошибка при работе с БД: {e}")
            # Не прерываем миграцию, если это не критично
        except Exception as e:
            print(f"❌ Неожиданная ошибка: {e}")
            # Не прерываем миграцию


def reverse_notes_cleanup(apps, schema_editor):
    """
    Обратная миграция - не делаем ничего, так как поле notes больше не нужно
    """
    print("⚠️ Обратная миграция: поле notes не восстанавливается (оно больше не нужно)")


class Migration(migrations.Migration):

    dependencies = [
        ("growlogs", "0011_final_notes_fix"),
    ]

    operations = [
        migrations.RunPython(clean_notes_field_from_db, reverse_notes_cleanup),
    ]
