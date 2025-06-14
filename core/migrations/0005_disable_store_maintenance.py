from django.db import migrations


def disable_store_maintenance(apps, schema_editor):
    """Отключаем режим обслуживания для раздела 'store'."""
    MaintenanceModeSetting = apps.get_model('core', 'MaintenanceModeSetting')
    try:
        maintenance = MaintenanceModeSetting.objects.get(section_name='store')
        if maintenance.is_enabled:
            maintenance.is_enabled = False
            maintenance.save(update_fields=['is_enabled'])
    except MaintenanceModeSetting.DoesNotExist:
        # Запись не найдена – ничего не делаем
        pass


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_set_store_maintenance'),
    ]

    operations = [
        migrations.RunPython(disable_store_maintenance, noop),
    ]
