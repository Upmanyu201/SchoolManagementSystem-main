#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Validate All ImpScripts for Syntax and Logic Errors"""

import os
import sys
import ast
import py_compile
from pathlib import Path

def validate_syntax(filepath):
    """Validate Python syntax"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            code = f.read()
        ast.parse(code)
        py_compile.compile(filepath, doraise=True)
        return True, "OK"
    except SyntaxError as e:
        return False, f"Syntax Error: Line {e.lineno}: {e.msg}"
    except Exception as e:
        return False, f"Error: {str(e)}"

def check_required_patterns(filepath):
    """Check for required patterns"""
    issues = []
    warnings = []
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        lines = content.split('\n')
    
    # Check UTF-8 encoding declaration (first 3 lines)
    has_utf8 = any('# -*- coding: utf-8 -*-' in line for line in lines[0:3])
    if not has_utf8:
        issues.append("Missing UTF-8 encoding declaration")
    
    # Check for os.chdir in __main__ block
    if '__main__' in content:
        if 'os.chdir(Path(__file__).parent.parent)' not in content:
            issues.append("Missing os.chdir() in __main__ block")
    
    # Check subprocess encoding and errors parameter
    if 'subprocess.run' in content:
        if "encoding='utf-8'" not in content:
            issues.append("subprocess.run missing encoding='utf-8'")
        if "errors='replace'" not in content:
            warnings.append("subprocess.run missing errors='replace'")
    
    # Check for timeout in subprocess calls
    if 'subprocess.run' in content:
        if 'timeout=' not in content:
            warnings.append("subprocess.run missing timeout parameter")
    
    # Check for pause before exit
    if '__main__' in content:
        if 'input(' not in content or 'Press Enter' not in content:
            issues.append("Missing pause before exit")
    
    # Check for working directory display
    if 'def main(' in content:
        if 'os.getcwd()' not in content and 'Working Directory' not in content:
            warnings.append("Missing working directory display")
    
    # Check for helper function (if uses venv)
    if 'venv' in content and 'Scripts' in content:
        if 'def get_venv_python()' not in content:
            warnings.append("Missing get_venv_python() helper function")
    
    # Combine issues and warnings
    all_issues = issues + [f"Warning: {w}" for w in warnings]
    return all_issues

def main():
    """Validate all scripts"""
    from datetime import datetime
    print("=" * 70)
    print("  VALIDATING ALL IMPSCRIPTS")
    print("=" * 70)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Working Directory: {os.getcwd()}")
    
    scripts_dir = Path(__file__).parent
    scripts = [
        'check_system.py',
        'install_python.py',
        'setup_environment.py',
        'database_setup.py',
        'run_tests.py',
        'comprehensive_health_check.py',
        'enhanced_start_server.py',
        'quick_setup.py'
    ]
    
    all_valid = True
    results = []
    
    for script in scripts:
        filepath = scripts_dir / script
        
        if not filepath.exists():
            results.append((script, False, "File not found"))
            all_valid = False
            continue
        
        # Syntax validation
        valid, msg = validate_syntax(filepath)
        
        if not valid:
            results.append((script, False, msg))
            all_valid = False
            continue
        
        # Pattern checks
        issues = check_required_patterns(filepath)
        
        if issues:
            results.append((script, False, "; ".join(issues)))
            all_valid = False
        else:
            results.append((script, True, "All checks passed"))
    
    # Print results
    print("\nVALIDATION RESULTS:")
    print("-" * 70)
    
    passed = 0
    failed = 0
    warnings = 0
    
    for script, valid, msg in results:
        status = "✅" if valid else "❌"
        print(f"{status} {script:35} {msg}")
        
        if valid:
            passed += 1
        else:
            if 'Warning:' in msg:
                warnings += 1
            else:
                failed += 1
    
    print("=" * 70)
    print(f"\n📊 Summary: {passed} passed, {failed} failed, {warnings} warnings")
    
    if all_valid:
        print("🎉 ALL SCRIPTS VALIDATED SUCCESSFULLY!")
        return 0
    else:
        print("❌ SOME SCRIPTS HAVE ISSUES - SEE ABOVE")
        print("\n💡 Tip: Run individual scripts to see detailed error messages")
        return 1

if __name__ == "__main__":
    try:
        exit_code = main()
        input("\nPress Enter to continue...")
        sys.exit(exit_code)
    except Exception as e:
        print(f"\n❌ Validation error: {e}")
        input("\nPress Enter to continue...")
        sys.exit(1)
