#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Database Setup & Migration Manager"""

import os
import sys
import subprocess
import platform
import shutil
from pathlib import Path
from datetime import datetime

def print_header(title):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)

def get_venv_python():
    """Get virtual environment Python path"""
    if platform.system() == "Windows":
        return Path("venv") / "Scripts" / "python.exe"
    return Path("venv") / "bin" / "python"

def run_command(cmd, timeout=60):
    """Run command safely"""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding='utf-8',
            errors='replace'
        )
        return result
    except subprocess.TimeoutExpired:
        return None
    except Exception as e:
        print(f"   ⚠️  Command failed: {e}")
        return None

def backup_database():
    """Backup existing database"""
    print("\n💾 Checking for existing database...")
    
    db_file = Path("db.sqlite3")
    if db_file.exists():
        backup_name = f"db_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sqlite3"
        backup_path = Path("backups") / backup_name
        backup_path.parent.mkdir(exist_ok=True)
        
        try:
            shutil.copy2(db_file, backup_path)
            print(f"   ✅ Database backed up to: {backup_path}")
            return True
        except Exception as e:
            print(f"   ⚠️  Backup failed: {e}")
            return False
    
    print("   ℹ️  No existing database found")
    return True

def run_makemigrations():
    """Create migrations"""
    print("\n🔨 Creating migrations...")
    
    venv_python = get_venv_python()
    if not venv_python.exists():
        print("   ❌ Virtual environment not found!")
        return False
    
    result = run_command([str(venv_python), "manage.py", "makemigrations"])
    if result and result.returncode == 0:
        print("   ✅ Migrations created")
        if result.stdout:
            print(f"   {result.stdout.strip()}")
        return True
    
    print("   ⚠️  makemigrations had issues")
    if result and result.stderr:
        print(f"   Error: {result.stderr[:300]}")
    return False

def run_migrate():
    """Apply migrations"""
    print("\n🚀 Applying migrations...")
    
    venv_python = get_venv_python()
    if not venv_python.exists():
        print("   ❌ Virtual environment not found!")
        return False
    
    result = run_command([str(venv_python), "manage.py", "migrate"])
    if result and result.returncode == 0:
        print("   ✅ Migrations applied")
        return True
    
    print("   ❌ migrate failed")
    if result and result.stderr:
        print(f"   Error: {result.stderr[:300]}")
    return False

def collect_static():
    """Collect static files"""
    print("\n📦 Collecting static files...")
    
    venv_python = get_venv_python()
    if not venv_python.exists():
        print("   ⚠️  Virtual environment not found (skipping)")
        return True  # Optional task
    
    result = run_command([str(venv_python), "manage.py", "collectstatic", "--noinput"])
    if result and result.returncode == 0:
        print("   ✅ Static files collected")
        return True
    
    print("   ⚠️  Static collection failed (optional)")
    if result and result.stderr:
        print(f"   Warning: {result.stderr[:200]}")
    return True  # Optional task, don't fail setup

def verify_database():
    """Verify database"""
    print("\n🔍 Verifying database...")
    
    venv_python = get_venv_python()
    if not venv_python.exists():
        print("   ❌ Virtual environment not found!")
        return False
    
    result = run_command([str(venv_python), "manage.py", "check", "--database", "default"])
    if result and result.returncode == 0:
        print("   ✅ Database verification passed")
        return True
    
    print("   ⚠️  Database verification failed")
    if result and result.stderr:
        print(f"   Error: {result.stderr[:300]}")
    return False

def main():
    """Main database setup"""
    print_header("DATABASE SETUP & MIGRATION")
    print(f"Working Directory: {os.getcwd()}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    tasks = [
        ("Backup Database", backup_database, False),
        ("Create Migrations", run_makemigrations, True),
        ("Apply Migrations", run_migrate, True),
        ("Collect Static", collect_static, False),
        ("Verify Database", verify_database, False)
    ]
    
    success = 0
    critical_success = 0
    critical_total = 0
    
    for task_name, task_func, is_critical in tasks:
        result = task_func()
        if result:
            success += 1
            if is_critical:
                critical_success += 1
        
        if is_critical:
            critical_total += 1
            if not result:
                print(f"\n❌ Critical task '{task_name}' failed!")
                break
    
    print_header("DATABASE SETUP SUMMARY")
    print(f"✅ Completed: {success}/{len(tasks)} tasks")
    print(f"✅ Critical: {critical_success}/{critical_total} required tasks")
    
    if critical_success == critical_total:
        print("\n🎉 Database is ready!")
        return 0
    
    print("\n❌ Database setup failed - critical tasks incomplete!")
    return 1

if __name__ == "__main__":
    try:
        os.chdir(Path(__file__).parent.parent)
        exit_code = main()
        input("\nPress Enter to continue...")
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️  Setup cancelled")
        input("\nPress Enter to continue...")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        input("\nPress Enter to continue...")
        sys.exit(1)
