#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Enhanced Server Starter"""

import os
import sys
import subprocess
import platform
import socket
import webbrowser
import time
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

def check_port(port):
    """Check if port is available"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(('127.0.0.1', port))
        sock.close()
        return True
    except OSError:
        return False

def find_available_port(start_port=8000):
    """Find available port"""
    for port in range(start_port, start_port + 100):
        if check_port(port):
            return port
    return None

def get_network_info():
    """Get network information"""
    try:
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        return hostname, local_ip
    except Exception:
        return "localhost", "127.0.0.1"

def run_django_checks():
    """Run Django checks"""
    print("\n🔍 Running Django checks...")
    
    venv_python = get_venv_python()
    if not venv_python.exists():
        print("   ❌ Virtual environment not found")
        return False
    
    try:
        result = subprocess.run(
            [str(venv_python), "manage.py", "check"],
            capture_output=True,
            text=True,
            timeout=30,
            encoding='utf-8',
            errors='replace'
        )
        if result.returncode == 0:
            print("   ✅ Django checks passed")
            return True
        print("   ⚠️  Django checks had warnings")
        if result.stderr:
            print(f"   {result.stderr[:300]}")
        return True
    except Exception as e:
        print(f"   ⚠️  Check failed: {e}")
        return False

def start_server():
    """Start Django server"""
    print_header("DJANGO DEVELOPMENT SERVER")
    print(f"Working Directory: {os.getcwd()}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    venv_python = get_venv_python()
    if not venv_python.exists():
        print("\n❌ Virtual environment not found!")
        print("Please run 'Complete Fresh Installation' first.")
        return 1
    
    print(f"\n✅ Using: {venv_python}")
    
    run_django_checks()
    
    port = find_available_port(8000)
    if not port:
        print("❌ No available ports found!")
        return 1
    
    hostname, local_ip = get_network_info()
    
    print_header("SERVER INFORMATION")
    print(f"Local URL:     http://127.0.0.1:{port}/")
    print(f"Network URL:   http://{local_ip}:{port}/")
    print(f"Hostname:      {hostname}")
    print("=" * 70)
    
    try:
        print("\nOpen browser automatically? (Y/n): ", end='', flush=True)
        # Use select with timeout on Unix, simple input on Windows
        if platform.system() == "Windows":
            open_browser = input().strip().lower()
        else:
            import select
            ready, _, _ = select.select([sys.stdin], [], [], 5)
            if ready:
                open_browser = sys.stdin.readline().strip().lower()
            else:
                open_browser = 'y'
                print("y (timeout)")
        
        if open_browser != 'n':
            print("Opening browser in 2 seconds...")
            time.sleep(2)
            try:
                webbrowser.open(f"http://127.0.0.1:{port}/")
            except Exception as e:
                print(f"   ⚠️  Could not open browser: {e}")
    except (KeyboardInterrupt, EOFError):
        print("\nSkipping browser...")
    
    print(f"\n🚀 Starting server on port {port}...")
    print("Press Ctrl+C to stop")
    print("=" * 70 + "\n")
    
    try:
        # Don't capture output - let server output show in console
        subprocess.run(
            [str(venv_python), "manage.py", "runserver", f"0.0.0.0:{port}"]
        )
    except KeyboardInterrupt:
        print("\n\n🛑 Server stopped by user")
    except Exception as e:
        print(f"\n❌ Server error: {e}")
        return 1
    
    print("\n👋 Server shutdown complete")
    return 0

if __name__ == "__main__":
    try:
        os.chdir(Path(__file__).parent.parent)
        exit_code = start_server()
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
