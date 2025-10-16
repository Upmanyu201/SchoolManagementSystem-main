from django.core.management.base import BaseCommand
from django.core.cache import cache
from django.db import connection
from django.conf import settings
import os


class Command(BaseCommand):
    help = 'Optimize the school management system for better performance'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear-cache',
            action='store_true',
            help='Clear all caches',
        )
        parser.add_argument(
            '--warm-cache',
            action='store_true',
            help='Warm up caches with common data',
        )
        parser.add_argument(
            '--optimize-db',
            action='store_true',
            help='Optimize database indexes and queries',
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Run all optimizations',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🚀 Starting School Management System Optimization...')
        )

        if options['all']:
            options['clear_cache'] = True
            options['warm_cache'] = True
            options['optimize_db'] = True

        if options['clear_cache']:
            self.clear_caches()

        if options['optimize_db']:
            self.optimize_database()

        if options['warm_cache']:
            self.warm_caches()

        self.stdout.write(
            self.style.SUCCESS('✅ System optimization completed successfully!')
        )

    def clear_caches(self):
        """Clear all system caches"""
        self.stdout.write('🧹 Clearing caches...')
        
        try:
            cache.clear()
            self.stdout.write(
                self.style.SUCCESS('   ✓ All caches cleared')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'   ✗ Cache clearing failed: {str(e)}')
            )

    def optimize_database(self):
        """Optimize database performance"""
        self.stdout.write('🔧 Optimizing database...')
        
        try:
            with connection.cursor() as cursor:
                # SQLite specific optimizations
                if 'sqlite' in settings.DATABASES['default']['ENGINE']:
                    self.stdout.write('   📊 Applying SQLite optimizations...')
                    
                    # Analyze tables for better query planning
                    cursor.execute("ANALYZE;")
                    self.stdout.write('   ✓ Database analysis completed')
                    
                    # Vacuum database to reclaim space
                    cursor.execute("VACUUM;")
                    self.stdout.write('   ✓ Database vacuum completed')
                    
                    # Check and create missing indexes
                    self.create_missing_indexes(cursor)
                
                else:
                    self.stdout.write('   ℹ️  Non-SQLite database detected, skipping SQLite optimizations')
                    
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'   ✗ Database optimization failed: {str(e)}')
            )

    def create_missing_indexes(self, cursor):
        """Create missing database indexes for better performance"""
        self.stdout.write('   📈 Creating performance indexes...')
        
        indexes = [
            # Student indexes for faster queries
            "CREATE INDEX IF NOT EXISTS idx_students_name ON students_student(first_name, last_name);",
            "CREATE INDEX IF NOT EXISTS idx_students_mobile ON students_student(mobile_number);",
            "CREATE INDEX IF NOT EXISTS idx_students_email ON students_student(email);",
            "CREATE INDEX IF NOT EXISTS idx_students_due_amount ON students_student(due_amount);",
            "CREATE INDEX IF NOT EXISTS idx_students_created_at ON students_student(created_at);",
            
            # Fee-related indexes
            "CREATE INDEX IF NOT EXISTS idx_fee_deposits_student ON student_fees_feedeposit(student_id);",
            "CREATE INDEX IF NOT EXISTS idx_fee_deposits_date ON student_fees_feedeposit(deposit_date);",
            "CREATE INDEX IF NOT EXISTS idx_fee_deposits_amount ON student_fees_feedeposit(paid_amount);",
            
            # Attendance indexes
            "CREATE INDEX IF NOT EXISTS idx_attendance_student_date ON attendance_attendance(student_id, date);",
            "CREATE INDEX IF NOT EXISTS idx_attendance_status ON attendance_attendance(status);",
            
            # User activity indexes
            "CREATE INDEX IF NOT EXISTS idx_users_last_login ON users_customuser(last_login);",
            "CREATE INDEX IF NOT EXISTS idx_users_active ON users_customuser(is_active);",
        ]
        
        created_count = 0
        for index_sql in indexes:
            try:
                cursor.execute(index_sql)
                created_count += 1
            except Exception as e:
                # Index might already exist, continue
                pass
        
        self.stdout.write(f'   ✓ {created_count} indexes processed')

    def warm_caches(self):
        """Warm up system caches with common data"""
        self.stdout.write('🔥 Warming up caches...')
        
        try:
            # Import services
            from students.services import StudentService
            from core.cache_middleware import CacheWarmer
            
            # Warm student caches
            self.stdout.write('   📚 Warming student caches...')
            CacheWarmer.warm_student_caches()
            self.stdout.write('   ✓ Student caches warmed')
            
            # Warm system caches
            self.stdout.write('   🏠 Warming system caches...')
            CacheWarmer.warm_system_caches()
            self.stdout.write('   ✓ System caches warmed')
            
            # Pre-load dashboard stats
            self.stdout.write('   📊 Pre-loading dashboard statistics...')
            StudentService.get_dashboard_stats()
            self.stdout.write('   ✓ Dashboard stats cached')
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'   ✗ Cache warming failed: {str(e)}')
            )

    def display_system_info(self):
        """Display current system information"""
        self.stdout.write('\n📋 System Information:')
        
        try:
            # Database info
            with connection.cursor() as cursor:
                if 'sqlite' in settings.DATABASES['default']['ENGINE']:
                    cursor.execute("SELECT COUNT(*) FROM students_student;")
                    student_count = cursor.fetchone()[0]
                    
                    cursor.execute("SELECT COUNT(*) FROM users_customuser;")
                    user_count = cursor.fetchone()[0]
                    
                    self.stdout.write(f'   👥 Total Students: {student_count}')
                    self.stdout.write(f'   🔐 Total Users: {user_count}')
                    
                    # Database size
                    db_path = settings.DATABASES['default']['NAME']
                    if os.path.exists(db_path):
                        db_size = os.path.getsize(db_path) / (1024 * 1024)  # MB
                        self.stdout.write(f'   💾 Database Size: {db_size:.2f} MB')
            
            # Cache info
            try:
                cache.set('test_key', 'test_value', 1)
                cache_status = '✅ Working'
                cache.delete('test_key')
            except:
                cache_status = '❌ Not Working'
            
            self.stdout.write(f'   🗄️  Cache Status: {cache_status}')
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'   ✗ Could not retrieve system info: {str(e)}')
            )