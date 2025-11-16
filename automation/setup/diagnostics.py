#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
System Diagnostics Module
Comprehensive system health and requirements checking
"""

import os
import sys
import json
import platform
import subprocess
from pathlib import Path
from datetime import datetime

try:
    from colorama import init, Fore, Style
    init(autoreset=True)
except ImportError:
    class Fore:
        GREEN = RED = YELLOW = CYAN = MAGENTA = ""
    class Style:
        BRIGHT = RESET_ALL = ""

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

BASE_DIR = Path(__file__).resolve().parent.parent.parent


class SystemDiagnostics:
    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "checks": {},
            "warnings": [],
            "errors": [],
            "score": 0
        }
    
    def print_header(self, title):
        print("\n" + "=" * 70)
        print(f"{Fore.CYAN}{Style.BRIGHT}  {title}")
        print("=" * 70)
    
    def check_python_version(self):
        """Check Python version"""
        print(f"\n{Fore.CYAN}Checking Python version...")
        version = sys.version_info
        version_str = f"{version.major}.{version.minor}.{version.micro}"
        
        if version >= (3, 8):
            print(f"{Fore.GREEN}✓ Python {version_str} (OK)")
            self.results["checks"]["python_version"] = {
                "status": "pass",
                "version": version_str,
                "required": "3.8+"
            }
            return True
        else:
            print(f"{Fore.RED}✗ Python {version_str} (Requires 3.8+)")
            self.results["checks"]["python_version"] = {
                "status": "fail",
                "version": version_str,
                "required": "3.8+"
            }
            self.results["errors"].append(f"Python version {version_str} is too old")
            return False
    
    def check_system_resources(self):
        """Check system resources"""
        print(f"\n{Fore.CYAN}Checking system resources...")
        
        if not HAS_PSUTIL:
            print(f"{Fore.YELLOW}⚠ psutil not installed - skipping resource check")
            self.results["warnings"].append("psutil not available for resource monitoring")
            return True
        
        # CPU
        cpu_count = psutil.cpu_count()
        cpu_percent = psutil.cpu_percent(interval=1)
        print(f"{Fore.GREEN}✓ CPU: {cpu_count} cores, {cpu_percent}% usage")
        
        # Memory
        memory = psutil.virtual_memory()
        memory_gb = memory.total / (1024**3)
        memory_percent = memory.percent
        
        if memory_gb >= 2:
            print(f"{Fore.GREEN}✓ RAM: {memory_gb:.1f} GB ({memory_percent}% used)")
            ram_status = "pass"
        else:
            print(f"{Fore.YELLOW}⚠ RAM: {memory_gb:.1f} GB (Low - recommend 2GB+)")
            self.results["warnings"].append(f"Low RAM: {memory_gb:.1f} GB")
            ram_status = "warning"
        
        # Disk
        disk = psutil.disk_usage(str(BASE_DIR))
        disk_free_gb = disk.free / (1024**3)
        disk_percent = disk.percent
        
        if disk_free_gb >= 1:
            print(f"{Fore.GREEN}✓ Disk: {disk_free_gb:.1f} GB free ({disk_percent}% used)")
            disk_status = "pass"
        else:
            print(f"{Fore.RED}✗ Disk: {disk_free_gb:.1f} GB free (Critical)")
            self.results["errors"].append(f"Low disk space: {disk_free_gb:.1f} GB")
            disk_status = "fail"
        
        self.results["checks"]["system_resources"] = {
            "cpu_cores": cpu_count,
            "cpu_usage": cpu_percent,
            "ram_gb": round(memory_gb, 1),
            "ram_usage": memory_percent,
            "ram_status": ram_status,
            "disk_free_gb": round(disk_free_gb, 1),
            "disk_usage": disk_percent,
            "disk_status": disk_status
        }
        
        return disk_status != "fail"
    
    def check_network(self):
        """Check network connectivity"""
        print(f"\n{Fore.CYAN}Checking network...")
        
        try:
            import socket
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            print(f"{Fore.GREEN}✓ Hostname: {hostname}")
            print(f"{Fore.GREEN}✓ Local IP: {local_ip}")
            
            self.results["checks"]["network"] = {
                "status": "pass",
                "hostname": hostname,
                "local_ip": local_ip
            }
            return True
        except Exception as e:
            print(f"{Fore.RED}✗ Network check failed: {e}")
            self.results["checks"]["network"] = {
                "status": "fail",
                "error": str(e)
            }
            self.results["errors"].append(f"Network error: {e}")
            return False
    
    def check_port_availability(self, port=8000):
        """Check if port is available"""
        print(f"\n{Fore.CYAN}Checking port {port}...")
        
        try:
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(('127.0.0.1', port))
            sock.close()
            
            if result != 0:
                print(f"{Fore.GREEN}✓ Port {port} is available")
                self.results["checks"]["port"] = {
                    "status": "pass",
                    "port": port,
                    "available": True
                }
                return True
            else:
                print(f"{Fore.YELLOW}⚠ Port {port} is in use")
                self.results["checks"]["port"] = {
                    "status": "warning",
                    "port": port,
                    "available": False
                }
                self.results["warnings"].append(f"Port {port} is already in use")
                return True  # Not critical
        except Exception as e:
            print(f"{Fore.RED}✗ Port check failed: {e}")
            return True  # Not critical
    
    def check_django_installation(self):
        """Check Django installation"""
        print(f"\n{Fore.CYAN}Checking Django installation...")
        
        # Check manage.py
        manage_py = BASE_DIR / "manage.py"
        if manage_py.exists():
            print(f"{Fore.GREEN}✓ manage.py found")
        else:
            print(f"{Fore.RED}✗ manage.py not found")
            self.results["errors"].append("manage.py not found")
            return False
        
        # Check settings.py
        settings_py = BASE_DIR / "school_management" / "settings.py"
        if settings_py.exists():
            print(f"{Fore.GREEN}✓ settings.py found")
        else:
            print(f"{Fore.RED}✗ settings.py not found")
            self.results["errors"].append("settings.py not found")
            return False
        
        # Try importing Django
        try:
            import django
            print(f"{Fore.GREEN}✓ Django {django.get_version()} installed")
            self.results["checks"]["django"] = {
                "status": "pass",
                "version": django.get_version()
            }
            return True
        except ImportError:
            print(f"{Fore.RED}✗ Django not installed")
            self.results["checks"]["django"] = {
                "status": "fail",
                "error": "Django not installed"
            }
            self.results["errors"].append("Django not installed")
            return False
    
    def check_database(self):
        """Check database status"""
        print(f"\n{Fore.CYAN}Checking database...")
        
        db_file = BASE_DIR / "db.sqlite3"
        if db_file.exists():
            size_mb = db_file.stat().st_size / (1024**2)
            print(f"{Fore.GREEN}✓ Database exists ({size_mb:.2f} MB)")
            self.results["checks"]["database"] = {
                "status": "pass",
                "exists": True,
                "size_mb": round(size_mb, 2)
            }
        else:
            print(f"{Fore.YELLOW}⚠ Database not found (needs initialization)")
            self.results["checks"]["database"] = {
                "status": "warning",
                "exists": False
            }
            self.results["warnings"].append("Database not initialized")
        
        return True
    
    def check_static_files(self):
        """Check static files"""
        print(f"\n{Fore.CYAN}Checking static files...")
        
        static_dir = BASE_DIR / "static"
        staticfiles_dir = BASE_DIR / "staticfiles"
        
        if static_dir.exists():
            print(f"{Fore.GREEN}✓ Static directory exists")
        else:
            print(f"{Fore.YELLOW}⚠ Static directory not found")
            self.results["warnings"].append("Static directory not found")
        
        if staticfiles_dir.exists():
            print(f"{Fore.GREEN}✓ Staticfiles directory exists")
        else:
            print(f"{Fore.YELLOW}⚠ Staticfiles not collected")
            self.results["warnings"].append("Static files not collected")
        
        return True
    
    def check_virtual_environment(self):
        """Check virtual environment"""
        print(f"\n{Fore.CYAN}Checking virtual environment...")
        
        venv_path = BASE_DIR / "venv"
        in_venv = hasattr(sys, 'real_prefix') or (
            hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix
        )
        
        if venv_path.exists():
            print(f"{Fore.GREEN}✓ Virtual environment exists")
            if in_venv:
                print(f"{Fore.GREEN}✓ Currently in virtual environment")
                self.results["checks"]["venv"] = {
                    "status": "pass",
                    "exists": True,
                    "active": True
                }
            else:
                print(f"{Fore.YELLOW}⚠ Not in virtual environment")
                self.results["checks"]["venv"] = {
                    "status": "warning",
                    "exists": True,
                    "active": False
                }
                self.results["warnings"].append("Not running in virtual environment")
        else:
            print(f"{Fore.YELLOW}⚠ Virtual environment not found")
            self.results["checks"]["venv"] = {
                "status": "warning",
                "exists": False,
                "active": False
            }
            self.results["warnings"].append("Virtual environment not created")
        
        return True
    
    def check_node_npm(self):
        """Check Node.js and npm"""
        print(f"\n{Fore.CYAN}Checking Node.js and npm...")
        
        try:
            result = subprocess.run(
                ["node", "--version"],
                capture_output=True,
                text=True,
                shell=True
            )
            if result.returncode == 0:
                node_version = result.stdout.strip()
                print(f"{Fore.GREEN}✓ Node.js {node_version}")
                
                result = subprocess.run(
                    ["npm", "--version"],
                    capture_output=True,
                    text=True,
                    shell=True
                )
                if result.returncode == 0:
                    npm_version = result.stdout.strip()
                    print(f"{Fore.GREEN}✓ npm {npm_version}")
                    self.results["checks"]["node_npm"] = {
                        "status": "pass",
                        "node_version": node_version,
                        "npm_version": npm_version
                    }
                    return True
        except:
            pass
        
        print(f"{Fore.YELLOW}⚠ Node.js/npm not found (optional for Tailwind CSS)")
        self.results["checks"]["node_npm"] = {
            "status": "warning",
            "installed": False
        }
        self.results["warnings"].append("Node.js not installed (optional)")
        return True
    
    def calculate_score(self):
        """Calculate health score"""
        total_checks = len(self.results["checks"])
        passed = sum(1 for check in self.results["checks"].values() 
                    if isinstance(check, dict) and check.get("status") == "pass")
        
        if total_checks > 0:
            self.results["score"] = int((passed / total_checks) * 100)
        else:
            self.results["score"] = 0
    
    def print_summary(self):
        """Print diagnostic summary"""
        self.print_header("Diagnostic Summary")
        
        self.calculate_score()
        score = self.results["score"]
        
        if score >= 80:
            color = Fore.GREEN
            status = "Excellent"
        elif score >= 60:
            color = Fore.YELLOW
            status = "Good"
        else:
            color = Fore.RED
            status = "Needs Attention"
        
        print(f"\n{color}Health Score: {score}/100 ({status})")
        
        if self.results["errors"]:
            print(f"\n{Fore.RED}Errors ({len(self.results['errors'])}):")
            for error in self.results["errors"]:
                print(f"  ✗ {error}")
        
        if self.results["warnings"]:
            print(f"\n{Fore.YELLOW}Warnings ({len(self.results['warnings'])}):")
            for warning in self.results["warnings"]:
                print(f"  ⚠ {warning}")
        
        if not self.results["errors"] and not self.results["warnings"]:
            print(f"\n{Fore.GREEN}✓ All checks passed!")
    
    def save_report(self):
        """Save diagnostic report"""
        report_dir = BASE_DIR / "logs"
        report_dir.mkdir(exist_ok=True)
        report_file = report_dir / f"diagnostics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(report_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\n{Fore.CYAN}Report saved to: {report_file}")
    
    def run_all_checks(self):
        """Run all diagnostic checks"""
        self.print_header("🔍 System Diagnostics")
        
        checks = [
            self.check_python_version,
            self.check_system_resources,
            self.check_network,
            self.check_port_availability,
            self.check_virtual_environment,
            self.check_django_installation,
            self.check_database,
            self.check_static_files,
            self.check_node_npm,
        ]
        
        for check in checks:
            try:
                check()
            except Exception as e:
                print(f"{Fore.RED}✗ Check failed: {e}")
                self.results["errors"].append(f"Check error: {e}")
        
        self.print_summary()
        self.save_report()
        
        return self.results["score"] >= 60


def main():
    """Main entry point"""
    diagnostics = SystemDiagnostics()
    success = diagnostics.run_all_checks()
    
    if not success:
        print(f"\n{Fore.RED}System diagnostics failed. Please fix the errors above.")
        sys.exit(1)
    else:
        print(f"\n{Fore.GREEN}System diagnostics passed!")
        sys.exit(0)


if __name__ == "__main__":
    main()
