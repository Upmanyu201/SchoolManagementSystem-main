#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Factory Reset Module
Reset the application to fresh installation state
"""

import os
import sys
import json
import shutil
import subprocess
from pathlib import Path
from datetime import datetime

try:
    from colorama import init, Fore, Style
    init(autoreset=True)
except ImportError:
    class Fore:
        GREEN = RED = YELLOW = CYAN = MAGENTA = WHITE = ""
    class Style:
        BRIGHT = RESET_ALL = ""

BASE_DIR = Path(__file__).resolve().parent.parent.parent


class FactoryReset:
    def __init__(self):
        self.backup_created = False
        self.backup_path = None
    
    def print_header(self, title):
        print("\n" + "=" * 70)
        print(f"{Fore.RED}{Style.BRIGHT}  {title}")
        print("=" * 70)
    
    def print_warning(self, message):
        print(f"{Fore.YELLOW}⚠ {message}")
    
    def print_success(self, message):
        print(f"{Fore.GREEN}✓ {message}")
    
    def print_error(self, message):
        print(f"{Fore.RED}✗ {message}")
    
    def print_info(self, message):
        print(f"{Fore.CYAN}ℹ {message}")
    
    def create_backup(self):
        """Create backup before reset"""
        self.print_info("Creating backup before reset...")
        
        backup_dir = BASE_DIR / "backups" / f"factory_reset_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        items_to_backup = []
        
        # Backup database
        db_file = BASE_DIR / "db.sqlite3"
        if db_file.exists():
            shutil.copy2(db_file, backup_dir / "db.sqlite3")
            items_to_backup.append("database")
        
        # Backup media files
        media_dir = BASE_DIR / "media"
        if media_dir.exists():
            shutil.copytree(media_dir, backup_dir / "media", dirs_exist_ok=True)
            items_to_backup.append("media files")
        
        # Backup config files
        config_dir = BASE_DIR / "config"
        if config_dir.exists():
            shutil.copytree(config_dir, backup_dir / "config", dirs_exist_ok=True)
            items_to_backup.append("configuration")
        
        # Backup .env
        env_file = BASE_DIR / ".env"
        if env_file.exists():
            shutil.copy2(env_file, backup_dir / ".env")
            items_to_backup.append(".env file")
        
        if items_to_backup:
            self.backup_path = backup_dir
            self.backup_created = True
            self.print_success(f"Backup created: {backup_dir}")
            self.print_info(f"Backed up: {', '.join(items_to_backup)}")
            return True
        else:
            self.print_warning("No files to backup")
            return True
    
    def delete_database(self):
        """Delete database file"""
        self.print_info("Deleting database...")
        
        db_file = BASE_DIR / "db.sqlite3"
        if db_file.exists():
            try:
                db_file.unlink()
                self.print_success("Database deleted")
                return True
            except Exception as e:
                self.print_error(f"Failed to delete database: {e}")
                return False
        else:
            self.print_info("Database not found")
            return True
    
    def delete_migrations(self):
        """Delete migration files"""
        self.print_info("Deleting migration files...")
        
        deleted_count = 0
        migration_dirs = list(BASE_DIR.rglob("migrations"))
        
        for migration_dir in migration_dirs:
            if migration_dir.is_dir() and "venv" not in str(migration_dir):
                for migration_file in migration_dir.glob("0*.py"):
                    try:
                        migration_file.unlink()
                        deleted_count += 1
                    except Exception as e:
                        self.print_error(f"Failed to delete {migration_file}: {e}")
        
        if deleted_count > 0:
            self.print_success(f"Deleted {deleted_count} migration files")
        else:
            self.print_info("No migration files found")
        
        return True
    
    def delete_media_files(self, preserve=False):
        """Delete media files"""
        if preserve:
            self.print_info("Preserving media files")
            return True
        
        self.print_info("Deleting media files...")
        
        media_dir = BASE_DIR / "media"
        if media_dir.exists():
            try:
                shutil.rmtree(media_dir)
                media_dir.mkdir(exist_ok=True)
                self.print_success("Media files deleted")
                return True
            except Exception as e:
                self.print_error(f"Failed to delete media files: {e}")
                return False
        else:
            self.print_info("Media directory not found")
            return True
    
    def delete_static_files(self):
        """Delete collected static files"""
        self.print_info("Deleting collected static files...")
        
        staticfiles_dir = BASE_DIR / "staticfiles"
        if staticfiles_dir.exists():
            try:
                shutil.rmtree(staticfiles_dir)
                self.print_success("Static files deleted")
                return True
            except Exception as e:
                self.print_error(f"Failed to delete static files: {e}")
                return False
        else:
            self.print_info("Staticfiles directory not found")
            return True
    
    def delete_logs(self):
        """Delete log files"""
        self.print_info("Deleting log files...")
        
        logs_dir = BASE_DIR / "logs"
        if logs_dir.exists():
            deleted_count = 0
            for log_file in logs_dir.glob("*.log"):
                try:
                    log_file.unlink()
                    deleted_count += 1
                except Exception as e:
                    self.print_error(f"Failed to delete {log_file}: {e}")
            
            if deleted_count > 0:
                self.print_success(f"Deleted {deleted_count} log files")
            else:
                self.print_info("No log files found")
        else:
            self.print_info("Logs directory not found")
        
        return True
    
    def delete_cache(self):
        """Delete cache files"""
        self.print_info("Deleting cache files...")
        
        deleted_count = 0
        
        # Delete __pycache__ directories
        for pycache_dir in BASE_DIR.rglob("__pycache__"):
            if "venv" not in str(pycache_dir):
                try:
                    shutil.rmtree(pycache_dir)
                    deleted_count += 1
                except Exception as e:
                    self.print_error(f"Failed to delete {pycache_dir}: {e}")
        
        # Delete .pyc files
        for pyc_file in BASE_DIR.rglob("*.pyc"):
            if "venv" not in str(pyc_file):
                try:
                    pyc_file.unlink()
                    deleted_count += 1
                except Exception as e:
                    pass
        
        if deleted_count > 0:
            self.print_success(f"Deleted {deleted_count} cache items")
        else:
            self.print_info("No cache files found")
        
        return True
    
    def reset_config(self):
        """Reset configuration files"""
        self.print_info("Resetting configuration...")
        
        config_dir = BASE_DIR / "config"
        if config_dir.exists():
            # Reset setup config
            setup_config = config_dir / "setup_config.json"
            default_setup = {
                "first_run": True,
                "setup_completed": False,
                "database_initialized": False,
                "admin_created": False,
                "network_configured": False,
                "tailwind_compiled": False,
                "setup_date": None,
                "python_version": None,
                "installation_path": None
            }
            
            with open(setup_config, 'w') as f:
                json.dump(default_setup, f, indent=2)
            
            self.print_success("Configuration reset to defaults")
        
        return True
    
    def show_reset_menu(self):
        """Show reset options menu"""
        self.print_header("🔄 Factory Reset Options")
        
        print(f"\n{Fore.WHITE}Select reset type:")
        print(f"\n{Fore.CYAN}1. {Fore.WHITE}Soft Reset")
        print(f"   - Delete database and migrations")
        print(f"   - Preserve media files")
        print(f"   - Keep configuration")
        
        print(f"\n{Fore.CYAN}2. {Fore.WHITE}Standard Reset")
        print(f"   - Delete database and migrations")
        print(f"   - Delete static files and cache")
        print(f"   - Preserve media files")
        print(f"   - Reset configuration")
        
        print(f"\n{Fore.CYAN}3. {Fore.WHITE}Complete Reset")
        print(f"   - Delete everything except venv")
        print(f"   - Delete media files")
        print(f"   - Delete logs")
        print(f"   - Reset to fresh installation")
        
        print(f"\n{Fore.CYAN}4. {Fore.WHITE}Cancel")
        
        while True:
            choice = input(f"\n{Fore.YELLOW}Enter choice (1-4): ").strip()
            if choice in ['1', '2', '3', '4']:
                return choice
            print(f"{Fore.RED}Invalid choice. Please enter 1, 2, 3, or 4.")
    
    def confirm_reset(self, reset_type):
        """Confirm reset action"""
        self.print_warning(f"\n⚠️  WARNING: This will perform a {reset_type}!")
        self.print_warning("This action cannot be undone (except from backup).")
        
        response = input(f"\n{Fore.YELLOW}Type 'RESET' to confirm: ").strip()
        return response == 'RESET'
    
    def perform_soft_reset(self):
        """Perform soft reset"""
        self.print_header("Performing Soft Reset")
        
        steps = [
            self.create_backup,
            self.delete_database,
            self.delete_migrations,
            self.delete_cache,
        ]
        
        for step in steps:
            if not step():
                self.print_error("Reset failed at step")
                return False
        
        self.print_success("\nSoft reset completed!")
        return True
    
    def perform_standard_reset(self):
        """Perform standard reset"""
        self.print_header("Performing Standard Reset")
        
        steps = [
            self.create_backup,
            self.delete_database,
            self.delete_migrations,
            self.delete_static_files,
            self.delete_cache,
            self.reset_config,
        ]
        
        for step in steps:
            if not step():
                self.print_error("Reset failed at step")
                return False
        
        self.print_success("\nStandard reset completed!")
        return True
    
    def perform_complete_reset(self):
        """Perform complete reset"""
        self.print_header("Performing Complete Reset")
        
        steps = [
            self.create_backup,
            self.delete_database,
            self.delete_migrations,
            lambda: self.delete_media_files(preserve=False),
            self.delete_static_files,
            self.delete_logs,
            self.delete_cache,
            self.reset_config,
        ]
        
        for step in steps:
            if not step():
                self.print_error("Reset failed at step")
                return False
        
        self.print_success("\nComplete reset completed!")
        return True
    
    def show_next_steps(self):
        """Show next steps after reset"""
        print(f"\n{Fore.CYAN}Next Steps:")
        print(f"  1. Run setup wizard: python setup/setup_wizard.py")
        print(f"  2. Or use quick setup: setup_master.bat")
        
        if self.backup_created:
            print(f"\n{Fore.GREEN}Backup Location:")
            print(f"  {self.backup_path}")
            print(f"\n{Fore.CYAN}To restore from backup:")
            print(f"  - Copy files from backup directory back to project root")
    
    def run(self):
        """Run factory reset"""
        try:
            choice = self.show_reset_menu()
            
            if choice == '4':
                print(f"\n{Fore.YELLOW}Reset cancelled.")
                return
            
            reset_types = {
                '1': ('Soft Reset', self.perform_soft_reset),
                '2': ('Standard Reset', self.perform_standard_reset),
                '3': ('Complete Reset', self.perform_complete_reset),
            }
            
            reset_name, reset_func = reset_types[choice]
            
            if not self.confirm_reset(reset_name):
                print(f"\n{Fore.YELLOW}Reset cancelled.")
                return
            
            if reset_func():
                self.show_next_steps()
            else:
                self.print_error("\nReset failed. Check errors above.")
                if self.backup_created:
                    print(f"\n{Fore.CYAN}Backup available at: {self.backup_path}")
        
        except KeyboardInterrupt:
            print(f"\n{Fore.YELLOW}Reset cancelled by user.")
        except Exception as e:
            self.print_error(f"Fatal error: {e}")
            import traceback
            traceback.print_exc()


def main():
    """Main entry point"""
    reset = FactoryReset()
    reset.run()


if __name__ == "__main__":
    main()
