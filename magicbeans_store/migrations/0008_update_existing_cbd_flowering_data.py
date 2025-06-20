# Generated by Django 4.2.21 on 2025-05-23 22:XX:XX

from django.db import migrations

def update_strain_data_to_new_choices(apps, schema_editor):
    """Обновляем существующие данные под новые choices"""
    Strain = apps.get_model('magicbeans_store', 'Strain')

    for strain in Strain.objects.all():
        # Обновление CBD content под реалистичные значения 0-3%
        old_cbd = strain.cbd_content

        if old_cbd in ['0-1']:
            strain.cbd_content = '0-0.5'
        elif old_cbd in ['1-5']:
            strain.cbd_content = '0.5-1'
        elif old_cbd in ['5-10']:
            strain.cbd_content = '1-1.5'
        elif old_cbd in ['10-15']:
            strain.cbd_content = '1.5-2'
        elif old_cbd in ['15-20']:
            strain.cbd_content = '2-2.5'
        elif old_cbd in ['20+']:
            strain.cbd_content = '3+'
        else:
            strain.cbd_content = 'unknown'

        # Обновление flowering time под упрощенные диапазоны
        old_flowering = strain.flowering_time

        if old_flowering in ['6-8']:
            strain.flowering_time = '6-8'
        elif old_flowering in ['8-10']:
            strain.flowering_time = '8-10'
        elif old_flowering in ['10-12']:
            strain.flowering_time = '10-12'
        elif old_flowering in ['12-14', '14-16', '16-20', '20-25', '25-30', '30+']:
            strain.flowering_time = '12+'
        elif old_flowering in ['auto']:
            strain.flowering_time = 'auto'
        else:
            strain.flowering_time = 'unknown'

        strain.save()

def reverse_update_strain_data(apps, schema_editor):
    """Обратная миграция - оставляем данные как есть"""
    pass

class Migration(migrations.Migration):

    dependencies = [
        ('magicbeans_store', '0007_fix_cbd_flowering_choices'),
    ]

    operations = [
        migrations.RunPython(
            update_strain_data_to_new_choices,
            reverse_update_strain_data
        ),
    ]
