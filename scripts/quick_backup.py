#!/usr/bin/env python3
import subprocess
import os
from datetime import datetime

def run_command(cmd):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding='utf-8', errors='replace')
    return result.returncode == 0

def main():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = f"rocketchat_backups/backup_{timestamp}"

    # Create backup directory
    os.makedirs(backup_dir, exist_ok=True)

    print(f"Creating backup: {backup_dir}")

    # Export main collections
    collections = ['users', 'rocketchat_room', 'rocketchat_subscription', 'rocketchat_settings']

    for collection in collections:
        cmd = f'docker exec magic_beans_new-mongo-1 mongoexport --db=rocketchat --collection={collection} --out=/tmp/{collection}.json'
        if run_command(cmd):
            # Copy from container
            copy_cmd = f'docker cp magic_beans_new-mongo-1:/tmp/{collection}.json {backup_dir}/'
            run_command(copy_cmd)
            print(f"✅ Backed up {collection}")
        else:
            print(f"❌ Failed to backup {collection}")

    print(f"✅ Backup completed: {backup_dir}")

if __name__ == "__main__":
    main()
