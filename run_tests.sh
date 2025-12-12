#!/bin/bash

# Test runner script for all Vantage components
# Runs tests with coverage and generates reports

set -e

echo "================================"
echo "Vantage Test Suite"
echo "================================"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

function run_tests() {
    local component=$1
    local path=$2
    
    echo ""
    echo "Testing $component..."
    echo "--------------------------------"
    
    if [ -d "$path/tests" ]; then
        cd "$path"
        
        # Install test dependencies if requirements.txt exists
        if [ -f "tests/requirements.txt" ]; then
            echo "Installing test dependencies..."
            pip install -q -r tests/requirements.txt 2>/dev/null || true
        fi
        
        # For agent, config already has coverage options in pyproject.toml
        if [ "$component" = "Agent" ]; then
            # Just run pytest, coverage options are in pyproject.toml
            if pytest tests/ -v; then
                echo -e "${GREEN}✓ $component tests passed${NC}"
            else
                echo -e "${RED}✗ $component tests failed${NC}"
                cd - > /dev/null
                return 1
            fi
        else
            # For other components, add coverage options
            if pytest tests/ -v --cov --cov-report=term --cov-report=html 2>/dev/null; then
                echo -e "${GREEN}✓ $component tests passed${NC}"
            else
                # Fallback without coverage if pytest-cov not installed
                echo "Coverage not available, running without coverage..."
                if pytest tests/ -v; then
                    echo -e "${GREEN}✓ $component tests passed${NC}"
                else
                    echo -e "${RED}✗ $component tests failed${NC}"
                    cd - > /dev/null
                    return 1
                fi
            fi
        fi
        
        cd - > /dev/null
    else
        echo "No tests found for $component"
    fi
}

# Run tests for each component
echo "Starting test suite..."
echo ""

FAILED_COMPONENTS=()

run_tests "Agent" "vantage-agent" || FAILED_COMPONENTS+=("Agent")
run_tests "Collector" "vantage-collector" || FAILED_COMPONENTS+=("Collector")
run_tests "Worker" "vantage-worker" || FAILED_COMPONENTS+=("Worker")
run_tests "API" "vantage-api" || FAILED_COMPONENTS+=("API")

# Run integration tests if services are running
echo ""
echo "Checking for running services..."
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "Services are running - executing integration tests"
    echo "--------------------------------"
    
    if pytest tests/test_integration_complete.py -v; then
        echo -e "${GREEN}✓ Integration tests passed${NC}"
    else
        echo -e "${RED}✗ Integration tests failed${NC}"
        exit 1
    fi
else
    echo "⚠ Services not running - skipping integration tests"
    echo "  Run 'docker-compose up -d' to start services"
fi

echo ""
echo "================================"
if [ ${#FAILED_COMPONENTS[@]} -eq 0 ]; then
    echo -e "${GREEN}All tests passed!${NC}"
else
    echo -e "${RED}Some tests failed:${NC}"
    for component in "${FAILED_COMPONENTS[@]}"; do
        echo -e "  ${RED}✗ $component${NC}"
    done
fi
echo "================================"
echo ""
echo "Coverage reports generated in each component's htmlcov/ directory"

# Exit with error if any tests failed
if [ ${#FAILED_COMPONENTS[@]} -gt 0 ]; then
    exit 1
fi
