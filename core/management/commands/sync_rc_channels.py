import os
import json
import requests
from django.core.management.base import BaseCommand

RC_API_URL = os.getenv("ROCKETCHAT_API_URL", "http://127.0.0.1:3000/api/v1")
RC_ADMIN_TOKEN = os.getenv("ROCKETCHAT_ADMIN_TOKEN")
RC_ADMIN_USER_ID = os.getenv("ROCKETCHAT_ADMIN_USER_ID")

CHANNELS = [
    {"name": "general", "private": False},
    {"name": "vip", "private": True},
]


class Command(BaseCommand):
    help = "Creates or updates Rocket.Chat channels (#general, #vip) with proper privacy and roles."

    def handle(self, *args, **options):
        if not RC_ADMIN_TOKEN or not RC_ADMIN_USER_ID:
            self.stderr.write(self.style.ERROR("ROCKETCHAT_ADMIN_TOKEN / USER_ID not set in env."))
            return

        headers = {
            "X-Auth-Token": RC_ADMIN_TOKEN,
            "X-User-Id": RC_ADMIN_USER_ID,
            "Content-Type": "application/json",
        }

        # Fetch existing
        r = requests.get(f"{RC_API_URL}/rooms.get", headers=headers)
        r.raise_for_status()
        existing = {room['name']: room for room in r.json().get('update', [])}

        for ch in CHANNELS:
            name = ch['name']
            if name in existing:
                self.stdout.write(f"Channel #{name} already exists, skipping")
                continue
            endpoint = "groups.create" if ch['private'] else "channels.create"
            payload = {"name": name}
            resp = requests.post(f"{RC_API_URL}/{endpoint}", headers=headers, data=json.dumps(payload))
            resp.raise_for_status()
            self.stdout.write(self.style.SUCCESS(f"Created channel #{name}"))
