#!/usr/bin/env python3
"""
Demo Mode Reset Script
Resets the application to demo mode by clearing license data
"""

import os
import sys
import django
from datetime import datetime, timedelta

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'school_management.settings')
django.setup()

from demo.models import DemoStatus, LicenseActivation
from demo.secure_license_service import SecureLicenseService

def reset_demo_mode():
    """Reset application to demo mode using Django models"""
    print("=" * 60)
    print("🔄 DEMO MODE RESET SCRIPT")
    print("=" * 60)
    
    try:
        print("1. Getting hardware fingerprint...")
        machine_id = SecureLicenseService.get_hardware_fingerprint()
        print(f"   Machine ID: {machine_id}")
        
        print("\n2. Clearing existing demo status...")
        # Delete all existing demo statuses
        deleted_demo_count = DemoStatus.objects.all().delete()[0]
        print(f"   Cleared {deleted_demo_count} demo status records")
        
        print("\n3. Clearing license activation history...")
        # Delete all license activation attempts
        deleted_activation_count = LicenseActivation.objects.all().delete()[0]
        print(f"   Cleared {deleted_activation_count} activation attempts")
        
        print("\n4. Creating fresh demo status...")
        # Calculate new demo expiry (15 days from now)
        from django.utils import timezone
        now = timezone.now()
        demo_expires = now + timedelta(minutes=15*24*60)
        
        # Create new demo status
        demo_status = DemoStatus.objects.create(
            machine_id=machine_id,
            demo_started=now,
            demo_expires=demo_expires,
            is_licensed=False,
            license_key=None,
            activated_by=None,
            activated_at=None
        )
        
        print(f"   ✅ New demo status created")
        print(f"   📅 Demo started: {now.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   ⏰ Demo expires: {demo_expires.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   📊 Days remaining: {demo_status.days_remaining}")
        
        print("\n5. Verifying demo status...")
        # Verify the reset worked
        current_status = DemoStatus.get_current_status()
        print(f"   Machine ID: {current_status.machine_id}")
        print(f"   Is Active: {'✅ Yes' if current_status.is_active else '❌ No'}")
        print(f"   Is Licensed: {'✅ Yes' if current_status.is_licensed else '❌ No'}")
        print(f"   Days Remaining: {current_status.days_remaining}")
        
        print("\n" + "=" * 60)
        print("🎉 DEMO MODE RESET COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print("\n📋 Summary:")
        print(f"   • Demo period: 15 days (expires {demo_expires.strftime('%Y-%m-%d')})")
        print(f"   • License status: Unlicensed")
        print(f"   • Machine ID: {machine_id}")
        print(f"   • All modules: Available for {current_status.days_remaining} days")
        print("\n💡 You can now use the School Management System for 15 days!")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error resetting demo mode: {e}")
        import traceback
        traceback.print_exc()
        return False

def verify_demo_status():
    """Verify current demo status using Django models"""
    print("\n" + "=" * 60)
    print("🔍 DEMO STATUS VERIFICATION")
    print("=" * 60)
    
    try:
        # Get current demo status
        demo_status = DemoStatus.get_current_status()
        
        print(f"📱 Machine ID: {demo_status.machine_id}")
        print(f"📅 Demo Started: {demo_status.demo_started.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"⏰ Demo Expires: {demo_status.demo_expires.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📊 Days Remaining: {demo_status.days_remaining}")
        print(f"✅ Is Active: {'Yes' if demo_status.is_active else 'No'}")
        print(f"🔐 Is Licensed: {'Yes' if demo_status.is_licensed else 'No'}")
        
        if demo_status.license_key:
            print(f"🔑 License Key: {demo_status.license_key[:20]}...")
            
            # Validate current license
            is_valid, message = SecureLicenseService.validate_secure_license(demo_status.license_key)
            print(f"🛡️  License Valid: {'Yes' if is_valid else 'No'}")
            print(f"📝 Validation: {message}")
            
        if demo_status.activated_at:
            print(f"🎯 Activated At: {demo_status.activated_at.strftime('%Y-%m-%d %H:%M:%S')}")
            
        if demo_status.activated_by:
            print(f"👤 Activated By: {demo_status.activated_by.get_full_name() or demo_status.activated_by.username}")
        
        # Show recent activation attempts
        recent_attempts = LicenseActivation.objects.order_by('-attempted_at')[:3]
        if recent_attempts:
            print("\n📝 Recent License Attempts:")
            for attempt in recent_attempts:
                status_icon = "✅" if attempt.success else "❌"
                print(f"   {status_icon} {attempt.attempted_at.strftime('%Y-%m-%d %H:%M')} - {attempt.license_key_attempted[:15]}...")
                if attempt.error_message:
                    print(f"      Error: {attempt.error_message}")
        
        # Overall status
        print("\n" + "=" * 60)
        if demo_status.is_licensed:
            print("🎉 STATUS: FULLY LICENSED")
            print("All features are permanently unlocked!")
        elif demo_status.is_active:
            print(f"⏳ STATUS: DEMO ACTIVE ({demo_status.days_remaining} days left)")
            print("All features are available during the trial period.")
        else:
            print("🔒 STATUS: DEMO EXPIRED")
            print("License activation required to continue using the system.")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ Error checking demo status: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Main function"""
    if len(sys.argv) > 1 and sys.argv[1] == '--verify':
        verify_demo_status()
        return
    
    print("🔄 SCHOOL MANAGEMENT SYSTEM - DEMO RESET")
    print("\nThis script will reset the application to demo mode.")
    print("\n📋 What this will do:")
    print("   • Clear any existing license activation")
    print("   • Reset demo period to 15 full days")
    print("   • Clear all activation history")
    print("   • Restore access to all 17 modules")
    print("   • Enable all 26 ML models")
    print("\n⚠️  Warning: This will deactivate any current license!")
    print()
    
    confirm = input("Continue with demo reset? (y/N): ").strip().lower()
    
    if confirm in ['y', 'yes']:
        success = reset_demo_mode()
        if success:
            print("\n" + "="*60)
            verify_demo_status()
            print("\n🎉 Demo mode has been successfully reset!")
            print("\n🚀 Next Steps:")
            print("   1. Start the Django server: python manage.py runserver")
            print("   2. Access the system at: http://127.0.0.1:8000/")
            print("   3. Enjoy 15 days of full access to all features!")
            print("\n💡 To purchase a permanent license, contact:")
            print("   📧 Email: Upmanyu201@gmail.com")
            print("   📞 Phone: +91-9955590919")
        else:
            print("\n❌ Failed to reset demo mode. Check the error messages above.")
    else:
        print("\n🚫 Demo reset cancelled.")

if __name__ == "__main__":
    main()