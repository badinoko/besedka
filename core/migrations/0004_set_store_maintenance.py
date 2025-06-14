from django.db import migrations


def create_store_maintenance(apps, schema_editor):
    MaintenanceModeSetting = apps.get_model('core', 'MaintenanceModeSetting')

    # Создаём или обновляем запись для магаза 'store'
    maintenance, created = MaintenanceModeSetting.objects.get_or_create(
        section_name='store',
        defaults={
            'is_enabled': True,
            'title': 'Магазин временно недоступен',
            'message': 'Мы работаем над обновлением магазина. Пожалуйста, зайдите позже.',
            'color_scheme': 'blue',
            'expected_recovery_time': 'В ближайшее время',
        }
    )

    # Если запись уже была, но выключена, включаем режим обслуживания
    if not created and not maintenance.is_enabled:
        maintenance.is_enabled = True
        maintenance.save(update_fields=['is_enabled'])


def noop(apps, schema_editor):
    """Пустая обратная миграция, поскольку удалять запись не требуется."""
    pass


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0003_maintenancemodesetting'),
    ]

    operations = [
        migrations.RunPython(create_store_maintenance, noop),
    ]
