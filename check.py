#!/usr/bin/env python3
"""
Complete Vantage Platform Health Check
Verifies all components and data flow
"""

import requests
import subprocess
import json
import time
import sys
from typing import Dict, List, Tuple

# Colors for terminal output
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
BLUE = '\033[94m'
RESET = '\033[0m'
BOLD = '\033[1m'

def print_header(text: str):
    print(f"\n{BOLD}{BLUE}{'=' * 80}{RESET}")
    print(f"{BOLD}{BLUE}{text.center(80)}{RESET}")
    print(f"{BOLD}{BLUE}{'=' * 80}{RESET}\n")

def print_success(text: str):
    print(f"{GREEN}✓{RESET} {text}")

def print_error(text: str):
    print(f"{RED}✗{RESET} {text}")

def print_warning(text: str):
    print(f"{YELLOW}⚠{RESET} {text}")

def print_info(text: str):
    print(f"{BLUE}ℹ{RESET} {text}")

def check_docker_running() -> bool:
    """Check if Docker daemon is running"""
    try:
        result = subprocess.run(['docker', 'ps'], capture_output=True, timeout=5)
        return result.returncode == 0
    except:
        return False

def check_docker_compose_services() -> Dict[str, str]:
    """Check status of docker-compose services"""
    try:
        result = subprocess.run(
            ['docker-compose', 'ps', '--format', 'json'],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode != 0:
            return {}
        
        services = {}
        for line in result.stdout.strip().split('\n'):
            if line:
                try:
                    service_data = json.loads(line)
                    name = service_data.get('Service', service_data.get('Name', 'unknown'))
                    state = service_data.get('State', 'unknown')
                    services[name] = state
                except:
                    pass
        
        return services
    except:
        return {}

def check_service_health(name: str, url: str, endpoint: str = '/health') -> Tuple[bool, str]:
    """Check if service is healthy"""
    try:
        response = requests.get(f"{url}{endpoint}", timeout=5)
        if response.status_code == 200:
            data = response.json()
            status = data.get('status', 'unknown')
            return True, status
        return False, f"HTTP {response.status_code}"
    except requests.exceptions.ConnectionError:
        return False, "Connection refused"
    except requests.exceptions.Timeout:
        return False, "Timeout"
    except Exception as e:
        return False, str(e)

def check_kafka_topics() -> List[str]:
    """Check Kafka topics in Redpanda"""
    try:
        # Use docker exec to run rpk topic list
        result = subprocess.run(
            ['docker', 'exec', 'vantage-redpanda', 'rpk', 'topic', 'list'],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            topics = []
            for line in result.stdout.strip().split('\n'):
                if line and not line.startswith('NAME'):
                    topic = line.split()[0] if line.split() else None
                    if topic:
                        topics.append(topic)
            return topics
        return []
    except:
        return []

def check_kafka_messages(topic: str = 'metrics-raw') -> int:
    """Check number of messages in Kafka topic"""
    try:
        result = subprocess.run(
            ['docker', 'exec', 'vantage-redpanda', 'rpk', 'topic', 'describe', topic],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            # Parse output to get message count
            for line in result.stdout.split('\n'):
                if 'high watermark' in line.lower():
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if 'watermark' in part.lower() and i + 1 < len(parts):
                            try:
                                return int(parts[i + 1])
                            except:
                                pass
        return 0
    except:
        return 0

def check_database_metrics() -> Tuple[int, List[str]]:
    """Check metrics in SQLite database"""
    try:
        result = subprocess.run(
            ['docker', 'exec', 'vantage-worker', 'sqlite3', '/app/data/metrics.db',
             'SELECT COUNT(*), GROUP_CONCAT(DISTINCT service_name) FROM metrics;'],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            output = result.stdout.strip()
            if '|' in output:
                count_str, services_str = output.split('|', 1)
                count = int(count_str)
                services = services_str.split(',') if services_str else []
                return count, services
        return 0, []
    except:
        return 0, []

def check_api_authentication() -> Dict[str, any]:
    """Check API authentication configuration"""
    results = {
        'collector': {'enabled': None, 'configured': None},
        'api': {'enabled': None, 'configured': None}
    }
    
    # Check collector
    try:
        result = subprocess.run(
            ['docker', 'exec', 'vantage-collector', 'printenv'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        env_vars = result.stdout
        results['collector']['enabled'] = 'VANTAGE_AUTH_ENABLED=true' in env_vars
        results['collector']['configured'] = 'VANTAGE_API_KEY=' in env_vars and \
                                            'VANTAGE_API_KEY=\n' not in env_vars
    except:
        pass
    
    # Check API
    try:
        result = subprocess.run(
            ['docker', 'exec', 'vantage-api', 'printenv'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        env_vars = result.stdout
        results['api']['enabled'] = 'API_AUTH_ENABLED=true' in env_vars
        results['api']['configured'] = 'API_KEY=' in env_vars and \
                                      'API_KEY=\n' not in env_vars
    except:
        pass
    
    return results

def test_data_flow() -> Dict[str, bool]:
    """Test complete data flow"""
    results = {}
    
    # Send test metric
    test_metric = {
        "metrics": [{
            "timestamp": int(time.time() * 1000),
            "service_name": "health-check",
            "metric_name": "test.metric",
            "metric_type": "counter",
            "value": 1.0
        }],
        "service_name": "health-check",
        "environment": "test"
    }
    
    try:
        response = requests.post(
            'http://localhost:8000/v1/metrics',
            json=test_metric,
            timeout=5
        )
        results['collector_accepts'] = response.status_code in [200, 202]
    except:
        results['collector_accepts'] = False
    
    # Wait for processing
    time.sleep(3)
    
    # Check if metric appears in API
    try:
        response = requests.get(
            'http://localhost:8001/api/metrics/timeseries',
            params={'service': 'health-check', 'range': 60},
            timeout=5
        )
        data = response.json()
        results['api_returns_data'] = len(data) > 0
    except:
        results['api_returns_data'] = False
    
    return results

def main():
    print_header("VANTAGE PLATFORM COMPREHENSIVE HEALTH CHECK")
    
    all_checks_passed = True
    
    # 1. Docker Check
    print_header("1. DOCKER ENVIRONMENT")
    if check_docker_running():
        print_success("Docker daemon is running")
    else:
        print_error("Docker daemon is not running")
        all_checks_passed = False
        sys.exit(1)
    
    # 2. Docker Compose Services
    print_header("2. DOCKER COMPOSE SERVICES")
    services = check_docker_compose_services()
    
    expected_services = ['redpanda', 'collector', 'worker', 'api', 'dashboard']
    
    for service in expected_services:
        if service in services:
            if services[service] == 'running':
                print_success(f"{service}: {services[service]}")
            else:
                print_error(f"{service}: {services[service]}")
                all_checks_passed = False
        else:
            print_error(f"{service}: not found")
            all_checks_passed = False
    
    # 3. Service Health Checks
    print_header("3. SERVICE HEALTH CHECKS")
    
    health_checks = [
        ('Collector', 'http://localhost:8000', '/health'),
        ('API', 'http://localhost:8001', '/'),
        ('Dashboard', 'http://localhost:3000', '/'),
    ]
    
    for name, url, endpoint in health_checks:
        is_healthy, status = check_service_health(name, url, endpoint)
        if is_healthy:
            print_success(f"{name}: {status}")
        else:
            print_error(f"{name}: {status}")
            all_checks_passed = False
    
    # 4. Kafka/Redpanda Check
    print_header("4. KAFKA/REDPANDA STATUS")
    
    topics = check_kafka_topics()
    if 'metrics-raw' in topics:
        print_success(f"Topic 'metrics-raw' exists")
        
        msg_count = check_kafka_messages('metrics-raw')
        print_info(f"Messages in topic: {msg_count}")
    else:
        print_error("Topic 'metrics-raw' not found")
        if topics:
            print_info(f"Available topics: {', '.join(topics)}")
        all_checks_passed = False
    
    # 5. Database Check
    print_header("5. DATABASE STATUS")
    
    metric_count, services_in_db = check_database_metrics()
    if metric_count > 0:
        print_success(f"Database contains {metric_count} metrics")
        if services_in_db:
            print_info(f"Services: {', '.join(services_in_db)}")
    else:
        print_warning("Database is empty (no metrics yet)")
        print_info("Run: python send_test_metrics.py")
    
    # 6. Authentication Check
    print_header("6. AUTHENTICATION CONFIGURATION")
    
    auth_status = check_api_authentication()
    
    # Collector
    coll_auth = auth_status['collector']
    if coll_auth['enabled'] is not None:
        if coll_auth['enabled']:
            if coll_auth['configured']:
                print_success("Collector: Authentication enabled and API key configured")
            else:
                print_error("Collector: Authentication enabled but API key NOT configured")
                print_warning("  Set VANTAGE_API_KEY in .env file")
                all_checks_passed = False
        else:
            print_info("Collector: Authentication disabled")
    
    # API
    api_auth = auth_status['api']
    if api_auth['enabled'] is not None:
        if api_auth['enabled']:
            if api_auth['configured']:
                print_success("API: Authentication enabled and API key configured")
            else:
                print_error("API: Authentication enabled but API key NOT configured")
                print_warning("  Set API_KEY in .env file")
                all_checks_passed = False
        else:
            print_info("API: Authentication disabled")
    
    # 7. Data Flow Test
    print_header("7. DATA FLOW TEST")
    
    print_info("Sending test metric...")
    flow_results = test_data_flow()
    
    if flow_results.get('collector_accepts', False):
        print_success("Collector accepted metric")
    else:
        print_error("Collector rejected metric")
        all_checks_passed = False
    
    if flow_results.get('api_returns_data', False):
        print_success("Metric appeared in API (complete pipeline working)")
    else:
        print_warning("Metric not found in API (pipeline may have issues)")
    
    # Final Summary
    print_header("SUMMARY")
    
    if all_checks_passed and metric_count > 0:
        print_success(f"{BOLD}ALL SYSTEMS OPERATIONAL{RESET}")
        print_success("Platform is working correctly!")
    elif all_checks_passed:
        print_warning(f"{BOLD}SYSTEMS OK - WAITING FOR DATA{RESET}")
        print_info("Services are running. Send test metrics to verify data flow.")
        print_info("Run: python send_test_metrics.py")
    else:
        print_error(f"{BOLD}ISSUES DETECTED{RESET}")
        print_warning("Review the errors above and fix configuration.")
    
    print("\n" + "=" * 80 + "\n")
    
    # Print helpful commands
    print_header("USEFUL COMMANDS")
    print(f"{BLUE}View logs:{RESET}")
    print("  docker-compose logs -f collector")
    print("  docker-compose logs -f worker")
    print("  docker-compose logs -f api")
    print()
    print(f"{BLUE}Restart services:{RESET}")
    print("  docker-compose restart")
    print()
    print(f"{BLUE}View Kafka messages:{RESET}")
    print("  docker exec vantage-redpanda rpk topic consume metrics-raw")
    print()
    print(f"{BLUE}Query database:{RESET}")
    print("  docker exec vantage-worker sqlite3 /app/data/metrics.db 'SELECT COUNT(*) FROM metrics;'")
    print()
    print(f"{BLUE}Check environment variables:{RESET}")
    print("  docker exec vantage-collector printenv | grep VANTAGE")
    print("  docker exec vantage-api printenv | grep API")
    print()

if __name__ == "__main__":
    main()