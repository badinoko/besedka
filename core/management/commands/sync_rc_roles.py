import os
import json
import re
import requests
from django.core.management.base import BaseCommand
from django.conf import settings
from pathlib import Path

RC_API_URL = os.getenv("ROCKETCHAT_API_URL", "http://127.0.0.1:3000/api/v1")
RC_ADMIN_TOKEN = os.getenv("ROCKETCHAT_ADMIN_TOKEN")
RC_ADMIN_USER_ID = os.getenv("ROCKETCHAT_ADMIN_USER_ID")

MD_ROLE_PATTERN = re.compile(r"###\s+1\.\d+\.\s+\*\*(?P<role>[^\*]+)\*\*")


class Command(BaseCommand):
    """Синхронизирует роли из BESEDKA_USER_SYSTEM.md с Rocket.Chat (Custom Roles)."""

    def handle(self, *args, **options):
        if not RC_ADMIN_TOKEN or not RC_ADMIN_USER_ID:
            self.stderr.write(self.style.ERROR("ROCKETCHAT_ADMIN_TOKEN / USER_ID not set in env."))
            return

        headers = {
            "X-Auth-Token": RC_ADMIN_TOKEN,
            "X-User-Id": RC_ADMIN_USER_ID,
            "Content-Type": "application/json",
        }

        roles = self._extract_roles()
        for role in roles:
            self.stdout.write(f"Sync role: {role}")
            r = requests.get(f"{RC_API_URL}/roles.list", headers=headers)
            r.raise_for_status()
            existing = [r_['name'] for r_ in r.json().get('roles', [])]
            if role.lower() in existing:
                continue
            payload = {"name": role.lower(), "description": role}
            resp = requests.post(f"{RC_API_URL}/roles.create", headers=headers, data=json.dumps(payload))
            resp.raise_for_status()
            self.stdout.write(self.style.SUCCESS(f"Created role {role}"))

    def _extract_roles(self):
        roles_md = (Path(settings.BASE_DIR) / "BESEDKA_USER_SYSTEM.md").read_text(encoding="utf-8")
        roles = []
        for match in MD_ROLE_PATTERN.finditer(roles_md):
            roles.append(match.group("role").strip())
        return roles
