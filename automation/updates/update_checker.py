#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Offline Update Checker
Check for updates via GitHub releases with offline caching
"""

import os
import sys
import json
import hashlib
from pathlib import Path
from datetime import datetime, timedelta

try:
    from colorama import init, Fore, Style
    init(autoreset=True)
except ImportError:
    class Fore:
        GREEN = RED = YELLOW = CYAN = WHITE = MAGENTA = ""
    class Style:
        BRIGHT = RESET_ALL = ""

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

BASE_DIR = Path(__file__).resolve().parent.parent.parent
CONFIG_DIR = BASE_DIR / "automation" / "config"
VERSION_FILE = CONFIG_DIR / "version.json"
CACHE_FILE = CONFIG_DIR / "update_cache.json"


class UpdateChecker:
    def __init__(self):
        self.config = self.load_config()
        self.cache = self.load_cache()
        self.current_version = self.config.get("current_version", "1.0.0")
        self.github_repo = self.config.get("github_repo", "")
    
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
    
    def print_warning(self, message):
        print(f"{Fore.YELLOW}⚠ {message}")
    
    def load_config(self):
        """Load version configuration"""
        if VERSION_FILE.exists():
            with open(VERSION_FILE, 'r') as f:
                return json.load(f)
        return {
            "current_version": "1.0.0",
            "github_repo": "",
            "update_channel": "stable",
            "auto_check_updates": True,
            "check_interval_hours": 24
        }
    
    def save_config(self):
        """Save version configuration"""
        CONFIG_DIR.mkdir(exist_ok=True)
        with open(VERSION_FILE, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def load_cache(self):
        """Load update cache"""
        if CACHE_FILE.exists():
            with open(CACHE_FILE, 'r') as f:
                return json.load(f)
        return {
            "last_check": None,
            "latest_version": None,
            "releases": []
        }
    
    def save_cache(self):
        """Save update cache"""
        CONFIG_DIR.mkdir(exist_ok=True)
        with open(CACHE_FILE, 'w') as f:
            json.dump(self.cache, f, indent=2)
    
    def parse_version(self, version_str):
        """Parse version string to tuple"""
        try:
            # Remove 'v' prefix if present
            version_str = version_str.lstrip('v')
            parts = version_str.split('.')
            return tuple(int(p) for p in parts[:3])
        except:
            return (0, 0, 0)
    
    def compare_versions(self, version1, version2):
        """Compare two version strings"""
        v1 = self.parse_version(version1)
        v2 = self.parse_version(version2)
        
        if v1 > v2:
            return 1
        elif v1 < v2:
            return -1
        else:
            return 0
    
    def should_check_updates(self):
        """Check if it's time to check for updates"""
        if not self.config.get("auto_check_updates", True):
            return False
        
        last_check = self.cache.get("last_check")
        if not last_check:
            return True
        
        try:
            last_check_time = datetime.fromisoformat(last_check)
            interval_hours = self.config.get("check_interval_hours", 24)
            next_check = last_check_time + timedelta(hours=interval_hours)
            return datetime.now() >= next_check
        except:
            return True
    
    def check_online_updates(self):
        """Check for updates from GitHub"""
        if not HAS_REQUESTS:
            self.print_warning("requests library not installed - cannot check online")
            return False
        
        if not self.github_repo:
            self.print_warning("GitHub repository not configured")
            return False
        
        self.print_info("Checking for updates online...")
        
        try:
            # GitHub API endpoint
            api_url = f"https://api.github.com/repos/{self.github_repo}/releases"
            
            response = requests.get(api_url, timeout=10)
            response.raise_for_status()
            
            releases = response.json()
            
            if not releases:
                self.print_info("No releases found")
                return False
            
            # Filter by update channel
            channel = self.config.get("update_channel", "stable")
            if channel == "stable":
                releases = [r for r in releases if not r.get("prerelease", False)]
            
            # Get latest release
            latest_release = releases[0] if releases else None
            
            if latest_release:
                latest_version = latest_release.get("tag_name", "").lstrip('v')
                
                # Update cache
                self.cache["last_check"] = datetime.now().isoformat()
                self.cache["latest_version"] = latest_version
                self.cache["releases"] = releases[:5]  # Keep last 5 releases
                self.save_cache()
                
                self.print_success(f"Latest version: {latest_version}")
                return True
            
        except requests.exceptions.RequestException as e:
            self.print_error(f"Failed to check updates: {e}")
            return False
        except Exception as e:
            self.print_error(f"Error checking updates: {e}")
            return False
    
    def check_local_updates(self):
        """Check for updates from local file"""
        self.print_info("Checking for updates from local cache...")
        
        # Check if update file exists
        update_file = BASE_DIR / "automation" / "updates" / "latest_release.json"
        if update_file.exists():
            try:
                with open(update_file, 'r') as f:
                    release_data = json.load(f)
                
                latest_version = release_data.get("version", "")
                
                if latest_version:
                    self.cache["latest_version"] = latest_version
                    self.cache["last_check"] = datetime.now().isoformat()
                    self.save_cache()
                    
                    self.print_success(f"Found local update: {latest_version}")
                    return True
            except Exception as e:
                self.print_error(f"Failed to read local update file: {e}")
        
        # Use cached data
        if self.cache.get("latest_version"):
            self.print_info(f"Using cached version: {self.cache['latest_version']}")
            return True
        
        self.print_warning("No update information available")
        return False
    
    def check_updates(self, force=False):
        """Check for updates"""
        self.print_header("🔄 Update Checker")
        
        print(f"\n{Fore.CYAN}Current Version: {Fore.WHITE}{self.current_version}")
        
        # Check if should check updates
        if not force and not self.should_check_updates():
            last_check = self.cache.get("last_check")
            if last_check:
                try:
                    last_check_time = datetime.fromisoformat(last_check)
                    self.print_info(f"Last checked: {last_check_time.strftime('%Y-%m-%d %H:%M')}")
                except:
                    pass
            
            if self.cache.get("latest_version"):
                print(f"{Fore.CYAN}Latest Version: {Fore.WHITE}{self.cache['latest_version']}")
                self.compare_and_notify()
            return
        
        # Try online check first
        if HAS_REQUESTS and self.github_repo:
            if self.check_online_updates():
                self.compare_and_notify()
                return
        
        # Fallback to local check
        if self.check_local_updates():
            self.compare_and_notify()
    
    def compare_and_notify(self):
        """Compare versions and notify user"""
        latest_version = self.cache.get("latest_version")
        
        if not latest_version:
            return
        
        print(f"{Fore.CYAN}Latest Version: {Fore.WHITE}{latest_version}")
        
        comparison = self.compare_versions(latest_version, self.current_version)
        
        if comparison > 0:
            print(f"\n{Fore.GREEN}✨ New version available!")
            print(f"{Fore.YELLOW}Current: {self.current_version} → Latest: {latest_version}")
            self.show_update_options()
        elif comparison < 0:
            print(f"\n{Fore.CYAN}You're running a newer version than released")
        else:
            print(f"\n{Fore.GREEN}✓ You're running the latest version")
    
    def show_update_options(self):
        """Show update options"""
        print(f"\n{Fore.CYAN}Update Options:")
        print(f"  1. View changelog")
        print(f"  2. Download update")
        print(f"  3. Configure GitHub repository")
        print(f"  4. Skip this version")
        
        choice = input(f"\n{Fore.YELLOW}Enter choice (1-4) or press Enter to skip: ").strip()
        
        if choice == '1':
            self.show_changelog()
        elif choice == '2':
            self.download_update()
        elif choice == '3':
            self.configure_repo()
        elif choice == '4':
            self.print_info("Update skipped")
    
    def show_changelog(self):
        """Show changelog for latest version"""
        self.print_header("📝 Changelog")
        
        releases = self.cache.get("releases", [])
        if releases:
            latest = releases[0]
            print(f"\n{Fore.CYAN}Version: {Fore.WHITE}{latest.get('tag_name', 'Unknown')}")
            print(f"{Fore.CYAN}Released: {Fore.WHITE}{latest.get('published_at', 'Unknown')}")
            print(f"\n{Fore.WHITE}{latest.get('body', 'No changelog available')}")
        else:
            self.print_warning("No changelog available")
    
    def download_update(self):
        """Download update"""
        self.print_info("Opening download page...")
        
        if self.github_repo:
            url = f"https://github.com/{self.github_repo}/releases/latest"
            print(f"\n{Fore.CYAN}Download URL: {Fore.WHITE}{url}")
            
            try:
                import webbrowser
                webbrowser.open(url)
                self.print_success("Opened in browser")
            except:
                self.print_info("Please open the URL manually")
        else:
            self.print_warning("GitHub repository not configured")
    
    def configure_repo(self):
        """Configure GitHub repository"""
        self.print_header("⚙️  Configure Repository")
        
        print(f"\n{Fore.CYAN}Current repository: {Fore.WHITE}{self.github_repo or 'Not set'}")
        print(f"\n{Fore.YELLOW}Enter GitHub repository (format: owner/repo)")
        print(f"{Fore.YELLOW}Example: microsoft/vscode")
        
        repo = input(f"\n{Fore.CYAN}Repository: ").strip()
        
        if repo and '/' in repo:
            self.config["github_repo"] = repo
            self.github_repo = repo
            self.save_config()
            self.print_success(f"Repository set to: {repo}")
        else:
            self.print_error("Invalid repository format")
    
    def import_update_file(self, file_path):
        """Import update information from file"""
        self.print_header("📥 Import Update File")
        
        try:
            with open(file_path, 'r') as f:
                update_data = json.load(f)
            
            version = update_data.get("version")
            if version:
                # Save to local updates directory
                updates_dir = BASE_DIR / "automation" / "updates"
                updates_dir.mkdir(exist_ok=True)
                
                local_file = updates_dir / "latest_release.json"
                with open(local_file, 'w') as f:
                    json.dump(update_data, f, indent=2)
                
                self.print_success(f"Update file imported: {version}")
                self.check_local_updates()
            else:
                self.print_error("Invalid update file format")
        except Exception as e:
            self.print_error(f"Failed to import update file: {e}")
    
    def show_menu(self):
        """Show interactive menu"""
        while True:
            self.print_header("🔄 Update Manager")
            
            print(f"\n{Fore.CYAN}Current Version: {Fore.WHITE}{self.current_version}")
            if self.cache.get("latest_version"):
                print(f"{Fore.CYAN}Latest Version: {Fore.WHITE}{self.cache['latest_version']}")
            
            print(f"\n{Fore.CYAN}1. {Fore.WHITE}Check for Updates")
            print(f"{Fore.CYAN}2. {Fore.WHITE}View Changelog")
            print(f"{Fore.CYAN}3. {Fore.WHITE}Configure Repository")
            print(f"{Fore.CYAN}4. {Fore.WHITE}Import Update File")
            print(f"{Fore.CYAN}5. {Fore.WHITE}Settings")
            print(f"{Fore.CYAN}6. {Fore.WHITE}Exit")
            
            choice = input(f"\n{Fore.YELLOW}Enter choice (1-6): ").strip()
            
            if choice == '1':
                self.check_updates(force=True)
                input(f"\n{Fore.CYAN}Press Enter to continue...")
            elif choice == '2':
                self.show_changelog()
                input(f"\n{Fore.CYAN}Press Enter to continue...")
            elif choice == '3':
                self.configure_repo()
                input(f"\n{Fore.CYAN}Press Enter to continue...")
            elif choice == '4':
                file_path = input(f"\n{Fore.CYAN}Enter file path: ").strip()
                if file_path:
                    self.import_update_file(file_path)
                input(f"\n{Fore.CYAN}Press Enter to continue...")
            elif choice == '5':
                self.configure_settings()
                input(f"\n{Fore.CYAN}Press Enter to continue...")
            elif choice == '6':
                print(f"\n{Fore.GREEN}Goodbye!")
                break
            else:
                print(f"{Fore.RED}Invalid choice")
                input(f"\n{Fore.CYAN}Press Enter to continue...")
    
    def configure_settings(self):
        """Configure update settings"""
        self.print_header("⚙️  Update Settings")
        
        print(f"\n{Fore.CYAN}1. Auto-check updates: {Fore.WHITE}{self.config.get('auto_check_updates', True)}")
        print(f"{Fore.CYAN}2. Check interval: {Fore.WHITE}{self.config.get('check_interval_hours', 24)} hours")
        print(f"{Fore.CYAN}3. Update channel: {Fore.WHITE}{self.config.get('update_channel', 'stable')}")
        
        choice = input(f"\n{Fore.YELLOW}Change setting (1-3) or Enter to skip: ").strip()
        
        if choice == '1':
            self.config["auto_check_updates"] = not self.config.get("auto_check_updates", True)
            self.save_config()
            self.print_success("Setting updated")
        elif choice == '2':
            hours = input(f"{Fore.CYAN}Enter check interval (hours): ").strip()
            try:
                self.config["check_interval_hours"] = int(hours)
                self.save_config()
                self.print_success("Setting updated")
            except:
                self.print_error("Invalid number")
        elif choice == '3':
            print(f"\n{Fore.CYAN}1. Stable")
            print(f"{Fore.CYAN}2. Beta (includes pre-releases)")
            channel_choice = input(f"\n{Fore.YELLOW}Choose channel (1-2): ").strip()
            if channel_choice == '1':
                self.config["update_channel"] = "stable"
            elif channel_choice == '2':
                self.config["update_channel"] = "beta"
            self.save_config()
            self.print_success("Setting updated")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Update Checker')
    parser.add_argument('--check', action='store_true', help='Check for updates')
    parser.add_argument('--force', action='store_true', help='Force check even if recently checked')
    parser.add_argument('--import', dest='import_file', help='Import update file')
    
    args = parser.parse_args()
    
    checker = UpdateChecker()
    
    if args.import_file:
        checker.import_update_file(args.import_file)
    elif args.check:
        checker.check_updates(force=args.force)
    else:
        checker.show_menu()


if __name__ == "__main__":
    main()
