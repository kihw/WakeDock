#!/usr/bin/env python3
"""
WakeDock Development Utilities
Quick helper script for common development tasks
"""

import subprocess
import sys
import time
import requests
import argparse
import json
from pathlib import Path


def run_command(cmd: list, cwd: Path = None, check: bool = True):
    """Run a command and return the result."""
    try:
        result = subprocess.run(cmd, cwd=cwd, check=check, capture_output=True, text=True)
        return result
    except subprocess.CalledProcessError as e:
        print(f"Command failed: {' '.join(cmd)}")
        print(f"Error: {e.stderr}")
        if check:
            sys.exit(1)
        return e


def check_service(url: str, name: str) -> bool:
    """Check if a service is running."""
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            print(f"✅ {name} is running at {url}")
            return True
        else:
            print(f"❌ {name} responded with status {response.status_code}")
            return False
    except requests.exceptions.RequestException:
        print(f"❌ {name} is not responding at {url}")
        return False


def wait_for_service(url: str, name: str, max_wait: int = 60) -> bool:
    """Wait for a service to become available."""
    print(f"⏳ Waiting for {name} to start...")
    
    for i in range(max_wait):
        if check_service(url, name):
            return True
        time.sleep(1)
        if i % 10 == 0 and i > 0:
            print(f"   Still waiting... ({i}s)")
    
    print(f"❌ {name} did not start within {max_wait} seconds")
    return False


def status():
    """Check status of all WakeDock services."""
    print("🔍 Checking WakeDock service status...\n")
    
    services = [
        ("http://localhost:8000/api/v1/health", "WakeDock API"),
        ("http://localhost:3000", "Dashboard"),
        ("http://localhost:2019/config/", "Caddy Admin API"),
    ]
    
    all_running = True
    for url, name in services:
        if not check_service(url, name):
            all_running = False
    
    print()
    if all_running:
        print("🎉 All services are running!")
    else:
        print("⚠️  Some services are not running. Use 'dev' command to start them.")


def dev():
    """Start development environment."""
    print("🚀 Starting WakeDock development environment...\n")
    
    # Start API server
    print("Starting API server...")
    api_process = subprocess.Popen([
        sys.executable, "manage.py", "dev"
    ], cwd=Path.cwd())
    
    # Wait for API to start
    if wait_for_service("http://localhost:8000/api/v1/health", "API"):
        print("✅ API server is ready")
    else:
        print("❌ Failed to start API server")
        api_process.terminate()
        return
    
    print("\n📝 Development environment is ready!")
    print("   • API: http://localhost:8000")
    print("   • API Docs: http://localhost:8000/api/docs")
    print("   • Dashboard: http://localhost:3000 (start with 'npm run dev')")
    print("\n🛑 Press Ctrl+C to stop")
    
    try:
        api_process.wait()
    except KeyboardInterrupt:
        print("\n🛑 Shutting down...")
        api_process.terminate()
        api_process.wait()


def test():
    """Run the test suite."""
    print("🧪 Running WakeDock test suite...\n")
    
    # Run unit tests
    print("Running unit tests...")
    result = run_command([sys.executable, "-m", "pytest", "tests/unit/", "-v"], check=False)
    
    if result.returncode == 0:
        print("✅ Unit tests passed")
    else:
        print("❌ Unit tests failed")
        return False
    
    # Run integration tests if API is running
    if check_service("http://localhost:8000/api/v1/health", "API"):
        print("\nRunning integration tests...")
        result = run_command([sys.executable, "-m", "pytest", "tests/integration/", "-v"], check=False)
        
        if result.returncode == 0:
            print("✅ Integration tests passed")
        else:
            print("❌ Integration tests failed")
            return False
    else:
        print("⚠️  Skipping integration tests (API not running)")
    
    print("\n🎉 All tests completed!")
    return True


def build():
    """Build production images."""
    print("🔨 Building WakeDock production images...\n")
    
    # Build API image
    print("Building API image...")
    run_command([
        "docker", "build", 
        "-f", "Dockerfile.prod",
        "-t", "wakedock:latest",
        "."
    ])
    
    # Build dashboard image
    print("Building dashboard image...")
    run_command([
        "docker", "build",
        "-f", "dashboard/Dockerfile.prod", 
        "-t", "wakedock-dashboard:latest",
        "dashboard/"
    ], cwd=Path("dashboard"))
    
    print("✅ Production images built successfully!")


def deploy():
    """Deploy to production."""
    print("🚀 Deploying WakeDock to production...\n")
    
    # Build images first
    build()
    
    # Deploy with docker-compose
    print("Starting production deployment...")
    run_command([
        "docker-compose",
        "-f", "docker-compose.yml",
        "-f", "docker-compose.prod.yml",
        "up", "-d"
    ])
    
    # Wait for services
    if wait_for_service("http://localhost:8000/api/v1/health", "Production API", 120):
        print("✅ Production deployment successful!")
        print("   • API: http://localhost:8000")
        print("   • Dashboard: http://localhost:3000")
    else:
        print("❌ Production deployment failed")


def logs():
    """Show logs from all services."""
    print("📋 WakeDock service logs...\n")
    
    try:
        subprocess.run([
            "docker-compose", "logs", "-f", "--tail=50"
        ])
    except KeyboardInterrupt:
        print("\n🛑 Stopped viewing logs")


def backup():
    """Create a backup."""
    print("💾 Creating WakeDock backup...\n")
    
    # Run backup script
    backup_script = Path("scripts/backup.sh")
    if backup_script.exists():
        if sys.platform == "win32":
            # On Windows, run with Git Bash or WSL
            run_command(["bash", str(backup_script)])
        else:
            run_command([str(backup_script)])
        print("✅ Backup completed!")
    else:
        print("❌ Backup script not found")


def main():
    parser = argparse.ArgumentParser(description="WakeDock Development Utilities")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Commands
    subparsers.add_parser("status", help="Check service status")
    subparsers.add_parser("dev", help="Start development environment")
    subparsers.add_parser("test", help="Run test suite")
    subparsers.add_parser("build", help="Build production images")
    subparsers.add_parser("deploy", help="Deploy to production")
    subparsers.add_parser("logs", help="Show service logs")
    subparsers.add_parser("backup", help="Create backup")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Execute command
    commands = {
        "status": status,
        "dev": dev,
        "test": test,
        "build": build,
        "deploy": deploy,
        "logs": logs,
        "backup": backup,
    }
    
    if args.command in commands:
        commands[args.command]()
    else:
        print(f"Unknown command: {args.command}")
        parser.print_help()


if __name__ == "__main__":
    main()
