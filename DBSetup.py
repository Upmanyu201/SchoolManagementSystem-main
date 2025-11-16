# c. DBSetup.py
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Database Setup with Fresh Migrations Option"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
from datetime import datetime

def print_header(title):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)

def get_venv_python():
    if sys.platform == "win32":
        return Path("venv") / "Scripts" / "python.exe"
    return Path("venv") / "bin" / "python"

def run_command(cmd):
    try:
        return subprocess.run(cmd, capture_output=True, text=True, check=True)
    except Exception as e:
        print(f"?? Command failed: {e}")
        return None

def backup_db():
    db_file = Path("db.sqlite3")
    if db_file.exists():
        backup_path = Path("backups") / f"db_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sqlite3"
        backup_path.parent.mkdir(exist_ok=True)
        shutil.copy2(db_file, backup_path)
        print(f"? Backed up to {backup_path}")
        return True
    print("?? No DB to backup")
    return True

def check_migrations_exist():
    migration_dirs = list(Path(".").rglob("migrations"))
    for dir in migration_dirs:
        if list(dir.glob("00*.py")):
            return True
    return False

def delete_migrations():
    print("\n??? Deleting old migration files...")
    migration_dirs = list(Path(".").rglob("migrations"))
    for dir in migration_dirs:
        for file in dir.glob("00*.py"):
            file.unlink()
            print(f"Deleted {file}")
    return True

def handle_fresh_migrations():
    db_file = Path("db.sqlite3")
    if not db_file.exists() and check_migrations_exist():
        print("?? DB missing but migrations exist. Creating fresh...")
        response = input("Delete old migrations and create new? (y/N): ").strip().lower()
        if response == 'y':
            delete_migrations()
            return True
    return False

def make_migrations():
    print("\n?? Making migrations...")
    venv_python = get_venv_python()
    result = run_command([str(venv_python), "manage.py", "makemigrations"])
    if result:
        print("? Done")
        return True
    return False

def migrate():
    print("\n?? Migrating DB...")
    venv_python = get_venv_python()
    result = run_command([str(venv_python), "manage.py", "migrate"])
    if result:
        print("? Migrated")
        return True
    return False

def main():
    print_header("DATABASE SETUP")
    backup_db()
    fresh = handle_fresh_migrations()
    if make_migrations() and migrate():
        print("\n?? DB ready!")
    else:
        print("\n? Issues occurred. Check logs.")

if __name__ == "__main__":
    try:
        os.chdir(Path(__file__).parent.parent)
        main()
        input("\nPress Enter to continue...")
    except Exception as e:
        print(f"? Fatal error: {e}")
        input("\nPress Enter to continue...")