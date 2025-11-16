# 🎓 School Management System - Automation Guide

## 🚀 Quick Start (3 Steps)

### Step 1: Install Automation Tools
```bash
INSTALL_TOOLS.bat
```
Installs required Python packages for automation tools.

### Step 2: Run Setup Wizard
```bash
SETUP_WIZARD.bat
```
Complete automated setup of the application.

### Step 3: Launch Application
```bash
LAUNCH_SERVER.bat
```
Start the server with automatic network detection.

---

## 📁 New Folder Structure

```
School-Management-System/
│
├── automation/                          # All automation tools
│   ├── config/                         # Configuration files
│   │   ├── version.json
│   │   ├── setup_config.json
│   │   ├── network_config.json
│   │   └── update_cache.json
│   │
│   ├── scripts/                        # Batch file launchers
│   │   ├── start.bat                   # Main menu
│   │   ├── install_setup_tools.bat
│   │   ├── setup_wizard.bat
│   │   ├── launch_server.bat
│   │   ├── quick_actions.bat
│   │   ├── diagnostics.bat
│   │   ├── check_updates.bat
│   │   └── factory_reset.bat
│   │
│   ├── setup/                          # Setup tools
│   │   ├── setup_wizard.py
│   │   ├── diagnostics.py
│   │   └── factory_reset.py
│   │
│   ├── server/                         # Server management
│   │   ├── launch_server.py
│   │   └── network_manager.py
│   │
│   ├── updates/                        # Update management
│   │   └── update_checker.py
│   │
│   ├── tools/                          # Utility tools
│   │   └── quick_actions.py
│   │
│   ├── requirements_setup.txt          # Dependencies
│   └── README.md                       # Automation docs
│
├── docs/                               # Documentation
│   └── automation/                     # Automation docs
│       ├── START_HERE.md
│       ├── README_NEW_FEATURES.md
│       ├── SETUP_GUIDE.md
│       ├── QUICK_REFERENCE.md
│       ├── FEATURES.md
│       ├── ARCHITECTURE.md
│       ├── WORKFLOW.md
│       ├── IMPLEMENTATION_SUMMARY.md
│       └── NEW_FILES_INDEX.md
│
├── Root Launchers (Double-click these):
│   ├── INSTALL_TOOLS.bat               # Install dependencies
│   ├── SETUP_WIZARD.bat                # Run setup
│   ├── START_AUTOMATION.bat            # Main menu
│   ├── LAUNCH_SERVER.bat               # Quick start
│   └── AUTOMATION_GUIDE.md             # This file
│
└── [Your existing Django project files...]
```

---

## 🎯 Root Launchers (Easy Access)

These files are in the project root for easy access:

### INSTALL_TOOLS.bat
Install automation tool dependencies.
```bash
Double-click: INSTALL_TOOLS.bat
```

### SETUP_WIZARD.bat
Run the complete setup wizard.
```bash
Double-click: SETUP_WIZARD.bat
```

### START_AUTOMATION.bat
Open the main automation menu.
```bash
Double-click: START_AUTOMATION.bat
```

### LAUNCH_SERVER.bat
Quick start the server.
```bash
Double-click: LAUNCH_SERVER.bat
```

---

## 📚 Documentation Location

All automation documentation is now in:
```
docs/automation/
```

### Key Documents

**Getting Started:**
- `docs/automation/START_HERE.md` - **Start here!**
- `docs/automation/README_NEW_FEATURES.md` - Feature overview
- `docs/automation/SETUP_GUIDE.md` - Complete setup guide

**Daily Use:**
- `docs/automation/QUICK_REFERENCE.md` - Command reference
- `docs/automation/WORKFLOW.md` - Visual guides

**Complete Reference:**
- `docs/automation/FEATURES.md` - All features
- `docs/automation/ARCHITECTURE.md` - Technical details
- `docs/automation/IMPLEMENTATION_SUMMARY.md` - Implementation
- `docs/automation/NEW_FILES_INDEX.md` - File index

---

## 🔧 Direct Access to Tools

### From Project Root

**Using Batch Files:**
```bash
automation\scripts\start.bat              # Main menu
automation\scripts\setup_wizard.bat       # Setup wizard
automation\scripts\launch_server.bat      # Launch server
automation\scripts\quick_actions.bat      # Quick actions
automation\scripts\diagnostics.bat        # Diagnostics
automation\scripts\check_updates.bat      # Check updates
automation\scripts\factory_reset.bat      # Factory reset
```

**Using Python:**
```bash
python automation/setup/setup_wizard.py
python automation/server/launch_server.py
python automation/setup/diagnostics.py
python automation/tools/quick_actions.py
python automation/updates/update_checker.py
python automation/server/network_manager.py
python automation/setup/factory_reset.py
```

---

## ⚙️ Configuration Files

All configuration is in `automation/config/`:

```
automation/config/version.json          # Version & updates
automation/config/setup_config.json     # Setup status
automation/config/network_config.json   # Network settings
automation/config/update_cache.json     # Update cache
```

---

## 🎓 Usage Scenarios

### First Time Setup
```bash
1. INSTALL_TOOLS.bat
2. SETUP_WIZARD.bat
3. LAUNCH_SERVER.bat
```

### Daily Development
```bash
LAUNCH_SERVER.bat
# Or
START_AUTOMATION.bat → Quick Start
```

### Maintenance
```bash
START_AUTOMATION.bat → Quick Actions
```

### Troubleshooting
```bash
automation\scripts\diagnostics.bat
```

### Updates
```bash
automation\scripts\check_updates.bat
```

---

## 📖 Where to Find Things

### Need to...

**Install dependencies?**
→ `INSTALL_TOOLS.bat`

**Setup for first time?**
→ `SETUP_WIZARD.bat`

**Start the server?**
→ `LAUNCH_SERVER.bat`

**Access all tools?**
→ `START_AUTOMATION.bat`

**Check system health?**
→ `automation\scripts\diagnostics.bat`

**Backup database?**
→ `automation\scripts\quick_actions.bat` → Backup Database

**Reset system?**
→ `automation\scripts\factory_reset.bat`

**Check for updates?**
→ `automation\scripts\check_updates.bat`

**Generate QR codes?**
→ `python automation/server/network_manager.py --qr`

**Read documentation?**
→ `docs/automation/START_HERE.md`

---

## 🔍 File Locations

### Python Scripts
All in `automation/` subdirectories:
- Setup tools: `automation/setup/`
- Server tools: `automation/server/`
- Update tools: `automation/updates/`
- Utility tools: `automation/tools/`

### Batch Files
All in `automation/scripts/`:
- Main menu: `start.bat`
- Individual tools: `*.bat`

### Configuration
All in `automation/config/`:
- Settings: `*.json`

### Documentation
All in `docs/automation/`:
- Guides: `*.md`

---

## 💡 Pro Tips

1. **Use root launchers** for quick access
2. **Bookmark** `docs/automation/QUICK_REFERENCE.md`
3. **Run diagnostics** weekly
4. **Check updates** regularly
5. **Backup** before major changes

---

## 🆘 Quick Help

### Something not working?

**Step 1:** Run diagnostics
```bash
automation\scripts\diagnostics.bat
```

**Step 2:** Check documentation
```bash
docs\automation\START_HERE.md
```

**Step 3:** Check logs
```bash
logs\django.log
```

---

## 🎉 Benefits of New Structure

✅ **Organized** - Everything in one place  
✅ **Clean** - Separated from main project  
✅ **Easy Access** - Root launchers  
✅ **Documented** - Comprehensive guides  
✅ **Maintainable** - Clear structure  
✅ **Scalable** - Easy to extend  

---

## 📞 Need More Help?

### Documentation
- Start: `docs/automation/START_HERE.md`
- Setup: `docs/automation/SETUP_GUIDE.md`
- Reference: `docs/automation/QUICK_REFERENCE.md`
- Features: `docs/automation/FEATURES.md`

### Tools
- Diagnostics: `automation\scripts\diagnostics.bat`
- Quick Actions: `automation\scripts\quick_actions.bat`

### Automation Folder
- Overview: `automation/README.md`

---

## ✨ What's New?

### Organized Structure
- All automation tools in `automation/` folder
- All documentation in `docs/automation/` folder
- Clean separation from main project

### Easy Access
- Root launchers for common tasks
- No need to navigate deep folders
- Double-click to run

### Better Maintenance
- Clear folder structure
- Logical organization
- Easy to find files

---

**🎓 School Management System**  
*Professional Automation Tools*

**Quick Start:** `INSTALL_TOOLS.bat` → `SETUP_WIZARD.bat` → `LAUNCH_SERVER.bat`

**Documentation:** `docs/automation/START_HERE.md`

**Main Menu:** `START_AUTOMATION.bat`
