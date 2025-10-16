from django.core.management.base import BaseCommand
from django.db import transaction
from fines.models import Fine, FineStudent
from core.fee_management.services import fee_service
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Fix incorrectly applied fines by removing from wrong classes'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--fine-id',
            type=int,
            help='Fix specific fine by ID',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be fixed without making changes',
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Fix all class-specific fines with issues',
        )
    
    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🔧 Fine Application Fix Tool')
        )
        self.stdout.write('=' * 50)
        
        if options['fine_id']:
            self.fix_specific_fine(options['fine_id'], options['dry_run'])
        elif options['all']:
            self.fix_all_fines(options['dry_run'])
        else:
            self.analyze_all_fines()
    
    def fix_specific_fine(self, fine_id, dry_run=False):
        """Fix a specific fine by ID"""
        try:
            fine = Fine.objects.get(id=fine_id)
            
            self.stdout.write(f"\n📋 Analyzing Fine ID: {fine_id}")
            self.stdout.write(f"   Type: {fine.fine_type.name}")
            self.stdout.write(f"   Scope: {fine.target_scope}")
            
            if fine.target_scope != 'Class' or not fine.class_section:
                self.stdout.write(
                    self.style.WARNING(f"   ⚠️  This fine is not class-specific, skipping")
                )
                return
            
            # Verify the fine application
            verification = fee_service.verify_fine_application(fine_id)
            
            if 'error' in verification:
                self.stdout.write(
                    self.style.ERROR(f"   ❌ Error verifying: {verification['error']}")
                )
                return
            
            self.stdout.write(f"   Intended Class: {verification['intended_class']}")
            self.stdout.write(f"   Students Affected: {verification['students_affected']}")
            
            if verification['is_correct']:
                self.stdout.write(
                    self.style.SUCCESS(f"   ✅ Fine application is correct")
                )
                return
            
            # Show issues
            self.stdout.write(
                self.style.ERROR(f"   🚨 Issues Found:")
            )
            for issue in verification['issues_found']:
                self.stdout.write(f"      - {issue}")
            
            # Show class breakdown
            self.stdout.write(f"   📊 Class Distribution:")
            for class_name, count in verification['class_breakdown'].items():
                status = "✅" if class_name == verification['intended_class'] else "❌"
                self.stdout.write(f"      {status} {class_name}: {count} students")
            
            if dry_run:
                self.stdout.write(
                    self.style.WARNING(f"   🔍 DRY RUN: Would fix this fine")
                )
                return
            
            # Fix the fine
            result = fee_service.fix_incorrect_fine_application(fine_id)
            
            if result['success']:
                self.stdout.write(
                    self.style.SUCCESS(f"   ✅ Fixed: {result['message']}")
                )
            else:
                self.stdout.write(
                    self.style.ERROR(f"   ❌ Fix failed: {result['error']}")
                )
                
        except Fine.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f"❌ Fine with ID {fine_id} not found")
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"❌ Error fixing fine {fine_id}: {str(e)}")
            )
    
    def fix_all_fines(self, dry_run=False):
        """Fix all class-specific fines with issues"""
        self.stdout.write(f"\n🔧 Fixing All Class-Specific Fines")
        self.stdout.write('=' * 40)
        
        class_fines = Fine.objects.filter(
            target_scope='Class',
            class_section__isnull=False
        )
        
        if not class_fines.exists():
            self.stdout.write(
                self.style.WARNING("⚠️  No class-specific fines found")
            )
            return
        
        fixed_count = 0
        error_count = 0
        
        for fine in class_fines:
            try:
                verification = fee_service.verify_fine_application(fine.id)
                
                if 'error' in verification:
                    self.stdout.write(
                        self.style.ERROR(f"❌ Error verifying fine {fine.id}: {verification['error']}")
                    )
                    error_count += 1
                    continue
                
                if verification['is_correct']:
                    continue  # Skip correct fines
                
                self.stdout.write(f"\n🔧 Fixing Fine ID: {fine.id}")
                self.stdout.write(f"   Type: {fine.fine_type.name}")
                self.stdout.write(f"   Intended: {verification['intended_class']}")
                
                if dry_run:
                    self.stdout.write(
                        self.style.WARNING(f"   🔍 DRY RUN: Would fix this fine")
                    )
                    continue
                
                result = fee_service.fix_incorrect_fine_application(fine.id)
                
                if result['success']:
                    self.stdout.write(
                        self.style.SUCCESS(f"   ✅ {result['message']}")
                    )
                    fixed_count += 1
                else:
                    self.stdout.write(
                        self.style.ERROR(f"   ❌ {result['error']}")
                    )
                    error_count += 1
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"❌ Error processing fine {fine.id}: {str(e)}")
                )
                error_count += 1
        
        # Summary
        self.stdout.write(f"\n📊 SUMMARY")
        self.stdout.write(f"   Total Class Fines: {class_fines.count()}")
        self.stdout.write(f"   Fixed: {fixed_count}")
        self.stdout.write(f"   Errors: {error_count}")
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(f"   🔍 This was a dry run - no changes made")
            )
    
    def analyze_all_fines(self):
        """Analyze all fines and show issues"""
        self.stdout.write(f"\n🔍 Analyzing All Fines")
        self.stdout.write('=' * 30)
        
        fines = Fine.objects.all().order_by('-applied_date')
        
        if not fines.exists():
            self.stdout.write(
                self.style.WARNING("⚠️  No fines found in the system")
            )
            return
        
        issues_found = 0
        
        for fine in fines:
            self.stdout.write(f"\n📋 Fine ID: {fine.id}")
            self.stdout.write(f"   Type: {fine.fine_type.name}")
            self.stdout.write(f"   Scope: {fine.target_scope}")
            self.stdout.write(f"   Amount: ₹{fine.amount}")
            
            if fine.target_scope == 'Class' and fine.class_section:
                verification = fee_service.verify_fine_application(fine.id)
                
                if 'error' in verification:
                    self.stdout.write(
                        self.style.ERROR(f"   ❌ Error: {verification['error']}")
                    )
                    continue
                
                self.stdout.write(f"   Intended: {verification['intended_class']}")
                self.stdout.write(f"   Students: {verification['students_affected']}")
                
                if verification['is_correct']:
                    self.stdout.write(
                        self.style.SUCCESS(f"   ✅ Correct")
                    )
                else:
                    issues_found += 1
                    self.stdout.write(
                        self.style.ERROR(f"   🚨 Issues Found:")
                    )
                    for issue in verification['issues_found']:
                        self.stdout.write(f"      - {issue}")
            
            elif fine.target_scope == 'All':
                fine_students = FineStudent.objects.filter(fine=fine)
                self.stdout.write(f"   Students: {fine_students.count()}")
                self.stdout.write(
                    self.style.SUCCESS(f"   ✅ All Students Fine")
                )
        
        # Summary
        self.stdout.write(f"\n📊 ANALYSIS SUMMARY")
        self.stdout.write(f"   Total Fines: {fines.count()}")
        self.stdout.write(f"   Issues Found: {issues_found}")
        
        if issues_found > 0:
            self.stdout.write(f"\n🔧 TO FIX ISSUES:")
            self.stdout.write(f"   Run: python manage.py fix_fine_applications --all")
            self.stdout.write(f"   Or: python manage.py fix_fine_applications --fine-id <ID>")
            self.stdout.write(f"   Add --dry-run to see what would be changed")