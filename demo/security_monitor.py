#!/usr/bin/env python3
"""
SECURITY MONITOR - Anti-Piracy Protection
Real-time monitoring for license tampering and piracy attempts
"""

import hashlib
import json
import os
import time
from datetime import datetime, timedelta
from django.utils import timezone
from django.conf import settings
from django.core.cache import cache
import logging

logger = logging.getLogger('demo.security')

class SecurityMonitor:
    """Real-time security monitoring for license protection"""
    
    SECURITY_CACHE_KEY = 'license_security_check'
    CHECK_INTERVAL = 300  # 5 minutes
    
    @classmethod
    def log_security_event(cls, event_type, details, severity='INFO'):
        """Log security events with structured format"""
        
        event_data = {
            'timestamp': datetime.now().isoformat(),
            'event_type': event_type,
            'details': details,
            'severity': severity,
            'user_agent': getattr(cls, '_current_request', {}).get('HTTP_USER_AGENT', 'Unknown'),
            'ip_address': getattr(cls, '_current_request', {}).get('REMOTE_ADDR', 'Unknown')
        }
        
        # Log to file
        if severity == 'CRITICAL':
            logger.critical(f"SECURITY ALERT: {event_type} - {details}")
        elif severity == 'WARNING':
            logger.warning(f"SECURITY WARNING: {event_type} - {details}")
        else:
            logger.info(f"SECURITY INFO: {event_type} - {details}")
        
        # Store in cache for dashboard
        security_events = cache.get('security_events', [])
        security_events.append(event_data)
        
        # Keep only last 100 events
        if len(security_events) > 100:
            security_events = security_events[-100:]
        
        cache.set('security_events', security_events, 86400)  # 24 hours
    
    @classmethod
    def check_file_integrity(cls):
        """Check critical files for tampering"""
        
        critical_files = [
            'demo/services.py',
            'demo/models.py',
            'demo/secure_license_service.py',
            'demo/security_monitor.py'
        ]
        
        integrity_data = cache.get('file_integrity', {})
        
        for file_path in critical_files:
            full_path = os.path.join(settings.BASE_DIR, file_path)
            
            if os.path.exists(full_path):
                try:
                    with open(full_path, 'rb') as f:
                        content = f.read()
                    
                    current_hash = hashlib.sha256(content).hexdigest()
                    
                    if file_path in integrity_data:
                        if integrity_data[file_path] != current_hash:
                            cls.log_security_event(
                                'FILE_TAMPERING',
                                f'Critical file modified: {file_path}',
                                'CRITICAL'
                            )
                    
                    integrity_data[file_path] = current_hash
                    
                except Exception as e:
                    cls.log_security_event(
                        'FILE_ACCESS_ERROR',
                        f'Cannot read critical file {file_path}: {e}',
                        'WARNING'
                    )
        
        cache.set('file_integrity', integrity_data, 86400)
    
    @classmethod
    def check_license_consistency(cls):
        """Check for license inconsistencies that might indicate piracy"""
        
        from .models import DemoStatus, LicenseActivation
        
        try:
            # Check for multiple active licenses
            active_licenses = DemoStatus.objects.filter(is_licensed=True).count()
            
            if active_licenses > 1:
                cls.log_security_event(
                    'MULTIPLE_LICENSES',
                    f'Multiple active licenses detected: {active_licenses}',
                    'CRITICAL'
                )
            
            # Check for suspicious activation patterns
            recent_activations = LicenseActivation.objects.filter(
                attempted_at__gte=timezone.now() - timedelta(hours=1)
            ).count()
            
            if recent_activations > 5:
                cls.log_security_event(
                    'SUSPICIOUS_ACTIVATIONS',
                    f'Too many activation attempts in 1 hour: {recent_activations}',
                    'WARNING'
                )
            
            # Check for failed activations with same license key
            failed_attempts = LicenseActivation.objects.filter(
                success=False,
                attempted_at__gte=timezone.now() - timedelta(days=1)
            ).values('license_key_attempted').distinct().count()
            
            if failed_attempts > 10:
                cls.log_security_event(
                    'BRUTE_FORCE_ATTEMPT',
                    f'Multiple failed activations detected: {failed_attempts}',
                    'CRITICAL'
                )
                
        except Exception as e:
            cls.log_security_event(
                'MONITOR_ERROR',
                f'License consistency check failed: {e}',
                'WARNING'
            )
    
    @classmethod
    def check_system_integrity(cls):
        """Check system for signs of tampering or debugging"""
        
        try:
            # Check for common debugging tools
            import psutil
            
            suspicious_processes = [
                'ollydbg', 'x64dbg', 'ida', 'ghidra', 'cheat engine',
                'process hacker', 'wireshark', 'fiddler'
            ]
            
            running_processes = [p.name().lower() for p in psutil.process_iter(['name'])]
            
            for suspicious in suspicious_processes:
                if any(suspicious in proc for proc in running_processes):
                    cls.log_security_event(
                        'DEBUGGING_TOOL_DETECTED',
                        f'Suspicious process detected: {suspicious}',
                        'WARNING'
                    )
            
            # Check for virtual machine indicators
            vm_indicators = [
                'vmware', 'virtualbox', 'qemu', 'xen', 'hyper-v'
            ]
            
            system_info = ' '.join([
                os.environ.get('COMPUTERNAME', ''),
                os.environ.get('USERNAME', ''),
                str(psutil.virtual_memory().total)
            ]).lower()
            
            for indicator in vm_indicators:
                if indicator in system_info:
                    cls.log_security_event(
                        'VIRTUAL_ENVIRONMENT',
                        f'Virtual machine indicator detected: {indicator}',
                        'INFO'
                    )
                    break
                    
        except ImportError:
            # psutil not available - skip system checks
            pass
        except Exception as e:
            cls.log_security_event(
                'SYSTEM_CHECK_ERROR',
                f'System integrity check failed: {e}',
                'WARNING'
            )
    
    @classmethod
    def perform_security_check(cls):
        """Perform comprehensive security check"""
        
        # Check if we need to run (rate limiting)
        last_check = cache.get(cls.SECURITY_CACHE_KEY)
        current_time = time.time()
        
        if last_check and (current_time - last_check) < cls.CHECK_INTERVAL:
            return  # Skip check
        
        cls.log_security_event('SECURITY_CHECK_START', 'Starting security monitoring check')
        
        # Run all security checks
        cls.check_file_integrity()
        cls.check_license_consistency()
        cls.check_system_integrity()
        
        # Update last check time
        cache.set(cls.SECURITY_CACHE_KEY, current_time, cls.CHECK_INTERVAL * 2)
        
        cls.log_security_event('SECURITY_CHECK_COMPLETE', 'Security monitoring check completed')
    
    @classmethod
    def get_security_status(cls):
        """Get current security status for dashboard"""
        
        security_events = cache.get('security_events', [])
        
        # Count events by severity in last 24 hours
        recent_events = [
            event for event in security_events
            if datetime.fromisoformat(event['timestamp']) > datetime.now() - timedelta(days=1)
        ]
        
        critical_count = len([e for e in recent_events if e['severity'] == 'CRITICAL'])
        warning_count = len([e for e in recent_events if e['severity'] == 'WARNING'])
        
        # Determine overall security level
        if critical_count > 0:
            security_level = 'CRITICAL'
            security_message = f'{critical_count} critical security issues detected'
        elif warning_count > 5:
            security_level = 'HIGH'
            security_message = f'{warning_count} security warnings detected'
        elif warning_count > 0:
            security_level = 'MEDIUM'
            security_message = f'{warning_count} security warnings detected'
        else:
            security_level = 'LOW'
            security_message = 'No security issues detected'
        
        return {
            'security_level': security_level,
            'security_message': security_message,
            'critical_events': critical_count,
            'warning_events': warning_count,
            'total_events': len(recent_events),
            'last_check': cache.get(cls.SECURITY_CACHE_KEY),
            'recent_events': recent_events[-10:]  # Last 10 events
        }
    
    @classmethod
    def set_request_context(cls, request):
        """Set current request context for logging"""
        cls._current_request = {
            'HTTP_USER_AGENT': request.META.get('HTTP_USER_AGENT', 'Unknown'),
            'REMOTE_ADDR': request.META.get('REMOTE_ADDR', 'Unknown')
        }

# Middleware for automatic security monitoring
class SecurityMonitoringMiddleware:
    """Django middleware for automatic security monitoring"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Set request context
        SecurityMonitor.set_request_context(request)
        
        # Perform security check (rate limited)
        try:
            SecurityMonitor.perform_security_check()
        except Exception as e:
            logger.error(f'Security monitoring failed: {e}')
        
        response = self.get_response(request)
        return response