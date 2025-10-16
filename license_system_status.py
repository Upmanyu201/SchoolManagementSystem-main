#!/usr/bin/env python3
"""
License System Status Report
Shows the current status of the license system after TDD fixes
"""

import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'school_management.settings')
django.setup()

from demo.secure_license_service import SecureLicenseService
from demo.models import DemoStatus, LicenseActivation
from demo.security_monitor import SecurityMonitor

def show_license_system_status():
    """Show comprehensive license system status"""
    
    print("=" * 80)
    print("🔐 LICENSE SYSTEM STATUS REPORT")
    print("=" * 80)
    
    # System Information
    print("\n📊 SYSTEM INFORMATION")
    print("-" * 40)
    fingerprint = SecureLicenseService.get_hardware_fingerprint()
    print(f"Hardware Fingerprint: {fingerprint}")
    print(f"Master Key Status: {'✅ Set' if SecureLicenseService.MASTER_KEY != 'CHANGE_IN_PRODUCTION_2024' else '⚠️  Default (Change in Production)'}")
    
    # Database Status
    print("\n💾 DATABASE STATUS")
    print("-" * 40)
    demo_statuses = DemoStatus.objects.all().count()
    license_attempts = LicenseActivation.objects.all().count()
    active_licenses = DemoStatus.objects.filter(is_licensed=True).count()
    
    print(f"Demo Status Records: {demo_statuses}")
    print(f"License Activation Attempts: {license_attempts}")
    print(f"Active Licenses: {active_licenses}")
    
    # Current Demo Status
    print("\n🎯 CURRENT DEMO STATUS")
    print("-" * 40)
    current_status = DemoStatus.get_current_status()
    print(f"Machine ID: {current_status.machine_id}")
    print(f"Licensed: {'✅ Yes' if current_status.is_licensed else '❌ No'}")
    print(f"Demo Active: {'✅ Yes' if current_status.is_active else '❌ No'}")
    print(f"Days Remaining: {current_status.days_remaining}")
    
    if current_status.license_key:
        print(f"License Key: {current_status.license_key[:20]}...")
        print(f"Activated At: {current_status.activated_at}")
        
        # Validate current license
        is_valid, message = SecureLicenseService.validate_secure_license(current_status.license_key)
        print(f"License Valid: {'✅ Yes' if is_valid else '❌ No'}")
        print(f"Validation Message: {message}")
    
    # Recent License Attempts
    print("\n📝 RECENT LICENSE ATTEMPTS")
    print("-" * 40)
    recent_attempts = LicenseActivation.objects.order_by('-attempted_at')[:5]
    
    if recent_attempts:
        for attempt in recent_attempts:
            status_icon = "✅" if attempt.success else "❌"
            print(f"{status_icon} {attempt.attempted_at.strftime('%Y-%m-%d %H:%M:%S')} - {attempt.license_key_attempted[:15]}...")
            if attempt.error_message:
                print(f"   Error: {attempt.error_message}")
    else:
        print("No license attempts found")
    
    # Security Status
    print("\n🛡️ SECURITY STATUS")
    print("-" * 40)
    security_status = SecurityMonitor.get_security_status()
    
    level_icons = {
        'LOW': '🟢',
        'MEDIUM': '🟡', 
        'HIGH': '🟠',
        'CRITICAL': '🔴'
    }
    
    print(f"Security Level: {level_icons.get(security_status['security_level'], '❓')} {security_status['security_level']}")
    print(f"Security Message: {security_status['security_message']}")
    print(f"Critical Events: {security_status['critical_events']}")
    print(f"Warning Events: {security_status['warning_events']}")
    print(f"Total Events (24h): {security_status['total_events']}")
    
    # Test License Generation
    print("\n🧪 LIVE LICENSE TEST")
    print("-" * 40)
    test_license = SecureLicenseService.generate_secure_license(fingerprint, "STATUS_TEST")
    print(f"Generated Test License: {test_license[:30]}...")
    print(f"License Length: {len(test_license)} characters")
    print(f"Format: {'✅ SMS-FULL' if test_license.startswith('SMS-FULL-') else '❌ Invalid'}")
    
    # Validate test license
    is_valid, message = SecureLicenseService.validate_secure_license(test_license)
    print(f"Test Validation: {'✅ Pass' if is_valid else '❌ Fail'}")
    print(f"Validation Result: {message}")
    
    # System Health Summary
    print("\n🏥 SYSTEM HEALTH SUMMARY")
    print("-" * 40)
    
    health_checks = [
        ("Hardware Fingerprint", len(fingerprint) == 24 and all(c in '0123456789abcdef' for c in fingerprint)),
        ("License Generation", test_license.startswith('SMS-FULL-')),
        ("License Validation", is_valid),
        ("Database Connection", demo_statuses >= 0),
        ("Security Monitoring", security_status['security_level'] in ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'])
    ]
    
    all_healthy = True
    for check_name, is_healthy in health_checks:
        status_icon = "✅" if is_healthy else "❌"
        print(f"{status_icon} {check_name}")
        if not is_healthy:
            all_healthy = False
    
    print("\n" + "=" * 80)
    if all_healthy:
        print("🎉 LICENSE SYSTEM STATUS: FULLY OPERATIONAL")
        print("All components are working correctly!")
    else:
        print("⚠️  LICENSE SYSTEM STATUS: ISSUES DETECTED")
        print("Some components need attention.")
    print("=" * 80)
    
    return all_healthy

if __name__ == "__main__":
    show_license_system_status()