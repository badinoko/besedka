from django.db import migrations

def update_roles(apps, schema_editor):
    """
    Обновляет роли пользователей в соответствии с новой системой ролей.
    """
    User = apps.get_model('users', 'User')
    
    # Обновление прав администраторов
    for user in User.objects.filter(is_superuser=True):
        user.role = 'owner'
        user.save()
    
    # Установка роли 'admin' для всех staff пользователей, которые не имеют роли
    for user in User.objects.filter(is_staff=True, role=''):
        user.role = 'admin'
        user.save()
    
    # Гарантируем, что все администраторы магазина имеют флаг is_staff
    for user in User.objects.filter(role__in=['store_owner', 'store_admin']):
        user.is_staff = True
        user.save()

class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_user_is_banned_alter_user_role_and_more'),
    ]

    operations = [
        migrations.RunPython(update_roles, migrations.RunPython.noop),
    ] 