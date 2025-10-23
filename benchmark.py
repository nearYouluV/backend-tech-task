"""
Simple performance benchmark script for Event Analytics API.
Tests basic ingestion and query performance.
"""

import asyncio
import time
import statistics
from datetime import datetime, timedelta
from uuid import uuid4
from typing import List, Dict, Any, Optional
import httpx
import json
import random

# Configuration
API_BASE_URL = "http://localhost:8000"
BENCHMARK_EVENTS = [100, 1000, 5000, 10000]  # Including larger batches


class SimpleBenchmark:
    """Simple performance benchmark."""
    
    def __init__(self):
        self.auth_token = None
    
    def generate_test_events(self, count: int) -> List[Dict[str, Any]]:
        """Generate test events for benchmarking."""
        events = []
        base_time = datetime.now() - timedelta(days=7)  # Recent events
        
        event_types = ["login", "view_item", "purchase", "logout", "search"]
        user_ids = [f"user_{i}" for i in range(1, min(count // 5, 100) + 1)]
        
        for i in range(count):
            event_time = base_time + timedelta(
                days=random.randint(0, 6),
                hours=random.randint(0, 23),
                minutes=random.randint(0, 59)
            )
            
            events.append({
                "event_id": str(uuid4()),
                "user_id": random.choice(user_ids),
                "event_type": random.choice(event_types),
                "occurred_at": event_time.isoformat(),
                "properties": {
                    "session_id": f"session_{random.randint(1000, 9999)}",
                    "page": f"page_{random.randint(1, 10)}"
                }
            })
        
        return events
    
    async def test_api_health(self) -> bool:
        """Test if API is accessible."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{API_BASE_URL}/health")
                return response.status_code == 200
        except:
            return False
    
    async def get_auth_token(self) -> Optional[str]:
        """Get authentication token for API access."""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Create test user
                signup_data = {
                    "username": "benchmark_test",
                    "email": "benchmark@example.com",
                    "password": "testpass123"
                }
                
                signup_response = await client.post(
                    f"{API_BASE_URL}/api/v1/auth/signup",
                    json=signup_data
                )
                
                if signup_response.status_code not in [200, 201]:
                    print("User may already exist, trying login...")
                
                # Login to get token
                login_data = {
                    "username": "benchmark_test",
                    "password": "testpass123"
                }
                
                login_response = await client.post(
                    f"{API_BASE_URL}/api/v1/auth/login",
                    json=login_data
                )
                
                if login_response.status_code == 200:
                    token = login_response.json().get("access_token")
                    print("Authentication successful")
                    return token
                else:
                    print(f"Login failed: {login_response.status_code} - {login_response.text}")
                    return None
                    
        except Exception as e:
            print(f"Authentication error: {e}")
            return None
    
    async def benchmark_basic_ingestion(self, events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Benchmark basic event ingestion with batch splitting."""
        if not self.auth_token:
            print("Getting authentication token...")
            self.auth_token = await self.get_auth_token()
            if not self.auth_token:
                return {
                    "event_count": len(events),
                    "duration_seconds": 0,
                    "events_per_second": 0,
                    "status_code": 0,
                    "success": False,
                    "error": "Authentication failed"
                }
        
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        # Split into batches of 1000 events
        batch_size = 1000
        total_events = len(events)
        batches = [events[i:i + batch_size] for i in range(0, total_events, batch_size)]
        
        print(f"Splitting into {len(batches)} batch(es) of max {batch_size} events")
        
        start_time = time.time()
        successful_batches = 0
        failed_batches = 0
        
        try:
            async with httpx.AsyncClient(timeout=300.0) as client:
                for i, batch in enumerate(batches):
                    batch_start = time.time()
                    response = await client.post(
                        f"{API_BASE_URL}/api/v1/events",
                        json={"events": batch},
                        headers=headers
                    )
                    batch_end = time.time()
                    
                    if response.status_code in [200, 201]:
                        successful_batches += 1
                        print(f"Batch {i+1}/{len(batches)}: {len(batch)} events in {batch_end - batch_start:.2f}s")
                    else:
                        failed_batches += 1
                        print(f"Batch {i+1}/{len(batches)} failed: {response.status_code}")
            
            end_time = time.time()
            duration = end_time - start_time
            
            return {
                "event_count": total_events,
                "duration_seconds": duration,
                "events_per_second": total_events / duration,
                "status_code": 200 if failed_batches == 0 else 207,  # 207 = Multi-Status
                "success": failed_batches == 0,
                "successful_batches": successful_batches,
                "failed_batches": failed_batches,
                "total_batches": len(batches),
                "response_preview": f"{successful_batches}/{len(batches)} batches successful"
            }
        except Exception as e:
            end_time = time.time()
            return {
                "event_count": total_events,
                "duration_seconds": end_time - start_time,
                "events_per_second": 0,
                "status_code": 0,
                "success": False,
                "error": str(e)
            }
    
    async def benchmark_basic_queries(self) -> Dict[str, Any]:
        """Benchmark basic analytics queries."""
        results = {}
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                # Test basic health
                start_time = time.time()
                health_response = await client.get(f"{API_BASE_URL}/health")
                health_duration = time.time() - start_time
                
                results["health"] = {
                    "duration_seconds": health_duration,
                    "status_code": health_response.status_code,
                    "success": health_response.status_code == 200
                }
                
                # Test API health
                start_time = time.time()
                api_health_response = await client.get(f"{API_BASE_URL}/api/v1/health")
                api_health_duration = time.time() - start_time
                
                results["api_health"] = {
                    "duration_seconds": api_health_duration,
                    "status_code": api_health_response.status_code,
                    "success": api_health_response.status_code == 200
                }
                
                # Test cold storage health
                start_time = time.time()
                cold_health_response = await client.get(f"{API_BASE_URL}/api/v1/cold-storage/health")
                cold_health_duration = time.time() - start_time
                
                results["cold_storage_health"] = {
                    "duration_seconds": cold_health_duration,
                    "status_code": cold_health_response.status_code,
                    "success": cold_health_response.status_code == 200
                }
                
                # Test events health
                start_time = time.time()
                events_health_response = await client.get(f"{API_BASE_URL}/api/v1/events/health")
                events_health_duration = time.time() - start_time
                
                results["events_health"] = {
                    "duration_seconds": events_health_duration,
                    "status_code": events_health_response.status_code,
                    "success": events_health_response.status_code == 200
                }
                
        except Exception as e:
            results["error"] = str(e)
        
        return results
    
    async def run_benchmark(self) -> Dict[str, Any]:
        """Run the complete benchmark."""
        print("Starting Performance Benchmark")
        print("=" * 50)
        
        results = {
            "benchmark_timestamp": datetime.now().isoformat(),
            "api_accessible": False,
            "ingestion_tests": {},
            "query_tests": {},
            "summary": {}
        }
        
        # Test API accessibility
        print("Testing API accessibility...")
        api_accessible = await self.test_api_health()
        results["api_accessible"] = api_accessible
        
        if not api_accessible:
            print("API is not accessible")
            return results
        
        print("API is accessible")
        
        # Test different batch sizes
        ingestion_rates = []
        
        for event_count in BENCHMARK_EVENTS:
            print(f"\nTesting {event_count:,} events...")
            
            # Generate test data
            events = self.generate_test_events(event_count)
            
            # Test ingestion
            ingestion_result = await self.benchmark_basic_ingestion(events)
            results["ingestion_tests"][f"{event_count}_events"] = ingestion_result
            
            if ingestion_result["success"]:
                print(f"Ingested {event_count:,} events in {ingestion_result['duration_seconds']:.2f}s")
                print(f"Rate: {ingestion_result['events_per_second']:.2f} events/sec")
                ingestion_rates.append(ingestion_result['events_per_second'])
            else:
                print(f"Failed: {ingestion_result.get('error', 'Unknown error')}")
                print(f"Status: {ingestion_result['status_code']}")
                if ingestion_result.get('response_preview'):
                    print(f"Response: {ingestion_result['response_preview']}")
            
            # Small delay between tests
            await asyncio.sleep(1)
        
        # Test basic queries
        print(f"\nTesting Basic Queries...")
        query_results = await self.benchmark_basic_queries()
        results["query_tests"] = query_results
        
        for query_type, result in query_results.items():
            if "error" not in result:
                status = "OK" if result["success"] else "FAIL"
                print(f"{status} {query_type}: {result['duration_seconds']:.3f}s (status: {result['status_code']})")
        
        # Calculate summary
        if ingestion_rates:
            results["summary"] = {
                "successful_tests": len(ingestion_rates),
                "max_ingestion_rate": max(ingestion_rates),
                "avg_ingestion_rate": statistics.mean(ingestion_rates),
                "min_ingestion_rate": min(ingestion_rates),
                "total_events_processed": sum(
                    result["event_count"] for result in results["ingestion_tests"].values() 
                    if result["success"]
                )
            }
            
            print(f"\nSummary:")
            summary = results["summary"]
            print(f"Max ingestion rate: {summary['max_ingestion_rate']:.2f} events/sec")
            print(f"Avg ingestion rate: {summary['avg_ingestion_rate']:.2f} events/sec")
            print(f"Total events processed: {summary['total_events_processed']:,}")
            print(f"Successful tests: {summary['successful_tests']}/{len(BENCHMARK_EVENTS)}")
        else:
            print(f"\nNo successful ingestion tests")
        
        return results


async def main():
    """Run the simple benchmark."""
    benchmark = SimpleBenchmark()
    
    try:
        results = await benchmark.run_benchmark()
        
        # Save results
        with open("benchmark_results.json", "w") as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\n💾 Results saved to benchmark_results.json")
        
        # Print key metrics
        if results.get("summary"):
            summary = results["summary"]
            print(f"\n🎯 Key Performance Metrics:")
            print(f"   • Peak Performance: {summary['max_ingestion_rate']:.0f} events/sec")
            print(f"   • Average Performance: {summary['avg_ingestion_rate']:.0f} events/sec")
            print(f"   • Total Events Tested: {summary['total_events_processed']:,}")
        
        return 0
        
    except Exception as e:
        print(f"❌ Benchmark failed: {e}")
        return 1


if __name__ == "__main__":
    exit(asyncio.run(main()))
