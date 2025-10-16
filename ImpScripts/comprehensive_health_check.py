#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Comprehensive Health Check - System validation"""

import os
import sys
import subprocess
import platform
import socket
from pathlib import Path
from datetime import datetime

def print_header(title):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)

def print_section(title):
    print(f"\n{'='*20} {title} {'='*20}")

def get_venv_python():
    """Get virtual environment Python path"""
    if platform.system() == "Windows":
        return Path("venv") / "Scripts" / "python.exe"
    return Path("venv") / "bin" / "python"

def run_command(cmd, timeout=10):
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
    except Exception:
        return None

def check_python_installation():
    """Check Python"""
    print_section("PYTHON INSTALLATION")
    
    try:
        # Check system Python
        version = sys.version_info
        version_str = f"{version.major}.{version.minor}.{version.micro}"
        print(f"✅ System Python: {version_str}")
        print(f"✅ System Path: {sys.executable}")
        
        # Check if venv Python exists and show it
        venv_python = get_venv_python()
        if venv_python.exists():
            print(f"✅ Virtual Env: {venv_python}")
        else:
            print(f"⚠️  Virtual Env: Not found")
        
        if version >= (3, 8):
            print("✅ Python version compatible")
            return True
        
        print("❌ Python version too old (requires 3.8+)")
        return False
    except Exception as e:
        print(f"❌ Python check failed: {e}")
        return False

def check_virtual_environment():
    """Check virtual environment"""
    print_section("VIRTUAL ENVIRONMENT")
    
    venv_python = get_venv_python()
    
    if venv_python.exists():
        print("✅ Virtual environment found")
        print(f"✅ Location: {venv_python}")
        return True
    
    print("❌ Virtual environment not found")
    return False

def check_dependencies():
    """Check dependencies"""
    print_section("DEPENDENCIES CHECK")
    
    venv_python = get_venv_python()
    
    if not venv_python.exists():
        print("❌ Virtual environment not found")
        return False
    
    packages = ["django", "djangorestframework", "pillow", "requests"]
    all_installed = True
    
    for package in packages:
        result = run_command([str(venv_python), "-c", f"import {package}"])
        if result and result.returncode == 0:
            print(f"✅ {package}")
        else:
            print(f"❌ {package} not installed")
            all_installed = False
    
    return all_installed

def check_database():
    """Check database"""
    print_section("DATABASE CHECK")
    
    db_file = Path("db.sqlite3")
    if db_file.exists():
        size = db_file.stat().st_size
        print(f"✅ Database found ({size} bytes)")
        
        venv_python = get_venv_python()
        
        if venv_python.exists():
            result = run_command([str(venv_python), "manage.py", "check", "--database", "default"], timeout=30)
            if result and result.returncode == 0:
                print("✅ Database connection successful")
                return True
            
            print("⚠️  Database check had issues")
            return False
        
        print("⚠️  Cannot check database (venv missing)")
        return False
    
    print("❌ Database file not found")
    return False

def check_static_files():
    """Check static files"""
    print_section("STATIC FILES CHECK")
    
    found_any = False
    for dir_name in ["static", "staticfiles", "media"]:
        if Path(dir_name).exists():
            print(f"✅ {dir_name}/ found")
            found_any = True
        else:
            print(f"⚠️  {dir_name}/ not found")
    
    return found_any

def check_network():
    """Check network"""
    print_section("NETWORK CHECK")
    
    try:
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        print(f"✅ Hostname: {hostname}")
        print(f"✅ Local IP: {local_ip}")
        
        # Check port availability (non-critical)
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.bind(('127.0.0.1', 8000))
            sock.close()
            print("✅ Port 8000 available")
        except OSError:
            print("⚠️  Port 8000 in use (server may be running)")
        
        return True
    except Exception as e:
        print(f"⚠️  Network check: {e}")
        return False

def check_permissions():
    """Check permissions"""
    print_section("PERMISSIONS CHECK")
    
    for file_name in ["manage.py", "requirements.txt"]:
        if Path(file_name).exists():
            if os.access(file_name, os.R_OK):
                print(f"✅ {file_name} readable")
            else:
                print(f"❌ {file_name} not readable")
                return False
        else:
            print(f"⚠️  {file_name} not found")
    
    try:
        test_file = Path("health_check_test.tmp")
        test_file.write_text("test")
        test_file.unlink()
        print("✅ Write permissions OK")
        return True
    except Exception as e:
        print(f"❌ Write permissions failed: {e}")
        return False

def run_comprehensive_health_check():
    """Run all checks"""
    print_header("COMPREHENSIVE SYSTEM HEALTH CHECK")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Platform: {platform.system()} {platform.release()}")
    print(f"Directory: {os.getcwd()}")
    
    checks = [
        ("Python", check_python_installation),
        ("Virtual Environment", check_virtual_environment),
        ("Dependencies", check_dependencies),
        ("Database", check_database),
        ("Static Files", check_static_files),
        ("Network", check_network),
        ("Permissions", check_permissions)
    ]
    
    passed = 0
    failed = []
    
    for name, func in checks:
        try:
            if func():
                passed += 1
            else:
                failed.append(name)
        except Exception as e:
            print(f"❌ {name} crashed: {e}")
            failed.append(name)
    
    print_header("HEALTH CHECK SUMMARY")
    
    success_rate = (passed / len(checks)) * 100
    print(f"Health Score: {success_rate:.1f}% ({passed}/{len(checks)})")
    
    if success_rate >= 90:
        print("🎉 EXCELLENT - System ready!")
        status = 0
    elif success_rate >= 70:
        print("✅ GOOD - System functional")
        status = 0
    elif success_rate >= 50:
        print("⚠️  FAIR - Some issues")
        status = 1
    else:
        print("❌ POOR - Major issues")
        status = 1
    
    if failed:
        print(f"\nFailed ({len(failed)}): {', '.join(failed)}")
        print("\nRun 'Complete Fresh Installation' to fix")
    
    return status

def main():
    """Main function"""
    try:
        os.chdir(Path(__file__).parent.parent)
        return run_comprehensive_health_check()
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        return 1

if __name__ == "__main__":
    try:
        exit_code = main()
        print("\n" + "=" * 70)
        input("Press Enter to continue...")
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️  Cancelled")
        input("\nPress Enter to continue...")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        input("\nPress Enter to continue...")
        sys.exit(1)
