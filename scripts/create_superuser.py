import os
import django
import sys

# Добавляем путь к корню проекта
sys.path.append('/app')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser(
        username='admin',
        email='admin@example.com',
        password='admin123'
    )
    print('Superuser created successfully')
else:
    print('Superuser already exists') 