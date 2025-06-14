import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
django.setup()
from django.test import Client
client = Client()
paths = ['/', '/news/', '/gallery/', '/growlogs/', '/store/']
for p in paths:
    try:
        r = client.get(p)
        print(f"{p} -> {r.status_code}")
    except Exception as e:
        print(f"{p} -> error {e.__class__.__name__}: {e}")
