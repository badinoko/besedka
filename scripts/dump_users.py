import sys, pathlib, os, json, django

# Add project root to PYTHONPATH so that 'config' package is importable
PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")

django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

data = list(
    User.objects.values("id", "username", "role", "is_staff", "is_superuser")
)

print(json.dumps(data, ensure_ascii=False, indent=2))
