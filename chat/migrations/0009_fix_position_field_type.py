# Generated manually by developer 2025-07-11 18:28
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0008_add_position_tracking'),
    ]

    operations = [
        # Удаляем поле с неправильным типом
        migrations.RemoveField(
            model_name='userchatposition',
            name='last_visible_message_id',
        ),

        # Добавляем поле с правильным типом UUID
        migrations.AddField(
            model_name='userchatposition',
            name='last_visible_message_id',
            field=models.UUIDField(blank=True, help_text='UUID последнего видимого сообщения', null=True),
        ),
    ]
