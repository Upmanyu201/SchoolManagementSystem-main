#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Network Manager
Real-time network monitoring and QR code generation
"""

import os
import sys
import json
import socket
import platform
import subprocess
from pathlib import Path
from datetime import datetime

try:
    from colorama import init, Fore, Style
    init(autoreset=True)
except ImportError:
    class Fore:
        GREEN = RED = YELLOW = CYAN = WHITE = ""
    class Style:
        BRIGHT = RESET_ALL = ""

try:
    import qrcode
    HAS_QRCODE = True
except ImportError:
    HAS_QRCODE = False

BASE_DIR = Path(__file__).resolve().parent.parent.parent


class NetworkManager:
    def __init__(self, port=8000):
        self.port = port
        self.networks = []
    
    def print_header(self, title):
        print("\n" + "=" * 70)
        print(f"{Fore.CYAN}{Style.BRIGHT}  {title}")
        print("=" * 70)
    
    def detect_all_networks(self):
        """Detect all network interfaces"""
        networks = []
        
        # Localhost
        networks.append({
            'name': 'Localhost',
            'ip': '127.0.0.1',
            'type': 'localhost',
            'url': f'http://127.0.0.1:{self.port}/'
        })
        
        # Get hostname IP
        try:
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            if local_ip and local_ip != '127.0.0.1':
                networks.append({
                    'name': 'Local Network',
                    'ip': local_ip,
                    'type': 'local',
                    'url': f'http://{local_ip}:{self.port}/'
                })
        except:
            pass
        
        # Windows specific network detection
        if platform.system() == "Windows":
            try:
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
                    
                    if 'adapter' in line.lower():
                        current_adapter = line.split(':')[0].strip()
                    
                    if 'IPv4' in line and ':' in line:
                        ip = line.split(':')[1].strip()
                        if ip and ip not in [n['ip'] for n in networks]:
                            adapter_type = 'unknown'
                            adapter_name = current_adapter or 'Network'
                            
                            if current_adapter:
                                lower_adapter = current_adapter.lower()
                                if 'wi-fi' in lower_adapter or 'wireless' in lower_adapter:
                                    adapter_type = 'wifi'
                                    adapter_name = 'Wi-Fi'
                                elif 'ethernet' in lower_adapter:
                                    adapter_type = 'ethernet'
                                    adapter_name = 'Ethernet'
                                elif 'local area connection' in lower_adapter:
                                    adapter_type = 'hotspot'
                                    adapter_name = 'Mobile Hotspot'
                            
                            networks.append({
                                'name': adapter_name,
                                'ip': ip,
                                'type': adapter_type,
                                'url': f'http://{ip}:{self.port}/'
                            })
            except:
                pass
        
        self.networks = networks
        return networks
    
    def display_networks(self):
        """Display all detected networks"""
        self.print_header("📡 Network Status")
        
        if not self.networks:
            self.detect_all_networks()
        
        if not self.networks:
            print(f"{Fore.RED}No networks detected")
            return
        
        print()
        for i, network in enumerate(self.networks, 1):
            icon = {
                'localhost': '🖥️ ',
                'wifi': '📶',
                'ethernet': '🔌',
                'hotspot': '📱',
                'local': '🌐',
                'unknown': '🔗'
            }.get(network['type'], '🔗')
            
            print(f"{Fore.CYAN}{i}. {icon} {Fore.WHITE}{network['name']}")
            print(f"   {Fore.GREEN}{network['url']}")
            print()
    
    def generate_qr_code(self, url, filename=None):
        """Generate QR code for URL"""
        if not HAS_QRCODE:
            print(f"{Fore.YELLOW}⚠ qrcode library not installed")
            print(f"{Fore.CYAN}Install with: pip install qrcode[pil]")
            return False
        
        try:
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(url)
            qr.make(fit=True)
            
            if filename:
                img = qr.make_image(fill_color="black", back_color="white")
                img.save(filename)
                print(f"{Fore.GREEN}✓ QR code saved to {filename}")
            else:
                # Print QR code to terminal
                qr.print_ascii(invert=True)
            
            return True
        except Exception as e:
            print(f"{Fore.RED}✗ Failed to generate QR code: {e}")
            return False
    
    def generate_all_qr_codes(self):
        """Generate QR codes for all networks"""
        self.print_header("📱 QR Codes for Mobile Access")
        
        if not self.networks:
            self.detect_all_networks()
        
        qr_dir = BASE_DIR / "qr_codes"
        qr_dir.mkdir(exist_ok=True)
        
        for network in self.networks:
            if network['type'] != 'localhost':
                print(f"\n{Fore.CYAN}{network['name']} - {network['url']}")
                
                filename = qr_dir / f"qr_{network['type']}_{network['ip'].replace('.', '_')}.png"
                self.generate_qr_code(network['url'], filename)
        
        print(f"\n{Fore.GREEN}QR codes saved to: {qr_dir}")
    
    def monitor_networks(self, interval=5):
        """Monitor networks for changes"""
        self.print_header("🔄 Network Monitor")
        print(f"{Fore.CYAN}Monitoring networks every {interval} seconds...")
        print(f"{Fore.YELLOW}Press Ctrl+C to stop\n")
        
        previous_networks = []
        
        try:
            while True:
                current_networks = self.detect_all_networks()
                
                # Check for changes
                current_ips = set(n['ip'] for n in current_networks)
                previous_ips = set(n['ip'] for n in previous_networks)
                
                new_ips = current_ips - previous_ips
                removed_ips = previous_ips - current_ips
                
                if new_ips or removed_ips:
                    print(f"\n{Fore.YELLOW}[{datetime.now().strftime('%H:%M:%S')}] Network change detected!")
                    
                    for ip in new_ips:
                        network = next(n for n in current_networks if n['ip'] == ip)
                        print(f"{Fore.GREEN}✓ Connected: {network['name']} ({ip})")
                    
                    for ip in removed_ips:
                        network = next(n for n in previous_networks if n['ip'] == ip)
                        print(f"{Fore.RED}✗ Disconnected: {network['name']} ({ip})")
                    
                    self.display_networks()
                
                previous_networks = current_networks
                
                import time
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print(f"\n{Fore.YELLOW}Monitoring stopped")
    
    def show_menu(self):
        """Show interactive menu"""
        while True:
            self.print_header("🌐 Network Manager")
            
            print(f"\n{Fore.CYAN}1. {Fore.WHITE}Show Networks")
            print(f"{Fore.CYAN}2. {Fore.WHITE}Generate QR Codes")
            print(f"{Fore.CYAN}3. {Fore.WHITE}Monitor Networks")
            print(f"{Fore.CYAN}4. {Fore.WHITE}Refresh Detection")
            print(f"{Fore.CYAN}5. {Fore.WHITE}Exit")
            
            choice = input(f"\n{Fore.YELLOW}Enter choice (1-5): ").strip()
            
            if choice == '1':
                self.detect_all_networks()
                self.display_networks()
                input(f"\n{Fore.CYAN}Press Enter to continue...")
            elif choice == '2':
                self.generate_all_qr_codes()
                input(f"\n{Fore.CYAN}Press Enter to continue...")
            elif choice == '3':
                self.monitor_networks()
            elif choice == '4':
                self.detect_all_networks()
                print(f"{Fore.GREEN}✓ Networks refreshed")
                input(f"\n{Fore.CYAN}Press Enter to continue...")
            elif choice == '5':
                print(f"\n{Fore.GREEN}Goodbye!")
                break
            else:
                print(f"{Fore.RED}Invalid choice")
                input(f"\n{Fore.CYAN}Press Enter to continue...")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Network Manager')
    parser.add_argument('--port', type=int, default=8000, help='Server port')
    parser.add_argument('--monitor', action='store_true', help='Start monitoring mode')
    parser.add_argument('--qr', action='store_true', help='Generate QR codes')
    
    args = parser.parse_args()
    
    manager = NetworkManager(port=args.port)
    
    if args.monitor:
        manager.detect_all_networks()
        manager.monitor_networks()
    elif args.qr:
        manager.detect_all_networks()
        manager.generate_all_qr_codes()
    else:
        manager.show_menu()


if __name__ == "__main__":
    main()
