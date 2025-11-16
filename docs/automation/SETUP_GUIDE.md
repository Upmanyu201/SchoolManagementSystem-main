# 🎓 School Management System - Complete Setup Guide

## 🚀 Quick Start

### First Time Setup
```bash
# Run the setup wizard
setup_wizard.bat
```

The setup wizard will:
- ✅ Check system requirements
- ✅ Install Python dependencies
- ✅ Initialize database
- ✅ Compile Tailwind CSS
- ✅ Create admin account
- ✅ Configure network settings
- ✅ Run system tests

### Launch Application
```bash
# Start the server with auto-browser opening
launch_server.bat

# Or use quick actions menu
quick_actions.bat
```

---

## 📋 Available Tools

### 1. Setup Wizard (`setup_wizard.bat`)
**First-run setup wizard for complete system initialization**

Features:
- Interactive step-by-step setup
- System requirements validation
- Automatic dependency installation
- Database initialization with migrations
- Tailwind CSS compilation
- Admin account creation
- Network configuration
- Final system health check

Usage:
```bash
setup_wizard.bat
```

Or directly:
```bash
python setup/setup_wizard.py
```

---

### 2. Quick Actions Menu (`quick_actions.bat`)
**One-stop menu for all common tasks**

Available Actions:
- 🚀 Start/Stop Server
- 🌐 Network Manager
- 💾 Backup Database
- 🗄️  Run Migrations
- 👤 Create Superuser
- 🧹 Clear Cache
- 📦 Collect Static Files
- 📋 View Logs
- 🔍 Run Diagnostics
- 🔄 Check Updates
- 🔄 Factory Reset

Usage:
```bash
quick_actions.bat
```

---

### 3. Server Launcher (`launch_server.bat`)
**Smart server launcher with network detection**

Features:
- Automatic port detection and conflict resolution
- Multi-network interface detection (Wi-Fi, Ethernet, Hotspot)
- Auto-open browser when server is ready
- Background process management
- Real-time server monitoring
- Network configuration saving

Usage:
```bash
# Standard launch
launch_server.bat

# With options
python server/launch_server.py --port 8080 --no-browser
```

Access URLs:
- Local: `http://127.0.0.1:8000/`
- Network: `http://[your-ip]:8000/`

---

### 4. Network Manager (`server/network_manager.py`)
**Network monitoring and QR code generation**

Features:
- Real-time network interface detection
- QR code generation for mobile access
- Network change monitoring
- Multiple IP address display
- Connection status tracking

Usage:
```bash
python server/network_manager.py

# Generate QR codes
python server/network_manager.py --qr

# Monitor networks
python server/network_manager.py --monitor
```

---

### 5. System Diagnostics (`diagnostics.bat`)
**Comprehensive system health check**

Checks:
- Python version compatibility
- System resources (CPU, RAM, Disk)
- Network connectivity
- Port availability
- Django installation
- Database status
- Static files
- Virtual environment
- Node.js/npm (for Tailwind)

Usage:
```bash
diagnostics.bat
```

Generates:
- Health score (0-100)
- Detailed diagnostic report
- JSON report in `logs/diagnostics_*.json`

---

### 6. Update Checker (`check_updates.bat`)
**Offline-capable update management**

Features:
- GitHub releases integration
- Offline update caching
- Version comparison
- Changelog viewing
- Manual update file import
- Configurable check intervals
- Stable/Beta channel selection

Usage:
```bash
# Interactive menu
check_updates.bat

# Quick check
python updates/update_checker.py --check

# Force check
python updates/update_checker.py --check --force

# Import update file
python updates/update_checker.py --import path/to/update.json
```

Configuration:
- Edit `config/version.json` to set GitHub repository
- Set check interval and auto-update preferences

---

### 7. Factory Reset (`factory_reset.bat`)
**Reset application to fresh state**

Reset Types:

**Soft Reset:**
- Delete database and migrations
- Preserve media files
- Keep configuration

**Standard Reset:**
- Delete database and migrations
- Delete static files and cache
- Preserve media files
- Reset configuration

**Complete Reset:**
- Delete everything except venv
- Delete media files
- Delete logs
- Full fresh installation

Usage:
```bash
factory_reset.bat
```

⚠️ **Warning:** Always creates backup before reset!

---

## 📁 Directory Structure

```
School-Management-System/
├── setup/                      # Setup and initialization
│   ├── setup_wizard.py        # Main setup wizard
│   ├── diagnostics.py         # System diagnostics
│   └── factory_reset.py       # Factory reset tool
│
├── server/                     # Server management
│   ├── launch_server.py       # Smart server launcher
│   └── network_manager.py     # Network tools
│
├── updates/                    # Update management
│   ├── update_checker.py      # Update checker
│   └── latest_release.json    # Cached release info
│
├── tools/                      # Utility tools
│   └── quick_actions.py       # Quick actions menu
│
├── config/                     # Configuration files
│   ├── version.json           # Version information
│   ├── setup_config.json      # Setup status
│   ├── network_config.json    # Network settings
│   └── update_cache.json      # Update cache
│
├── backups/                    # Automatic backups
├── logs/                       # Application logs
├── qr_codes/                   # Generated QR codes
│
└── Batch Files:
    ├── setup_wizard.bat       # Run setup wizard
    ├── quick_actions.bat      # Quick actions menu
    ├── launch_server.bat      # Start server
    ├── diagnostics.bat        # Run diagnostics
    ├── check_updates.bat      # Check updates
    └── factory_reset.bat      # Factory reset
```

---

## 🔧 Configuration Files

### version.json
```json
{
  "current_version": "1.0.0",
  "github_repo": "your-org/school-management-system",
  "update_channel": "stable",
  "auto_check_updates": true,
  "check_interval_hours": 24
}
```

### setup_config.json
```json
{
  "first_run": true,
  "setup_completed": false,
  "database_initialized": false,
  "admin_created": false,
  "network_configured": false,
  "tailwind_compiled": false
}
```

### network_config.json
```json
{
  "default_port": 8000,
  "auto_open_browser": true,
  "detected_networks": [],
  "preferred_network": null,
  "allow_external_access": true
}
```

---

## 🎯 Common Workflows

### First Time Installation
```bash
1. setup_wizard.bat          # Complete setup
2. launch_server.bat         # Start server
3. Access http://127.0.0.1:8000/
```

### Daily Development
```bash
1. launch_server.bat         # Start server
2. Work on your code
3. Ctrl+C to stop server
```

### Troubleshooting
```bash
1. diagnostics.bat           # Check system health
2. quick_actions.bat         # Access maintenance tools
3. View logs or clear cache
```

### Database Issues
```bash
1. quick_actions.bat
2. Select "Backup Database"
3. Select "Run Migrations"
4. Or use factory_reset.bat for clean slate
```

### Network Setup for Mobile Access
```bash
1. launch_server.bat         # Start server
2. python server/network_manager.py --qr
3. Scan QR code with mobile device
```

### Update Application
```bash
1. check_updates.bat         # Check for updates
2. View changelog
3. Download and apply update
```

---

## 🔒 Security Features

- Automatic backup before destructive operations
- Configuration validation
- Port conflict detection
- Network security checks
- Session management
- Secure update verification

---

## 🐛 Troubleshooting

### Server Won't Start
```bash
1. diagnostics.bat           # Check system
2. Check port 8000 availability
3. Verify virtual environment
4. Check logs in logs/django.log
```

### Database Errors
```bash
1. Backup database first
2. factory_reset.bat → Soft Reset
3. Or manually: python manage.py migrate
```

### Import Errors
```bash
1. Activate virtual environment
2. pip install -r requirements.txt
3. Or run setup_wizard.bat again
```

### Network Not Detected
```bash
1. Check firewall settings
2. Verify network adapter is enabled
3. Run: python server/network_manager.py
```

---

## 📊 System Requirements

**Minimum:**
- Python 3.8+
- 2 GB RAM
- 1 GB free disk space
- Windows 10/11

**Recommended:**
- Python 3.10+
- 4 GB RAM
- 5 GB free disk space
- Node.js 16+ (for Tailwind CSS)

---

## 🆘 Getting Help

### Check Logs
```bash
# View recent logs
quick_actions.bat → View Logs

# Or directly
type logs\django.log
```

### Run Diagnostics
```bash
diagnostics.bat
```

### System Health
```bash
python setup/diagnostics.py
```

---

## 📝 Additional Notes

### Virtual Environment
All scripts automatically detect and use the virtual environment if available.

### Backups
Automatic backups are created in `backups/` directory before:
- Factory reset
- Database recreation
- Major configuration changes

### Logs
All operations are logged to `logs/` directory:
- `django.log` - Application logs
- `diagnostics_*.json` - Diagnostic reports

### QR Codes
Generated QR codes for mobile access are saved in `qr_codes/` directory.

---

## 🎉 Success Indicators

✅ Setup completed successfully
✅ Server starts without errors
✅ Browser opens automatically
✅ Network interfaces detected
✅ Database migrations applied
✅ Static files collected
✅ Health score > 80%

---

## 🔄 Update Process

1. Check for updates: `check_updates.bat`
2. View changelog
3. Backup current installation
4. Download update
5. Apply update
6. Run migrations if needed
7. Test application

---

**🎓 School Management System**  
*Simplified setup, powerful management*
