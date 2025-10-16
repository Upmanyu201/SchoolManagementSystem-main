# Modern Backup & Restore System - 2025

A comprehensive backup and restore system for the School Management System with modern UI, security features, and enterprise-grade functionality.

## Features

### 🔒 Security
- CSRF protection on all endpoints
- File path validation to prevent directory traversal
- Input sanitization and validation
- Permission-based access control
- Secure file handling with size limits

### 🎨 Modern UI
- Professional gradient design
- Smooth animations and transitions
- Responsive layout for all devices
- Real-time progress indicators
- Interactive drag-and-drop file upload
- Toast notifications for user feedback

### ⚡ Performance
- Async operations for better responsiveness
- Pagination for large backup lists
- Background job processing
- Efficient file handling
- Optimized database queries

### 📊 Backup Types
- **Full System Backup**: Complete database backup
- **Students Data**: Student records, fees, and attendance
- **Financial Records**: Fees, payments, and fines
- **Teachers & Subjects**: Staff and academic data

## Usage

### Web Interface

1. **Access the System**
   - Navigate to `/backup/` in your browser
   - Requires login and appropriate permissions

2. **Create Backup**
   - Click "Create Backup" button
   - Select backup type and optional custom name
   - Monitor progress in real-time

3. **Restore Data**
   - Click "Restore Data" button
   - Upload JSON backup file or select from history
   - Choose merge or replace mode
   - Confirm and monitor restoration

### Command Line

```bash
# Create backups
python manage.py backup_system create --type=full --name=daily_backup
python manage.py backup_system create --type=students

# Restore from backup
python manage.py backup_system restore --file=backup.json --mode=merge

# List backups
python manage.py backup_system list --limit=10

# Clean up old backups
python manage.py backup_system cleanup --days=30

# Check system status
python manage.py backup_system status

# Verify backup integrity
python manage.py backup_system verify --file=backup.json
```

## API Endpoints

### Backup Operations
- `POST /backup/api/create/` - Create new backup
- `GET /backup/api/history/` - Get backup history
- `GET /backup/api/status/<job_id>/` - Get job status

### Restore Operations
- `POST /backup/api/restore/upload/` - Restore from uploaded file
- `POST /backup/api/restore/history/<backup_id>/` - Restore from history

### Utility Endpoints
- `GET /backup/api/download/<backup_id>/` - Download backup file
- `DELETE /backup/api/delete/<backup_id>/` - Delete backup
- `GET /backup/api/export/history/` - Export backup history as CSV

## Configuration

### Settings
```python
# Backup directory (default: BASE_DIR/backups)
BACKUP_DIR = os.path.join(BASE_DIR, 'backups')

# Maximum file size for uploads (100MB)
MAX_BACKUP_FILE_SIZE = 100 * 1024 * 1024

# Backup retention period (days)
BACKUP_RETENTION_DAYS = 30
```

### Permissions
Required permissions for backup operations:
- `backup.add_backupjob` - Create backups
- `backup.add_restorejob` - Restore data
- `backup.delete_backupjob` - Delete backups
- `backup.view_backupjob` - View backup history

## Security Features

### File Validation
- JSON format validation
- File size limits (100MB max)
- Path traversal prevention
- Malicious filename sanitization

### Access Control
- User authentication required
- Permission-based authorization
- CSRF token validation
- Secure file storage

### Data Protection
- Backup file checksums
- Secure temporary file handling
- Automatic cleanup of temp files
- Audit trail for all operations

## Monitoring

### System Status
The system provides real-time monitoring of:
- Database connectivity
- Storage space usage
- Recent job statuses
- Service health

### Logging
All operations are logged with appropriate levels:
- INFO: Successful operations
- WARNING: Non-critical issues
- ERROR: Failed operations
- DEBUG: Detailed debugging information

## Troubleshooting

### Common Issues

1. **Permission Denied**
   - Ensure user has required permissions
   - Check file system permissions for backup directory

2. **File Not Found**
   - Verify backup file exists in backup directory
   - Check file path security restrictions

3. **Invalid JSON Format**
   - Validate backup file structure
   - Use `backup_system verify` command

4. **Restore Failures**
   - Check database connectivity
   - Verify backup file integrity
   - Review error logs for details

### Debug Mode
Enable debug logging in settings:
```python
LOGGING = {
    'loggers': {
        'backup': {
            'level': 'DEBUG',
            'handlers': ['console', 'file'],
        }
    }
}
```

## Development

### Running Tests
```bash
python manage.py test backup
```

### Code Structure
- `views.py` - Main view functions
- `secure_views.py` - API endpoints with security
- `models.py` - Database models
- `urls.py` - URL routing
- `management/commands/` - CLI commands
- `templates/backup/` - HTML templates
- `static/` - CSS and JavaScript files

## License

This backup system is part of the School Management System project.