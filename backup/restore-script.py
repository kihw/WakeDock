#!/usr/bin/env python3
"""
WakeDock restore script.
Restore WakeDock data and configurations from backup archives.
"""

import argparse
import asyncio
import json
import logging
import os
import shutil
import tarfile
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import subprocess
import yaml

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class RestoreManager:
    """Manages restore operations for WakeDock."""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or "/app/config/config.yml"
        self.backup_dir = Path("/app/backups")
        self.temp_dir = Path(tempfile.mkdtemp(prefix="wakedock_restore_"))
        
        # Load configuration
        self.config = self._load_config()
        
    def _load_config(self) -> Dict:
        """Load WakeDock configuration."""
        try:
            if Path(self.config_path).exists():
                with open(self.config_path) as f:
                    return yaml.safe_load(f) or {}
        except Exception as e:
            logger.warning(f"Could not load config from {self.config_path}: {e}")
        return {}
    
    def _get_database_url(self) -> Optional[str]:
        """Get database URL from config or environment."""
        # Try environment variable first
        db_url = os.getenv("DATABASE_URL")
        if db_url:
            return db_url
        
        # Try config file
        db_config = self.config.get("database", {})
        return db_config.get("url")
    
    def list_backups(self) -> List[Dict]:
        """List available backup archives."""
        backups = []
        
        for backup_file in sorted(self.backup_dir.glob("*.tar.gz"), reverse=True):
            stat = backup_file.stat()
            backups.append({
                "name": backup_file.name,
                "path": str(backup_file),
                "size": stat.st_size,
                "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
            })
        
        return backups
    
    async def extract_backup(self, backup_path: Path) -> Path:
        """Extract backup archive to temporary directory."""
        logger.info(f"Extracting backup: {backup_path.name}")
        
        if not backup_path.exists():
            raise FileNotFoundError(f"Backup file not found: {backup_path}")
        
        extract_dir = self.temp_dir / "extracted"
        extract_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            with tarfile.open(backup_path, "r:gz") as tar:
                tar.extractall(extract_dir)
            
            # The backup should be in a 'backup' subdirectory
            backup_content_dir = extract_dir / "backup"
            if not backup_content_dir.exists():
                # Try to find the backup content
                subdirs = [d for d in extract_dir.iterdir() if d.is_dir()]
                if subdirs:
                    backup_content_dir = subdirs[0]
                else:
                    backup_content_dir = extract_dir
            
            logger.info(f"Backup extracted to: {backup_content_dir}")
            return backup_content_dir
            
        except Exception as e:
            logger.error(f"Failed to extract backup: {e}")
            raise
    
    async def get_backup_info(self, backup_dir: Path) -> Dict:
        """Get information about the backup."""
        info_file = backup_dir / "data" / "system_info.json"
        
        if info_file.exists():
            try:
                with open(info_file) as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Could not read backup info: {e}")
        
        return {
            "backup_date": "unknown",
            "wakedock_version": "unknown",
            "docker_version": "unknown"
        }
    
    async def confirm_restore(self, backup_info: Dict) -> bool:
        """Confirm restore operation with user."""
        print("\\n" + "="*60)
        print("RESTORE CONFIRMATION")
        print("="*60)
        print(f"Backup Date: {backup_info.get('backup_date', 'unknown')}")
        print(f"WakeDock Version: {backup_info.get('wakedock_version', 'unknown')}")
        print(f"Docker Version: {backup_info.get('docker_version', 'unknown')}")
        print("\\n⚠️  WARNING: This will replace current WakeDock data!")
        print("⚠️  Make sure WakeDock is stopped before proceeding.")
        print("\\nWhat will be restored:")
        print("- Database (if present)")
        print("- Configuration files")
        print("- Application data")
        print("- Logs")
        
        response = input("\\nDo you want to continue? (yes/no): ").lower().strip()
        return response in ["yes", "y"]
    
    async def restore_database(self, backup_dir: Path) -> bool:
        """Restore database from backup."""
        db_backup_file = backup_dir / "database.sql"
        sqlite_backup_file = backup_dir / "database.sqlite"
        
        db_url = self._get_database_url()
        if not db_url:
            logger.warning("No database URL found, skipping database restore")
            return False
        
        if db_url.startswith("postgresql://") and db_backup_file.exists():
            return await self._restore_postgresql(db_url, db_backup_file)
        elif db_url.startswith("sqlite:///") and sqlite_backup_file.exists():
            return await self._restore_sqlite(db_url, sqlite_backup_file)
        else:
            logger.warning("No compatible database backup found")
            return False
    
    async def _restore_postgresql(self, db_url: str, backup_file: Path) -> bool:
        """Restore PostgreSQL database."""
        logger.info("Restoring PostgreSQL database...")
        
        try:
            # Use psql to restore backup
            cmd = [
                "psql",
                "--no-password",
                "--quiet",
                db_url
            ]
            
            with open(backup_file, 'r') as f:
                result = subprocess.run(
                    cmd,
                    stdin=f,
                    stderr=subprocess.PIPE,
                    text=True
                )
            
            if result.returncode != 0:
                logger.error(f"Database restore failed: {result.stderr}")
                return False
            
            logger.info("Database restored successfully")
            return True
            
        except FileNotFoundError:
            logger.error("psql not found. Please install PostgreSQL client tools.")
            return False
        except Exception as e:
            logger.error(f"Database restore failed: {e}")
            return False
    
    async def _restore_sqlite(self, db_url: str, backup_file: Path) -> bool:
        """Restore SQLite database."""
        logger.info("Restoring SQLite database...")
        
        # Extract file path from URL
        db_path = db_url.replace("sqlite:///", "")
        target_path = Path(db_path)
        
        try:
            # Create backup of existing database
            if target_path.exists():
                backup_path = target_path.with_suffix(f"{target_path.suffix}.backup")
                shutil.copy2(target_path, backup_path)
                logger.info(f"Existing database backed up to: {backup_path}")
            
            # Restore from backup
            target_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(backup_file, target_path)
            
            logger.info("SQLite database restored successfully")
            return True
            
        except Exception as e:
            logger.error(f"SQLite restore failed: {e}")
            return False
    
    async def restore_configurations(self, backup_dir: Path) -> bool:
        """Restore configuration files."""
        logger.info("Restoring configurations...")
        
        config_backup_dir = backup_dir / "config"
        if not config_backup_dir.exists():
            logger.warning("No configuration backup found")
            return False
        
        try:
            # Restore WakeDock config
            wakedock_config = config_backup_dir / "wakedock"
            if wakedock_config.exists():
                target_dir = Path("/app/config")
                
                # Backup existing config
                if target_dir.exists():
                    backup_target = target_dir.with_suffix(".backup")
                    if backup_target.exists():
                        shutil.rmtree(backup_target)
                    shutil.move(target_dir, backup_target)
                
                shutil.copytree(wakedock_config, target_dir)
                logger.info("WakeDock configuration restored")
            
            # Restore Caddy config
            caddy_config = config_backup_dir / "caddy"
            if caddy_config.exists():
                target_dir = Path("/app/caddy")
                
                # Backup existing config
                if target_dir.exists():
                    backup_target = target_dir.with_suffix(".backup")
                    if backup_target.exists():
                        shutil.rmtree(backup_target)
                    shutil.move(target_dir, backup_target)
                
                shutil.copytree(caddy_config, target_dir)
                logger.info("Caddy configuration restored")
            
            # Restore environment file
            env_backup = config_backup_dir / ".env"
            if env_backup.exists():
                env_target = Path("/app/.env")
                
                # Backup existing .env
                if env_target.exists():
                    backup_target = env_target.with_suffix(".backup")
                    shutil.copy2(env_target, backup_target)
                
                shutil.copy2(env_backup, env_target)
                logger.info("Environment file restored")
            
            # Restore Docker Compose files
            for compose_file in ["docker-compose.yml", "docker-compose.override.yml"]:
                compose_backup = config_backup_dir / compose_file
                if compose_backup.exists():
                    compose_target = Path(f"/app/{compose_file}")
                    
                    # Backup existing file
                    if compose_target.exists():
                        backup_target = compose_target.with_suffix(".backup")
                        shutil.copy2(compose_target, backup_target)
                    
                    shutil.copy2(compose_backup, compose_target)
                    logger.info(f"{compose_file} restored")
            
            return True
            
        except Exception as e:
            logger.error(f"Configuration restore failed: {e}")
            return False
    
    async def restore_data(self, backup_dir: Path) -> bool:
        """Restore application data."""
        logger.info("Restoring application data...")
        
        data_backup_dir = backup_dir / "data"
        if not data_backup_dir.exists():
            logger.warning("No data backup found")
            return False
        
        try:
            # Restore application data
            app_data_backup = data_backup_dir / "app_data"
            if app_data_backup.exists():
                target_dir = Path("/app/data")
                
                # Backup existing data
                if target_dir.exists():
                    backup_target = target_dir.with_suffix(".backup")
                    if backup_target.exists():
                        shutil.rmtree(backup_target)
                    shutil.move(target_dir, backup_target)
                
                shutil.copytree(app_data_backup, target_dir)
                logger.info("Application data restored")
            
            # Restore logs
            logs_backup = data_backup_dir / "logs"
            if logs_backup.exists():
                target_dir = Path("/app/logs")
                target_dir.mkdir(parents=True, exist_ok=True)
                
                for log_file in logs_backup.glob("*"):
                    target_file = target_dir / log_file.name
                    
                    # Don't overwrite current logs, rename with timestamp
                    if target_file.exists():
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        target_file = target_dir / f"{log_file.stem}_restored_{timestamp}{log_file.suffix}"
                    
                    shutil.copy2(log_file, target_file)
                
                logger.info("Logs restored")
            
            return True
            
        except Exception as e:
            logger.error(f"Data restore failed: {e}")
            return False
    
    async def post_restore_tasks(self) -> None:
        """Perform post-restore tasks."""
        logger.info("Performing post-restore tasks...")
        
        # Set proper file permissions
        try:
            # Make scripts executable
            scripts_dir = Path("/app/scripts")
            if scripts_dir.exists():
                for script in scripts_dir.glob("*.sh"):
                    script.chmod(0o755)
            
            # Set config file permissions
            config_dir = Path("/app/config")
            if config_dir.exists():
                for config_file in config_dir.rglob("*"):
                    if config_file.is_file():
                        config_file.chmod(0o644)
            
            logger.info("File permissions updated")
            
        except Exception as e:
            logger.warning(f"Could not update file permissions: {e}")
        
        # Recommendations for user
        print("\\n" + "="*60)
        print("RESTORE COMPLETED")
        print("="*60)
        print("\\n📋 Next steps:")
        print("1. Review restored configuration files")
        print("2. Update any environment-specific settings")
        print("3. Start WakeDock services:")
        print("   docker-compose up -d")
        print("4. Verify that all services are working correctly")
        print("5. Check logs for any errors:")
        print("   docker-compose logs -f")
        print("\\n⚠️  Note: Backup files of replaced data are saved with .backup extension")
    
    async def run_restore(
        self,
        backup_path: Path,
        force: bool = False,
        database_only: bool = False,
        config_only: bool = False
    ) -> bool:
        """Run complete restore process."""
        try:
            logger.info("Starting WakeDock restore process...")
            
            # Extract backup
            backup_dir = await self.extract_backup(backup_path)
            
            # Get backup info
            backup_info = await self.get_backup_info(backup_dir)
            
            # Confirm restore (unless forced)
            if not force:
                if not await self.confirm_restore(backup_info):
                    logger.info("Restore cancelled by user")
                    return False
            
            success = True
            
            # Restore database
            if not config_only:
                db_success = await self.restore_database(backup_dir)
                if database_only:
                    return db_success
                success = success and db_success
            
            # Restore configurations
            if not database_only:
                config_success = await self.restore_configurations(backup_dir)
                success = success and config_success
                
                # Restore application data
                data_success = await self.restore_data(backup_dir)
                success = success and data_success
            
            # Post-restore tasks
            await self.post_restore_tasks()
            
            if success:
                logger.info("Restore completed successfully!")
            else:
                logger.warning("Restore completed with some errors")
            
            return success
            
        except Exception as e:
            logger.error(f"Restore failed: {e}")
            return False
        
        finally:
            # Cleanup temporary directory
            if self.temp_dir.exists():
                shutil.rmtree(self.temp_dir)


async def main():
    """Main restore script entry point."""
    parser = argparse.ArgumentParser(description="WakeDock Restore Tool")
    parser.add_argument(
        "backup",
        nargs="?",
        help="Path to backup file or backup name"
    )
    parser.add_argument(
        "--config",
        "-c",
        help="Path to WakeDock configuration file",
        default="/app/config/config.yml"
    )
    parser.add_argument(
        "--list",
        "-l",
        action="store_true",
        help="List available backups"
    )
    parser.add_argument(
        "--force",
        "-f",
        action="store_true",
        help="Force restore without confirmation"
    )
    parser.add_argument(
        "--database-only",
        action="store_true",
        help="Restore database only"
    )
    parser.add_argument(
        "--config-only",
        action="store_true",
        help="Restore configuration only"
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create restore manager
    restore_manager = RestoreManager(config_path=args.config)
    
    if args.list:
        # List backups
        backups = restore_manager.list_backups()
        
        if not backups:
            print("No backups found.")
            return
        
        print(f"{'Name':<40} {'Size':<10} {'Created':<20}")
        print("-" * 75)
        
        for backup in backups:
            size_mb = backup['size'] / (1024 * 1024)
            created = datetime.fromisoformat(backup['created']).strftime('%Y-%m-%d %H:%M')
            print(f"{backup['name']:<40} {size_mb:>7.1f} MB {created:<20}")
        
        return
    
    if not args.backup:
        parser.error("Backup file or name is required (use --list to see available backups)")
    
    # Determine backup path
    backup_path = Path(args.backup)
    
    if not backup_path.is_absolute():
        # Try to find backup by name
        backup_dir = Path("/app/backups")
        if not args.backup.endswith(".tar.gz"):
            # Find latest backup with this prefix
            matching_backups = sorted(
                backup_dir.glob(f"{args.backup}*.tar.gz"),
                reverse=True
            )
            if matching_backups:
                backup_path = matching_backups[0]
            else:
                backup_path = backup_dir / f"{args.backup}.tar.gz"
        else:
            backup_path = backup_dir / args.backup
    
    if not backup_path.exists():
        print(f"Backup file not found: {backup_path}")
        print("Use --list to see available backups")
        exit(1)
    
    # Run restore
    success = await restore_manager.run_restore(
        backup_path,
        force=args.force,
        database_only=args.database_only,
        config_only=args.config_only
    )
    
    exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
