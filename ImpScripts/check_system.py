#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""System Requirements Checker"""

import os
import sys
import platform
import subprocess
import shutil
from pathlib import Path

def print_header(title):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)

def check_python():
    """Check Python version"""
    print("\n🔍 Checking Python...")
    version = sys.version_info
    print(f"   System Version: {version.major}.{version.minor}.{version.micro}")
    print(f"   System Path: {sys.executable}")
    
    # Check venv Python
    venv_python = Path("venv") / "Scripts" / "python.exe" if platform.system() == "Windows" else Path("venv") / "bin" / "python"
    if venv_python.exists():
        print(f"   ✅ Virtual Env: {venv_python}")
    else:
        print(f"   ⚠️  Virtual Env: Not found")
    
    if version >= (3, 8):
        print("   ✅ Python version compatible (3.8+)")
        return True
    
    print(f"   ❌ Python {version.major}.{version.minor} too old (requires 3.8+)")
    return False

def check_pip():
    """Check pip"""
    print("\n🔍 Checking pip...")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "--version"],
            capture_output=True,
            text=True,
            timeout=10,
            encoding='utf-8',
            errors='replace'
        )
        if result.returncode == 0:
            print(f"   ✅ {result.stdout.strip()}")
            return True
    except Exception as e:
        print(f"   ❌ pip check failed: {e}")
    return False

def check_git():
    """Check Git (optional)"""
    print("\n🔍 Checking Git...")
    if shutil.which("git"):
        try:
            result = subprocess.run(
                ["git", "--version"],
                capture_output=True,
                text=True,
                timeout=10,
                encoding='utf-8',
                errors='replace'
            )
            print(f"   ✅ {result.stdout.strip()}")
            return True
        except Exception:
            pass
    print("   ⚠️  Git not found (optional)")
    return False

def check_project_files():
    """Check required project files"""
    print("\n🔍 Checking Project Files...")
    
    required = ["manage.py", "requirements.txt"]
    all_found = True
    
    for file in required:
        if Path(file).exists():
            print(f"   ✅ {file}")
        else:
            print(f"   ❌ {file} not found")
            all_found = False
    
    return all_found

def main():
    """Run all checks"""
    print_header("SYSTEM REQUIREMENTS CHECK")
    print(f"Platform: {platform.system()} {platform.release()}")
    print(f"Working Directory: {os.getcwd()}")
    
    checks = [
        ("Python Version", check_python, True),
        ("pip Installation", check_pip, True),
        ("Git Installation", check_git, False),
        ("Project Files", check_project_files, True)
    ]
    
    passed = 0
    required_passed = 0
    required_total = 0
    
    for name, func, required in checks:
        result = func()
        if required:
            required_total += 1
            if result:
                required_passed += 1
                passed += 1
        elif result:
            passed += 1
    
    print_header("CHECK SUMMARY")
    print(f"✅ Passed: {passed}/{len(checks)} checks")
    print(f"✅ Required: {required_passed}/{required_total} critical checks")
    
    if required_passed == required_total:
        print("\n🎉 System is ready for installation!")
        return 0
    
    print("\n❌ System has critical issues - fix required checks")
    return 1

if __name__ == "__main__":
    try:
        # Change to project directory first
        os.chdir(Path(__file__).parent.parent)
        exit_code = main()
        input("\nPress Enter to continue...")
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️  Check cancelled")
        input("\nPress Enter to continue...")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        input("\nPress Enter to continue...")
        sys.exit(1)
