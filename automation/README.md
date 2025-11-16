# 🎓 School Management System - Automation Tools

## 📁 Directory Structure

```
automation/
├── config/                      # Configuration files
│   ├── version.json            # Version management
│   ├── setup_config.json       # Setup status
│   ├── network_config.json     # Network settings
│   └── update_cache.json       # Update cache (auto-generated)
│
├── scripts/                     # Batch file launchers
│   ├── start.bat               # Main menu
│   ├── install_setup_tools.bat # Install dependencies
│   ├── setup_wizard.bat        # Setup wizard
│   ├── launch_server.bat       # Server launcher
│   ├── quick_actions.bat       # Quick actions menu
│   ├── diagnostics.bat         # System diagnostics
│   ├── check_updates.bat       # Update checker
│   └── factory_reset.bat       # Factory reset
│
├── setup/                       # Setup and initialization
│   ├── setup_wizard.py         # Interactive setup wizard
│   ├── diagnostics.py          # System health checks
│   └── factory_reset.py        # Reset functionality
│
├── server/                      # Server management
│   ├── launch_server.py        # Smart server launcher
│   └── network_manager.py      # Network tools
│
├── updates/                     # Update management
│   └── update_checker.py       # Update checker
│
├── tools/                       # Utility tools
│   └── quick_actions.py        # Quick actions menu
│
├── requirements_setup.txt       # Additional dependencies
└── README.md                    # This file
```

---

## 🚀 Quick Start

### From Project Root

**Step 1: Install Dependencies**
```bash
INSTALL_TOOLS.bat
```

**Step 2: Run Setup**
```bash
SETUP_WIZARD.bat
```

**Step 3: Launch Application**
```bash
LAUNCH_SERVER.bat
```

**Or use the main menu:**
```bash
START_AUTOMATION.bat
```

---

## 📚 Component Overview

### Configuration (`config/`)
- **version.json** - Current version and update settings
- **setup_config.json** - Setup completion status
- **network_config.json** - Network interface settings
- **update_cache.json** - Cached update information

### Scripts (`scripts/`)
Windows batch files for easy access to all tools.

### Setup (`setup/`)
- **setup_wizard.py** - Complete automated setup
- **diagnostics.py** - System health monitoring
- **factory_reset.py** - Safe system reset

### Server (`server/`)
- **launch_server.py** - Intelligent server launcher
- **network_manager.py** - Network detection and QR codes

### Updates (`updates/`)
- **update_checker.py** - GitHub integration and offline updates

### Tools (`tools/`)
- **quick_actions.py** - All-in-one maintenance menu

---

## 🎯 Usage

### Direct Python Execution

From project root:

```bash
# Setup wizard
python automation/setup/setup_wizard.py

# Launch server
python automation/server/launch_server.py

# System diagnostics
python automation/setup/diagnostics.py

# Quick actions
python automation/tools/quick_actions.py

# Update checker
python automation/updates/update_checker.py

# Network manager
python automation/server/network_manager.py

# Factory reset
python automation/setup/factory_reset.py
```

### Using Batch Files

From project root:

```bash
# Main menu
START_AUTOMATION.bat

# Or individual tools
SETUP_WIZARD.bat
LAUNCH_SERVER.bat
INSTALL_TOOLS.bat
```

---

## ⚙️ Configuration

### Edit Configuration Files

All configuration files are in `automation/config/`:

**version.json** - Update settings:
```json
{
  "current_version": "1.0.0",
  "github_repo": "your-org/school-management-system",
  "update_channel": "stable",
  "auto_check_updates": true,
  "check_interval_hours": 24
}
```

**network_config.json** - Network settings:
```json
{
  "default_port": 8000,
  "auto_open_browser": true,
  "allow_external_access": true
}
```

---

## 🔧 Dependencies

Install additional dependencies:

```bash
pip install -r automation/requirements_setup.txt
```

Or use the installer:
```bash
INSTALL_TOOLS.bat
```

**Required packages:**
- psutil - System monitoring
- qrcode - QR code generation
- requests - Update checking
- colorama - Colored terminal output
- tqdm - Progress bars

---

## 📖 Documentation

Complete documentation is available in `docs/automation/`:

- **START_HERE.md** - Quick start guide
- **README_NEW_FEATURES.md** - Feature overview
- **SETUP_GUIDE.md** - Detailed setup instructions
- **QUICK_REFERENCE.md** - Command reference
- **FEATURES.md** - Complete feature list
- **ARCHITECTURE.md** - Technical architecture
- **WORKFLOW.md** - Visual workflow guides
- **IMPLEMENTATION_SUMMARY.md** - Implementation details
- **NEW_FILES_INDEX.md** - File index

---

## 🐛 Troubleshooting

### Common Issues

**Import errors:**
```bash
INSTALL_TOOLS.bat
```

**Server won't start:**
```bash
python automation/setup/diagnostics.py
```

**Database errors:**
```bash
python automation/setup/factory_reset.py
# Choose "Soft Reset"
```

**Network issues:**
```bash
python automation/server/network_manager.py
```

---

## 🎓 Features

✅ **Automated Setup** - One-click installation  
✅ **Smart Server** - Auto network detection  
✅ **Health Monitoring** - System diagnostics  
✅ **Update Management** - GitHub integration  
✅ **Factory Reset** - Safe system reset  
✅ **Quick Actions** - All tools in one place  
✅ **QR Codes** - Mobile access  
✅ **Full Documentation** - Comprehensive guides  

---

## 📞 Support

For help:
1. Check `docs/automation/` for documentation
2. Run diagnostics: `python automation/setup/diagnostics.py`
3. View logs in `logs/` directory

---

**🎓 School Management System Automation**  
*Professional Setup & Management Tools*
