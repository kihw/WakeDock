"""
Dependencies Service for WakeDock maintenance operations
"""

import subprocess
import asyncio
import json
import re
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime

from wakedock.config import get_settings


class DependenciesService:
    """Service for managing system dependencies"""
    
    def __init__(self):
        self.settings = get_settings()
        self.app_root = Path("/app")
    
    async def check_dependencies(self) -> Dict[str, Any]:
        """Check all system dependencies"""
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "overall_status": "healthy",
            "categories": {},
            "issues": []
        }
        
        # Check Docker dependencies
        docker_status = await self._check_docker_dependencies()
        results["categories"]["docker"] = docker_status
        
        # Check Python dependencies
        python_status = await self._check_python_dependencies()
        results["categories"]["python"] = python_status
        
        # Check Node.js dependencies (for dashboard)
        node_status = await self._check_node_dependencies()
        results["categories"]["node"] = node_status
        
        # Check system dependencies
        system_status = await self._check_system_dependencies()
        results["categories"]["system"] = system_status
        
        # Aggregate issues
        all_issues = []
        for category, status in results["categories"].items():
            if status.get("issues"):
                all_issues.extend(status["issues"])
        
        results["issues"] = all_issues
        
        # Determine overall status
        if any(category.get("status") == "error" for category in results["categories"].values()):
            results["overall_status"] = "error"
        elif any(category.get("status") == "warning" for category in results["categories"].values()):
            results["overall_status"] = "warning"
        
        return results
    
    async def _check_docker_dependencies(self) -> Dict[str, Any]:
        """Check Docker-related dependencies"""
        
        status = {
            "status": "healthy",
            "components": {},
            "issues": []
        }
        
        # Check Docker engine
        docker_engine = await self._check_command("docker --version")
        status["components"]["docker_engine"] = docker_engine
        
        # Check Docker Compose
        docker_compose = await self._check_command("docker-compose --version")
        status["components"]["docker_compose"] = docker_compose
        
        # Check running containers
        containers_status = await self._check_docker_containers()
        status["components"]["containers"] = containers_status
        
        # Check Docker volumes
        volumes_status = await self._check_docker_volumes()
        status["components"]["volumes"] = volumes_status
        
        # Check Docker networks
        networks_status = await self._check_docker_networks()
        status["components"]["networks"] = networks_status
        
        # Aggregate issues
        for component, comp_status in status["components"].items():
            if comp_status.get("issues"):
                status["issues"].extend(comp_status["issues"])
        
        # Determine status
        if any(comp.get("status") == "error" for comp in status["components"].values()):
            status["status"] = "error"
        elif any(comp.get("status") == "warning" for comp in status["components"].values()):
            status["status"] = "warning"
        
        return status
    
    async def _check_python_dependencies(self) -> Dict[str, Any]:
        """Check Python dependencies"""
        
        status = {
            "status": "healthy",
            "components": {},
            "issues": []
        }
        
        # Check Python version
        python_version = await self._check_command("python --version")
        status["components"]["python_version"] = python_version
        
        # Check pip packages
        pip_status = await self._check_pip_packages()
        status["components"]["pip_packages"] = pip_status
        
        # Check requirements.txt vs installed
        requirements_status = await self._check_requirements_sync()
        status["components"]["requirements_sync"] = requirements_status
        
        # Check for security vulnerabilities
        security_status = await self._check_python_security()
        status["components"]["security"] = security_status
        
        # Aggregate issues
        for component, comp_status in status["components"].items():
            if comp_status.get("issues"):
                status["issues"].extend(comp_status["issues"])
        
        # Determine status
        if any(comp.get("status") == "error" for comp in status["components"].values()):
            status["status"] = "error"
        elif any(comp.get("status") == "warning" for comp in status["components"].values()):
            status["status"] = "warning"
        
        return status
    
    async def _check_node_dependencies(self) -> Dict[str, Any]:
        """Check Node.js dependencies for dashboard"""
        
        status = {
            "status": "healthy",
            "components": {},
            "issues": []
        }
        
        dashboard_dir = self.app_root / "dashboard"
        
        if not dashboard_dir.exists():
            status["status"] = "error"
            status["issues"].append("Dashboard directory not found")
            return status
        
        # Check Node.js version
        node_version = await self._check_command("node --version", cwd=dashboard_dir)
        status["components"]["node_version"] = node_version
        
        # Check npm version
        npm_version = await self._check_command("npm --version", cwd=dashboard_dir)
        status["components"]["npm_version"] = npm_version
        
        # Check package.json vs node_modules
        packages_status = await self._check_npm_packages(dashboard_dir)
        status["components"]["npm_packages"] = packages_status
        
        # Check for security vulnerabilities
        npm_audit = await self._check_npm_security(dashboard_dir)
        status["components"]["security"] = npm_audit
        
        # Aggregate issues
        for component, comp_status in status["components"].items():
            if comp_status.get("issues"):
                status["issues"].extend(comp_status["issues"])
        
        # Determine status
        if any(comp.get("status") == "error" for comp in status["components"].values()):
            status["status"] = "error"
        elif any(comp.get("status") == "warning" for comp in status["components"].values()):
            status["status"] = "warning"
        
        return status
    
    async def _check_system_dependencies(self) -> Dict[str, Any]:
        """Check system-level dependencies"""
        
        status = {
            "status": "healthy",
            "components": {},
            "issues": []
        }
        
        # Check required system commands
        system_commands = ["curl", "tar", "gzip", "git"]
        
        for cmd in system_commands:
            cmd_status = await self._check_command(f"which {cmd}")
            status["components"][f"command_{cmd}"] = cmd_status
        
        # Check disk space
        disk_status = await self._check_disk_space()
        status["components"]["disk_space"] = disk_status
        
        # Check memory usage
        memory_status = await self._check_memory_usage()
        status["components"]["memory"] = memory_status
        
        # Aggregate issues
        for component, comp_status in status["components"].items():
            if comp_status.get("issues"):
                status["issues"].extend(comp_status["issues"])
        
        # Determine status
        if any(comp.get("status") == "error" for comp in status["components"].values()):
            status["status"] = "error"
        elif any(comp.get("status") == "warning" for comp in status["components"].values()):
            status["status"] = "warning"
        
        return status
    
    async def _check_command(self, command: str, cwd: Optional[Path] = None) -> Dict[str, Any]:
        """Check if a command exists and works"""
        
        try:
            proc = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd
            )
            
            stdout, stderr = await proc.communicate()
            
            if proc.returncode == 0:
                return {
                    "status": "healthy",
                    "output": stdout.decode().strip(),
                    "issues": []
                }
            else:
                return {
                    "status": "error",
                    "output": stderr.decode().strip(),
                    "issues": [f"Command '{command}' failed with exit code {proc.returncode}"]
                }
                
        except Exception as e:
            return {
                "status": "error",
                "output": str(e),
                "issues": [f"Command '{command}' failed: {str(e)}"]
            }
    
    async def _check_docker_containers(self) -> Dict[str, Any]:
        """Check Docker containers status"""
        
        try:
            proc = await asyncio.create_subprocess_exec(
                "docker-compose", "-f", "docker-compose.yml", "ps", "--format", "json",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await proc.communicate()
            
            if proc.returncode == 0:
                containers_output = stdout.decode().strip()
                containers = []
                issues = []
                
                for line in containers_output.split('\n'):
                    if line.strip():
                        try:
                            container = json.loads(line)
                            containers.append(container)
                            
                            # Check if container is running
                            if container.get("State") != "running":
                                issues.append(f"Container {container.get('Name')} is not running: {container.get('State')}")
                                
                        except json.JSONDecodeError:
                            continue
                
                status = "error" if issues else "healthy"
                
                return {
                    "status": status,
                    "containers": containers,
                    "issues": issues
                }
            else:
                return {
                    "status": "error",
                    "containers": [],
                    "issues": [f"Failed to get container status: {stderr.decode()}"]
                }
                
        except Exception as e:
            return {
                "status": "error",
                "containers": [],
                "issues": [f"Failed to check containers: {str(e)}"]
            }
    
    async def _check_docker_volumes(self) -> Dict[str, Any]:
        """Check Docker volumes"""
        
        try:
            proc = await asyncio.create_subprocess_exec(
                "docker", "volume", "ls", "--format", "{{.Name}}",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await proc.communicate()
            
            if proc.returncode == 0:
                volumes = stdout.decode().strip().split('\n')
                wakedock_volumes = [v for v in volumes if v and 'wakedock' in v]
                
                return {
                    "status": "healthy",
                    "volumes": wakedock_volumes,
                    "count": len(wakedock_volumes),
                    "issues": []
                }
            else:
                return {
                    "status": "error",
                    "volumes": [],
                    "issues": [f"Failed to list volumes: {stderr.decode()}"]
                }
                
        except Exception as e:
            return {
                "status": "error",
                "volumes": [],
                "issues": [f"Failed to check volumes: {str(e)}"]
            }
    
    async def _check_docker_networks(self) -> Dict[str, Any]:
        """Check Docker networks"""
        
        try:
            proc = await asyncio.create_subprocess_exec(
                "docker", "network", "ls", "--format", "{{.Name}}",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await proc.communicate()
            
            if proc.returncode == 0:
                networks = stdout.decode().strip().split('\n')
                wakedock_networks = [n for n in networks if n and 'wakedock' in n]
                
                return {
                    "status": "healthy",
                    "networks": wakedock_networks,
                    "count": len(wakedock_networks),
                    "issues": []
                }
            else:
                return {
                    "status": "error",
                    "networks": [],
                    "issues": [f"Failed to list networks: {stderr.decode()}"]
                }
                
        except Exception as e:
            return {
                "status": "error",
                "networks": [],
                "issues": [f"Failed to check networks: {str(e)}"]
            }
    
    async def _check_pip_packages(self) -> Dict[str, Any]:
        """Check pip packages"""
        
        try:
            proc = await asyncio.create_subprocess_exec(
                "pip", "list", "--format=json",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await proc.communicate()
            
            if proc.returncode == 0:
                packages = json.loads(stdout.decode())
                
                return {
                    "status": "healthy",
                    "packages": packages,
                    "count": len(packages),
                    "issues": []
                }
            else:
                return {
                    "status": "error",
                    "packages": [],
                    "issues": [f"Failed to list pip packages: {stderr.decode()}"]
                }
                
        except Exception as e:
            return {
                "status": "error",
                "packages": [],
                "issues": [f"Failed to check pip packages: {str(e)}"]
            }
    
    async def _check_requirements_sync(self) -> Dict[str, Any]:
        """Check if installed packages match requirements.txt"""
        
        requirements_file = self.app_root / "requirements.txt"
        
        if not requirements_file.exists():
            return {
                "status": "warning",
                "sync_status": "no_requirements_file",
                "issues": ["requirements.txt not found"]
            }
        
        try:
            # Read requirements
            with open(requirements_file) as f:
                requirements = f.read().strip().split('\n')
            
            # Get installed packages
            pip_status = await self._check_pip_packages()
            if pip_status["status"] == "error":
                return pip_status
            
            installed_packages = {pkg["name"].lower(): pkg["version"] for pkg in pip_status["packages"]}
            
            missing_packages = []
            version_mismatches = []
            
            for req in requirements:
                req = req.strip()
                if not req or req.startswith('#'):
                    continue
                
                # Parse requirement
                match = re.match(r'^([a-zA-Z0-9_-]+)([>=<!=]+)?(.+)?', req)
                if not match:
                    continue
                
                package_name = match.group(1).lower()
                operator = match.group(2)
                required_version = match.group(3)
                
                if package_name not in installed_packages:
                    missing_packages.append(package_name)
                elif operator and required_version:
                    installed_version = installed_packages[package_name]
                    if operator == "==" and installed_version != required_version:
                        version_mismatches.append({
                            "package": package_name,
                            "required": required_version,
                            "installed": installed_version
                        })
            
            issues = []
            if missing_packages:
                issues.append(f"Missing packages: {', '.join(missing_packages)}")
            if version_mismatches:
                issues.extend([f"{vm['package']}: required {vm['required']}, installed {vm['installed']}" 
                              for vm in version_mismatches])
            
            status = "error" if missing_packages else ("warning" if version_mismatches else "healthy")
            
            return {
                "status": status,
                "sync_status": "synced" if not issues else "out_of_sync",
                "missing_packages": missing_packages,
                "version_mismatches": version_mismatches,
                "issues": issues
            }
            
        except Exception as e:
            return {
                "status": "error",
                "sync_status": "check_failed",
                "issues": [f"Failed to check requirements sync: {str(e)}"]
            }
    
    async def _check_python_security(self) -> Dict[str, Any]:
        """Check for Python security vulnerabilities"""
        
        try:
            proc = await asyncio.create_subprocess_exec(
                "pip", "install", "--dry-run", "--report", "-", ".",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await proc.communicate()
            
            # For now, just check if safety is available and use it
            safety_check = await self._check_command("safety check --json")
            
            if safety_check["status"] == "healthy":
                try:
                    safety_output = json.loads(safety_check["output"])
                    vulnerabilities = safety_output if isinstance(safety_output, list) else []
                    
                    status = "error" if vulnerabilities else "healthy"
                    issues = [f"Vulnerability in {vuln.get('package', 'unknown')}: {vuln.get('advisory', 'No details')}" 
                             for vuln in vulnerabilities]
                    
                    return {
                        "status": status,
                        "vulnerabilities": vulnerabilities,
                        "issues": issues
                    }
                except json.JSONDecodeError:
                    pass
            
            return {
                "status": "warning",
                "vulnerabilities": [],
                "issues": ["Safety tool not available for security scanning"]
            }
            
        except Exception as e:
            return {
                "status": "warning",
                "vulnerabilities": [],
                "issues": [f"Security check failed: {str(e)}"]
            }
    
    async def _check_npm_packages(self, dashboard_dir: Path) -> Dict[str, Any]:
        """Check npm packages in dashboard"""
        
        try:
            proc = await asyncio.create_subprocess_exec(
                "npm", "list", "--json",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=dashboard_dir
            )
            
            stdout, stderr = await proc.communicate()
            
            # npm list returns non-zero exit code even for warnings
            npm_output = json.loads(stdout.decode())
            
            issues = []
            if "problems" in npm_output:
                issues.extend(npm_output["problems"])
            
            status = "warning" if issues else "healthy"
            
            return {
                "status": status,
                "dependencies": npm_output.get("dependencies", {}),
                "issues": issues
            }
            
        except Exception as e:
            return {
                "status": "error",
                "dependencies": {},
                "issues": [f"Failed to check npm packages: {str(e)}"]
            }
    
    async def _check_npm_security(self, dashboard_dir: Path) -> Dict[str, Any]:
        """Check npm security vulnerabilities"""
        
        try:
            proc = await asyncio.create_subprocess_exec(
                "npm", "audit", "--json",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=dashboard_dir
            )
            
            stdout, stderr = await proc.communicate()
            
            try:
                audit_output = json.loads(stdout.decode())
                
                vulnerabilities = audit_output.get("vulnerabilities", {})
                metadata = audit_output.get("metadata", {})
                
                total_vulns = metadata.get("vulnerabilities", {}).get("total", 0)
                
                status = "error" if total_vulns > 0 else "healthy"
                issues = [f"Found {total_vulns} npm security vulnerabilities"] if total_vulns > 0 else []
                
                return {
                    "status": status,
                    "vulnerabilities": vulnerabilities,
                    "metadata": metadata,
                    "issues": issues
                }
                
            except json.JSONDecodeError:
                return {
                    "status": "warning",
                    "vulnerabilities": {},
                    "issues": ["Could not parse npm audit output"]
                }
                
        except Exception as e:
            return {
                "status": "warning",
                "vulnerabilities": {},
                "issues": [f"npm audit failed: {str(e)}"]
            }
    
    async def _check_disk_space(self) -> Dict[str, Any]:
        """Check disk space"""
        
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
                    # Parse df output
                    parts = lines[1].split()
                    filesystem = parts[0]
                    size = parts[1]
                    used = parts[2]
                    available = parts[3]
                    use_percent = parts[4]
                    
                    # Extract percentage as number
                    use_percent_num = int(use_percent.rstrip('%'))
                    
                    issues = []
                    status = "healthy"
                    
                    if use_percent_num > 90:
                        status = "error"
                        issues.append(f"Disk usage critically high: {use_percent}")
                    elif use_percent_num > 80:
                        status = "warning"
                        issues.append(f"Disk usage high: {use_percent}")
                    
                    return {
                        "status": status,
                        "filesystem": filesystem,
                        "size": size,
                        "used": used,
                        "available": available,
                        "use_percent": use_percent,
                        "issues": issues
                    }
            
            return {
                "status": "error",
                "issues": [f"Failed to check disk space: {stderr.decode()}"]
            }
            
        except Exception as e:
            return {
                "status": "error",
                "issues": [f"Failed to check disk space: {str(e)}"]
            }
    
    async def _check_memory_usage(self) -> Dict[str, Any]:
        """Check memory usage"""
        
        try:
            proc = await asyncio.create_subprocess_exec(
                "free", "-h",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await proc.communicate()
            
            if proc.returncode == 0:
                lines = stdout.decode().strip().split('\n')
                
                # Parse memory line
                for line in lines:
                    if line.startswith('Mem:'):
                        parts = line.split()
                        total = parts[1]
                        used = parts[2]
                        free = parts[3]
                        
                        # Calculate usage percentage (rough estimation)
                        try:
                            used_bytes = self._parse_memory_size(used)
                            total_bytes = self._parse_memory_size(total)
                            use_percent = (used_bytes / total_bytes) * 100
                            
                            issues = []
                            status = "healthy"
                            
                            if use_percent > 90:
                                status = "error"
                                issues.append(f"Memory usage critically high: {use_percent:.1f}%")
                            elif use_percent > 80:
                                status = "warning"
                                issues.append(f"Memory usage high: {use_percent:.1f}%")
                            
                            return {
                                "status": status,
                                "total": total,
                                "used": used,
                                "free": free,
                                "use_percent": f"{use_percent:.1f}%",
                                "issues": issues
                            }
                            
                        except ValueError:
                            pass
                        
                        break
            
            return {
                "status": "error",
                "issues": [f"Failed to check memory usage: {stderr.decode()}"]
            }
            
        except Exception as e:
            return {
                "status": "error",
                "issues": [f"Failed to check memory usage: {str(e)}"]
            }
    
    def _parse_memory_size(self, size_str: str) -> int:
        """Parse memory size string to bytes"""
        
        size_str = size_str.strip().upper()
        
        multipliers = {
            'K': 1024,
            'M': 1024 ** 2,
            'G': 1024 ** 3,
            'T': 1024 ** 4
        }
        
        for suffix, multiplier in multipliers.items():
            if size_str.endswith(suffix):
                return int(float(size_str[:-1]) * multiplier)
        
        # Assume bytes if no suffix
        return int(size_str)
    
    async def update_dependencies(self, category: str = "all") -> Dict[str, Any]:
        """Update dependencies"""
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "category": category,
            "updates": {}
        }
        
        if category in ["all", "python"]:
            python_update = await self._update_python_dependencies()
            results["updates"]["python"] = python_update
        
        if category in ["all", "node"]:
            node_update = await self._update_node_dependencies()
            results["updates"]["node"] = node_update
        
        return results
    
    async def _update_python_dependencies(self) -> Dict[str, Any]:
        """Update Python dependencies"""
        
        try:
            # Update pip first
            proc = await asyncio.create_subprocess_exec(
                "pip", "install", "--upgrade", "pip",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            await proc.communicate()
            
            # Update packages from requirements.txt
            requirements_file = self.app_root / "requirements.txt"
            if requirements_file.exists():
                proc = await asyncio.create_subprocess_exec(
                    "pip", "install", "--upgrade", "-r", str(requirements_file),
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                
                stdout, stderr = await proc.communicate()
                
                if proc.returncode == 0:
                    return {
                        "status": "success",
                        "message": "Python dependencies updated successfully",
                        "output": stdout.decode()
                    }
                else:
                    return {
                        "status": "error",
                        "message": "Failed to update Python dependencies",
                        "error": stderr.decode()
                    }
            else:
                return {
                    "status": "warning",
                    "message": "requirements.txt not found"
                }
                
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to update Python dependencies: {str(e)}"
            }
    
    async def _update_node_dependencies(self) -> Dict[str, Any]:
        """Update Node.js dependencies"""
        
        dashboard_dir = self.app_root / "dashboard"
        
        if not dashboard_dir.exists():
            return {
                "status": "warning",
                "message": "Dashboard directory not found"
            }
        
        try:
            proc = await asyncio.create_subprocess_exec(
                "npm", "update",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=dashboard_dir
            )
            
            stdout, stderr = await proc.communicate()
            
            if proc.returncode == 0:
                return {
                    "status": "success",
                    "message": "Node.js dependencies updated successfully",
                    "output": stdout.decode()
                }
            else:
                return {
                    "status": "error",
                    "message": "Failed to update Node.js dependencies",
                    "error": stderr.decode()
                }
                
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to update Node.js dependencies: {str(e)}"
            }
    
    async def get_dependency_status(self, dependency_type: str = "all") -> Dict[str, Any]:
        """Get status of specific dependency type"""
        
        full_status = await self.check_dependencies()
        
        if dependency_type == "all":
            return full_status
        
        if dependency_type in full_status["categories"]:
            return {
                "timestamp": full_status["timestamp"],
                "category": dependency_type,
                "status": full_status["categories"][dependency_type]
            }
        
        return {
            "error": f"Unknown dependency type: {dependency_type}",
            "available_types": list(full_status["categories"].keys())
        }
