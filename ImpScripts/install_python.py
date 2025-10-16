#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Python Installation & Upgrade Manager"""

import os
import sys
import subprocess
from pathlib import Path

def print_header(title):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)

def upgrade_pip():
    """Upgrade pip to latest version"""
    print("\n🔄 Upgrading pip...")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "--upgrade", "pip"],
            capture_output=True,
            text=True,
            timeout=120,
            encoding='utf-8',
            errors='replace'
        )
        
        if result.returncode == 0:
            print("   ✅ pip upgraded successfully")
            
            version_result = subprocess.run(
                [sys.executable, "-m", "pip", "--version"],
                capture_output=True,
                text=True,
                timeout=10,
                encoding='utf-8',
                errors='replace'
            )
            if version_result.returncode == 0:
                print(f"   📦 {version_result.stdout.strip()}")
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

def install_wheel():
    """Install wheel for faster package installation"""
    print("\n🔄 Installing wheel...")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "wheel"],
            capture_output=True,
            text=True,
            timeout=60,
            encoding='utf-8',
            errors='replace'
        )
        
        if result.returncode == 0:
            print("   ✅ wheel installed")
            return True
        else:
            print("   ⚠️  wheel installation failed (optional)")
            if result.stderr:
                print(f"   Warning: {result.stderr[:200]}")
            return True  # Optional, don't fail
            
    except subprocess.TimeoutExpired:
        print("   ⚠️  wheel installation timed out (optional)")
        return True  # Optional, don't fail
    except Exception as e:
        print(f"   ⚠️  wheel installation error: {e} (optional)")
        return True  # Optional, don't fail

def main():
    """Main installation process"""
    print_header("PYTHON INSTALLATION & CONFIGURATION")
    print(f"Python Version: {sys.version.split()[0]}")
    print(f"Python Path: {sys.executable}")
    print(f"Working Directory: {os.getcwd()}")
    
    tasks = [
        ("Upgrade pip", upgrade_pip),
        ("Install wheel", install_wheel)
    ]
    
    success_count = sum(1 for _, func in tasks if func())
    
    print_header("INSTALLATION SUMMARY")
    print(f"✅ Completed: {success_count}/{len(tasks)} tasks")
    print("\n🎉 Python environment is ready!")
    return 0

if __name__ == "__main__":
    try:
        # Change to project directory first
        os.chdir(Path(__file__).parent.parent)
        exit_code = main()
        input("\nPress Enter to continue...")
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️  Installation cancelled")
        input("\nPress Enter to continue...")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        input("\nPress Enter to continue...")
        sys.exit(1)
