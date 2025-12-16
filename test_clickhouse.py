"""Test script to verify ClickHouse database layer implementation."""

import sys
sys.path.insert(0, '/home/krishna-mouli/Desktop/MyRepos/Vantage/vantage-worker')

from worker.database_clickhouse import ClickHouseDatabase
import time

def test_clickhouse_connection():
    """Test 1: ClickHouse connection."""
    print("=" * 60)
    print("TEST 1: ClickHouse Connection")
    print("=" * 60)
    
    try:
        db = ClickHouseDatabase(
            host="localhost",
            port=9000,
            database="vantage",
            user="default",
            password=""
        )
        
        db.connect()
        print("✓ Successfully connected to ClickHouse")
        
        # Test query
        with db.get_client() as client:
            result = client.execute("SELECT 1")
            print(f"✓ Test query successful: {result}")
        
        db.disconnect()
        print("✓ Disconnected successfully")
        return True
        
    except Exception as e:
        print(f"✗ Connection failed: {e}")
        return False


def test_schema_initialization():
    """Test 2: Schema initialization."""
    print("\n" + "=" * 60)
    print("TEST 2: Schema Initialization")
    print("=" * 60)
    
    try:
        db = ClickHouseDatabase(
            host="localhost",
            port=9000,
            database="vantage"
        )
        
        db.connect()
        db.init_schema()
        print("✓ Schema initialized successfully")
        
        # Verify tables exist
        with db.get_client() as client:
            result = client.execute(
                "SHOW TABLES FROM vantage"
            )
            tables = [row[0] for row in result]
            print(f"✓ Tables created: {', '.join(tables)}")
            
            expected_tables = ['metrics', 'traces', 'spans', 'alerts', 'query_log']
            for table in expected_tables:
                if table in tables:
                    print(f"  ✓ {table}")
                else:
                    print(f"  ✗ {table} MISSING")
        
        db.disconnect()
        return True
        
    except Exception as e:
        print(f"✗ Schema initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_insert_metrics():
    """Test 3: Insert sample metrics."""
    print("\n" + "=" * 60)
    print("TEST 3: Insert Sample Metrics")
    print("=" * 60)
    
    try:
        db = ClickHouseDatabase(
            host="localhost",
            port=9000,
            database="vantage"
        )
        
        db.connect()
        
        # Create sample metrics
        now_ms = int(time.time() * 1000)
        metrics = [
            {
                "timestamp": now_ms,
                "service_name": "test-service",
                "metric_name": "http.request.duration",
                "metric_type": "gauge",
                "value": 123.45,
                "endpoint": "/api/test",
                "method": "GET",
                "status_code": 200,
                "duration_ms": 123.45,
                "tags": {"env": "test", "version": "1.0"},
                "trace_id": "abc123",
                "span_id": "span456",
            },
            {
                "timestamp": now_ms + 1000,
                "service_name": "test-service",
                "metric_name": "http.request.count",
                "metric_type": "counter",
                "value": 1.0,
                "endpoint": "/api/test",
                "method": "POST",
                "status_code": 201,
                "tags": {},
            }
        ]
        
        count = db.insert_metrics_batch(metrics)
        print(f"✓ Inserted {count} metrics successfully")
        
        # Verify insertion
        with db.get_client() as client:
            result = client.execute(
                "SELECT count() FROM vantage.metrics WHERE service_name = 'test-service'"
            )
            row_count = result[0][0]
            print(f"✓ Verified {row_count} metrics in database")
            
            # Show sample data
            result = client.execute(
                """SELECT service_name, metric_name, value, endpoint 
                   FROM vantage.metrics 
                   WHERE service_name = 'test-service' 
                   LIMIT 5"""
            )
            print("\nSample data:")
            for row in result:
                print(f"  {row[0]:20} | {row[1]:30} | {row[2]:8.2f} | {row[3]}")
        
        db.disconnect()
        return True
        
    except Exception as e:
        print(f"✗ Insert test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_query_performance():
    """Test 4: Query performance."""
    print("\n" + "=" * 60)
    print("TEST 4: Query Performance")
    print("=" * 60)
    
    try:
        db = ClickHouseDatabase(
            host="localhost",
            port=9000,
            database="vantage"
        )
        
        db.connect()
        
        with db.get_client() as client:
            # Test aggregation query
            start = time.time()
            result = client.execute(
                """SELECT 
                    service_name,
                    metric_name,
                    count() as count,
                    avg(value) as avg_value,
                    max(value) as max_value
                   FROM vantage.metrics
                   GROUP BY service_name, metric_name
                   ORDER BY count DESC
                   LIMIT 10"""
            )
            duration = (time.time() - start) * 1000
            
            print(f"✓ Aggregation query completed in {duration:.2f}ms")
            print("\nTop metrics:")
            for row in result:
                print(f"  {row[0]:20} | {row[1]:30} | Count: {row[2]:5} | Avg: {row[3]:8.2f}")
        
        db.disconnect()
        return True
        
    except Exception as e:
        print(f"✗ Query test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("CLICKHOUSE DATABASE LAYER TESTING")
    print("=" * 60 + "\n")
    
    results = {
        "Connection": test_clickhouse_connection(),
        "Schema Initialization": test_schema_initialization(),
        "Insert Metrics": test_insert_metrics(),
        "Query Performance": test_query_performance(),
    }
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status:10} | {test_name}")
    
    print("\n" + "=" * 60)
    print(f"Result: {passed}/{total} tests passed")
    print("=" * 60 + "\n")
    
    return all(results.values())


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
