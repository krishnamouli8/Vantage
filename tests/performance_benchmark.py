"""Performance benchmarking for Vantage Platform.

Measures throughput, latency, and resource utilization under various loads.
"""

import time
import statistics
import asyncio
import aiohttp
import json
from dataclasses import dataclass
from typing import List
import sys


@dataclass
class BenchmarkResult:
    """Results from a benchmark run."""
    test_name: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    duration_seconds: float
    throughput_rps: float
    latencies_ms: List[float]
    p50: float
    p95: float
    p99: float
    min_latency: float
    max_latency: float
    error_rate: float


class VantageBenchmark:
    """Performance benchmark suite."""
    
    def __init__(self, collector_url: str = "http://localhost:8000"):
        """Initialize benchmark.
        
        Args:
            collector_url: URL of collector service
        """
        self.collector_url = collector_url
        self.results: List[BenchmarkResult] = []
    
    async def _send_metric(self, session,metric_data: dict) -> tuple[bool, float]:
        """Send single metric request.
        
        Returns:
            (success, latency_ms)
        """
        start = time.time()
        
        try:
            async with session.post(
                f"{self.collector_url}/v1/metrics",
                json={"metrics": [metric_data]},
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                latency = (time.time() - start) * 1000
                success = response.status in (200, 202)
                return success, latency
        except Exception:
            latency = (time.time() - start) * 1000
            return False, latency
    
    def _generate_metric(self, timestamp: int) -> dict:
        """Generate sample metric."""
        return {
            "timestamp": timestamp,
            "service_name": "benchmark-service",
            "metric_name": "test.metric",
            "metric_type": "gauge",
            "value": 123.45,
            "endpoint": "/api/test",
            "method": "GET",
            "status_code": 200,
            "duration_ms": 100.0,
            "tags": {"env": "benchmark"}
        }
    
    async def run_throughput_test(
        self,
        requests_per_second: int,
        duration_seconds: int
    ) -> BenchmarkResult:
        """Test sustained throughput.
        
        Args:
            requests_per_second: Target RPS
            duration_seconds: Test duration
            
        Returns:
            Benchmark results
        """
        print(f"\n🔥 Throughput Test: {requests_per_second} RPS for {duration_seconds}s")
        
        total_requests = requests_per_second *duration_seconds
        interval = 1.0 / requests_per_second
        
        latencies = []
        successes = 0
        failures = 0
        
        start_time = time.time()
        
        async with aiohttp.ClientSession() as session:
            for i in range(total_requests):
                timestamp = int(time.time() * 1000)
                metric = self._generate_metric(timestamp)
                
                success, latency = await self._send_metric(session, metric)
                
                latencies.append(latency)
                if success:
                    successes += 1
                else:
                    failures += 1
                
                # Progress indicator
                if (i + 1) % 100 == 0:
                    print(f"  Progress: {i + 1}/{total_requests} requests", end='\r')
                
                # Rate limiting
                await asyncio.sleep(interval)
        
        duration = time.time() - start_time
        
        print(f"\n  Completed: {total_requests} requests in {duration:.2f}s")
        
        return BenchmarkResult(
            test_name=f"Throughput {requests_per_second} RPS",
            total_requests=total_requests,
            successful_requests=successes,
            failed_requests=failures,
            duration_seconds=duration,
            throughput_rps=total_requests / duration,
            latencies_ms=latencies,
            p50=statistics.median(latencies),
            p95=statistics.quantiles(latencies, n=20)[18] if len(latencies) > 20 else max(latencies),
            p99=statistics.quantiles(latencies, n=100)[98] if len(latencies) > 100 else max(latencies),
            min_latency=min(latencies),
            max_latency=max(latencies),
            error_rate=failures / total_requests
        )
    
    async def run_burst_test(
        self,
        concurrent_requests: int
    ) -> BenchmarkResult:
        """Test burst capacity.
        
        Args:
            concurrent_requests: Number of simultaneous requests
            
        Returns:
            Benchmark results
        """
        print(f"\n💥 Burst Test: {concurrent_requests} concurrent requests")
        
        start_time = time.time()
        
        async with aiohttp.ClientSession() as session:
            tasks = []
            timestamp = int(time.time() * 1000)
            
            for _ in range(concurrent_requests):
                metric = self._generate_metric(timestamp)
                task = self._send_metric(session, metric)
                tasks.append(task)
            
            results = await asyncio.gather(*tasks)
        
        duration = time.time() - start_time
        
        successes = sum(1 for success,_ in results if success)
        failures = concurrent_requests - successes
        latencies = [latency for _, latency in results]
        
        print(f"  Completed: {concurrent_requests} requests in {duration:.2f}s")
        
        return BenchmarkResult(
            test_name=f"Burst {concurrent_requests} requests",
            total_requests=concurrent_requests,
            successful_requests=successes,
            failed_requests=failures,
            duration_seconds=duration,
            throughput_rps=concurrent_requests / duration,
            latencies_ms=latencies,
            p50=statistics.median(latencies),
            p95=statistics.quantiles(latencies, n=20)[18] if len(latencies) > 20 else max(latencies),
            p99=statistics.quantiles(latencies, n=100)[98] if len(latencies) > 100 else max(latencies),
            min_latency=min(latencies),
            max_latency=max(latencies),
            error_rate=failures / concurrent_requests
        )
    
    def print_results(self):
        """Print benchmark results."""
        print("\n" + "=" * 80)
        print("BENCHMARK RESULTS")
        print("=" * 80)
        
        for result in self.results:
            print(f"\n{result.test_name}")
            print(f"  Total Requests: {result.total_requests}")
            print(f"  Successful: {result.successful_requests}")
            print(f"  Failed: {result.failed_requests}")
            print(f"  Error Rate: {result.error_rate * 100:.2f}%")
            print(f"  Duration: {result.duration_seconds:.2f}s")
            print(f"  Throughput: {result.throughput_rps:.2f} req/s")
            print(f"  Latency:")
            print(f"    Min: {result.min_latency:.2f}ms")
            print(f"    Median (p50): {result.p50:.2f}ms")
            print(f"    p95: {result.p95:.2f}ms")
            print(f"    p99: {result.p99:.2f}ms")
            print(f"    Max: {result.max_latency:.2f}ms")
            
            # Performance grade
            grade = "✅ PASS" if result.error_rate < 0.01 and result.p99 < 500 else "⚠️  WARNING"
            print(f"  Grade: {grade}")
        
        print("\n" + "=" * 80)
    
    async def run_all(self):
        """Run all benchmark tests."""
        print("=" * 80)
        print("VANTAGE PERFORMANCE BENCHMARK")
        print("=" * 80)
        
        # Test 1: Low load (100 RPS)
        result = await self.run_throughput_test(requests_per_second=100, duration_seconds=10)
        self.results.append(result)
        
        # Test 2: Medium load (500 RPS)
        result = await self.run_throughput_test(requests_per_second=500, duration_seconds=10)
        self.results.append(result)
        
        # Test 3: High load (1000 RPS)
        result = await self.run_throughput_test(requests_per_second=1000, duration_seconds=10)
        self.results.append(result)
        
        # Test 4: Burst capacity
        result = await self.run_burst_test(concurrent_requests=1000)
        self.results.append(result)
        
        # Print results
        self.print_results()
        
        # Return overall success
        all_passed = all(r.error_rate < 0.01 and r.p99 < 500 for r in self.results)
        return all_passed


async def main():
    """Main benchmark entry point."""
    benchmark = VantageBenchmark()
    
    try:
        success = await benchmark.run_all()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Benchmark failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

# Usage:
# python tests/performance_benchmark.py
#
# Expected results:
# - 100 RPS: < 0.1% errors, p99 < 100ms
# - 500 RPS: < 0.5% errors, p99 < 200ms
# - 1000 RPS: < 1% errors, p99 < 500ms
# - 1000 burst: < 1% errors, p99 < 500ms
