#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quick Actions Menu
One-stop menu for common tasks
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

try:
    from colorama import init, Fore, Style
    init(autoreset=True)
except ImportError:
    class Fore:
        GREEN = RED = YELLOW = CYAN = WHITE = MAGENTA = ""
    class Style:
        BRIGHT = RESET_ALL = ""

BASE_DIR = Path(__file__).resolve().parent.parent.parent


class QuickActions:
    def __init__(self):
        self.venv_python = self.get_venv_python()
    
    def print_header(self, title):
        print("\n" + "=" * 70)
        print(f"{Fore.CYAN}{Style.BRIGHT}  {title}")
        print("=" * 70)
    
    def print_success(self, message):
        print(f"{Fore.GREEN}✓ {message}")
    
    def print_error(self, message):
        print(f"{Fore.RED}✗ {message}")
    
    def print_info(self, message):
        print(f"{Fore.CYAN}ℹ {message}")
    
    def get_venv_python(self):
        """Get virtual environment python path"""
        venv_path = BASE_DIR / "venv"
        if platform.system() == "Windows":
            venv_python = venv_path / "Scripts" / "python.exe"
        else:
            venv_python = venv_path / "bin" / "python"
        
        return venv_python if venv_python.exists() else sys.executable
    
    def run_command(self, cmd, cwd=None):
        """Run command"""
        try:
            result = subprocess.run(
                cmd,
                cwd=cwd or BASE_DIR,
                capture_output=True,
                text=True,
                timeout=300
            )
            return result.returncode == 0, result.stdout, result.stderr
        except Exception as e:
            return False, "", str(e)
    
    def start_server(self):
        """Start development server"""
        self.print_header("🚀 Starting Server")
        
        script = BASE_DIR / "automation" / "server" / "launch_server.py"
        if script.exists():
            self.print_info("Launching server...")
            subprocess.run([str(self.venv_python), str(script)], cwd=BASE_DIR)
        else:
            self.print_error("Server launcher not found")
    
    def stop_server(self):
        """Stop development server"""
        self.print_header("🛑 Stopping Server")
        
        pid_file = BASE_DIR / "server.pid"
        if pid_file.exists():
            try:
                with open(pid_file, 'r') as f:
                    pid = int(f.read().strip())
                
                try:
                    import psutil
                    process = psutil.Process(pid)
                    process.terminate()
                    process.wait(timeout=5)
                    pid_file.unlink()
                    self.print_success("Server stopped")
                except:
                    self.print_error("Failed to stop server")
            except:
                self.print_error("Invalid PID file")
        else:
            self.print_info("Server not running")
    
    def backup_database(self):
        """Backup database"""
        self.print_header("💾 Backup Database")
        
        db_file = BASE_DIR / "db.sqlite3"
        if not db_file.exists():
            self.print_error("Database not found")
            return
        
        from datetime import datetime
        import shutil
        
        backup_dir = BASE_DIR / "backups"
        backup_dir.mkdir(exist_ok=True)
        
        backup_file = backup_dir / f"db_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sqlite3"
        
        try:
            shutil.copy2(db_file, backup_file)
            self.print_success(f"Database backed up to: {backup_file.name}")
        except Exception as e:
            self.print_error(f"Backup failed: {e}")
    
    def clear_cache(self):
        """Clear cache files"""
        self.print_header("🧹 Clear Cache")
        
        deleted_count = 0
        
        # Delete __pycache__
        for pycache_dir in BASE_DIR.rglob("__pycache__"):
            if "venv" not in str(pycache_dir):
                try:
                    import shutil
                    shutil.rmtree(pycache_dir)
                    deleted_count += 1
                except:
                    pass
        
        # Delete .pyc files
        for pyc_file in BASE_DIR.rglob("*.pyc"):
            if "venv" not in str(pyc_file):
                try:
                    pyc_file.unlink()
                    deleted_count += 1
                except:
                    pass
        
        self.print_success(f"Deleted {deleted_count} cache items")
    
    def view_logs(self):
        """View recent logs"""
        self.print_header("📋 Recent Logs")
        
        log_file = BASE_DIR / "logs" / "django.log"
        if log_file.exists():
            try:
                with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                    recent_lines = lines[-50:]  # Last 50 lines
                    
                    print(f"\n{Fore.CYAN}Last 50 log entries:")
                    print()
                    for line in recent_lines:
                        print(line.rstrip())
            except Exception as e:
                self.print_error(f"Failed to read logs: {e}")
        else:
            self.print_info("No log file found")
    
    def run_diagnostics(self):
        """Run system diagnostics"""
        self.print_header("🔍 System Diagnostics")
        
        script = BASE_DIR / "automation" / "setup" / "diagnostics.py"
        if script.exists():
            subprocess.run([str(self.venv_python), str(script)], cwd=BASE_DIR)
        else:
            self.print_error("Diagnostics script not found")
    
    def check_updates(self):
        """Check for updates"""
        self.print_header("🔄 Check Updates")
        
        script = BASE_DIR / "automation" / "updates" / "update_checker.py"
        if script.exists():
            subprocess.run([str(self.venv_python), str(script), "--check", "--force"], cwd=BASE_DIR)
        else:
            self.print_error("Update checker not found")
    
    def factory_reset(self):
        """Factory reset"""
        self.print_header("🔄 Factory Reset")
        
        script = BASE_DIR / "automation" / "setup" / "factory_reset.py"
        if script.exists():
            subprocess.run([str(self.venv_python), str(script)], cwd=BASE_DIR)
        else:
            self.print_error("Factory reset script not found")
    
    def create_superuser(self):
        """Create superuser"""
        self.print_header("👤 Create Superuser")
        
        self.print_info("Creating Django superuser...")
        subprocess.run([str(self.venv_python), "manage.py", "createsuperuser"], cwd=BASE_DIR)
    
    def collect_static(self):
        """Collect static files"""
        self.print_header("📦 Collect Static Files")
        
        self.print_info("Collecting static files...")
        success, stdout, stderr = self.run_command(
            [str(self.venv_python), "manage.py", "collectstatic", "--noinput"]
        )
        
        if success:
            self.print_success("Static files collected")
        else:
            self.print_error(f"Failed: {stderr[:200]}")
    
    def run_migrations(self):
        """Run database migrations"""
        self.print_header("🗄️  Run Migrations")
        
        self.print_info("Making migrations...")
        success, stdout, stderr = self.run_command(
            [str(self.venv_python), "manage.py", "makemigrations"]
        )
        
        if success or "No changes detected" in stdout:
            self.print_success("Migrations created")
        else:
            self.print_error(f"Failed: {stderr[:200]}")
            return
        
        self.print_info("Applying migrations...")
        success, stdout, stderr = self.run_command(
            [str(self.venv_python), "manage.py", "migrate"]
        )
        
        if success:
            self.print_success("Migrations applied")
        else:
            self.print_error(f"Failed: {stderr[:200]}")
    
    def network_manager(self):
        """Open network manager"""
        self.print_header("🌐 Network Manager")
        
        script = BASE_DIR / "automation" / "server" / "network_manager.py"
        if script.exists():
            subprocess.run([str(self.venv_python), str(script)], cwd=BASE_DIR)
        else:
            self.print_error("Network manager not found")
    
    def show_menu(self):
        """Show main menu"""
        while True:
            self.print_header("⚡ Quick Actions Menu")
            
            print(f"\n{Fore.CYAN}Server Management:")
            print(f"  {Fore.YELLOW}1. {Fore.WHITE}Start Server")
            print(f"  {Fore.YELLOW}2. {Fore.WHITE}Stop Server")
            print(f"  {Fore.YELLOW}3. {Fore.WHITE}Network Manager")
            
            print(f"\n{Fore.CYAN}Database:")
            print(f"  {Fore.YELLOW}4. {Fore.WHITE}Backup Database")
            print(f"  {Fore.YELLOW}5. {Fore.WHITE}Run Migrations")
            print(f"  {Fore.YELLOW}6. {Fore.WHITE}Create Superuser")
            
            print(f"\n{Fore.CYAN}Maintenance:")
            print(f"  {Fore.YELLOW}7. {Fore.WHITE}Clear Cache")
            print(f"  {Fore.YELLOW}8. {Fore.WHITE}Collect Static Files")
            print(f"  {Fore.YELLOW}9. {Fore.WHITE}View Logs")
            
            print(f"\n{Fore.CYAN}System:")
            print(f"  {Fore.YELLOW}10. {Fore.WHITE}Run Diagnostics")
            print(f"  {Fore.YELLOW}11. {Fore.WHITE}Check Updates")
            print(f"  {Fore.YELLOW}12. {Fore.WHITE}Factory Reset")
            
            print(f"\n{Fore.YELLOW}0. {Fore.WHITE}Exit")
            
            choice = input(f"\n{Fore.CYAN}Enter choice: ").strip()
            
            actions = {
                '1': self.start_server,
                '2': self.stop_server,
                '3': self.network_manager,
                '4': self.backup_database,
                '5': self.run_migrations,
                '6': self.create_superuser,
                '7': self.clear_cache,
                '8': self.collect_static,
                '9': self.view_logs,
                '10': self.run_diagnostics,
                '11': self.check_updates,
                '12': self.factory_reset,
            }
            
            if choice == '0':
                print(f"\n{Fore.GREEN}Goodbye!")
                break
            elif choice in actions:
                try:
                    actions[choice]()
                    input(f"\n{Fore.CYAN}Press Enter to continue...")
                except KeyboardInterrupt:
                    print(f"\n{Fore.YELLOW}Action cancelled")
                    input(f"\n{Fore.CYAN}Press Enter to continue...")
            else:
                print(f"{Fore.RED}Invalid choice")
                input(f"\n{Fore.CYAN}Press Enter to continue...")


def main():
    """Main entry point"""
    actions = QuickActions()
    actions.show_menu()


if __name__ == "__main__":
    main()
