# 🎓 School Management System - Architecture Overview

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    School Management System                      │
│                         Main Entry Point                         │
│                          start.bat                               │
└────────────────────────┬────────────────────────────────────────┘
                         │
         ┌───────────────┼───────────────┐
         │               │               │
         ▼               ▼               ▼
┌────────────────┐ ┌────────────┐ ┌──────────────┐
│  Setup System  │ │   Server   │ │    Tools     │
│                │ │ Management │ │  & Utilities │
└────────────────┘ └────────────┘ └──────────────┘
```

---

## 📦 Component Architecture

### 1. Setup System

```
setup/
├── setup_wizard.py          ← Main Setup Orchestrator
│   ├── System Check
│   ├── Dependencies
│   ├── Database Init
│   ├── Tailwind CSS
│   ├── Admin Creation
│   ├── Network Config
│   └── System Test
│
├── diagnostics.py           ← Health Monitoring
│   ├── Python Check
│   ├── Resource Monitor
│   ├── Network Test
│   ├── Port Check
│   ├── Django Verify
│   ├── Database Check
│   └── Health Score
│
└── factory_reset.py         ← Reset Manager
    ├── Soft Reset
    ├── Standard Reset
    ├── Complete Reset
    ├── Backup Creator
    └── Restore Helper
```

### 2. Server Management

```
server/
├── launch_server.py         ← Server Orchestrator
│   ├── Port Manager
│   ├── Network Detector
│   ├── Browser Launcher
│   ├── Process Manager
│   └── Monitor Thread
│
└── network_manager.py       ← Network Tools
    ├── Interface Scanner
    ├── QR Generator
    ├── Change Monitor
    └── Status Display
```

### 3. Update System

```
updates/
└── update_checker.py        ← Update Manager
    ├── GitHub API
    ├── Version Parser
    ├── Cache Manager
    ├── Changelog Viewer
    └── Download Helper
```

### 4. Tools & Utilities

```
tools/
└── quick_actions.py         ← Action Dispatcher
    ├── Server Control
    ├── Database Tools
    ├── Maintenance
    └── System Tools
```

---

## 🔄 Data Flow

### Setup Flow

```
User
  │
  ├─► setup_wizard.bat
  │     │
  │     ├─► Check System Requirements
  │     │     └─► diagnostics.py
  │     │
  │     ├─► Install Dependencies
  │     │     └─► pip install
  │     │
  │     ├─► Initialize Database
  │     │     └─► Django migrations
  │     │
  │     ├─► Compile Tailwind
  │     │     └─► npm build
  │     │
  │     ├─► Create Admin
  │     │     └─► Django createsuperuser
  │     │
  │     ├─► Configure Network
  │     │     └─► network_manager.py
  │     │
  │     └─► Test System
  │           └─► Django check
  │
  └─► Configuration Saved
        └─► config/setup_config.json
```

### Server Launch Flow

```
User
  │
  ├─► launch_server.bat
  │     │
  │     ├─► Check Port Availability
  │     │     └─► Find alternative if needed
  │     │
  │     ├─► Detect Networks
  │     │     ├─► Wi-Fi
  │     │     ├─► Ethernet
  │     │     └─► Hotspot
  │     │
  │     ├─► Start Django Server
  │     │     └─► python manage.py runserver
  │     │
  │     ├─► Monitor Output
  │     │     └─► Wait for "Starting development server"
  │     │
  │     └─► Open Browser
  │           └─► webbrowser.open()
  │
  └─► Server Running
        ├─► Display URLs
        └─► Save PID
```

### Update Check Flow

```
User
  │
  ├─► check_updates.bat
  │     │
  │     ├─► Load Current Version
  │     │     └─► config/version.json
  │     │
  │     ├─► Check Update Source
  │     │     ├─► Online: GitHub API
  │     │     └─► Offline: Local cache
  │     │
  │     ├─► Compare Versions
  │     │     └─► Semantic version parsing
  │     │
  │     ├─► Display Results
  │     │     ├─► Current version
  │     │     ├─► Latest version
  │     │     └─► Changelog
  │     │
  │     └─► Save Cache
  │           └─► config/update_cache.json
  │
  └─► User Action
        ├─► Download
        ├─► Skip
        └─► Configure
```

---

## 🗄️ Configuration Architecture

```
config/
├── version.json             ← Version Management
│   ├── current_version
│   ├── github_repo
│   ├── update_channel
│   └── auto_check_updates
│
├── setup_config.json        ← Setup Status
│   ├── first_run
│   ├── setup_completed
│   ├── database_initialized
│   ├── admin_created
│   └── network_configured
│
├── network_config.json      ← Network Settings
│   ├── default_port
│   ├── auto_open_browser
│   ├── detected_networks
│   └── preferred_network
│
└── update_cache.json        ← Update Cache
    ├── last_check
    ├── latest_version
    └── releases[]
```

---

## 🔌 Integration Points

### Django Integration

```
School Management System (Django)
         │
         ├─► manage.py
         │     ├─► runserver    ← launch_server.py
         │     ├─► migrate      ← setup_wizard.py
         │     ├─► check        ← diagnostics.py
         │     └─► collectstatic
         │
         ├─► settings.py
         │     ├─► DATABASES
         │     ├─► STATIC_ROOT
         │     └─► ALLOWED_HOSTS
         │
         └─► db.sqlite3
               └─► Backup system
```

### External Dependencies

```
System Dependencies
├── Python 3.8+
│   ├─► Virtual Environment
│   └─► pip packages
│
├── Node.js (Optional)
│   ├─► npm
│   └─► Tailwind CSS
│
└── System Tools
    ├─► ipconfig (Windows)
    ├─► socket
    └─► subprocess
```

---

## 🔐 Security Architecture

```
Security Layers
├── Configuration Validation
│   ├─► Settings verification
│   └─► Port validation
│
├── Backup System
│   ├─► Automatic backups
│   ├─► Timestamped storage
│   └─► Restore capability
│
├── Confirmation Prompts
│   ├─► Destructive operations
│   └─► Factory reset
│
└── Error Handling
    ├─► Graceful failures
    ├─► Error recovery
    └─► Rollback support
```

---

## 📊 Monitoring Architecture

```
Monitoring System
├── System Health
│   ├─► CPU Usage
│   ├─► RAM Usage
│   ├─► Disk Space
│   └─► Health Score
│
├── Network Status
│   ├─► Interface Detection
│   ├─► Connection Status
│   └─► Change Monitoring
│
├── Application Logs
│   ├─► django.log
│   ├─► diagnostics_*.json
│   └─► backup.log
│
└── Process Management
    ├─► PID tracking
    ├─► Status monitoring
    └─► Graceful shutdown
```

---

## 🎯 User Interface Architecture

```
User Interfaces
├── Batch Files (Windows)
│   ├─► start.bat
│   ├─► setup_wizard.bat
│   ├─► launch_server.bat
│   ├─► quick_actions.bat
│   ├─► diagnostics.bat
│   ├─► check_updates.bat
│   └─► factory_reset.bat
│
├── Interactive Menus
│   ├─► Main Menu
│   ├─► Quick Actions
│   ├─► Network Manager
│   └─► Update Manager
│
└── Command Line
    ├─► Python scripts
    ├─► Django commands
    └─► Direct execution
```

---

## 🔄 Process Architecture

### Background Processes

```
Process Management
├── Server Process
│   ├─► Django runserver
│   ├─► PID: server.pid
│   └─► Monitor thread
│
├── Network Monitor
│   ├─► Interface scanner
│   ├─► Change detector
│   └─► Alert system
│
└── Update Checker
    ├─► Scheduled checks
    ├─► Cache updates
    └─► Notification system
```

---

## 📁 File System Architecture

```
Project Root
├── setup/                   ← Setup scripts
├── server/                  ← Server management
├── updates/                 ← Update system
├── tools/                   ← Utilities
├── config/                  ← Configuration
├── backups/                 ← Automatic backups
├── logs/                    ← Application logs
├── qr_codes/                ← Generated QR codes
├── venv/                    ← Virtual environment
├── static/                  ← Static files
├── media/                   ← Media files
├── *.bat                    ← Batch shortcuts
└── *.md                     ← Documentation
```

---

## 🌐 Network Architecture

```
Network Topology
├── Localhost (127.0.0.1)
│   └─► Local development
│
├── Wi-Fi Network
│   ├─► Local network access
│   └─► Multiple devices
│
├── Ethernet
│   ├─► Wired connection
│   └─► Stable access
│
└── Mobile Hotspot
    ├─► Mobile devices
    └─► QR code access
```

---

## 🔧 Dependency Architecture

```
Dependencies
├── Core (Required)
│   ├─► Django 5.0+
│   ├─► Python 3.8+
│   └─► SQLite
│
├── Setup Tools
│   ├─► colorama
│   ├─► psutil
│   └─► requests
│
├── Optional
│   ├─► qrcode
│   ├─► Node.js
│   └─► npm
│
└── System
    ├─► Windows 10/11
    └─► Command Prompt
```

---

## 🎨 Module Interaction

```
Module Interactions
┌──────────────┐
│ setup_wizard │
└──────┬───────┘
       │
       ├──► diagnostics
       ├──► network_manager
       └──► Django commands
              │
              ├──► makemigrations
              ├──► migrate
              ├──► createsuperuser
              └──► collectstatic

┌──────────────┐
│launch_server │
└──────┬───────┘
       │
       ├──► network_manager
       ├──► Process manager
       └──► Browser launcher

┌──────────────┐
│quick_actions │
└──────┬───────┘
       │
       ├──► launch_server
       ├──► diagnostics
       ├──► update_checker
       ├──► factory_reset
       └──► Django commands
```

---

## 📈 Scalability Architecture

```
Scalability Considerations
├── Modular Design
│   ├─► Independent components
│   ├─► Loose coupling
│   └─► Easy extension
│
├── Configuration-Driven
│   ├─► JSON configs
│   ├─► Environment variables
│   └─► Dynamic settings
│
├── Plugin-Ready
│   ├─► Hook system
│   ├─► Event handlers
│   └─► Custom actions
│
└── Future-Proof
    ├─► Version management
    ├─► Update system
    └─► Migration support
```

---

## 🔄 State Management

```
Application State
├── Setup State
│   └─► config/setup_config.json
│
├── Server State
│   └─► server.pid
│
├── Network State
│   └─► config/network_config.json
│
├── Update State
│   └─► config/update_cache.json
│
└── Application State
    └─► Django database
```

---

## 🎯 Execution Flow

```
Typical User Journey
1. First Time
   └─► setup_wizard.bat
       └─► Complete setup
           └─► launch_server.bat
               └─► Access application

2. Daily Use
   └─► start.bat
       └─► Quick Start
           └─► Server running
               └─► Work on application

3. Maintenance
   └─► quick_actions.bat
       └─► Select action
           └─► Execute task
               └─► Return to menu

4. Troubleshooting
   └─► diagnostics.bat
       └─► View health report
           └─► Fix issues
               └─► Verify with diagnostics
```

---

**🎓 School Management System**  
*Architecture Documentation v1.0*
