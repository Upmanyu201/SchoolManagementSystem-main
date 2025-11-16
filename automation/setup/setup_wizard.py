#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
School Management System - Setup Wizard
Interactive first-run setup for the application
"""

import os
import sys
import json
import subprocess
import platform
from pathlib import Path
from datetime import datetime

try:
    from colorama import init, Fore, Style
    init(autoreset=True)
    HAS_COLOR = True
except ImportError:
    HAS_COLOR = False
    class Fore:
        GREEN = RED = YELLOW = CYAN = MAGENTA = BLUE = WHITE = ""
    class Style:
        BRIGHT = RESET_ALL = ""

BASE_DIR = Path(__file__).resolve().parent.parent.parent
CONFIG_DIR = BASE_DIR / "automation" / "config"
SETUP_CONFIG = CONFIG_DIR / "setup_config.json"


class SetupWizard:
    def __init__(self):
        self.config = self.load_config()
        self.steps_completed = []
        self.errors = []
        
    def load_config(self):
        """Load setup configuration"""
        if SETUP_CONFIG.exists():
            with open(SETUP_CONFIG, 'r') as f:
                return json.load(f)
        return {
            "first_run": True,
            "setup_completed": False,
            "database_initialized": False,
            "admin_created": False,
            "network_configured": False,
            "tailwind_compiled": False
        }
    
    def save_config(self):
        """Save setup configuration"""
        CONFIG_DIR.mkdir(exist_ok=True)
        with open(SETUP_CONFIG, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def print_header(self, title):
        """Print formatted header"""
        print("\n" + "=" * 70)
        print(f"{Fore.CYAN}{Style.BRIGHT}  {title}")
        print("=" * 70)
    
    def print_success(self, message):
        """Print success message"""
        print(f"{Fore.GREEN}✓ {message}")
        
    def print_error(self, message):
        """Print error message"""
        print(f"{Fore.RED}✗ {message}")
        self.errors.append(message)
        
    def print_info(self, message):
        """Print info message"""
        print(f"{Fore.CYAN}ℹ {message}")
        
    def print_warning(self, message):
        """Print warning message"""
        print(f"{Fore.YELLOW}⚠ {message}")
    
    def run_command(self, cmd, cwd=None, shell=False):
        """Run command and return result"""
        try:
            result = subprocess.run(
                cmd,
                cwd=cwd or BASE_DIR,
                capture_output=True,
                text=True,
                shell=shell,
                timeout=300
            )
            return result.returncode == 0, result.stdout, result.stderr
        except Exception as e:
            return False, "", str(e)
    
    def welcome_screen(self):
        """Display welcome screen"""
        self.print_header("🎓 School Management System - Setup Wizard")
        print(f"\n{Fore.WHITE}Welcome to the School Management System!")
        print(f"{Fore.WHITE}This wizard will guide you through the initial setup.\n")
        print(f"{Fore.YELLOW}Setup Steps:")
        print(f"  1. System Requirements Check")
        print(f"  2. Python Dependencies Installation")
        print(f"  3. Database Initialization")
        print(f"  4. Tailwind CSS Compilation")
        print(f"  5. Admin Account Creation")
        print(f"  6. Network Configuration")
        print(f"  7. Final System Test\n")
        
        if not self.config.get("first_run", True):
            self.print_warning("Setup has been run before. Re-running will reset some configurations.")
            response = input(f"\n{Fore.CYAN}Continue? (y/N): ").strip().lower()
            if response != 'y':
                print(f"{Fore.YELLOW}Setup cancelled.")
                return False
        
        response = input(f"\n{Fore.CYAN}Press Enter to begin setup or 'q' to quit: ").strip().lower()
        return response != 'q'
    
    def check_system_requirements(self):
        """Check system requirements"""
        self.print_header("Step 1: System Requirements Check")
        
        all_ok = True
        
        # Check Python version
        py_version = sys.version_info
        if py_version >= (3, 8):
            self.print_success(f"Python {py_version.major}.{py_version.minor}.{py_version.micro} detected")
            self.config["python_version"] = f"{py_version.major}.{py_version.minor}.{py_version.micro}"
        else:
            self.print_error(f"Python 3.8+ required, found {py_version.major}.{py_version.minor}")
            all_ok = False
        
        # Check OS
        os_name = platform.system()
        self.print_info(f"Operating System: {os_name} {platform.release()}")
        
        # Check disk space
        try:
            import shutil
            total, used, free = shutil.disk_usage(BASE_DIR)
            free_gb = free // (2**30)
            if free_gb >= 1:
                self.print_success(f"Disk space: {free_gb} GB available")
            else:
                self.print_warning(f"Low disk space: {free_gb} GB available")
        except:
            self.print_warning("Could not check disk space")
        
        # Check if manage.py exists
        if (BASE_DIR / "manage.py").exists():
            self.print_success("Django project structure found")
        else:
            self.print_error("manage.py not found - invalid installation")
            all_ok = False
        
        # Check if venv exists
        venv_path = BASE_DIR / "venv"
        if venv_path.exists():
            self.print_success("Virtual environment found")
        else:
            self.print_warning("Virtual environment not found - will be created")
        
        self.config["installation_path"] = str(BASE_DIR)
        
        if all_ok:
            self.steps_completed.append("system_check")
            self.print_success("\nSystem requirements check passed!")
        else:
            self.print_error("\nSystem requirements check failed!")
        
        return all_ok

    def install_dependencies(self):
        """Install Python dependencies"""
        self.print_header("Step 2: Installing Python Dependencies")
        
        # Check if in virtual environment
        in_venv = hasattr(sys, 'real_prefix') or (
            hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix
        )
        
        if not in_venv:
            self.print_warning("Not in virtual environment")
            venv_path = BASE_DIR / "venv"
            if not venv_path.exists():
                self.print_info("Creating virtual environment...")
                success, stdout, stderr = self.run_command([sys.executable, "-m", "venv", "venv"])
                if success:
                    self.print_success("Virtual environment created")
                else:
                    self.print_error(f"Failed to create virtual environment: {stderr}")
                    return False
            
            # Get venv python
            if platform.system() == "Windows":
                venv_python = venv_path / "Scripts" / "python.exe"
            else:
                venv_python = venv_path / "bin" / "python"
            
            if not venv_python.exists():
                self.print_error("Virtual environment python not found")
                return False
        else:
            venv_python = sys.executable
            self.print_success("Already in virtual environment")
        
        # Upgrade pip
        self.print_info("Upgrading pip...")
        success, _, _ = self.run_command([str(venv_python), "-m", "pip", "install", "--upgrade", "pip"])
        if success:
            self.print_success("Pip upgraded")
        
        # Install requirements
        requirements_file = BASE_DIR / "requirements.txt"
        if requirements_file.exists():
            self.print_info("Installing dependencies (this may take a few minutes)...")
            success, stdout, stderr = self.run_command(
                [str(venv_python), "-m", "pip", "install", "-r", "requirements.txt"]
            )
            if success:
                self.print_success("Dependencies installed successfully")
                self.steps_completed.append("dependencies")
                return True
            else:
                self.print_error(f"Failed to install dependencies: {stderr[:200]}")
                return False
        else:
            self.print_error("requirements.txt not found")
            return False
    
    def initialize_database(self):
        """Initialize database"""
        self.print_header("Step 3: Database Initialization")
        
        venv_python = self.get_venv_python()
        if not venv_python:
            self.print_error("Virtual environment not found")
            return False
        
        # Check if database exists
        db_file = BASE_DIR / "db.sqlite3"
        if db_file.exists():
            self.print_warning("Database already exists")
            response = input(f"{Fore.CYAN}Recreate database? (y/N): ").strip().lower()
            if response == 'y':
                # Backup existing database
                backup_dir = BASE_DIR / "backups"
                backup_dir.mkdir(exist_ok=True)
                backup_file = backup_dir / f"db_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sqlite3"
                try:
                    import shutil
                    shutil.copy2(db_file, backup_file)
                    self.print_success(f"Database backed up to {backup_file.name}")
                    db_file.unlink()
                except Exception as e:
                    self.print_error(f"Failed to backup database: {e}")
                    return False
            else:
                self.print_info("Keeping existing database")
                self.config["database_initialized"] = True
                return True
        
        # Make migrations
        self.print_info("Creating migrations...")
        success, stdout, stderr = self.run_command([str(venv_python), "manage.py", "makemigrations"])
        if success:
            self.print_success("Migrations created")
        else:
            self.print_warning(f"Makemigrations: {stderr[:200]}")
        
        # Run migrations
        self.print_info("Applying migrations...")
        success, stdout, stderr = self.run_command([str(venv_python), "manage.py", "migrate"])
        if success:
            self.print_success("Database initialized successfully")
            self.config["database_initialized"] = True
            self.steps_completed.append("database")
            return True
        else:
            self.print_error(f"Migration failed: {stderr[:200]}")
            return False
    
    def compile_tailwind(self):
        """Compile Tailwind CSS"""
        self.print_header("Step 4: Tailwind CSS Compilation")
        
        # Check if Node.js is installed
        success, stdout, stderr = self.run_command(["node", "--version"], shell=True)
        if not success:
            self.print_warning("Node.js not found - Tailwind CSS compilation skipped")
            self.print_info("Install Node.js from https://nodejs.org/ to enable Tailwind CSS")
            return True  # Not critical, continue setup
        
        node_version = stdout.strip()
        self.print_success(f"Node.js {node_version} detected")
        
        # Check if package.json exists
        package_json = BASE_DIR / "package.json"
        if not package_json.exists():
            self.print_warning("package.json not found - skipping Tailwind compilation")
            return True
        
        # Install npm dependencies
        self.print_info("Installing npm dependencies...")
        success, stdout, stderr = self.run_command(["npm", "install"], shell=True)
        if success:
            self.print_success("npm dependencies installed")
        else:
            self.print_warning("npm install failed - continuing anyway")
        
        # Build Tailwind CSS
        self.print_info("Building Tailwind CSS...")
        success, stdout, stderr = self.run_command(["npm", "run", "build-css"], shell=True)
        if success:
            self.print_success("Tailwind CSS compiled successfully")
            self.config["tailwind_compiled"] = True
            self.steps_completed.append("tailwind")
            return True
        else:
            self.print_warning("Tailwind compilation failed - continuing anyway")
            return True  # Not critical
    
    def create_admin_account(self):
        """Create admin account"""
        self.print_header("Step 5: Admin Account Creation")
        
        venv_python = self.get_venv_python()
        if not venv_python:
            self.print_error("Virtual environment not found")
            return False
        
        self.print_info("Create an administrator account for the system")
        print()
        
        response = input(f"{Fore.CYAN}Create admin account now? (Y/n): ").strip().lower()
        if response == 'n':
            self.print_warning("Admin account creation skipped")
            self.print_info("You can create it later with: python manage.py createsuperuser")
            return True
        
        # Use Django's createsuperuser command
        self.print_info("Running Django createsuperuser...")
        try:
            result = subprocess.run(
                [str(venv_python), "manage.py", "createsuperuser"],
                cwd=BASE_DIR,
                timeout=300
            )
            if result.returncode == 0:
                self.print_success("Admin account created successfully")
                self.config["admin_created"] = True
                self.steps_completed.append("admin")
                return True
            else:
                self.print_warning("Admin account creation cancelled or failed")
                return True  # Not critical
        except Exception as e:
            self.print_error(f"Failed to create admin account: {e}")
            return True  # Not critical
    
    def configure_network(self):
        """Configure network settings"""
        self.print_header("Step 6: Network Configuration")
        
        self.print_info("Detecting network interfaces...")
        
        try:
            import socket
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            
            self.print_success(f"Hostname: {hostname}")
            self.print_success(f"Local IP: {local_ip}")
            
            # Save network config
            network_config_file = CONFIG_DIR / "network_config.json"
            network_config = {
                "default_port": 8000,
                "auto_open_browser": True,
                "detected_networks": [local_ip],
                "preferred_network": local_ip,
                "allow_external_access": True,
                "last_network_scan": datetime.now().isoformat()
            }
            
            with open(network_config_file, 'w') as f:
                json.dump(network_config, f, indent=2)
            
            self.print_success("Network configuration saved")
            self.config["network_configured"] = True
            self.steps_completed.append("network")
            return True
            
        except Exception as e:
            self.print_warning(f"Network detection failed: {e}")
            return True  # Not critical
    
    def run_system_test(self):
        """Run final system test"""
        self.print_header("Step 7: Final System Test")
        
        venv_python = self.get_venv_python()
        if not venv_python:
            self.print_error("Virtual environment not found")
            return False
        
        # Test Django check
        self.print_info("Running Django system check...")
        success, stdout, stderr = self.run_command([str(venv_python), "manage.py", "check"])
        if success:
            self.print_success("Django system check passed")
        else:
            self.print_warning(f"Django check warnings: {stderr[:200]}")
        
        # Test collectstatic
        self.print_info("Collecting static files...")
        success, stdout, stderr = self.run_command(
            [str(venv_python), "manage.py", "collectstatic", "--noinput"]
        )
        if success:
            self.print_success("Static files collected")
        else:
            self.print_warning("Static files collection had issues")
        
        self.steps_completed.append("system_test")
        return True
    
    def get_venv_python(self):
        """Get virtual environment python path"""
        venv_path = BASE_DIR / "venv"
        if platform.system() == "Windows":
            venv_python = venv_path / "Scripts" / "python.exe"
        else:
            venv_python = venv_path / "bin" / "python"
        
        return venv_python if venv_python.exists() else None
    
    def completion_screen(self):
        """Display completion screen"""
        self.print_header("🎉 Setup Complete!")
        
        print(f"\n{Fore.GREEN}Setup completed successfully!")
        print(f"\n{Fore.CYAN}Steps completed:")
        for step in self.steps_completed:
            print(f"  ✓ {step}")
        
        if self.errors:
            print(f"\n{Fore.YELLOW}Warnings/Errors encountered:")
            for error in self.errors:
                print(f"  ⚠ {error}")
        
        print(f"\n{Fore.WHITE}Next steps:")
        print(f"  1. Start the server: python server/launch_server.py")
        print(f"  2. Or use quick start: quick_start.bat")
        print(f"  3. Access the system at: http://127.0.0.1:8000/")
        
        if not self.config.get("admin_created"):
            print(f"\n{Fore.YELLOW}Don't forget to create an admin account:")
            print(f"  python manage.py createsuperuser")
        
        # Update config
        self.config["setup_completed"] = True
        self.config["first_run"] = False
        self.config["setup_date"] = datetime.now().isoformat()
        self.save_config()
        
        print(f"\n{Fore.GREEN}Setup configuration saved!")
    
    def run(self):
        """Run the setup wizard"""
        try:
            if not self.welcome_screen():
                return
            
            # Run setup steps
            steps = [
                ("System Requirements", self.check_system_requirements),
                ("Dependencies", self.install_dependencies),
                ("Database", self.initialize_database),
                ("Tailwind CSS", self.compile_tailwind),
                ("Admin Account", self.create_admin_account),
                ("Network", self.configure_network),
                ("System Test", self.run_system_test),
            ]
            
            for step_name, step_func in steps:
                try:
                    if not step_func():
                        response = input(f"\n{Fore.YELLOW}{step_name} failed. Continue? (y/N): ").strip().lower()
                        if response != 'y':
                            self.print_error("Setup cancelled by user")
                            return
                except KeyboardInterrupt:
                    print(f"\n{Fore.YELLOW}Setup interrupted by user")
                    return
                except Exception as e:
                    self.print_error(f"{step_name} error: {e}")
                    response = input(f"\n{Fore.YELLOW}Continue? (y/N): ").strip().lower()
                    if response != 'y':
                        return
            
            self.completion_screen()
            
        except KeyboardInterrupt:
            print(f"\n{Fore.YELLOW}Setup cancelled by user")
        except Exception as e:
            self.print_error(f"Fatal error: {e}")
            import traceback
            traceback.print_exc()


def main():
    """Main entry point"""
    wizard = SetupWizard()
    wizard.run()


if __name__ == "__main__":
    main()
