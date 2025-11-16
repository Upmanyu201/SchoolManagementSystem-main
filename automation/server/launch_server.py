#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Smart Server Launcher
Launches Django server with network detection and auto-browser opening
"""

import os
import sys
import json
import time
import socket
import subprocess
import webbrowser
import platform
import threading
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
CONFIG_DIR = BASE_DIR / "automation" / "config"
PID_FILE = BASE_DIR / "server.pid"


class ServerLauncher:
    def __init__(self, port=8000, auto_browser=True):
        self.port = port
        self.auto_browser = auto_browser
        self.server_process = None
        self.networks = []
        self.server_ready = False
        
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
    
    def get_venv_python(self):
        """Get virtual environment python path"""
        venv_path = BASE_DIR / "venv"
        if platform.system() == "Windows":
            venv_python = venv_path / "Scripts" / "python.exe"
        else:
            venv_python = venv_path / "bin" / "python"
        
        if venv_python.exists():
            return venv_python
        return sys.executable
    
    def check_port_available(self):
        """Check if port is available"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            result = sock.connect_ex(('127.0.0.1', self.port))
            sock.close()
            return result != 0
        except:
            return False
    
    def find_available_port(self, start_port=8000):
        """Find an available port"""
        for port in range(start_port, start_port + 100):
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                result = sock.connect_ex(('127.0.0.1', port))
                sock.close()
                if result != 0:
                    return port
            except:
                continue
        return None
    
    def detect_networks(self):
        """Detect all available network interfaces"""
        self.print_info("Detecting network interfaces...")
        
        networks = []
        
        # Get hostname and local IP
        try:
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            if local_ip and local_ip != '127.0.0.1':
                networks.append({
                    'name': 'Local Network',
                    'ip': local_ip,
                    'type': 'local'
                })
        except:
            pass
        
        # Try to get all network interfaces (Windows specific)
        if platform.system() == "Windows":
            try:
                import subprocess
                result = subprocess.run(
                    ['ipconfig'],
                    capture_output=True,
                    text=True,
                    shell=True
                )
                
                lines = result.stdout.split('\n')
                current_adapter = None
                
                for line in lines:
                    line = line.strip()
                    
                    # Detect adapter name
                    if 'adapter' in line.lower():
                        current_adapter = line.split(':')[0].strip()
                    
                    # Detect IPv4 address
                    if 'IPv4' in line and ':' in line:
                        ip = line.split(':')[1].strip()
                        if ip and ip not in [n['ip'] for n in networks]:
                            adapter_type = 'unknown'
                            if current_adapter:
                                if 'wi-fi' in current_adapter.lower() or 'wireless' in current_adapter.lower():
                                    adapter_type = 'wifi'
                                elif 'ethernet' in current_adapter.lower():
                                    adapter_type = 'ethernet'
                                elif 'local area connection' in current_adapter.lower():
                                    adapter_type = 'hotspot'
                            
                            networks.append({
                                'name': current_adapter or 'Network',
                                'ip': ip,
                                'type': adapter_type
                            })
            except:
                pass
        
        # Always add localhost
        if not any(n['ip'] == '127.0.0.1' for n in networks):
            networks.insert(0, {
                'name': 'Localhost',
                'ip': '127.0.0.1',
                'type': 'localhost'
            })
        
        self.networks = networks
        return networks
    
    def display_networks(self):
        """Display detected networks"""
        if not self.networks:
            self.detect_networks()
        
        print(f"\n{Fore.CYAN}📡 Available Networks:")
        print()
        
        for network in self.networks:
            icon = {
                'localhost': '🖥️ ',
                'wifi': '📶',
                'ethernet': '🔌',
                'hotspot': '📱',
                'local': '🌐',
                'unknown': '🔗'
            }.get(network['type'], '🔗')
            
            url = f"http://{network['ip']}:{self.port}/"
            print(f"  {icon} {Fore.WHITE}{network['name']}")
            print(f"     {Fore.GREEN}{url}")
            print()
        
        # Save network config
        self.save_network_config()
    
    def save_network_config(self):
        """Save network configuration"""
        CONFIG_DIR.mkdir(exist_ok=True)
        config_file = CONFIG_DIR / "network_config.json"
        
        config = {
            "default_port": self.port,
            "auto_open_browser": self.auto_browser,
            "detected_networks": self.networks,
            "last_network_scan": datetime.now().isoformat()
        }
        
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
    
    def monitor_server_output(self, process):
        """Monitor server output for ready signal"""
        while True:
            line = process.stdout.readline()
            if not line:
                break
            
            line_str = line.decode('utf-8', errors='ignore').strip()
            
            # Print server output
            if line_str:
                print(f"{Fore.WHITE}{line_str}")
            
            # Check if server is ready
            if 'Starting development server' in line_str or 'Quit the server' in line_str:
                if not self.server_ready:
                    self.server_ready = True
                    time.sleep(1)  # Give server a moment to fully start
                    
                    if self.auto_browser:
                        self.open_browser()
    
    def open_browser(self):
        """Open browser to server URL"""
        url = f"http://127.0.0.1:{self.port}/"
        self.print_success(f"Opening browser to {url}")
        
        try:
            webbrowser.open(url)
        except Exception as e:
            self.print_warning(f"Could not open browser: {e}")
            self.print_info(f"Please open manually: {url}")
    
    def save_pid(self, pid):
        """Save server process ID"""
        with open(PID_FILE, 'w') as f:
            f.write(str(pid))
    
    def load_pid(self):
        """Load server process ID"""
        if PID_FILE.exists():
            with open(PID_FILE, 'r') as f:
                return int(f.read().strip())
        return None
    
    def is_server_running(self):
        """Check if server is already running"""
        pid = self.load_pid()
        if pid:
            try:
                import psutil
                if psutil.pid_exists(pid):
                    return True
            except ImportError:
                # Fallback: check if port is in use
                return not self.check_port_available()
        return False
    
    def stop_existing_server(self):
        """Stop existing server"""
        pid = self.load_pid()
        if pid:
            try:
                import psutil
                process = psutil.Process(pid)
                process.terminate()
                process.wait(timeout=5)
                self.print_success("Stopped existing server")
                PID_FILE.unlink()
                return True
            except:
                pass
        return False
    
    def start_server(self, background=False):
        """Start Django development server"""
        self.print_header("🚀 Starting Server")
        
        # Check if server is already running
        if self.is_server_running():
            self.print_warning("Server appears to be already running")
            response = input(f"{Fore.CYAN}Stop and restart? (Y/n): ").strip().lower()
            if response != 'n':
                self.stop_existing_server()
                time.sleep(2)
            else:
                self.print_info("Keeping existing server")
                return False
        
        # Check port availability
        if not self.check_port_available():
            self.print_warning(f"Port {self.port} is in use")
            new_port = self.find_available_port(self.port + 1)
            if new_port:
                self.print_info(f"Using port {new_port} instead")
                self.port = new_port
            else:
                self.print_error("No available ports found")
                return False
        
        # Detect networks
        self.detect_networks()
        
        # Get python executable
        venv_python = self.get_venv_python()
        
        # Prepare command
        cmd = [
            str(venv_python),
            "manage.py",
            "runserver",
            f"0.0.0.0:{self.port}"
        ]
        
        self.print_info(f"Starting server on port {self.port}...")
        
        try:
            if background:
                # Start in background
                if platform.system() == "Windows":
                    process = subprocess.Popen(
                        cmd,
                        cwd=BASE_DIR,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        creationflags=subprocess.CREATE_NEW_CONSOLE
                    )
                else:
                    process = subprocess.Popen(
                        cmd,
                        cwd=BASE_DIR,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT
                    )
                
                self.server_process = process
                self.save_pid(process.pid)
                
                # Wait a bit and check if server started
                time.sleep(3)
                if process.poll() is None:
                    self.print_success("Server started in background")
                    self.display_networks()
                    
                    if self.auto_browser:
                        self.open_browser()
                    
                    return True
                else:
                    self.print_error("Server failed to start")
                    return False
            else:
                # Start in foreground
                self.print_success("Server starting...")
                self.display_networks()
                print(f"\n{Fore.YELLOW}Press Ctrl+C to stop the server")
                print()
                
                process = subprocess.Popen(
                    cmd,
                    cwd=BASE_DIR,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT
                )
                
                self.server_process = process
                self.save_pid(process.pid)
                
                # Monitor output in separate thread
                monitor_thread = threading.Thread(
                    target=self.monitor_server_output,
                    args=(process,),
                    daemon=True
                )
                monitor_thread.start()
                
                # Wait for process
                process.wait()
                
                return True
                
        except KeyboardInterrupt:
            self.print_info("\nShutting down server...")
            if self.server_process:
                self.server_process.terminate()
                self.server_process.wait()
            if PID_FILE.exists():
                PID_FILE.unlink()
            self.print_success("Server stopped")
            return True
        except Exception as e:
            self.print_error(f"Failed to start server: {e}")
            return False
    
    def run(self, background=False):
        """Run the server launcher"""
        return self.start_server(background=background)


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Smart Server Launcher')
    parser.add_argument('--port', type=int, default=8000, help='Port to run server on')
    parser.add_argument('--no-browser', action='store_true', help='Do not open browser automatically')
    parser.add_argument('--background', action='store_true', help='Run server in background')
    
    args = parser.parse_args()
    
    launcher = ServerLauncher(
        port=args.port,
        auto_browser=not args.no_browser
    )
    
    launcher.run(background=args.background)


if __name__ == "__main__":
    main()
