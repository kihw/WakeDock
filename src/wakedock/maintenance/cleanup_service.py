"""
Cleanup Service for WakeDock maintenance operations
"""

import asyncio
import shutil
import os
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from pathlib import Path

from wakedock.config import get_settings
from wakedock.core.orchestrator import DockerOrchestrator
from wakedock.utils.formatting import FormattingUtils


class CleanupService:
    """Service for cleaning up system resources"""
    
    def __init__(self, orchestrator: Optional[DockerOrchestrator] = None):
        self.orchestrator = orchestrator
        self.settings = get_settings()
        self.app_root = Path("/app")
        self._cleanup_running = False
        self._last_cleanup = None
    
    async def cleanup_docker_resources(self, options: Dict[str, Any]) -> Dict[str, Any]:
        """Clean up Docker resources"""
        
        # Mark cleanup as running
        self._cleanup_running = True
        
        try:
            results = {
                "timestamp": datetime.now().isoformat(),
                "cleanup_type": "docker_resources",
                "summary": {},
                "details": {},
                "errors": []
            }
        
            # Clean unused containers
            if options.get("containers", True):
                containers_result = await self._cleanup_docker_containers(options.get("force", False))
                results["details"]["containers"] = containers_result
                if containers_result.get("error"):
                    results["errors"].append(containers_result["error"])
             # Clean unused images
            if options.get("images", True):
                images_result = await self._cleanup_docker_images(options.get("force", False))
                results["details"]["images"] = images_result                
                if images_result.get("error"):
                    results["errors"].append(images_result["error"])
        
            # Clean unused volumes
            if options.get("volumes", False):  # Conservative default
                volumes_result = await self._cleanup_docker_volumes(options.get("force", False))
                results["details"]["volumes"] = volumes_result
                if volumes_result.get("error"):
                    results["errors"].append(volumes_result["error"])
            
            # Clean unused networks
            if options.get("networks", True):
                networks_result = await self._cleanup_docker_networks()
                results["details"]["networks"] = networks_result
                if networks_result.get("error"):
                    results["errors"].append(networks_result["error"])
            
            # Clean build cache
            if options.get("build_cache", True):
                cache_result = await self._cleanup_docker_build_cache()
                results["details"]["build_cache"] = cache_result
                if cache_result.get("error"):
                    results["errors"].append(cache_result["error"])
                     # Calculate total space reclaimed
            total_space = 0
            for detail in results["details"].values():
                if isinstance(detail, dict) and "space_reclaimed" in detail:
                    space_str = detail["space_reclaimed"]
                    try:
                        # Parse space string like "1.2GB" or "500MB"
                        if "GB" in space_str:
                            space_gb = float(space_str.replace("GB", "").strip())
                            total_space += space_gb * 1024 * 1024 * 1024
                        elif "MB" in space_str:
                            space_mb = float(space_str.replace("MB", "").strip())
                            total_space += space_mb * 1024 * 1024
                        elif "KB" in space_str:
                            space_kb = float(space_str.replace("KB", "").strip())
                            total_space += space_kb * 1024
                    except ValueError:
                        pass
        
            results["summary"]["total_space_reclaimed"] = FormattingUtils.format_bytes(total_space)
            results["summary"]["errors_count"] = len(results["errors"])
            results["summary"]["status"] = "error" if results["errors"] else "success"
            
            # Update last cleanup time
            self._last_cleanup = datetime.now()
            
            return results
            
        finally:
            # Mark cleanup as completed
            self._cleanup_running = False
    
    async def _cleanup_docker_containers(self, force: bool = False) -> Dict[str, Any]:
        """Clean up Docker containers"""
        
        try:
            # Get list of stopped containers
            cmd = ["docker", "container", "ls", "-a", "--filter", "status=exited", "--format", "{{.ID}}"]
            
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await proc.communicate()
            
            if proc.returncode != 0:
                return {"error": f"Failed to list containers: {stderr.decode()}"}
            
            container_ids = stdout.decode().strip().split('\n')
            container_ids = [cid for cid in container_ids if cid.strip()]
            
            if not container_ids:
                return {
                    "status": "success",
                    "removed_count": 0,
                    "message": "No stopped containers to remove"
                }
            
            # Remove stopped containers
            if force:
                remove_cmd = ["docker", "container", "rm", "-f"] + container_ids
            else:
                remove_cmd = ["docker", "container", "rm"] + container_ids
            
            proc = await asyncio.create_subprocess_exec(
                *remove_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await proc.communicate()
            
            if proc.returncode == 0:
                return {
                    "status": "success",
                    "removed_count": len(container_ids),
                    "removed_containers": container_ids
                }
            else:
                return {"error": f"Failed to remove containers: {stderr.decode()}"}
                
        except Exception as e:
            return {"error": f"Container cleanup failed: {str(e)}"}
    
    async def _cleanup_docker_images(self, force: bool = False) -> Dict[str, Any]:
        """Clean up Docker images"""
        
        try:
            # Remove dangling images
            cmd = ["docker", "image", "prune", "-f"]
            if force:
                cmd = ["docker", "image", "prune", "-a", "-f"]
            
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await proc.communicate()
            
            if proc.returncode == 0:
                output = stdout.decode()
                
                # Parse output for space reclaimed
                space_reclaimed = "0B"
                for line in output.split('\n'):
                    if "Total reclaimed space:" in line:
                        space_reclaimed = line.split(":")[-1].strip()
                        break
                
                return {
                    "status": "success",
                    "space_reclaimed": space_reclaimed,
                    "output": output
                }
            else:
                return {"error": f"Failed to prune images: {stderr.decode()}"}
                
        except Exception as e:
            return {"error": f"Image cleanup failed: {str(e)}"}
    
    async def _cleanup_docker_volumes(self, force: bool = False) -> Dict[str, Any]:
        """Clean up Docker volumes"""
        
        try:
            # Only remove unused volumes (not mounted by any container)
            cmd = ["docker", "volume", "prune", "-f"]
            
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await proc.communicate()
            
            if proc.returncode == 0:
                output = stdout.decode()
                
                # Parse output for space reclaimed
                space_reclaimed = "0B"
                for line in output.split('\n'):
                    if "Total reclaimed space:" in line:
                        space_reclaimed = line.split(":")[-1].strip()
                        break
                
                return {
                    "status": "success",
                    "space_reclaimed": space_reclaimed,
                    "output": output,
                    "warning": "Only unused volumes were removed"
                }
            else:
                return {"error": f"Failed to prune volumes: {stderr.decode()}"}
                
        except Exception as e:
            return {"error": f"Volume cleanup failed: {str(e)}"}
    
    async def _cleanup_docker_networks(self) -> Dict[str, Any]:
        """Clean up Docker networks"""
        
        try:
            cmd = ["docker", "network", "prune", "-f"]
            
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await proc.communicate()
            
            if proc.returncode == 0:
                output = stdout.decode()
                
                return {
                    "status": "success",
                    "output": output
                }
            else:
                return {"error": f"Failed to prune networks: {stderr.decode()}"}
                
        except Exception as e:
            return {"error": f"Network cleanup failed: {str(e)}"}
    
    async def _cleanup_docker_build_cache(self) -> Dict[str, Any]:
        """Clean up Docker build cache"""
        
        try:
            cmd = ["docker", "builder", "prune", "-f"]
            
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await proc.communicate()
            
            if proc.returncode == 0:
                output = stdout.decode()
                
                # Parse output for space reclaimed
                space_reclaimed = "0B"
                for line in output.split('\n'):
                    if "Total:" in line:
                        space_reclaimed = line.split()[-1].strip()
                        break
                
                return {
                    "status": "success",
                    "space_reclaimed": space_reclaimed,
                    "output": output
                }
            else:
                return {"error": f"Failed to prune build cache: {stderr.decode()}"}
                
        except Exception as e:
            return {"error": f"Build cache cleanup failed: {str(e)}"}
    
    async def cleanup_logs(self, options: Dict[str, Any]) -> Dict[str, Any]:
        """Clean up log files"""
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "cleanup_type": "logs",
            "summary": {},
            "details": {},
            "errors": []
        }
        
        # Clean application logs
        if options.get("app_logs", True):
            app_logs_result = await self._cleanup_app_logs(options.get("days_to_keep", 7))
            results["details"]["app_logs"] = app_logs_result
            if app_logs_result.get("error"):
                results["errors"].append(app_logs_result["error"])
        
        # Clean Docker logs
        if options.get("docker_logs", True):
            docker_logs_result = await self._cleanup_docker_logs()
            results["details"]["docker_logs"] = docker_logs_result
            if docker_logs_result.get("error"):
                results["errors"].append(docker_logs_result["error"])
        
        # Clean system logs (if accessible)
        if options.get("system_logs", False):
            system_logs_result = await self._cleanup_system_logs(options.get("days_to_keep", 7))
            results["details"]["system_logs"] = system_logs_result
            if system_logs_result.get("error"):
                results["errors"].append(system_logs_result["error"])
        
        # Calculate total space reclaimed
        total_space = 0
        for detail in results["details"].values():
            if isinstance(detail, dict) and "space_reclaimed_bytes" in detail:
                total_space += detail["space_reclaimed_bytes"]
        
        results["summary"]["total_space_reclaimed"] = FormattingUtils.format_bytes(total_space)
        results["summary"]["errors_count"] = len(results["errors"])
        results["summary"]["status"] = "error" if results["errors"] else "success"
        
        return results
    
    async def _cleanup_app_logs(self, days_to_keep: int) -> Dict[str, Any]:
        """Clean up application log files"""
        
        try:
            log_dirs = [
                self.app_root / "logs",
                Path("/var/log/wakedock"),
                Path("/app/logs")
            ]
            
            total_size_removed = 0
            files_removed = 0
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            
            for log_dir in log_dirs:
                if not log_dir.exists():
                    continue
                
                for log_file in log_dir.rglob("*.log*"):
                    try:
                        file_stat = log_file.stat()
                        file_modified = datetime.fromtimestamp(file_stat.st_mtime)
                        
                        if file_modified < cutoff_date:
                            file_size = file_stat.st_size
                            log_file.unlink()
                            total_size_removed += file_size
                            files_removed += 1
                            
                    except Exception as e:
                        continue
            
            return {
                "status": "success",
                "files_removed": files_removed,
                "space_reclaimed_bytes": total_size_removed,
                "space_reclaimed": FormattingUtils.format_bytes(total_size_removed),
                "days_to_keep": days_to_keep
            }
            
        except Exception as e:
            return {"error": f"App logs cleanup failed: {str(e)}"}
    
    async def _cleanup_docker_logs(self) -> Dict[str, Any]:
        """Clean up Docker container logs"""
        
        try:
            # Get list of containers
            proc = await asyncio.create_subprocess_exec(
                "docker", "container", "ls", "-a", "--format", "{{.ID}}",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await proc.communicate()
            
            if proc.returncode != 0:
                return {"error": f"Failed to list containers: {stderr.decode()}"}
            
            container_ids = stdout.decode().strip().split('\n')
            container_ids = [cid for cid in container_ids if cid.strip()]
            
            logs_truncated = 0
            total_size_before = 0
            total_size_after = 0
            
            for container_id in container_ids:
                try:
                    # Get log file path
                    inspect_proc = await asyncio.create_subprocess_exec(
                        "docker", "inspect", container_id, "--format", "{{.LogPath}}",
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )
                    
                    inspect_stdout, _ = await inspect_proc.communicate()
                    
                    if inspect_proc.returncode == 0:
                        log_path = Path(inspect_stdout.decode().strip())
                        
                        if log_path.exists():
                            size_before = log_path.stat().st_size
                            total_size_before += size_before
                            
                            # Truncate log file (keep last 1000 lines)
                            with open(log_path, 'r') as f:
                                lines = f.readlines()
                            
                            if len(lines) > 1000:
                                with open(log_path, 'w') as f:
                                    f.writelines(lines[-1000:])
                                
                                size_after = log_path.stat().st_size
                                total_size_after += size_after
                                logs_truncated += 1
                            else:
                                total_size_after += size_before
                                
                except Exception:
                    continue
            
            space_reclaimed = total_size_before - total_size_after
            
            return {
                "status": "success",
                "logs_truncated": logs_truncated,
                "space_reclaimed_bytes": space_reclaimed,
                "space_reclaimed": FormattingUtils.format_bytes(space_reclaimed)
            }
            
        except Exception as e:
            return {"error": f"Docker logs cleanup failed: {str(e)}"}
    
    async def _cleanup_system_logs(self, days_to_keep: int) -> Dict[str, Any]:
        """Clean up system log files (if accessible)"""
        
        try:
            # Common system log directories
            system_log_dirs = [
                Path("/var/log"),
                Path("/tmp"),
                Path("/var/tmp")
            ]
            
            total_size_removed = 0
            files_removed = 0
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            
            for log_dir in system_log_dirs:
                if not log_dir.exists() or not os.access(log_dir, os.R_OK):
                    continue
                
                try:
                    for log_file in log_dir.glob("*.log*"):
                        if not os.access(log_file, os.W_OK):
                            continue
                        
                        try:
                            file_stat = log_file.stat()
                            file_modified = datetime.fromtimestamp(file_stat.st_mtime)
                            
                            if file_modified < cutoff_date:
                                file_size = file_stat.st_size
                                log_file.unlink()
                                total_size_removed += file_size
                                files_removed += 1
                                
                        except Exception:
                            continue
                            
                except Exception:
                    continue
            
            return {
                "status": "success",
                "files_removed": files_removed,
                "space_reclaimed_bytes": total_size_removed,
                "space_reclaimed": FormattingUtils.format_bytes(total_size_removed),
                "days_to_keep": days_to_keep
            }
            
        except Exception as e:
            return {"error": f"System logs cleanup failed: {str(e)}"}
    
    async def cleanup_temp_files(self, options: Dict[str, Any]) -> Dict[str, Any]:
        """Clean up temporary files"""
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "cleanup_type": "temp_files",
            "summary": {},
            "details": {},
            "errors": []
        }
        
        # Clean application temp files
        if options.get("app_temp", True):
            app_temp_result = await self._cleanup_app_temp_files(options.get("days_to_keep", 1))
            results["details"]["app_temp"] = app_temp_result
            if app_temp_result.get("error"):
                results["errors"].append(app_temp_result["error"])
        
        # Clean system temp files
        if options.get("system_temp", True):
            system_temp_result = await self._cleanup_system_temp_files(options.get("days_to_keep", 1))
            results["details"]["system_temp"] = system_temp_result
            if system_temp_result.get("error"):
                results["errors"].append(system_temp_result["error"])
        
        # Clean Python cache files
        if options.get("python_cache", True):
            python_cache_result = await self._cleanup_python_cache()
            results["details"]["python_cache"] = python_cache_result
            if python_cache_result.get("error"):
                results["errors"].append(python_cache_result["error"])
        
        # Calculate total space reclaimed
        total_space = 0
        for detail in results["details"].values():
            if isinstance(detail, dict) and "space_reclaimed_bytes" in detail:
                total_space += detail["space_reclaimed_bytes"]
        
        results["summary"]["total_space_reclaimed"] = FormattingUtils.format_bytes(total_space)
        results["summary"]["errors_count"] = len(results["errors"])
        results["summary"]["status"] = "error" if results["errors"] else "success"
        
        return results
    
    async def _cleanup_app_temp_files(self, days_to_keep: int) -> Dict[str, Any]:
        """Clean up application temporary files"""
        
        try:
            temp_dirs = [
                self.app_root / "tmp",
                self.app_root / "temp",
                self.app_root / "cache",
                Path("/tmp/wakedock")
            ]
            
            total_size_removed = 0
            files_removed = 0
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            
            for temp_dir in temp_dirs:
                if not temp_dir.exists():
                    continue
                
                for item in temp_dir.rglob("*"):
                    if item.is_file():
                        try:
                            file_stat = item.stat()
                            file_modified = datetime.fromtimestamp(file_stat.st_mtime)
                            
                            if file_modified < cutoff_date:
                                file_size = file_stat.st_size
                                item.unlink()
                                total_size_removed += file_size
                                files_removed += 1
                                
                        except Exception:
                            continue
            
            return {
                "status": "success",
                "files_removed": files_removed,
                "space_reclaimed_bytes": total_size_removed,
                "space_reclaimed": FormattingUtils.format_bytes(total_size_removed),
                "days_to_keep": days_to_keep
            }
            
        except Exception as e:
            return {"error": f"App temp files cleanup failed: {str(e)}"}
    
    async def _cleanup_system_temp_files(self, days_to_keep: int) -> Dict[str, Any]:
        """Clean up system temporary files"""
        
        try:
            temp_dirs = [
                Path("/tmp"),
                Path("/var/tmp")
            ]
            
            total_size_removed = 0
            files_removed = 0
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            
            for temp_dir in temp_dirs:
                if not temp_dir.exists() or not os.access(temp_dir, os.R_OK):
                    continue
                
                try:
                    for item in temp_dir.iterdir():
                        if item.is_file() and os.access(item, os.W_OK):
                            try:
                                file_stat = item.stat()
                                file_modified = datetime.fromtimestamp(file_stat.st_mtime)
                                
                                if file_modified < cutoff_date and not item.name.startswith('.'):
                                    file_size = file_stat.st_size
                                    item.unlink()
                                    total_size_removed += file_size
                                    files_removed += 1
                                    
                            except Exception:
                                continue
                                
                except Exception:
                    continue
            
            return {
                "status": "success",
                "files_removed": files_removed,
                "space_reclaimed_bytes": total_size_removed,
                "space_reclaimed": FormattingUtils.format_bytes(total_size_removed),
                "days_to_keep": days_to_keep
            }
            
        except Exception as e:
            return {"error": f"System temp files cleanup failed: {str(e)}"}
    
    async def _cleanup_python_cache(self) -> Dict[str, Any]:
        """Clean up Python cache files"""
        
        try:
            total_size_removed = 0
            files_removed = 0
            
            # Find and remove __pycache__ directories
            for pycache_dir in self.app_root.rglob("__pycache__"):
                try:
                    for pyc_file in pycache_dir.rglob("*.pyc"):
                        file_size = pyc_file.stat().st_size
                        pyc_file.unlink()
                        total_size_removed += file_size
                        files_removed += 1
                    
                    # Remove the __pycache__ directory if empty
                    if not any(pycache_dir.iterdir()):
                        pycache_dir.rmdir()
                        
                except Exception:
                    continue
            
            # Remove .pyc files
            for pyc_file in self.app_root.rglob("*.pyc"):
                try:
                    file_size = pyc_file.stat().st_size
                    pyc_file.unlink()
                    total_size_removed += file_size
                    files_removed += 1
                except Exception:
                    continue
            
            return {
                "status": "success",
                "files_removed": files_removed,
                "space_reclaimed_bytes": total_size_removed,
                "space_reclaimed": FormattingUtils.format_bytes(total_size_removed)
            }
            
        except Exception as e:
            return {"error": f"Python cache cleanup failed: {str(e)}"}
    
    # Removed _format_bytes method - now using centralized FormattingUtils.format_bytes()
    
    async def get_cleanup_recommendations(self) -> Dict[str, Any]:
        """Get cleanup recommendations based on system state"""
        
        recommendations = {
            "timestamp": datetime.now().isoformat(),
            "recommendations": [],
            "estimated_space_savings": {}
        }
        
        # Check disk space
        try:
            proc = await asyncio.create_subprocess_exec(
                "df", "-h", "/",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await proc.communicate()
            
            if proc.returncode == 0:
                lines = stdout.decode().strip().split('\n')
                if len(lines) >= 2:
                    parts = lines[1].split()
                    use_percent = int(parts[4].rstrip('%'))
                    
                    if use_percent > 80:
                        recommendations["recommendations"].append({
                            "type": "critical",
                            "message": f"Disk usage is {use_percent}% - immediate cleanup recommended",
                            "actions": ["docker_cleanup", "log_cleanup", "temp_cleanup"]
                        })
                    elif use_percent > 60:
                        recommendations["recommendations"].append({
                            "type": "warning",
                            "message": f"Disk usage is {use_percent}% - cleanup recommended",
                            "actions": ["docker_cleanup", "log_cleanup"]
                        })
        except Exception:
            pass
        
        # Check for old Docker images
        try:
            proc = await asyncio.create_subprocess_exec(
                "docker", "images", "--format", "table {{.Repository}}:{{.Tag}}\t{{.CreatedAt}}\t{{.Size}}",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await proc.communicate()
            
            if proc.returncode == 0:
                lines = stdout.decode().strip().split('\n')[1:]  # Skip header
                old_images = 0
                
                for line in lines:
                    parts = line.split('\t')
                    if len(parts) >= 2:
                        created_str = parts[1]
                        # Simple check for "weeks ago" or "months ago"
                        if "week" in created_str or "month" in created_str:
                            old_images += 1
                
                if old_images > 5:
                    recommendations["recommendations"].append({
                        "type": "maintenance",
                        "message": f"Found {old_images} old Docker images",
                        "actions": ["docker_image_cleanup"]
                    })
        except Exception:
            pass
        
        # Check log file sizes
        log_dirs = [Path("/var/log"), self.app_root / "logs"]
        total_log_size = 0
        
        for log_dir in log_dirs:
            if log_dir.exists():
                try:
                    for log_file in log_dir.rglob("*.log*"):
                        if log_file.is_file():
                            total_log_size += log_file.stat().st_size
                except Exception:
                    continue
        
        if total_log_size > 100 * 1024 * 1024:  # > 100MB
            recommendations["recommendations"].append({
                "type": "maintenance",
                "message": f"Log files are using {FormattingUtils.format_bytes(total_log_size)}",
                "actions": ["log_cleanup"]
            })
        
        return recommendations
    
    async def get_status(self) -> str:
        """Get current cleanup service status"""
        try:
            if self._cleanup_running:
                return "running"
            
            # Check if cleanup is needed based on system usage
            needs_cleanup = await self._check_cleanup_needed()
            
            if needs_cleanup:
                return "needed"
            else:
                return "healthy"
                
        except Exception:
            return "error"
    
    async def _check_cleanup_needed(self) -> bool:
        """Check if system cleanup is needed"""
        try:
            # Check disk space
            total, used, free = shutil.disk_usage("/")
            disk_usage_percent = (used / total) * 100
            
            # Check if disk usage is high (>80%)
            if disk_usage_percent > 80:
                return True
            
            # Check for old log files
            log_dirs = ["/app/logs", "/var/log"]
            for log_dir in log_dirs:
                if Path(log_dir).exists():
                    total_log_size = sum(
                        f.stat().st_size for f in Path(log_dir).rglob('*') 
                        if f.is_file()
                    ) / (1024 * 1024)  # MB
                    
                    # If logs exceed 500MB, cleanup needed
                    if total_log_size > 500:
                        return True
            
            # Check for Docker containers/images that could be cleaned
            if self.orchestrator:
                try:
                    client = self.orchestrator.client
                    
                    # Check for stopped containers
                    stopped_containers = client.containers.list(
                        all=True, 
                        filters={"status": "exited"}
                    )
                    if len(stopped_containers) > 5:
                        return True
                    
                    # Check for dangling images
                    dangling_images = client.images.list(
                        filters={"dangling": True}
                    )
                    if len(dangling_images) > 3:
                        return True
                        
                except Exception:
                    pass
            
            return False
            
        except Exception:
            return False
