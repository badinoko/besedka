"""
ASGI config for besedka project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/dev/howto/deployment/asgi/

"""

import os

from django.core.asgi import get_asgi_application

# If DJANGO_SETTINGS_MODULE is unset, default to the local settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

# This application object is used by any ASGI server configured to use this file.
application = get_asgi_application()
