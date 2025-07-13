"""
Backup Service for WakeDock maintenance operations
"""

import os
import shutil
import tempfile
import tarfile
import gzip
import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from pathlib import Path
from uuid import uuid4

from wakedock.config import get_settings
from wakedock.core.orchestrator import DockerOrchestrator


class BackupService:
    """Service for creating and managing system backups"""
    
    def __init__(self, orchestrator: Optional[DockerOrchestrator] = None):
        self.orchestrator = orchestrator
        self.settings = get_settings()
        self.backup_dir = Path("/app/backups")
        self.backup_dir.mkdir(exist_ok=True)
    
    async def create_backup(
        self,
        backup_type: str = "full",
        include_volumes: bool = True,
        include_config: bool = True,
        include_database: bool = True,
        compression: bool = True
    ) -> Dict[str, Any]:
        """Create a new backup"""
        
        backup_id = str(uuid4())
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"wakedock_backup_{timestamp}_{backup_id[:8]}"
        
        temp_dir = Path(tempfile.mkdtemp(prefix="wakedock_backup_"))
        
        try:
            backup_metadata = {
                "id": backup_id,
                "name": backup_name,
                "type": backup_type,
                "created_at": datetime.now().isoformat(),
                "version": "1.0.0",
                "components": []
            }
            
            # Create database backup
            if include_database and backup_type in ["full", "database"]:
                await self._backup_database(temp_dir)
                backup_metadata["components"].append("database")
            
            # Create configuration backup
            if include_config and backup_type in ["full", "config"]:
                await self._backup_configuration(temp_dir)
                backup_metadata["components"].append("configuration")
            
            # Create volumes backup
            if include_volumes and backup_type in ["full", "volumes"]:
                await self._backup_volumes(temp_dir)
                backup_metadata["components"].append("volumes")
            
            # Save metadata
            metadata_file = temp_dir / "backup_info.json"
            with open(metadata_file, "w") as f:
                json.dump(backup_metadata, f, indent=2)
            
            # Create archive
            archive_path = self.backup_dir / f"{backup_name}.tar.gz"
            await self._create_archive(temp_dir, archive_path, compression)
            
            # Calculate size
            archive_size = archive_path.stat().st_size
            
            return {
                "id": backup_id,
                "name": backup_name,
                "type": backup_type,
                "size": archive_size,
                "created_at": datetime.now(),
                "status": "completed",
                "file_path": str(archive_path),
                "metadata": backup_metadata
            }
            
        finally:
            # Cleanup temporary directory
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    async def _backup_database(self, backup_dir: Path):
        """Backup database"""
        try:
            if self.orchestrator:
                # Use docker-compose to backup database
                cmd = [
                    "docker-compose", "-f", "docker-compose.yml",
                    "exec", "-T", "db", 
                    "pg_dump", "-U", "wakedock", "-d", "wakedock"
                ]
                
                proc = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                
                stdout, stderr = await proc.communicate()
                
                if proc.returncode == 0:
                    db_backup_file = backup_dir / "database_backup.sql"
                    with open(db_backup_file, "wb") as f:
                        f.write(stdout)
                    
                    # Compress database backup
                    with open(db_backup_file, "rb") as f_in:
                        with gzip.open(f"{db_backup_file}.gz", "wb") as f_out:
                            shutil.copyfileobj(f_in, f_out)
                    
                    # Remove uncompressed file
                    db_backup_file.unlink()
                else:
                    raise Exception(f"Database backup failed: {stderr.decode()}")
                    
        except Exception as e:
            raise Exception(f"Failed to backup database: {str(e)}")
    
    async def _backup_configuration(self, backup_dir: Path):
        """Backup configuration files"""
        config_backup_dir = backup_dir / "config"
        config_backup_dir.mkdir(exist_ok=True)
        
        # List of important config files/directories
        config_paths = [
            "/app/config",
            "/app/.env",
            "/app/docker-compose.yml",
            "/app/docker-compose.prod.yml",
            "/app/caddy"
        ]
        
        for config_path in config_paths:
            source_path = Path(config_path)
            if source_path.exists():
                try:
                    if source_path.is_file():
                        shutil.copy2(source_path, config_backup_dir / source_path.name)
                    elif source_path.is_dir():
                        dest_dir = config_backup_dir / source_path.name
                        shutil.copytree(source_path, dest_dir, dirs_exist_ok=True)
                except Exception as e:
                    print(f"Warning: Failed to backup {config_path}: {e}")
    
    async def _backup_volumes(self, backup_dir: Path):
        """Backup Docker volumes"""
        volumes_backup_dir = backup_dir / "volumes"
        volumes_backup_dir.mkdir(exist_ok=True)
        
        try:
            if self.orchestrator:
                # Get list of volumes
                proc = await asyncio.create_subprocess_exec(
                    "docker", "volume", "ls", "--format", "{{.Name}}",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                
                stdout, stderr = await proc.communicate()
                
                if proc.returncode == 0:
                    volumes = stdout.decode().strip().split('\n')
                    volumes = [v for v in volumes if v and 'wakedock' in v]
                    
                    for volume in volumes:
                        volume_backup_file = volumes_backup_dir / f"{volume}.tar.gz"
                        
                        # Create volume backup using docker
                        cmd = [
                            "docker", "run", "--rm",
                            "-v", f"{volume}:/data:ro",
                            "-v", f"{volumes_backup_dir}:/backup",
                            "alpine:latest",
                            "tar", "-czf", f"/backup/{volume}.tar.gz", "-C", "/data", "."
                        ]
                        
                        proc = await asyncio.create_subprocess_exec(*cmd)
                        await proc.communicate()
                        
        except Exception as e:
            print(f"Warning: Failed to backup volumes: {e}")
    
    async def _create_archive(self, source_dir: Path, archive_path: Path, compression: bool = True):
        """Create backup archive"""
        if compression:
            with tarfile.open(archive_path, "w:gz") as tar:
                tar.add(source_dir, arcname=".")
        else:
            with tarfile.open(archive_path.with_suffix(".tar"), "w") as tar:
                tar.add(source_dir, arcname=".")
    
    async def list_backups(self) -> List[Dict[str, Any]]:
        """List all available backups"""
        backups = []
        
        for backup_file in self.backup_dir.glob("wakedock_backup_*.tar.gz"):
            try:
                # Extract metadata from archive
                with tarfile.open(backup_file, "r:gz") as tar:
                    metadata_member = tar.getmember("backup_info.json")
                    metadata_file = tar.extractfile(metadata_member)
                    if metadata_file:
                        metadata = json.load(metadata_file)
                        
                        backup_info = {
                            "id": metadata.get("id"),
                            "name": metadata.get("name"),
                            "type": metadata.get("type"),
                            "size": backup_file.stat().st_size,
                            "created_at": datetime.fromisoformat(metadata.get("created_at")),
                            "status": "available",
                            "file_path": str(backup_file),
                            "metadata": metadata
                        }
                        backups.append(backup_info)
                        
            except Exception as e:
                print(f"Warning: Failed to read backup metadata from {backup_file}: {e}")
        
        # Sort by creation date, newest first
        backups.sort(key=lambda x: x["created_at"], reverse=True)
        return backups
    
    async def delete_backup(self, backup_id: str):
        """Delete a specific backup"""
        backups = await self.list_backups()
        backup_to_delete = None
        
        for backup in backups:
            if backup["id"] == backup_id:
                backup_to_delete = backup
                break
        
        if not backup_to_delete:
            raise ValueError(f"Backup with ID {backup_id} not found")
        
        backup_file = Path(backup_to_delete["file_path"])
        if backup_file.exists():
            backup_file.unlink()
        else:
            raise FileNotFoundError(f"Backup file {backup_file} not found")
    
    async def restore_backup(self, backup_file, options: Dict[str, Any]) -> Dict[str, Any]:
        """Restore from backup file"""
        temp_dir = Path(tempfile.mkdtemp(prefix="wakedock_restore_"))
        
        try:
            # Extract backup
            if hasattr(backup_file, 'file'):
                # Handle UploadFile
                temp_backup_path = temp_dir / "backup.tar.gz"
                with open(temp_backup_path, "wb") as f:
                    content = await backup_file.read()
                    f.write(content)
                backup_path = temp_backup_path
            else:
                backup_path = Path(backup_file)
            
            extract_dir = temp_dir / "extracted"
            extract_dir.mkdir(exist_ok=True)
            
            with tarfile.open(backup_path, "r:gz") as tar:
                tar.extractall(extract_dir)
            
            # Read metadata
            metadata_file = extract_dir / "backup_info.json"
            if metadata_file.exists():
                with open(metadata_file) as f:
                    metadata = json.load(f)
            else:
                metadata = {}
            
            restore_results = {}
            
            # Restore database
            if not options.get("config_only") and (extract_dir / "database_backup.sql.gz").exists():
                if options.get("database_only") or not options.get("config_only"):
                    await self._restore_database(extract_dir)
                    restore_results["database"] = "restored"
            
            # Restore configuration
            if not options.get("database_only") and (extract_dir / "config").exists():
                if options.get("config_only") or not options.get("database_only"):
                    await self._restore_configuration(extract_dir)
                    restore_results["configuration"] = "restored"
            
            # Restore volumes
            if not options.get("database_only") and not options.get("config_only"):
                if (extract_dir / "volumes").exists():
                    await self._restore_volumes(extract_dir)
                    restore_results["volumes"] = "restored"
            
            return {
                "metadata": metadata,
                "restored_components": restore_results,
                "timestamp": datetime.now().isoformat()
            }
            
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    async def _restore_database(self, restore_dir: Path):
        """Restore database from backup"""
        db_backup_file = restore_dir / "database_backup.sql.gz"
        
        if not db_backup_file.exists():
            raise FileNotFoundError("Database backup file not found")
        
        try:
            # Decompress and restore
            with gzip.open(db_backup_file, "rb") as f_in:
                sql_content = f_in.read()
            
            # Use docker-compose to restore database
            cmd = [
                "docker-compose", "-f", "docker-compose.yml",
                "exec", "-T", "db",
                "psql", "-U", "wakedock", "-d", "wakedock"
            ]
            
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await proc.communicate(input=sql_content)
            
            if proc.returncode != 0:
                raise Exception(f"Database restore failed: {stderr.decode()}")
                
        except Exception as e:
            raise Exception(f"Failed to restore database: {str(e)}")
    
    async def _restore_configuration(self, restore_dir: Path):
        """Restore configuration files"""
        config_dir = restore_dir / "config"
        
        if not config_dir.exists():
            return
        
        # Restore config files
        for item in config_dir.iterdir():
            dest_path = Path("/app") / item.name
            
            try:
                if item.is_file():
                    # Backup existing file
                    if dest_path.exists():
                        backup_path = Path(f"{dest_path}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}")
                        shutil.copy2(dest_path, backup_path)
                    
                    shutil.copy2(item, dest_path)
                    
                elif item.is_dir():
                    # Backup existing directory
                    if dest_path.exists():
                        backup_path = Path(f"{dest_path}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}")
                        shutil.copytree(dest_path, backup_path, dirs_exist_ok=True)
                        shutil.rmtree(dest_path)
                    
                    shutil.copytree(item, dest_path, dirs_exist_ok=True)
                    
            except Exception as e:
                print(f"Warning: Failed to restore {item}: {e}")
    
    async def _restore_volumes(self, restore_dir: Path):
        """Restore Docker volumes"""
        volumes_dir = restore_dir / "volumes"
        
        if not volumes_dir.exists():
            return
        
        for volume_backup in volumes_dir.glob("*.tar.gz"):
            volume_name = volume_backup.stem.replace(".tar", "")
            
            try:
                # Remove existing volume
                proc = await asyncio.create_subprocess_exec(
                    "docker", "volume", "rm", volume_name,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                await proc.communicate()
                
                # Create new volume
                proc = await asyncio.create_subprocess_exec(
                    "docker", "volume", "create", volume_name
                )
                await proc.communicate()
                
                # Restore volume data
                cmd = [
                    "docker", "run", "--rm",
                    "-v", f"{volume_name}:/restore",
                    "-v", f"{volume_backup}:/backup.tar.gz:ro",
                    "alpine:latest",
                    "sh", "-c", "cd /restore && tar -xzf /backup.tar.gz"
                ]
                
                proc = await asyncio.create_subprocess_exec(*cmd)
                await proc.communicate()
                
            except Exception as e:
                print(f"Warning: Failed to restore volume {volume_name}: {e}")
    
    async def cleanup_old_backups(self, retain_days: int = 7):
        """Clean up old backups"""
        cutoff_date = datetime.now() - timedelta(days=retain_days)
        
        backups = await self.list_backups()
        deleted_count = 0
        
        for backup in backups:
            if backup["created_at"] < cutoff_date:
                try:
                    await self.delete_backup(backup["id"])
                    deleted_count += 1
                except Exception as e:
                    print(f"Warning: Failed to delete old backup {backup['id']}: {e}")
        
        return {
            "deleted_count": deleted_count,
            "cutoff_date": cutoff_date.isoformat()
        }
