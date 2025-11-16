# 🎓 School Management System - Quick Reference Card

## 🚀 Quick Commands

### First Time Setup
```bash
setup_wizard.bat              # Complete setup wizard
```

### Daily Use
```bash
start.bat                     # Main menu
launch_server.bat             # Start server
quick_actions.bat             # Quick actions menu
```

### Maintenance
```bash
diagnostics.bat               # System health check
check_updates.bat             # Check for updates
```

### Emergency
```bash
factory_reset.bat             # Reset system
```

---

## 📋 Main Menu (start.bat)

```
1. Quick Start (Launch Server)
2. Setup Wizard (First Time)
3. Quick Actions Menu
4. System Diagnostics
5. Check for Updates
6. Network Manager
7. Factory Reset
8. Exit
```

---

## ⚡ Quick Actions Menu

```
Server Management:
  1. Start Server
  2. Stop Server
  3. Network Manager

Database:
  4. Backup Database
  5. Run Migrations
  6. Create Superuser

Maintenance:
  7. Clear Cache
  8. Collect Static Files
  9. View Logs

System:
  10. Run Diagnostics
  11. Check Updates
  12. Factory Reset
```

---

## 🌐 Access URLs

```
Local:     http://127.0.0.1:8000/
Network:   http://[your-ip]:8000/
```

---

## 📁 Important Directories

```
config/          Configuration files
backups/         Database backups
logs/            Application logs
qr_codes/        QR codes for mobile
setup/           Setup scripts
server/          Server management
updates/         Update management
tools/           Utility tools
```

---

## 🔧 Configuration Files

```
config/version.json          Version & updates
config/setup_config.json     Setup status
config/network_config.json   Network settings
config/update_cache.json     Update cache
```

---

## 📊 Log Files

```
logs/django.log              Application logs
logs/diagnostics_*.json      Diagnostic reports
logs/backup.log              Backup operations
logs/backup_security.log     Security events
```

---

## 🐛 Troubleshooting

### Server Won't Start
```bash
1. diagnostics.bat
2. Check port 8000
3. Check logs/django.log
```

### Database Errors
```bash
1. Backup database
2. factory_reset.bat → Soft Reset
3. Or: python manage.py migrate
```

### Import Errors
```bash
1. Activate venv
2. pip install -r requirements.txt
```

### Network Issues
```bash
1. python server/network_manager.py
2. Check firewall
3. Verify network adapter
```

---

## 🔄 Reset Types

### Soft Reset
- Delete database & migrations
- Keep media & config

### Standard Reset
- Delete database & migrations
- Delete cache & static
- Keep media
- Reset config

### Complete Reset
- Delete everything except venv
- Full fresh installation

---

## 📱 Mobile Access

```bash
1. launch_server.bat
2. python server/network_manager.py --qr
3. Scan QR code
4. Access from mobile
```

---

## 🔒 Backup Locations

```
backups/                     Manual backups
backups/factory_reset_*/     Reset backups
```

---

## ⚙️ Python Commands

### Setup
```bash
python setup/setup_wizard.py
python setup/diagnostics.py
python setup/factory_reset.py
```

### Server
```bash
python server/launch_server.py
python server/launch_server.py --port 8080
python server/launch_server.py --no-browser
python server/network_manager.py
python server/network_manager.py --qr
python server/network_manager.py --monitor
```

### Updates
```bash
python updates/update_checker.py
python updates/update_checker.py --check
python updates/update_checker.py --check --force
```

### Tools
```bash
python tools/quick_actions.py
```

### Django
```bash
python manage.py runserver
python manage.py migrate
python manage.py createsuperuser
python manage.py collectstatic
python manage.py check
```

---

## 🎯 Common Tasks

### Create Admin
```bash
quick_actions.bat → 6. Create Superuser
# Or
python manage.py createsuperuser
```

### Backup Database
```bash
quick_actions.bat → 4. Backup Database
```

### View Logs
```bash
quick_actions.bat → 9. View Logs
# Or
type logs\django.log
```

### Clear Cache
```bash
quick_actions.bat → 7. Clear Cache
```

### Run Migrations
```bash
quick_actions.bat → 5. Run Migrations
# Or
python manage.py makemigrations
python manage.py migrate
```

---

## 📈 Health Indicators

```
Score 80-100:  🟢 Excellent
Score 60-79:   🟡 Good
Score 0-59:    🔴 Needs Attention
```

---

## 🌐 Network Icons

```
🖥️  Localhost
📶 Wi-Fi
🔌 Ethernet
📱 Mobile Hotspot
🌐 Local Network
```

---

## ✅ Status Indicators

```
✓ Success
✗ Error
⚠ Warning
ℹ Information
🔄 In Progress
```

---

## 🔑 Keyboard Shortcuts

```
Ctrl+C         Stop server
Enter          Continue/Confirm
q              Quit (in menus)
```

---

## 📞 Quick Help

### Check System Health
```bash
diagnostics.bat
```

### Check Version
```bash
check_updates.bat
```

### View All Networks
```bash
python server/network_manager.py
```

### Emergency Reset
```bash
factory_reset.bat
```

---

## 🎓 Learning Path

### Day 1: Setup
```
1. setup_wizard.bat
2. Create admin account
3. launch_server.bat
4. Access application
```

### Day 2: Explore
```
1. quick_actions.bat
2. Try different features
3. Check diagnostics
4. View logs
```

### Day 3: Customize
```
1. Configure settings
2. Setup network access
3. Generate QR codes
4. Test mobile access
```

### Week 1: Maintain
```
1. Regular backups
2. Check updates
3. Monitor health
4. Review logs
```

---

## 💡 Pro Tips

1. **Always backup before major changes**
2. **Run diagnostics weekly**
3. **Check updates regularly**
4. **Use quick actions for common tasks**
5. **Monitor logs for issues**
6. **Keep virtual environment active**
7. **Use soft reset for database issues**
8. **Generate QR codes for mobile testing**
9. **Configure GitHub repo for updates**
10. **Read logs when troubleshooting**

---

## 🆘 Emergency Contacts

### System Issues
1. Run diagnostics
2. Check logs
3. Try soft reset

### Data Loss
1. Check backups/
2. Restore from backup
3. Re-run setup if needed

### Network Issues
1. Check firewall
2. Verify IP address
3. Use network manager

---

## 📚 Documentation

- `SETUP_GUIDE.md` - Complete setup guide
- `FEATURES.md` - Feature documentation
- `QUICK_REFERENCE.md` - This file
- `README.md` - Project overview

---

## 🔗 Useful Links

```
Local Admin:   http://127.0.0.1:8000/admin/
Local App:     http://127.0.0.1:8000/
```

---

**🎓 School Management System**  
*Quick Reference v1.0*

---

**Print this page for quick access!**
