#!/usr/bin/env python
"""Quick diagnostic script to detect easy view-counter inflation.
Run:  python scripts/check_view_counts.py
It logs in as the platform owner and hits one detail page of each type 10 times
within the same session, then prints the delta of views_count.
If delta > 1, counter is vulnerable to simple refresh inflation.
"""
import os
import sys
import django
from pathlib import Path

# Ensure project root is on sys.path when script is executed via ``python scripts/...``
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")
django.setup()

from django.contrib.auth import get_user_model
from django.test import Client
from news.models import Post
from gallery.models import Photo
from growlogs.models import GrowLog

User = get_user_model()
client = Client()

owner = User.objects.filter(username="owner").first()
if not owner:
    print("[ERROR] Owner user not found. Aborting.")
    sys.exit(1)

client.force_login(owner)

REPORT_WIDTH = 60

def test_counter(model, get_url, label):
    instance = model.objects.first()
    if not instance:
        print(f"{label:<20} | NO INSTANCES FOUND")
        return
    start = getattr(instance, "views_count", getattr(instance, "views", 0))
    url = get_url(instance)
    # Hit the detail page 10 times within same session
    for _ in range(10):
        response = client.get(url)
        if response.status_code != 200:
            print(f"{label:<20} | ERROR HTTP {response.status_code} on {url}")
            return
    # Refresh from DB
    instance.refresh_from_db()
    after = getattr(instance, "views_count", getattr(instance, "views", 0))
    delta = after - start
    status = "VULNERABLE" if delta > 1 else "OK"
    print(f"{label:<20} | start={start:<5} after={after:<5} delta={delta:<3} -> {status}")

print("\n=== VIEW COUNTER UNIQUENESS TEST ===")
print("label                | result")
print("-"*REPORT_WIDTH)

test_counter(Post, lambda p: p.get_absolute_url(), "News Post")

test_counter(Photo, lambda p: p.get_absolute_url(), "Gallery Photo")

test_counter(GrowLog, lambda g: g.get_absolute_url(), "GrowLog")
