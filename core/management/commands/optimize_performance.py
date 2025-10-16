# Performance Optimization Management Command
from django.core.management.base import BaseCommand
from django.core.cache import cache
from django.db import connection
import os
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Optimize system performance'
    
    def handle(self, *args, **options):
        self.stdout.write("🚀 Starting performance optimization...")
        
        # 1. Clear cache
        try:
            cache.clear()
            self.stdout.write("✅ Cache cleared")
        except Exception as e:
            self.stdout.write(f"❌ Cache clear failed: {e}")
        
        # 2. Optimize SQLite
        try:
            with connection.cursor() as cursor:
                cursor.execute("VACUUM;")
                cursor.execute("PRAGMA optimize;")
                cursor.execute("PRAGMA journal_mode = WAL;")
                cursor.execute("PRAGMA synchronous = NORMAL;")
                cursor.execute("PRAGMA cache_size = 10000;")
            self.stdout.write("✅ Database optimized")
        except Exception as e:
            self.stdout.write(f"❌ Database optimization failed: {e}")
        
        # 3. Check ML models
        from django.conf import settings
        models_dir = os.path.join(settings.BASE_DIR, 'models')
        if os.path.exists(models_dir):
            model_count = len([f for f in os.listdir(models_dir) if f.endswith('.pkl')])
            self.stdout.write(f"📊 Found {model_count} ML models")
        
        # 4. Database stats
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table';")
                table_count = cursor.fetchone()[0]
                
                cursor.execute("PRAGMA page_count;")
                page_count = cursor.fetchone()[0]
                
                cursor.execute("PRAGMA page_size;")
                page_size = cursor.fetchone()[0]
                
                db_size_mb = (page_count * page_size) / (1024 * 1024)
                
                self.stdout.write(f"📈 Database: {table_count} tables, {db_size_mb:.1f}MB")
        except Exception as e:
            self.stdout.write(f"❌ Stats failed: {e}")
        
        self.stdout.write("🎉 Performance optimization complete!")
        self.stdout.write("\n💡 Recommendations:")
        self.stdout.write("   • Restart the server for full effect")
        self.stdout.write("   • Run this command weekly")
        self.stdout.write("   • Monitor logs for performance issues")