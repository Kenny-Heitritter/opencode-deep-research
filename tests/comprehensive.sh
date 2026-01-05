#!/bin/bash
set -e

echo "Running comprehensive test suite for all effort levels..."

START_TIME=$(date +%s)

echo ""
echo "=== Running all tests ==="
python3 -m pytest tests/ -v --tb=short

END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

echo ""
echo "=== Comprehensive test suite completed ==="
echo "Total duration: ${DURATION}s"

if [ ${DURATION} -lt 300 ]; then
    echo "✓ All tests completed in under 5 minutes"
    exit 0
else
    echo "⚠ Tests took ${DURATION}s, which is over 5 minutes"
    exit 1
fi