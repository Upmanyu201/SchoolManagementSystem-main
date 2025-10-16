#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Quick Setup Script"""

import os
import sys
import subprocess
import platform
from pathlib import Path

def print_header(title):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)

def get_venv_python():
    """Get virtual environment Python path"""
    if platform.system() == "Windows":
        return Path("venv") / "Scripts" / "python.exe"
    return Path("venv") / "bin" / "python"

def get_venv_pip():
    """Get virtual environment pip path"""
    if platform.system() == "Windows":
        return Path("venv") / "Scripts" / "pip.exe"
    return Path("venv") / "bin" / "pip"

def run_command(cmd, description, timeout=300):
    """Run command with error handling"""
    print(f"\n{description}...")
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding='utf-8',
            errors='replace'
        )
        if result.returncode == 0:
            print(f"   ✅ {description} completed")
            return True
        print(f"   ❌ {description} failed")
        if result.stderr:
            print(f"   Error: {result.stderr[:200]}")
        return False
    except subprocess.TimeoutExpired:
        print(f"   ❌ {description} timed out after {timeout}s")
        return False
    except Exception as e:
        print(f"   ❌ {description} error: {e}")
        return False

def check_python():
    """Check Python"""
    print("\n🔍 Checking Python...")
    try:
        result = subprocess.run(
            [sys.executable, "--version"],
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
        print(f"   ⚠️  Python check error: {e}")
    print("   ❌ Python not working")
    return False

def setup_venv():
    """Setup virtual environment"""
    print("\n🔨 Setting up virtual environment...")
    
    if Path("venv").exists():
        print("   ✅ Virtual environment exists")
        return True
    
    return run_command(
        [sys.executable, "-m", "venv", "venv"],
        "Creating virtual environment",
        timeout=120
    )

def install_deps():
    """Install dependencies"""
    print("\n📦 Installing dependencies...")
    
    if not Path("requirements.txt").exists():
        print("   ❌ requirements.txt not found")
        return False
    
    pip_cmd = get_venv_pip()
    if not pip_cmd.exists():
        print("   ❌ Virtual environment pip not found")
        return False
    
    return run_command(
        [str(pip_cmd), "install", "-r", "requirements.txt"],
        "Installing dependencies",
        timeout=600  # 10 minutes for dependencies
    )

def setup_db():
    """Setup database"""
    print("\n🗄️  Setting up database...")
    
    python_cmd = get_venv_python()
    if not python_cmd.exists():
        print("   ❌ Virtual environment Python not found")
        return False
    
    if not run_command([str(python_cmd), "manage.py", "makemigrations"], "Creating migrations", timeout=60):
        return False
    
    return run_command([str(python_cmd), "manage.py", "migrate"], "Applying migrations", timeout=120)

def main():
    """Main setup"""
    print_header("QUICK SETUP")
    print(f"Working Directory: {os.getcwd()}")
    print(f"Platform: {platform.system()} {platform.release()}")
    
    steps = [
        ("Python Check", check_python),
        ("Virtual Environment", setup_venv),
        ("Dependencies", install_deps),
        ("Database", setup_db)
    ]
    
    failed = []
    for name, func in steps:
        if not func():
            failed.append(name)
    
    print_header("SETUP SUMMARY")
    
    if failed:
        print(f"❌ Failed: {', '.join(failed)}")
        return 1
    
    print("✅ All steps completed!")
    print("\nNext: python manage.py runserver")
    return 0

if __name__ == "__main__":
    try:
        os.chdir(Path(__file__).parent.parent)
        exit_code = main()
        input("\nPress Enter to continue...")
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️  Cancelled")
        input("\nPress Enter to continue...")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        input("\nPress Enter to continue...")
        sys.exit(1)
