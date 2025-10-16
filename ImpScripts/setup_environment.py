#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Virtual Environment Setup Manager"""

import os
import sys
import subprocess
import platform
import shutil
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

def create_virtual_environment():
    """Create virtual environment"""
    print("\n🔨 Creating virtual environment...")
    
    venv_path = Path("venv")
    
    if venv_path.exists():
        print(f"   ⚠️  Virtual environment exists")
        try:
            response = input("   Delete and recreate? (y/N): ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            response = 'n'
            print("n")
        
        if response == 'y':
            print("   🗑️  Removing old environment...")
            try:
                shutil.rmtree(venv_path)
            except Exception as e:
                print(f"   ❌ Failed to remove: {e}")
                return False
        else:
            print("   ✅ Using existing environment")
            return True
    
    try:
        result = subprocess.run(
            [sys.executable, "-m", "venv", "venv"],
            capture_output=True,
            text=True,
            timeout=120,
            encoding='utf-8',
            errors='replace'
        )
        
        if result.returncode == 0:
            print("   ✅ Virtual environment created")
            return True
        else:
            print("   ❌ Failed to create environment")
            if result.stderr:
                print(f"   Error: {result.stderr[:300]}")
            return False
            
    except subprocess.TimeoutExpired:
        print("   ❌ Environment creation timed out")
        return False
    except Exception as e:
        print(f"   ❌ Failed to create environment: {e}")
        return False

def verify_virtual_environment():
    """Verify virtual environment"""
    print("\n🔍 Verifying virtual environment...")
    
    venv_python = get_venv_python()
    
    if not venv_python.exists():
        print(f"   ❌ Python not found at: {venv_python}")
        return False
    
    try:
        result = subprocess.run(
            [str(venv_python), "--version"],
            capture_output=True,
            text=True,
            timeout=10,
            encoding='utf-8',
            errors='replace'
        )
        
        if result.returncode == 0:
            print(f"   ✅ {result.stdout.strip()}")
            return True
        else:
            print("   ❌ Virtual environment not working")
            if result.stderr:
                print(f"   Error: {result.stderr[:200]}")
            return False
            
    except subprocess.TimeoutExpired:
        print("   ❌ Verification timed out")
        return False
    except Exception as e:
        print(f"   ❌ Verification error: {e}")
        return False

def upgrade_venv_pip():
    """Upgrade pip in virtual environment"""
    print("\n🔄 Upgrading pip...")
    
    venv_python = get_venv_python()
    if not venv_python.exists():
        print("   ❌ Virtual environment not found")
        return False
    
    try:
        result = subprocess.run(
            [str(venv_python), "-m", "pip", "install", "--upgrade", "pip"],
            capture_output=True,
            text=True,
            timeout=120,
            encoding='utf-8',
            errors='replace'
        )
        
        if result.returncode == 0:
            print("   ✅ pip upgraded")
            return True
        else:
            print("   ⚠️  pip upgrade failed")
            if result.stderr:
                print(f"   Error: {result.stderr[:300]}")
            return False
            
    except subprocess.TimeoutExpired:
        print("   ⚠️  pip upgrade timed out")
        return False
    except Exception as e:
        print(f"   ⚠️  pip upgrade error: {e}")
        return False

def install_basic_packages():
    """Install basic packages"""
    print("\n📦 Installing basic packages...")
    
    venv_python = get_venv_python()
    if not venv_python.exists():
        print("   ⚠️  Virtual environment not found (skipping)")
        return True  # Optional
    
    try:
        result = subprocess.run(
            [str(venv_python), "-m", "pip", "install", "wheel", "setuptools"],
            capture_output=True,
            text=True,
            timeout=120,
            encoding='utf-8',
            errors='replace'
        )
        
        if result.returncode == 0:
            print("   ✅ Basic packages installed")
            return True
        else:
            print("   ⚠️  Package installation failed (optional)")
            if result.stderr:
                print(f"   Warning: {result.stderr[:200]}")
            return True  # Optional, don't fail
            
    except subprocess.TimeoutExpired:
        print("   ⚠️  Package installation timed out (optional)")
        return True  # Optional
    except Exception as e:
        print(f"   ⚠️  Package installation error: {e} (optional)")
        return True  # Optional

def main():
    """Main setup process"""
    from datetime import datetime
    print_header("VIRTUAL ENVIRONMENT SETUP")
    print(f"Working Directory: {os.getcwd()}")
    print(f"Python: {sys.version.split()[0]}")
    print(f"Platform: {platform.system()} {platform.release()}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    tasks = [
        ("Create Environment", create_virtual_environment, True),
        ("Verify Environment", verify_virtual_environment, True),
        ("Upgrade pip", upgrade_venv_pip, False),
        ("Install Packages", install_basic_packages, False)
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
    
    print_header("SETUP SUMMARY")
    print(f"✅ Completed: {success}/{len(tasks)} tasks")
    print(f"✅ Critical: {critical_success}/{critical_total} required tasks")
    
    if critical_success == critical_total:
        print("\n🎉 Virtual environment is ready!")
        return 0
    
    print("\n❌ Setup failed - critical tasks incomplete!")
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
