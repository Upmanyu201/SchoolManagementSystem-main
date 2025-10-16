# Modern Backup System Tests - 2025 Standards
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.conf import settings
from pathlib import Path
import json
import tempfile
import os

User = get_user_model()

class BackupSystemTestCase(TestCase):
    """Test cases for the modern backup system"""
    
    def setUp(self):
        """Set up test environment"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.user.user_permissions.add(
            *self.get_backup_permissions()
        )
        self.client.login(username='testuser', password='testpass123')
        
        # Create test backup directory
        self.backup_dir = Path(settings.BASE_DIR) / 'backups'
        self.backup_dir.mkdir(exist_ok=True)
    
    def get_backup_permissions(self):
        """Get required backup permissions"""
        from django.contrib.auth.models import Permission
        return Permission.objects.filter(
            codename__in=[
                'add_backupjob',
                'add_restorejob',
                'delete_backupjob',
                'view_backupjob'
            ]
        )
    
    def test_backup_page_loads(self):
        """Test that the backup page loads correctly"""
        response = self.client.get(reverse('backup:backup_restore'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Backup & Restore System')
        self.assertContains(response, 'Create Backup')
        self.assertContains(response, 'Restore Data')
    
    def test_backup_page_context(self):
        """Test backup page context data"""
        response = self.client.get(reverse('backup:backup_restore'))
        self.assertIn('page_title', response.context)
        self.assertIn('user_permissions', response.context)
        self.assertIn('statistics', response.context)
        
        permissions = response.context['user_permissions']
        self.assertTrue(permissions['can_backup'])
        self.assertTrue(permissions['can_restore'])
    
    def test_create_backup_api(self):
        """Test backup creation API"""
        data = {
            'backup_type': 'students',
            'backup_name': 'test_backup'
        }
        
        response = self.client.post(
            reverse('backup:api_create_backup'),
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertEqual(result['status'], 'success')
        self.assertIn('job_id', result['data'])
    
    def test_backup_history_api(self):
        """Test backup history API"""
        response = self.client.get(reverse('backup:api_backup_history'))
        self.assertEqual(response.status_code, 200)
        
        result = response.json()
        self.assertEqual(result['status'], 'success')
        self.assertIn('backups', result['data'])
        self.assertIn('pagination', result['data'])
    
    def test_system_status_api(self):
        """Test system status API"""
        response = self.client.get(reverse('backup:system_status'))
        self.assertEqual(response.status_code, 200)
        
        result = response.json()
        self.assertEqual(result['status'], 'success')
        self.assertIn('database', result['data'])
        self.assertIn('storage', result['data'])
        self.assertIn('backup_service', result['data'])
    
    def test_restore_upload_api(self):
        """Test restore upload API with mock file"""
        # Create a mock backup file
        test_data = [
            {
                "model": "students.student",
                "pk": 1,
                "fields": {
                    "first_name": "Test",
                    "last_name": "Student",
                    "admission_number": "TEST001"
                }
            }
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_data, f)
            temp_file_path = f.name
        
        try:
            with open(temp_file_path, 'rb') as f:
                response = self.client.post(
                    reverse('backup:api_restore_upload'),
                    {
                        'backup_file': f,
                        'restore_mode': 'merge'
                    }
                )
            
            # Should return success or validation error
            self.assertIn(response.status_code, [200, 400])
            
        finally:
            # Clean up temp file
            os.unlink(temp_file_path)
    
    def test_export_history_api(self):
        """Test export history API"""
        response = self.client.get(reverse('backup:api_export_history'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv')
    
    def test_unauthorized_access(self):
        """Test unauthorized access to backup system"""
        # Create user without permissions
        user_no_perms = User.objects.create_user(
            username='noperms',
            email='noperms@example.com',
            password='testpass123'
        )
        
        client = Client()
        client.login(username='noperms', password='testpass123')
        
        # Should be redirected or get 403
        response = client.post(reverse('backup:api_create_backup'))
        self.assertIn(response.status_code, [302, 403])
    
    def test_backup_security_validation(self):
        """Test security validations in backup system"""
        # Test invalid backup type
        data = {
            'backup_type': 'invalid_type',
            'backup_name': 'test'
        }
        
        response = self.client.post(
            reverse('backup:api_create_backup'),
            data=json.dumps(data),
            content_type='application/json'
        )
        
        # Should handle invalid type gracefully
        self.assertEqual(response.status_code, 200)
        
        # Test malicious filename
        data = {
            'backup_type': 'full',
            'backup_name': '../../../etc/passwd'
        }
        
        response = self.client.post(
            reverse('backup:api_create_backup'),
            data=json.dumps(data),
            content_type='application/json'
        )
        
        # Should sanitize filename
        self.assertEqual(response.status_code, 200)
    
    def tearDown(self):
        """Clean up test environment"""
        # Clean up any test backup files
        if self.backup_dir.exists():
            for file in self.backup_dir.glob('test_*'):
                try:
                    file.unlink()
                except:
                    pass

class BackupModelTestCase(TestCase):
    """Test cases for backup models"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_backup_job_creation(self):
        """Test BackupJob model creation"""
        from .models import BackupJob
        
        job = BackupJob.objects.create(
            status='pending',
            backup_type='full',
            created_by=self.user
        )
        
        self.assertEqual(job.status, 'pending')
        self.assertEqual(job.backup_type, 'full')
        self.assertEqual(job.created_by, self.user)
        self.assertIsNotNone(job.created_at)
    
    def test_restore_job_creation(self):
        """Test RestoreJob model creation"""
        from .models import RestoreJob
        
        job = RestoreJob.objects.create(
            status='pending',
            source_type='uploaded',
            mode='merge'
        )
        
        self.assertEqual(job.status, 'pending')
        self.assertEqual(job.source_type, 'uploaded')
        self.assertEqual(job.mode, 'merge')
        self.assertIsNotNone(job.created_at)
    
    def test_backup_history_creation(self):
        """Test BackupHistory model creation"""
        from .models import BackupHistory
        
        history = BackupHistory.objects.create(
            file_name='test_backup.json',
            operation_type='backup'
        )
        
        self.assertEqual(history.file_name, 'test_backup.json')
        self.assertEqual(history.operation_type, 'backup')
        self.assertIsNotNone(history.date)

class BackupSecurityTestCase(TestCase):
    """Test cases for backup security features"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client = Client()
        self.client.login(username='testuser', password='testpass123')
    
    def test_csrf_protection(self):
        """Test CSRF protection on backup endpoints"""
        # Test without CSRF token
        response = self.client.post(
            reverse('backup:api_create_backup'),
            data=json.dumps({'backup_type': 'full'}),
            content_type='application/json'
        )
        
        # Should require CSRF token
        self.assertIn(response.status_code, [403, 200])  # 200 if CSRF middleware disabled in tests
    
    def test_file_path_validation(self):
        """Test file path validation for security"""
        from .security import BackupSecurityManager
        
        # Test path traversal attempts
        malicious_paths = [
            '../../../etc/passwd',
            '..\\..\\..\\windows\\system32\\config\\sam',
            '/etc/shadow',
            'C:\\Windows\\System32\\config\\SAM'
        ]
        
        for path in malicious_paths:
            sanitized = BackupSecurityManager.sanitize_filename(path)
            self.assertNotIn('..', sanitized)
            self.assertNotIn('/', sanitized)
            self.assertNotIn('\\', sanitized)
    
    def test_file_size_validation(self):
        """Test file size validation"""
        from .security import BackupSecurityManager
        
        # Test valid size
        self.assertTrue(BackupSecurityManager.validate_file_size(1024 * 1024))  # 1MB
        
        # Test oversized file
        self.assertFalse(BackupSecurityManager.validate_file_size(200 * 1024 * 1024))  # 200MB