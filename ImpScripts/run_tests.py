#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
System Testing & Validation
Runs comprehensive tests to ensure system is working
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

def print_header(title):
    """Print formatted header"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)

def get_venv_python():
    """Get virtual environment Python path"""
    if platform.system() == "Windows":
        return Path("venv") / "Scripts" / "python.exe"
    return Path("venv") / "bin" / "python"

def run_command(cmd, timeout=30):
    """Run command and return result safely"""
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

def test_django_check():
    """Run Django system check"""
    print("\n🔍 Running Django system check...")
    
    venv_python = get_venv_python()
    if not venv_python.exists():
        print("   ❌ Virtual environment not found!")
        print("   💡 Run 'Python Installation and Environment Setup' first")
        return False
    
    result = run_command([str(venv_python), "manage.py", "check"])
    if result and result.returncode == 0:
        print("   ✅ Django system check passed")
        return True
    
    print("   ⚠️  Django check had issues")
    if result and result.stderr:
        print(f"   Error: {result.stderr[:300]}")
    return False

def test_database_connection():
    """Test database connectivity"""
    print("\n🔍 Testing database connection...")
    
    venv_python = get_venv_python()
    if not venv_python.exists():
        print("   ⚠️  Virtual environment not found, skipping...")
        return False
    
    result = run_command([str(venv_python), "manage.py", "check", "--database", "default"])
    if result and result.returncode == 0:
        print("   ✅ Database connection successful")
        return True
    
    print("   ⚠️  Database check failed")
    if result and result.stderr:
        print(f"   Error: {result.stderr[:300]}")
    return False

def test_migrations():
    """Check migration status"""
    print("\n🔍 Checking migrations...")
    
    venv_python = get_venv_python()
    if not venv_python.exists():
        print("   ⚠️  Virtual environment not found, skipping...")
        return False
    
    result = run_command([str(venv_python), "manage.py", "showmigrations"])
    if result and result.returncode == 0:
        if not result.stdout.strip():
            print("   ⚠️  No migrations found")
            return False
        if "[ ]" in result.stdout:
            print("   ⚠️  Some migrations not applied")
            print("   💡 Run 'Database Setup' to apply migrations")
            return False
        print("   ✅ All migrations applied")
        return True
    
    print("   ⚠️  Migration check failed")
    if result and result.stderr:
        print(f"   Error: {result.stderr[:300]}")
    return False

def test_static_files():
    """Check static files"""
    print("\n🔍 Checking static files...")
    
    found = []
    for dir_name in ["static", "staticfiles"]:
        if Path(dir_name).exists():
            found.append(dir_name)
            print(f"   ✅ {dir_name}/ directory found")
    
    if found:
        return True
    
    print("   ⚠️  No static directories found")
    return False

def test_media_directory():
    """Check media directory"""
    print("\n🔍 Checking media directory...")
    
    media_path = Path("media")
    if media_path.exists():
        print("   ✅ media/ directory found")
        return True
    
    try:
        media_path.mkdir(exist_ok=True)
        print("   ✅ media/ directory created")
        return True
    except OSError as e:
        print(f"   ❌ Failed to create media/ directory: {e}")
        return False

def test_import_modules():
    """Test importing Django modules"""
    print("\n🔍 Testing module imports...")
    
    venv_python = get_venv_python()
    if not venv_python.exists():
        print("   ⚠️  Virtual environment not found, skipping...")
        return False
    
    modules = ["django", "rest_framework", "PIL"]
    all_imported = True
    
    for module in modules:
        result = run_command([str(venv_python), "-c", f"import {module}"], timeout=10)
        if result and result.returncode == 0:
            print(f"   ✅ {module}")
        else:
            print(f"   ⚠️  {module} - not installed")
            all_imported = False
    
    return all_imported

def test_ml_models():
    """Check ML models availability"""
    print("\n🔍 Checking ML models...")
    
    models_dir = Path("models")
    if models_dir.exists():
        model_files = list(models_dir.glob("*.pkl"))
        if model_files:
            print(f"   ✅ Found {len(model_files)} ML model files")
            return True
        print("   ⚠️  No ML model files found (optional)")
        return True
    
    print("   ⚠️  models/ directory not found (optional)")
    return True

def test_settings():
    """Validate Django settings"""
    print("\n🔍 Validating Django settings...")
    
    venv_python = get_venv_python()
    if not venv_python.exists():
        print("   ⚠️  Virtual environment not found, skipping...")
        return False
    
    result = run_command([str(venv_python), "manage.py", "diffsettings"])
    if result and result.returncode == 0:
        print("   ✅ Settings validated")
        return True
    
    print("   ⚠️  Settings validation failed")
    if result and result.stderr:
        print(f"   Error: {result.stderr[:300]}")
    return False

def main():
    """Run all tests"""
    from datetime import datetime
    print_header("SYSTEM TESTING & VALIDATION")
    print(f"Working Directory: {os.getcwd()}")
    print(f"Platform: {platform.system()} {platform.release()}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    tests = [
        ("Django System Check", test_django_check, True),
        ("Database Connection", test_database_connection, True),
        ("Migration Status", test_migrations, True),
        ("Static Files", test_static_files, False),
        ("Media Directory", test_media_directory, False),
        ("Module Imports", test_import_modules, True),
        ("ML Models", test_ml_models, False),
        ("Django Settings", test_settings, True)
    ]
    
    passed = failed = warnings = 0
    
    for test_name, test_func, is_critical in tests:
        try:
            if test_func():
                passed += 1
            elif not is_critical:
                warnings += 1
            else:
                failed += 1
        except Exception as e:
            print(f"   ❌ Test crashed: {e}")
            if is_critical:
                failed += 1
            else:
                warnings += 1
    
    print_header("TEST SUMMARY")
    print(f"✅ Passed: {passed}/{len(tests)}")
    print(f"⚠️  Warnings: {warnings}/{len(tests)} (optional tests)")
    print(f"❌ Failed: {failed}/{len(tests)}")
    
    # Calculate success rate (passed + warnings as partial success)
    success_rate = ((passed + warnings * 0.5) / len(tests)) * 100
    print(f"\n📊 Success Rate: {success_rate:.1f}%")
    
    if success_rate >= 80:
        print("🎉 System is working well!")
        return 0
    elif success_rate >= 60:
        print("⚠️  System has some issues but is functional")
        return 0
    
    print("❌ System has critical issues")
    return 1

if __name__ == "__main__":
    try:
        os.chdir(Path(__file__).parent.parent)
        exit_code = main()
        print("\n" + "=" * 70)
        input("Press Enter to continue...")
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️  Testing cancelled")
        input("\nPress Enter to continue...")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        input("\nPress Enter to continue...")
        sys.exit(1)
