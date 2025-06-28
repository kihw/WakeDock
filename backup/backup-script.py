#!/usr/bin/env python3
"""
WakeDock backup script.
Automated backup system for WakeDock data and configurations.
"""

import argparse
import asyncio
import json
import logging
import os
import shutil
import tarfile
import tempfile
from datetime import datetime, timedelta
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


class BackupManager:
    """Manages backup operations for WakeDock."""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or "/app/config/config.yml"
        self.backup_dir = Path("/app/backups")
        self.temp_dir = Path(tempfile.mkdtemp(prefix="wakedock_backup_"))
        
        # Create backup directory if it doesn't exist
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Load configuration
        self.config = self._load_config()
        
        # Set backup configuration
        backup_config = self.config.get("backup", {})
        self.retention_days = backup_config.get("retention_days", 30)
        self.storage_config = backup_config.get("storage", {"type": "local"})
    
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
    
    async def backup_database(self) -> Optional[Path]:
        """Backup the database."""
        db_url = self._get_database_url()
        if not db_url:
            logger.warning("No database URL found, skipping database backup")
            return None
        
        logger.info("Starting database backup...")
        
        # Determine database type
        if db_url.startswith("postgresql://"):
            return await self._backup_postgresql(db_url)
        elif db_url.startswith("sqlite:///"):
            return await self._backup_sqlite(db_url)
        else:
            logger.warning(f"Unsupported database type: {db_url}")
            return None
    
    async def _backup_postgresql(self, db_url: str) -> Optional[Path]:
        """Backup PostgreSQL database."""
        backup_file = self.temp_dir / "database.sql"
        
        try:
            # Use pg_dump to create backup
            cmd = [
                "pg_dump",
                "--no-password",
                "--verbose",
                "--clean",
                "--no-acl",
                "--no-owner",
                db_url
            ]
            
            with open(backup_file, 'w') as f:
                result = subprocess.run(
                    cmd,
                    stdout=f,
                    stderr=subprocess.PIPE,
                    text=True
                )
            
            if result.returncode != 0:
                logger.error(f"pg_dump failed: {result.stderr}")
                return None
            
            logger.info(f"Database backup created: {backup_file}")
            return backup_file
            
        except FileNotFoundError:
            logger.error("pg_dump not found. Please install PostgreSQL client tools.")
            return None
        except Exception as e:
            logger.error(f"Database backup failed: {e}")
            return None
    
    async def _backup_sqlite(self, db_url: str) -> Optional[Path]:
        """Backup SQLite database."""
        # Extract file path from URL
        db_path = db_url.replace("sqlite:///", "")
        source_path = Path(db_path)
        
        if not source_path.exists():
            logger.warning(f"SQLite database not found: {source_path}")
            return None
        
        backup_file = self.temp_dir / "database.sqlite"
        
        try:
            shutil.copy2(source_path, backup_file)
            logger.info(f"SQLite backup created: {backup_file}")
            return backup_file
        except Exception as e:
            logger.error(f"SQLite backup failed: {e}")
            return None
    
    async def backup_configurations(self) -> Path:
        """Backup configuration files."""
        logger.info("Backing up configurations...")
        
        config_backup_dir = self.temp_dir / "config"
        config_backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Backup main config
        source_config_dir = Path("/app/config")
        if source_config_dir.exists():
            shutil.copytree(
                source_config_dir,
                config_backup_dir / "wakedock",
                dirs_exist_ok=True
            )
        
        # Backup Caddy config
        caddy_config_dir = Path("/app/caddy")
        if caddy_config_dir.exists():
            shutil.copytree(
                caddy_config_dir,
                config_backup_dir / "caddy",
                dirs_exist_ok=True
            )
        
        # Backup environment file
        env_file = Path("/app/.env")
        if env_file.exists():
            shutil.copy2(env_file, config_backup_dir / ".env")
        
        # Backup Docker Compose files
        for compose_file in ["docker-compose.yml", "docker-compose.override.yml"]:
            compose_path = Path(f"/app/{compose_file}")
            if compose_path.exists():
                shutil.copy2(compose_path, config_backup_dir / compose_file)
        
        logger.info(f"Configurations backed up to: {config_backup_dir}")
        return config_backup_dir
    
    async def backup_data(self) -> Optional[Path]:
        """Backup application data."""
        logger.info("Backing up application data...")
        
        data_backup_dir = self.temp_dir / "data"
        data_backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Backup service data (volumes, configs, etc.)
        data_dir = Path("/app/data")
        if data_dir.exists():
            shutil.copytree(
                data_dir,
                data_backup_dir / "app_data",
                dirs_exist_ok=True
            )
        
        # Backup logs (last 7 days)
        logs_dir = Path("/app/logs")
        if logs_dir.exists():
            logs_backup_dir = data_backup_dir / "logs"
            logs_backup_dir.mkdir(parents=True, exist_ok=True)
            
            cutoff_date = datetime.now() - timedelta(days=7)
            
            for log_file in logs_dir.glob("*.log*"):
                if log_file.stat().st_mtime > cutoff_date.timestamp():
                    shutil.copy2(log_file, logs_backup_dir / log_file.name)
        
        # Create system info
        system_info = {
            "backup_date": datetime.now().isoformat(),
            "wakedock_version": self._get_wakedock_version(),
            "docker_version": self._get_docker_version(),
            "system_info": self._get_system_info()
        }
        
        with open(data_backup_dir / "system_info.json", 'w') as f:
            json.dump(system_info, f, indent=2)
        
        logger.info(f"Application data backed up to: {data_backup_dir}")
        return data_backup_dir
    
    def _get_wakedock_version(self) -> str:
        """Get WakeDock version."""
        try:
            # Try to get version from package
            import wakedock
            return getattr(wakedock, '__version__', 'unknown')
        except:
            return 'unknown'
    
    def _get_docker_version(self) -> str:
        """Get Docker version."""
        try:
            result = subprocess.run(
                ["docker", "--version"],
                capture_output=True,
                text=True
            )
            return result.stdout.strip() if result.returncode == 0 else 'unknown'
        except:
            return 'unknown'
    
    def _get_system_info(self) -> Dict:
        """Get system information."""
        try:
            import platform
            return {
                "platform": platform.platform(),
                "python_version": platform.python_version(),
                "architecture": platform.architecture()[0]
            }
        except:
            return {}
    
    async def create_backup_archive(self, backup_name: str) -> Path:
        """Create compressed backup archive."""
        logger.info("Creating backup archive...")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        archive_name = f"{backup_name}_{timestamp}.tar.gz"
        archive_path = self.backup_dir / archive_name
        
        with tarfile.open(archive_path, "w:gz") as tar:
            tar.add(self.temp_dir, arcname="backup")
        
        logger.info(f"Backup archive created: {archive_path}")
        return archive_path
    
    async def cleanup_old_backups(self):
        """Remove old backup files."""
        logger.info("Cleaning up old backups...")
        
        cutoff_date = datetime.now() - timedelta(days=self.retention_days)
        removed_count = 0
        
        for backup_file in self.backup_dir.glob("*.tar.gz"):
            if backup_file.stat().st_mtime < cutoff_date.timestamp():
                try:
                    backup_file.unlink()
                    removed_count += 1
                    logger.info(f"Removed old backup: {backup_file.name}")
                except Exception as e:
                    logger.error(f"Failed to remove {backup_file.name}: {e}")
        
        if removed_count > 0:
            logger.info(f"Removed {removed_count} old backup files")
        else:
            logger.info("No old backups to remove")
    
    async def upload_to_storage(self, archive_path: Path) -> bool:
        """Upload backup to configured storage."""
        storage_type = self.storage_config.get("type", "local")
        
        if storage_type == "local":
            # Already stored locally, nothing to do
            return True
        elif storage_type == "s3":
            return await self._upload_to_s3(archive_path)
        else:
            logger.warning(f"Unsupported storage type: {storage_type}")
            return False
    
    async def _upload_to_s3(self, archive_path: Path) -> bool:
        """Upload backup to S3."""
        try:
            import boto3
            from botocore.exceptions import ClientError
            
            s3_config = self.storage_config
            bucket = s3_config.get("bucket")
            key_prefix = s3_config.get("key_prefix", "wakedock-backups/")
            
            if not bucket:
                logger.error("S3 bucket not configured")
                return False
            
            s3_client = boto3.client('s3')
            s3_key = f"{key_prefix}{archive_path.name}"
            
            logger.info(f"Uploading to S3: s3://{bucket}/{s3_key}")
            
            s3_client.upload_file(
                str(archive_path),
                bucket,
                s3_key,
                ExtraArgs={
                    'StorageClass': s3_config.get('storage_class', 'STANDARD'),
                    'ServerSideEncryption': 'AES256'
                }
            )
            
            logger.info("Backup uploaded to S3 successfully")
            return True
            
        except ImportError:
            logger.error("boto3 not installed. Install with: pip install boto3")
            return False
        except ClientError as e:
            logger.error(f"S3 upload failed: {e}")
            return False
        except Exception as e:
            logger.error(f"S3 upload error: {e}")
            return False
    
    async def run_backup(self, backup_name: str = "wakedock") -> bool:
        """Run complete backup process."""
        try:
            logger.info("Starting WakeDock backup process...")
            
            # Backup database
            db_backup = await self.backup_database()
            
            # Backup configurations
            config_backup = await self.backup_configurations()
            
            # Backup application data
            data_backup = await self.backup_data()
            
            # Create archive
            archive_path = await self.create_backup_archive(backup_name)
            
            # Upload to storage
            upload_success = await self.upload_to_storage(archive_path)
            
            # Cleanup old backups
            await self.cleanup_old_backups()
            
            # Calculate archive size
            archive_size = archive_path.stat().st_size / (1024 * 1024)  # MB
            
            logger.info(f"Backup completed successfully!")
            logger.info(f"Archive: {archive_path.name} ({archive_size:.1f} MB)")
            logger.info(f"Upload: {'Success' if upload_success else 'Failed'}")
            
            return True
            
        except Exception as e:
            logger.error(f"Backup failed: {e}")
            return False
        
        finally:
            # Cleanup temporary directory
            if self.temp_dir.exists():
                shutil.rmtree(self.temp_dir)
    
    def list_backups(self) -> List[Dict]:
        """List available backups."""
        backups = []
        
        for backup_file in sorted(self.backup_dir.glob("*.tar.gz")):
            stat = backup_file.stat()
            backups.append({
                "name": backup_file.name,
                "path": str(backup_file),
                "size": stat.st_size,
                "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
            })
        
        return backups


async def main():
    """Main backup script entry point."""
    parser = argparse.ArgumentParser(description="WakeDock Backup Tool")
    parser.add_argument(
        "--config",
        "-c",
        help="Path to WakeDock configuration file",
        default="/app/config/config.yml"
    )
    parser.add_argument(
        "--name",
        "-n",
        help="Backup name prefix",
        default="wakedock"
    )
    parser.add_argument(
        "--list",
        "-l",
        action="store_true",
        help="List available backups"
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
    
    # Create backup manager
    backup_manager = BackupManager(config_path=args.config)
    
    if args.list:
        # List backups
        backups = backup_manager.list_backups()
        
        if not backups:
            print("No backups found.")
            return
        
        print(f"{'Name':<30} {'Size':<10} {'Created':<20}")
        print("-" * 65)
        
        for backup in backups:
            size_mb = backup['size'] / (1024 * 1024)
            created = datetime.fromisoformat(backup['created']).strftime('%Y-%m-%d %H:%M')
            print(f"{backup['name']:<30} {size_mb:>7.1f} MB {created:<20}")
    else:
        # Run backup
        success = await backup_manager.run_backup(args.name)
        exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
