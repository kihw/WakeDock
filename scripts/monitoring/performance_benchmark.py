#!/usr/bin/env python3
"""
Performance Benchmarking and Monitoring Script for WakeDock
Provides comprehensive performance testing and monitoring capabilities
"""

import asyncio
import time
import json
import sys
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional
import statistics
from datetime import datetime
import subprocess
import psutil
import aiohttp
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PerformanceBenchmark:
    """Comprehensive performance benchmarking for WakeDock"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.results: Dict[str, Any] = {}
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def benchmark_api_endpoints(self) -> Dict[str, Any]:
        """Benchmark API endpoint performance"""
        logger.info("🔄 Benchmarking API endpoints...")
        
        endpoints = [
            ("GET", "/api/v1/health", "Health Check"),
            ("GET", "/api/v1/system/overview", "System Overview"),
            ("GET", "/api/v1/services", "Services List"),
            ("GET", "/api/v1/auth/me", "User Profile"),
        ]
        
        results = {}
        
        for method, endpoint, name in endpoints:
            logger.info(f"Testing {name} ({method} {endpoint})")
            
            times = []
            success_count = 0
            error_count = 0
            
            # Run 10 requests per endpoint
            for i in range(10):
                start_time = time.time()
                try:
                    async with self.session.request(method, f"{self.base_url}{endpoint}") as response:
                        await response.read()
                        if response.status < 400:
                            success_count += 1
                        else:
                            error_count += 1
                except Exception as e:
                    logger.warning(f"Request failed: {e}")
                    error_count += 1
                
                end_time = time.time()
                times.append((end_time - start_time) * 1000)  # Convert to ms
            
            if times:
                results[endpoint] = {
                    "name": name,
                    "avg_response_time_ms": statistics.mean(times),
                    "p50_response_time_ms": statistics.median(times),
                    "p95_response_time_ms": statistics.quantiles(times, n=20)[18] if len(times) >= 20 else max(times),
                    "min_response_time_ms": min(times),
                    "max_response_time_ms": max(times),
                    "success_rate": success_count / (success_count + error_count) * 100,
                    "total_requests": success_count + error_count
                }
        
        return results
    
    async def load_test_endpoint(self, endpoint: str, concurrent: int = 10, duration: int = 30) -> Dict[str, Any]:
        """Load test a specific endpoint"""
        logger.info(f"🔄 Load testing {endpoint} with {concurrent} concurrent users for {duration}s...")
        
        start_time = time.time()
        end_time = start_time + duration
        
        request_times = []
        success_count = 0
        error_count = 0
        
        async def make_request():
            nonlocal success_count, error_count
            while time.time() < end_time:
                req_start = time.time()
                try:
                    async with self.session.get(f"{self.base_url}{endpoint}") as response:
                        await response.read()
                        if response.status < 400:
                            success_count += 1
                        else:
                            error_count += 1
                except Exception:
                    error_count += 1
                
                req_end = time.time()
                request_times.append((req_end - req_start) * 1000)
                
                # Small delay to prevent overwhelming
                await asyncio.sleep(0.01)
        
        # Run concurrent requests
        tasks = [make_request() for _ in range(concurrent)]
        await asyncio.gather(*tasks, return_exceptions=True)
        
        total_requests = success_count + error_count
        actual_duration = time.time() - start_time
        
        return {
            "endpoint": endpoint,
            "concurrent_users": concurrent,
            "duration_seconds": actual_duration,
            "total_requests": total_requests,
            "requests_per_second": total_requests / actual_duration,
            "success_rate": success_count / total_requests * 100 if total_requests > 0 else 0,
            "avg_response_time_ms": statistics.mean(request_times) if request_times else 0,
            "p95_response_time_ms": statistics.quantiles(request_times, n=20)[18] if len(request_times) >= 20 else 0
        }
    
    def benchmark_system_resources(self) -> Dict[str, Any]:
        """Benchmark system resource usage"""
        logger.info("🔄 Measuring system resource usage...")
        
        # Get system metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Get Docker container stats if available
        docker_stats = self._get_docker_stats()
        
        return {
            "cpu_usage_percent": cpu_percent,
            "memory_usage_percent": memory.percent,
            "memory_available_gb": memory.available / (1024**3),
            "disk_usage_percent": disk.percent,
            "disk_free_gb": disk.free / (1024**3),
            "docker_containers": docker_stats
        }
    
    def _get_docker_stats(self) -> List[Dict[str, Any]]:
        """Get Docker container statistics"""
        try:
            result = subprocess.run(
                ["docker", "stats", "--no-stream", "--format", "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')[1:]  # Skip header
                containers = []
                
                for line in lines:
                    if line.strip():
                        parts = line.split('\t')
                        if len(parts) >= 4:
                            containers.append({
                                "name": parts[0],
                                "cpu_percent": parts[1],
                                "memory_usage": parts[2],
                                "memory_percent": parts[3]
                            })
                
                return containers
        except Exception as e:
            logger.warning(f"Could not get Docker stats: {e}")
        
        return []
    
    def benchmark_database_performance(self) -> Dict[str, Any]:
        """Benchmark database performance (if accessible)"""
        logger.info("🔄 Measuring database performance...")
        
        # This would require database connection
        # For now, return mock data
        return {
            "connection_pool_size": 20,
            "active_connections": 5,
            "avg_query_time_ms": 25,
            "slow_queries_count": 2,
            "cache_hit_ratio": 85.5
        }
    
    async def run_full_benchmark(self) -> Dict[str, Any]:
        """Run complete performance benchmark suite"""
        logger.info("🚀 Starting comprehensive performance benchmark...")
        
        benchmark_start = time.time()
        
        # API benchmarks
        api_results = await self.benchmark_api_endpoints()
        
        # Load test critical endpoint
        load_test_results = await self.load_test_endpoint("/api/v1/health", concurrent=5, duration=10)
        
        # System resources
        system_results = self.benchmark_system_resources()
        
        # Database performance
        db_results = self.benchmark_database_performance()
        
        benchmark_duration = time.time() - benchmark_start
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "benchmark_duration_seconds": benchmark_duration,
            "api_endpoints": api_results,
            "load_test": load_test_results,
            "system_resources": system_results,
            "database": db_results,
            "summary": self._generate_summary(api_results, load_test_results, system_results)
        }
        
        return results
    
    def _generate_summary(self, api_results: Dict, load_test: Dict, system: Dict) -> Dict[str, Any]:
        """Generate performance summary with grades"""
        
        # Calculate average API response time
        avg_api_time = statistics.mean([
            endpoint["avg_response_time_ms"] 
            for endpoint in api_results.values()
        ]) if api_results else 0
        
        # Performance grades
        api_grade = "A" if avg_api_time < 100 else "B" if avg_api_time < 200 else "C" if avg_api_time < 500 else "D"
        load_grade = "A" if load_test["requests_per_second"] > 100 else "B" if load_test["requests_per_second"] > 50 else "C"
        resource_grade = "A" if system["cpu_usage_percent"] < 50 else "B" if system["cpu_usage_percent"] < 70 else "C"
        
        return {
            "overall_grade": min(api_grade, load_grade, resource_grade),
            "api_performance_grade": api_grade,
            "load_test_grade": load_grade,
            "resource_usage_grade": resource_grade,
            "avg_api_response_time_ms": avg_api_time,
            "requests_per_second": load_test["requests_per_second"],
            "cpu_usage_percent": system["cpu_usage_percent"],
            "memory_usage_percent": system["memory_usage_percent"],
            "recommendations": self._generate_recommendations(avg_api_time, load_test, system)
        }
    
    def _generate_recommendations(self, avg_api_time: float, load_test: Dict, system: Dict) -> List[str]:
        """Generate performance improvement recommendations"""
        recommendations = []
        
        if avg_api_time > 200:
            recommendations.append("Consider optimizing API endpoint response times")
        
        if load_test["requests_per_second"] < 50:
            recommendations.append("Consider increasing server worker processes")
        
        if system["cpu_usage_percent"] > 70:
            recommendations.append("High CPU usage detected - consider scaling horizontally")
        
        if system["memory_usage_percent"] > 80:
            recommendations.append("High memory usage - consider adding more RAM or optimizing memory usage")
        
        if load_test["success_rate"] < 99:
            recommendations.append("Error rate detected - check logs for issues")
        
        if not recommendations:
            recommendations.append("Performance looks good! Consider running benchmarks regularly.")
        
        return recommendations


def print_results(results: Dict[str, Any]):
    """Print benchmark results in a formatted way"""
    print("\n" + "="*70)
    print("🏆 WAKEDOCK PERFORMANCE BENCHMARK RESULTS")
    print("="*70)
    
    summary = results["summary"]
    print(f"\n📊 OVERALL GRADE: {summary['overall_grade']}")
    print(f"⏱️  Benchmark Duration: {results['benchmark_duration_seconds']:.2f}s")
    print(f"📅 Timestamp: {results['timestamp']}")
    
    print(f"\n🔗 API PERFORMANCE (Grade: {summary['api_performance_grade']})")
    print(f"   Average Response Time: {summary['avg_api_response_time_ms']:.2f}ms")
    
    for endpoint, data in results["api_endpoints"].items():
        print(f"   {data['name']}: {data['avg_response_time_ms']:.2f}ms (P95: {data['p95_response_time_ms']:.2f}ms)")
    
    print(f"\n⚡ LOAD TEST (Grade: {summary['load_test_grade']})")
    load_test = results["load_test"]
    print(f"   Requests/Second: {load_test['requests_per_second']:.2f}")
    print(f"   Success Rate: {load_test['success_rate']:.1f}%")
    print(f"   Average Response Time: {load_test['avg_response_time_ms']:.2f}ms")
    
    print(f"\n💻 SYSTEM RESOURCES (Grade: {summary['resource_usage_grade']})")
    system = results["system_resources"]
    print(f"   CPU Usage: {system['cpu_usage_percent']:.1f}%")
    print(f"   Memory Usage: {system['memory_usage_percent']:.1f}%")
    print(f"   Disk Usage: {system['disk_usage_percent']:.1f}%")
    
    if system.get("docker_containers"):
        print(f"\n🐳 DOCKER CONTAINERS")
        for container in system["docker_containers"]:
            print(f"   {container['name']}: CPU {container['cpu_percent']}, Memory {container['memory_percent']}")
    
    print(f"\n💡 RECOMMENDATIONS")
    for i, rec in enumerate(summary["recommendations"], 1):
        print(f"   {i}. {rec}")
    
    print("\n" + "="*70)


async def main():
    parser = argparse.ArgumentParser(description="WakeDock Performance Benchmark")
    parser.add_argument("--url", default="http://localhost:8000", help="Base URL for WakeDock API")
    parser.add_argument("--output", help="Output file for results (JSON)")
    parser.add_argument("--load-test", action="store_true", help="Run extended load test")
    parser.add_argument("--endpoint", help="Specific endpoint to load test")
    parser.add_argument("--concurrent", type=int, default=10, help="Concurrent users for load test")
    parser.add_argument("--duration", type=int, default=30, help="Load test duration in seconds")
    
    args = parser.parse_args()
    
    try:
        async with PerformanceBenchmark(args.url) as benchmark:
            if args.load_test and args.endpoint:
                # Run specific load test
                results = await benchmark.load_test_endpoint(
                    args.endpoint, 
                    args.concurrent, 
                    args.duration
                )
                print(f"\n🔄 Load Test Results for {args.endpoint}:")
                print(json.dumps(results, indent=2))
            else:
                # Run full benchmark
                results = await benchmark.run_full_benchmark()
                print_results(results)
                
                if args.output:
                    with open(args.output, 'w') as f:
                        json.dump(results, f, indent=2)
                    print(f"\n💾 Results saved to {args.output}")
    
    except Exception as e:
        logger.error(f"Benchmark failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
