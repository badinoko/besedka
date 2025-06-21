from django.core.management.base import BaseCommand
from django.utils.translation import gettext_lazy as _
from core.models import MaintenanceModeSetting

class Command(BaseCommand):
    help = 'Инициализирует настройки режима технического обслуживания для всех определенных разделов.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Начало инициализации настроек режима обслуживания...'))

        created_count = 0
        updated_count = 0

        for section_value, section_display in MaintenanceModeSetting.SECTION_CHOICES:
            setting, created = MaintenanceModeSetting.objects.get_or_create(
                section_name=section_value,
                defaults={
                    'title': _(f'{section_display} временно недоступен'),
                    'message': _(f'Мы работаем над улучшением раздела "{section_display}". Пожалуйста, зайдите позже.'),
                    'expected_recovery_time': _('В ближайшее время'),
                    'color_scheme': 'blue',
                    'is_enabled': False
                }
            )

            if created:
                self.stdout.write(self.style.SUCCESS(f'Создана настройка для раздела: {section_display}'))
                created_count += 1
            else:
                # Можно добавить логику обновления, если нужно, но пока просто пропускаем
                # self.stdout.write(self.style.NOTICE(f'Настройка для раздела "{section_display}" уже существует.'))
                pass

        if created_count > 0:
            self.stdout.write(self.style.SUCCESS(f'Успешно создано {created_count} новых настроек.'))
        else:
            self.stdout.write(self.style.NOTICE('Новых настроек для создания не найдено. Все разделы уже инициализированы.'))

        self.stdout.write(self.style.SUCCESS('Инициализация настроек режима обслуживания завершена.'))
