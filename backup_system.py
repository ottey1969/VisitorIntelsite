"""
Comprehensive Backup System for Visitor Intel Platform
Creates multiple backup layers to prevent data loss
"""

import os
import json
import shutil
import zipfile
from datetime import datetime
from pathlib import Path
import sqlite3
import subprocess
from app import db, app
from models import Business, Conversation, ConversationMessage, Purchase, CreditPackage

class BackupManager:
    """Complete backup system for the AI conversation platform"""
    
    def __init__(self):
        self.backup_dir = Path("backups")
        self.backup_dir.mkdir(exist_ok=True)
        
    def create_full_backup(self) -> str:
        """Create a complete system backup with timestamp"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"visitor_intel_backup_{timestamp}"
        backup_path = self.backup_dir / backup_name
        backup_path.mkdir(exist_ok=True)
        
        print(f"Creating full backup: {backup_name}")
        
        # 1. Database backup
        self._backup_database(backup_path)
        
        # 2. Code backup
        self._backup_code(backup_path)
        
        # 3. Configuration backup
        self._backup_configuration(backup_path)
        
        # 4. Static files backup
        self._backup_static_files(backup_path)
        
        # 5. Create restoration instructions
        self._create_restoration_guide(backup_path)
        
        # 6. Create ZIP archive
        zip_path = self._create_zip_archive(backup_path, backup_name)
        
        print(f"✅ Full backup completed: {zip_path}")
        return str(zip_path)
    
    def _backup_database(self, backup_path: Path):
        """Backup all database data as JSON and SQL"""
        db_backup_dir = backup_path / "database"
        db_backup_dir.mkdir(exist_ok=True)
        
        with app.app_context():
            # Export all data as JSON (human-readable)
            backup_data = {
                'businesses': [self._serialize_business(b) for b in Business.query.all()],
                'conversations': [self._serialize_conversation(c) for c in Conversation.query.all()],
                'messages': [self._serialize_message(m) for m in ConversationMessage.query.all()],
                'purchases': [self._serialize_purchase(p) for p in Purchase.query.all()],
                'credit_packages': [self._serialize_credit_package(cp) for cp in CreditPackage.query.all()],
                'backup_metadata': {
                    'created_at': datetime.utcnow().isoformat(),
                    'total_businesses': Business.query.count(),
                    'total_conversations': Conversation.query.count(),
                    'total_messages': ConversationMessage.query.count(),
                    'platform_version': '1.0.0'
                }
            }
            
            # Save JSON backup
            with open(db_backup_dir / "complete_data.json", 'w') as f:
                json.dump(backup_data, f, indent=2, default=str)
            
            # Create PostgreSQL dump if available
            try:
                database_url = os.environ.get('DATABASE_URL')
                if database_url:
                    dump_file = db_backup_dir / "postgresql_dump.sql"
                    subprocess.run([
                        'pg_dump', database_url, '--no-password', '--file', str(dump_file)
                    ], check=True)
            except Exception as e:
                print(f"PostgreSQL dump failed (not critical): {e}")
        
        print("✅ Database backup completed")
    
    def _backup_code(self, backup_path: Path):
        """Backup all Python source code"""
        code_backup_dir = backup_path / "source_code"
        code_backup_dir.mkdir(exist_ok=True)
        
        # Core Python files
        python_files = [
            'main.py', 'app.py', 'routes.py', 'models.py',
            'ai_conversation.py', 'payment_handler.py', 'keepalive.py',
            'geo_language_detector.py', 'infographic_generator.py',
            'social_media_manager.py', 'auto_posting_scheduler.py',
            'subscription_manager.py', 'conversation_intelligence.py',
            'content_ecosystem.py', 'create_sample_infographic.py',
            'create_visitor_intel_logo.py', 'backup_system.py'
        ]
        
        for file in python_files:
            if os.path.exists(file):
                shutil.copy2(file, code_backup_dir)
        
        # Copy templates directory
        if os.path.exists('templates'):
            shutil.copytree('templates', code_backup_dir / 'templates')
        
        # Copy static directory
        if os.path.exists('static'):
            shutil.copytree('static', code_backup_dir / 'static')
        
        print("✅ Source code backup completed")
    
    def _backup_configuration(self, backup_path: Path):
        """Backup configuration files and settings"""
        config_backup_dir = backup_path / "configuration"
        config_backup_dir.mkdir(exist_ok=True)
        
        # Configuration files
        config_files = [
            'pyproject.toml', 'uv.lock', '.replit', 'replit.md'
        ]
        
        for file in config_files:
            if os.path.exists(file):
                shutil.copy2(file, config_backup_dir)
        
        # Environment variables template (without secrets)
        env_template = {
            'DATABASE_URL': 'postgresql://...',
            'OPENAI_API_KEY': 'sk-...',
            'ANTHROPIC_API_KEY': 'sk-ant-...',
            'PERPLEXITY_API_KEY': 'pplx-...',
            'GEMINI_API_KEY': 'AI...',
            'SESSION_SECRET': 'your-session-secret',
            'PAYPAL_CLIENT_ID': 'your-paypal-client-id',
            'PAYPAL_CLIENT_SECRET': 'your-paypal-secret'
        }
        
        with open(config_backup_dir / "environment_variables_template.json", 'w') as f:
            json.dump(env_template, f, indent=2)
        
        print("✅ Configuration backup completed")
    
    def _backup_static_files(self, backup_path: Path):
        """Backup generated assets and images"""
        static_backup_dir = backup_path / "assets"
        static_backup_dir.mkdir(exist_ok=True)
        
        # Copy attached assets if they exist
        if os.path.exists('attached_assets'):
            shutil.copytree('attached_assets', static_backup_dir / 'attached_assets')
        
        print("✅ Static files backup completed")
    
    def _create_zip_archive(self, backup_path: Path, backup_name: str) -> Path:
        """Create compressed ZIP archive of the backup"""
        zip_path = self.backup_dir / f"{backup_name}.zip"
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in backup_path.rglob('*'):
                if file_path.is_file():
                    arcname = file_path.relative_to(backup_path)
                    zipf.write(file_path, arcname)
        
        # Remove uncompressed backup directory
        shutil.rmtree(backup_path)
        
        return zip_path
    
    def _create_restoration_guide(self, backup_path: Path):
        """Create step-by-step restoration instructions"""
        guide = """
# Visitor Intel Platform Restoration Guide

## Quick Recovery Steps:

### 1. Set Up New Replit Project
- Create new Python Repl
- Upload all files from 'source_code' folder
- Copy 'configuration' files to root directory

### 2. Install Dependencies
```bash
# Install required packages
pip install flask flask-sqlalchemy anthropic openai google-genai requests psycopg2-binary gunicorn pillow pytz trafilatura
```

### 3. Set Environment Variables
- Copy values from 'environment_variables_template.json'
- Set your actual API keys in Replit Secrets:
  - OPENAI_API_KEY
  - ANTHROPIC_API_KEY
  - PERPLEXITY_API_KEY  
  - GEMINI_API_KEY
  - DATABASE_URL (PostgreSQL)
  - SESSION_SECRET

### 4. Restore Database
Option A (PostgreSQL):
```bash
psql $DATABASE_URL < database/postgresql_dump.sql
```

Option B (JSON Import):
- Run the platform once to create tables
- Use the database restoration script with 'complete_data.json'

### 5. Start the Platform
```bash
python main.py
```

## Files Included:
- ✅ Complete source code
- ✅ All templates and static files
- ✅ Database dump (JSON + SQL)
- ✅ Configuration files
- ✅ Asset files and images

## Critical Components Backed Up:
- 4-AI conversation system (OpenAI, Anthropic, Perplexity, Gemini)
- 24/7 keepalive system
- Payment processing
- Social media automation
- Infographic generation
- Geographic localization
- Admin dashboard
- Verification endpoints

## Support:
If restoration fails, check:
1. All environment variables are set correctly
2. Database connection is working
3. API keys are valid
4. Dependencies are installed

Your Visitor Intel platform will be fully operational after following these steps.
"""
        
        with open(backup_path / "RESTORATION_GUIDE.md", 'w') as f:
            f.write(guide)
        
        print("✅ Restoration guide created")
    
    def _serialize_business(self, business):
        """Convert Business object to dict"""
        return {
            'id': business.id,
            'name': business.name,
            'website': business.website,
            'description': business.description,
            'location': business.location,
            'phone': getattr(business, 'phone', None),
            'email': getattr(business, 'email', None),
            'industry': business.industry,
            'is_unlimited': business.is_unlimited,
            'credits_remaining': business.credits_remaining,
            'created_at': business.created_at,
            'share_url': getattr(business, 'share_url', None),
            'plan_type': business.plan_type,
            'custom_domain': getattr(business, 'custom_domain', None),
            'is_featured': business.is_featured,
            'subscription_type': getattr(business, 'subscription_type', 'credit'),
            'monthly_conversation_limit': getattr(business, 'monthly_conversation_limit', 0),
            'conversations_used_this_month': getattr(business, 'conversations_used_this_month', 0),
            'subscription_start_date': getattr(business, 'subscription_start_date', None),
            'subscription_end_date': getattr(business, 'subscription_end_date', None),
            'auto_renew': getattr(business, 'auto_renew', True)
        }
    
    def _serialize_conversation(self, conversation):
        """Convert Conversation object to dict"""
        return {
            'id': conversation.id,
            'business_id': conversation.business_id,
            'topic': conversation.topic,
            'status': conversation.status,
            'created_at': conversation.created_at
        }
    
    def _serialize_message(self, message):
        """Convert ConversationMessage object to dict"""
        return {
            'id': message.id,
            'conversation_id': message.conversation_id,
            'ai_agent_type': message.ai_agent_type,
            'ai_agent_name': message.ai_agent_name,
            'content': message.content,
            'created_at': message.created_at
        }
    
    def _serialize_purchase(self, purchase):
        """Convert Purchase object to dict"""
        return {
            'id': purchase.id,
            'business_id': purchase.business_id,
            'package_id': purchase.package_id,
            'amount': purchase.amount,
            'status': purchase.status,
            'paypal_order_id': purchase.paypal_order_id,
            'created_at': purchase.created_at
        }
    
    def _serialize_credit_package(self, package):
        """Convert CreditPackage object to dict"""
        return {
            'id': package.id,
            'name': package.name,
            'credits': package.credits,
            'price': package.price,
            'description': package.description
        }
    
    def list_backups(self) -> list:
        """List all available backups"""
        backups = []
        for backup_file in self.backup_dir.glob("visitor_intel_backup_*.zip"):
            stat = backup_file.stat()
            backups.append({
                'filename': backup_file.name,
                'size_mb': round(stat.st_size / (1024 * 1024), 2),
                'created': datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
            })
        return sorted(backups, key=lambda x: x['created'], reverse=True)
    
    def cleanup_old_backups(self, keep_count: int = 5):
        """Keep only the newest N backups"""
        backups = list(self.backup_dir.glob("visitor_intel_backup_*.zip"))
        backups.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
        for old_backup in backups[keep_count:]:
            old_backup.unlink()
            print(f"Deleted old backup: {old_backup.name}")

def create_backup():
    """Main backup function"""
    backup_manager = BackupManager()
    return backup_manager.create_full_backup()

def list_all_backups():
    """List all available backups"""
    backup_manager = BackupManager()
    return backup_manager.list_backups()

if __name__ == "__main__":
    # Create immediate backup
    backup_path = create_backup()
    print(f"\n🎉 BACKUP COMPLETED: {backup_path}")
    
    # Show all backups
    print("\n📦 Available Backups:")
    for backup in list_all_backups():
        print(f"  - {backup['filename']} ({backup['size_mb']} MB) - {backup['created']}")