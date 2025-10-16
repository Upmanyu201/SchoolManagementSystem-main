#!/usr/bin/env python3
"""
SECURE LICENSE SERVICE - Anti-Piracy Protection
Replaces vulnerable license system with enterprise-grade security
"""

import hashlib
import hmac
import secrets
import platform
import subprocess
import os
import json
from datetime import datetime, timedelta
from django.utils import timezone
from django.conf import settings
from .models import DemoStatus, LicenseActivation

class SecureLicenseService:
    """Enterprise-grade license service with anti-piracy protection"""
    
    # CRITICAL: These keys MUST be different in production
    MASTER_KEY = os.getenv('LICENSE_MASTER_KEY', 'CHANGE_IN_PRODUCTION_2024')
    VALIDATION_KEY = os.getenv('LICENSE_VALIDATION_KEY', 'VALIDATION_KEY_2024')
    
    @classmethod
    def get_hardware_fingerprint(cls):
        """Generate tamper-resistant hardware fingerprint"""
        fingerprint_data = []
        
        try:
            # 1. CPU Information (harder to spoof)
            if platform.system() == 'Windows':
                try:
                    # CPU Serial Number
                    result = subprocess.run(['wmic', 'cpu', 'get', 'processorid'], 
                                          capture_output=True, text=True, timeout=5)
                    if result.returncode == 0:
                        cpu_id = result.stdout.split('\n')[1].strip()
                        if cpu_id and cpu_id != 'ProcessorId':
                            fingerprint_data.append(f"cpu:{cpu_id}")
                    
                    # Motherboard Serial
                    result = subprocess.run(['wmic', 'baseboard', 'get', 'serialnumber'], 
                                          capture_output=True, text=True, timeout=5)
                    if result.returncode == 0:
                        mb_serial = result.stdout.split('\n')[1].strip()
                        if mb_serial and mb_serial != 'SerialNumber':
                            fingerprint_data.append(f"mb:{mb_serial}")
                    
                    # BIOS Serial
                    result = subprocess.run(['wmic', 'bios', 'get', 'serialnumber'], 
                                          capture_output=True, text=True, timeout=5)
                    if result.returncode == 0:
                        bios_serial = result.stdout.split('\n')[1].strip()
                        if bios_serial and bios_serial != 'SerialNumber':
                            fingerprint_data.append(f"bios:{bios_serial}")
                            
                except Exception:
                    pass
            
            # 2. Network MAC (primary network adapter only)
            import uuid
            mac = uuid.getnode()
            fingerprint_data.append(f"mac:{mac}")
            
            # 3. System Architecture
            fingerprint_data.append(f"arch:{platform.machine()}")
            fingerprint_data.append(f"os:{platform.system()}")
            
            # 4. Installation timestamp (prevents easy copying)
            install_marker = os.path.join(settings.BASE_DIR, '.install_id')
            if not os.path.exists(install_marker):
                install_id = secrets.token_hex(16)
                try:
                    with open(install_marker, 'w') as f:
                        f.write(install_id)
                except:
                    pass
            else:
                try:
                    with open(install_marker, 'r') as f:
                        install_id = f.read().strip()
                except:
                    install_id = 'fallback'
            
            fingerprint_data.append(f"install:{install_id}")
            
        except Exception:
            # Fallback fingerprint
            fingerprint_data = [f"mac:{uuid.getnode()}", f"arch:{platform.machine()}"]
        
        # Combine and hash
        combined = '|'.join(sorted(fingerprint_data))
        fingerprint = hashlib.sha256(combined.encode()).hexdigest()[:24]
        
        return fingerprint
    
    @classmethod
    def generate_secure_license(cls, hardware_fingerprint, customer_id=None, expiry_days=None):
        """Generate cryptographically secure license"""
        
        # License components
        timestamp = int(datetime.now().timestamp())
        customer_id = customer_id or 'DEMO'
        expiry = timestamp + (expiry_days * 86400) if expiry_days else 0
        
        # Create license payload
        payload = {
            'hw': hardware_fingerprint,
            'cid': customer_id,
            'ts': timestamp,
            'exp': expiry,
            'v': '2.0',  # Version
            'salt': secrets.token_hex(8)  # Add salt for security
        }
        
        # Sign with HMAC
        payload_str = json.dumps(payload, sort_keys=True)
        signature = hmac.new(
            cls.MASTER_KEY.encode(),
            payload_str.encode(),
            hashlib.sha256
        ).hexdigest()[:16]
        
        # Encode license
        import base64
        license_data = base64.b64encode(
            f"{payload_str}|{signature}".encode()
        ).decode().replace('=', '').replace('+', '-').replace('/', '_')
        
        # Format as SMS-FULL-{full_data} (new secure format)
        return f"SMS-FULL-{license_data}"
    
    @classmethod
    def validate_secure_license(cls, license_key):
        """Validate secure license with anti-tampering checks"""
        
        try:
            # Parse license format
            if license_key.startswith('SMS-FULL-'):
                # New full format
                license_data = license_key[9:]  # Remove 'SMS-FULL-'
            elif license_key.startswith('SMS-'):
                # Legacy format - not supported
                return False, "Legacy format not supported. Please regenerate license."
            else:
                return False, "Invalid license format"
            
            # Decode
            import base64
            try:
                # Restore base64 padding
                padding_needed = 4 - (len(license_data) % 4)
                if padding_needed != 4:
                    license_data += '=' * padding_needed
                
                # Restore base64 characters
                license_data = license_data.replace('-', '+').replace('_', '/')
                
                # Decode with proper error handling
                decoded_bytes = base64.b64decode(license_data)
                decoded = decoded_bytes.decode('utf-8', errors='ignore')
                
                # Validate decoded data is not empty
                if not decoded or len(decoded.strip()) == 0:
                    return False, "License data is empty or corrupted"
                    
            except Exception as e:
                return False, f"Invalid license encoding: {str(e)}"
            
            # Split payload and signature
            parts = decoded.split('|')
            if len(parts) != 2:
                return False, "Invalid license structure"
            
            payload_str, signature = parts
            
            # Verify signature
            expected_signature = hmac.new(
                cls.MASTER_KEY.encode(),
                payload_str.encode(),
                hashlib.sha256
            ).hexdigest()[:16]
            
            if not hmac.compare_digest(signature, expected_signature):
                return False, "License signature verification failed"
            
            # Parse payload
            payload = json.loads(payload_str)
            
            # Check hardware fingerprint
            current_fingerprint = cls.get_hardware_fingerprint()
            if payload['hw'] != current_fingerprint:
                return False, f"License not valid for this machine (HW mismatch)"
            
            # Check expiry
            if payload.get('exp', 0) > 0:
                if datetime.now().timestamp() > payload['exp']:
                    return False, "License has expired"
            
            return True, "Valid license"
            
        except Exception as e:
            return False, f"License validation error: {str(e)}"
    
    @classmethod
    def get_demo_status_secure(cls):
        """Get demo status with enhanced security checks"""
        status = DemoStatus.get_current_status()
        
        # Enhanced anti-piracy checks
        if status.is_licensed and status.license_key:
            is_valid, message = cls.validate_secure_license(status.license_key)
            
            if not is_valid:
                # License is invalid - possible tampering
                import logging
                logger = logging.getLogger('demo.security')
                logger.critical(f'LICENSE TAMPERING DETECTED: {message}')
                
                # Revoke license
                status.is_licensed = False
                status.license_key = None
                status.activated_by = None
                status.activated_at = None
                status.save()
                
                # Log security incident
                LicenseActivation.objects.create(
                    demo_status=status,
                    license_key_attempted=status.license_key or 'UNKNOWN',
                    error_message=f"Security violation: {message}",
                    success=False
                )
        
        return status
    
    @classmethod
    def activate_secure_license(cls, license_key, user=None):
        """Activate license with enhanced security"""
        import logging
        
        demo_status = cls.get_demo_status_secure()
        logger = logging.getLogger('demo.security')
        
        # Log activation attempt
        logger.info(f'Secure license activation attempt: {license_key[:8]}...')
        
        activation = LicenseActivation.objects.create(
            demo_status=demo_status,
            license_key_attempted=license_key,
            attempted_by=user
        )
        
        # Validate license
        is_valid, message = cls.validate_secure_license(license_key)
        
        if is_valid:
            # Check for duplicate activations
            existing = DemoStatus.objects.filter(
                license_key=license_key,
                is_licensed=True
            ).exclude(id=demo_status.id).first()
            
            if existing:
                logger.warning(f'DUPLICATE LICENSE DETECTED: {license_key[:8]}...')
                activation.error_message = "License already in use"
                activation.save()
                return False, "This license is already active on another installation"
            
            # Activate
            demo_status.is_licensed = True
            demo_status.license_key = license_key
            demo_status.activated_by = user
            demo_status.activated_at = timezone.now()
            demo_status.save()
            
            activation.success = True
            activation.save()
            
            logger.info(f'Secure license activated successfully')
            return True, "License activated successfully!"
        
        else:
            logger.warning(f'Secure license validation failed: {message}')
            activation.error_message = message
            activation.save()
            return False, message
    
    @classmethod
    def check_demo_limits(cls, module_name, action_type):
        """Check if action is allowed under demo limitations"""
        demo_status = cls.get_demo_status_secure()
        
        if demo_status.is_licensed:
            return True, "Licensed version - no limits"
        
        if not demo_status.is_active:
            return False, "Demo period has expired"
        
        # Module-specific limits
        if module_name == 'messaging':
            if action_type == 'bulk_sms':
                return False, "Bulk messaging requires licensed version"
            elif action_type == 'daily_sms_count':
                return True, f"Demo: {demo_status.days_remaining} days remaining"
        
        return True, f"Demo: {demo_status.days_remaining} days remaining"

# Backward compatibility wrapper
class LicenseService(SecureLicenseService):
    """Backward compatible wrapper for existing code"""
    
    @classmethod
    def get_machine_id(cls):
        """Legacy method - returns hardware fingerprint"""
        return cls.get_hardware_fingerprint()
    
    @classmethod
    def generate_license_key(cls, machine_id=None):
        """Legacy method - generates secure license"""
        fingerprint = machine_id or cls.get_hardware_fingerprint()
        return cls.generate_secure_license(fingerprint)
    
    @classmethod
    def validate_license_key(cls, license_key, machine_id=None):
        """Legacy method - validates secure license"""
        return cls.validate_secure_license(license_key)
    
    @classmethod
    def get_demo_status(cls):
        """Legacy method - returns secure demo status"""
        return cls.get_demo_status_secure()
    
    @classmethod
    def activate_license(cls, license_key, user=None):
        """Legacy method - activates secure license"""
        return cls.activate_secure_license(license_key, user)