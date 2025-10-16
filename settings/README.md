# Enhanced Settings Module

## Overview
The enhanced settings module provides comprehensive system configuration and management capabilities for the School Management System, integrating with the existing core modules and 26 ML models.

## Features

### 🎛️ System Configuration
- **Academic Settings**: Academic year, session dates, attendance requirements
- **Fee Management**: Late fees, bulk discounts, grace periods
- **ML Integration**: 26 trained models with configurable thresholds
- **Security**: Session timeouts, login attempts, lockout policies
- **Backup**: Automated backup scheduling and retention

### 🔔 Notification Management
- **Multi-Channel**: SMS (MSG91, Twilio), WhatsApp, Email
- **Templates**: Customizable message templates with placeholders
- **Testing**: Built-in notification testing functionality

### 🤖 AI/ML Configuration
- **Model Control**: Enable/disable individual ML models
- **Performance Tuning**: Batch sizes, cache duration, thresholds
- **Real-time vs Batch**: Configurable prediction modes

### 👤 User Preferences
- **UI Customization**: Themes, layouts, language preferences
- **Notifications**: Personal notification preferences
- **Module Settings**: Per-module configuration storage

### 📊 System Health Monitoring
- **Real-time Metrics**: Database size, response times, resource usage
- **ML Model Status**: Model availability and accuracy tracking
- **Health Dashboard**: Visual system status overview

### 🔧 Maintenance Tools
- **Cache Management**: Clear system cache
- **Database Optimization**: SQLite VACUUM operations
- **Log Cleanup**: Automated log file management
- **ML Model Updates**: Trigger model retraining

## Models

### SystemSettings
Core system configuration including academic, fee, attendance, messaging, ML, security, and backup settings.

### NotificationSettings
SMS, WhatsApp, and email configuration with customizable message templates.

### MLSettings
Machine learning model configuration with thresholds and performance settings.

### UserPreferences
Individual user interface and notification preferences.

### SystemHealth
System health metrics and monitoring data.

### AuditLog
Comprehensive audit trail for all settings changes.

## Integration Points

### Core Module Integration
- **Fee Calculation Engine**: Automatic settings sync for fee calculations
- **ML Service**: Dynamic configuration updates for 26 ML models
- **Messaging Service**: Real-time notification settings updates
- **Backup System**: Automated backup scheduling integration

### Existing System Compatibility
- **Django 5.1.6**: Full compatibility with existing Django setup
- **SQLite Database**: Optimized for existing SQLite configuration
- **User Management**: Integrates with CustomUser and module permissions
- **Caching**: Works with existing local memory cache setup

## Usage

### Installation
1. Add 'settings' to INSTALLED_APPS in Django settings
2. Run migrations: `python manage.py migrate`
3. Initialize default settings: `python manage.py init_settings`

### Access URLs
- Settings Dashboard: `/settings/`
- System Configuration: `/settings/system/`
- Notifications: `/settings/notifications/`
- ML Settings: `/settings/ml/`
- User Preferences: `/settings/preferences/`
- Security: `/settings/security/`
- Backup: `/settings/backup/`
- Maintenance: `/settings/maintenance/`
- Health Monitor: `/settings/health/`

### Management Commands
```bash
# Initialize default settings
python manage.py init_settings

# Force reset all settings
python manage.py init_settings --force

# System health check
python manage.py system_health_check

# Save health record to database
python manage.py system_health_check --save
```

## API Endpoints

### System Status API
```javascript
// Get real-time system status
fetch('/settings/api/status/')
  .then(response => response.json())
  .then(data => {
    console.log('System Status:', data.overall);
    console.log('Database:', data.database);
    console.log('ML Service:', data.ml_service);
  });
```

### Notification Testing
```javascript
// Test SMS notification
fetch('/settings/test-notification/', {
  method: 'POST',
  headers: {'Content-Type': 'application/x-www-form-urlencoded'},
  body: 'type=sms'
})
.then(response => response.json())
.then(data => console.log('SMS Test:', data.success));
```

## Security Features

### Audit Logging
All settings changes are automatically logged with:
- User information
- Timestamp
- Changed fields
- IP address
- Action type

### Permission Integration
- Uses existing `@module_required` decorators
- Respects user module permissions
- Separate view/edit permissions

### Data Protection
- Sensitive fields (API keys, passwords) are properly masked
- Input validation and sanitization
- CSRF protection on all forms

## Performance Optimizations

### Caching Strategy
- Settings cached for 1 hour
- Automatic cache invalidation on updates
- ML configuration caching for performance

### Database Optimization
- Proper indexing on frequently queried fields
- Efficient queries with select_related
- Minimal database hits through caching

### Async Support
- Async views for I/O operations
- Background task integration
- Real-time status updates

## Monitoring & Alerts

### Health Metrics
- Database size and performance
- Memory and CPU usage
- ML model availability
- Response time tracking

### Automated Alerts
- System health degradation
- Failed backup operations
- ML model accuracy drops
- Resource usage thresholds

## Integration with Existing Features

### ML Models (26 Models)
- student_performance_model.pkl
- student_dropout_model.pkl
- payment_delay_model.pkl
- attendance_pattern_model.pkl
- teacher_performance_model.pkl
- And 21 more models in /models/ directory

### Fee System Integration
- Automatic fee calculation updates
- Late fee configuration sync
- Bulk discount management
- Payment reminder scheduling

### Messaging Integration
- SMS provider configuration
- WhatsApp API setup
- Email SMTP configuration
- Template customization

### Backup Integration
- Automated backup scheduling
- Retention policy management
- Health monitoring integration
- Security compliance

## Best Practices

### Configuration Management
1. Use environment variables for sensitive data
2. Regular backup of settings configuration
3. Test notification settings before deployment
4. Monitor system health regularly

### Security Guidelines
1. Rotate API keys regularly
2. Use strong SMTP passwords
3. Enable audit logging
4. Regular security reviews

### Performance Tips
1. Monitor cache hit rates
2. Optimize ML model thresholds
3. Regular database maintenance
4. Resource usage monitoring

## Troubleshooting

### Common Issues
1. **ML Models Not Loading**: Check models directory permissions
2. **Notification Failures**: Verify API credentials and network connectivity
3. **Performance Issues**: Check database size and optimize queries
4. **Cache Problems**: Clear cache and restart application

### Debug Commands
```bash
# Check system health
python manage.py system_health_check

# Test database connectivity
python manage.py dbshell

# Clear all caches
python manage.py shell -c "from django.core.cache import cache; cache.clear()"
```

## Future Enhancements

### Planned Features
- Advanced ML model management
- Multi-tenant configuration
- API rate limiting configuration
- Advanced reporting dashboard
- Integration with external monitoring tools

### Scalability Considerations
- Redis cache backend support
- PostgreSQL migration support
- Distributed ML model management
- Load balancer configuration

This enhanced settings module provides a comprehensive foundation for system configuration while maintaining full compatibility with the existing School Management System architecture.