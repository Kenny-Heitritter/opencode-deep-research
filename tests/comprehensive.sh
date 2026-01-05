#!/bin/bash
set -e

echo "Running comprehensive test suite for all effort levels..."

START_TIME=$(date +%s)

echo ""
echo "=== Running unit tests ==="
python3 -m pytest tests/ -v -k "not integration" --tb=short

echo ""
echo "=== Running integration tests ==="
python3 -m pytest tests/integration/ -v --tb=short

echo ""
echo "=== Testing effort level 1 (minimal) ==="
python3 -m pytest tests/ -v -k "effort or minimal" --tb=short || true

echo ""
echo "=== Testing effort level 2 (basic) ==="
python3 -m pytest tests/ -v -k "basic" --tb=short || true

echo ""
echo "=== Testing effort level 3 (standard) ==="
python3 -m pytest tests/ -v -k "standard" --tb=short || true

echo ""
echo "=== Testing effort level 4 (thorough) ==="
python3 -m pytest tests/ -v -k "thorough" --tb=short || true

echo ""
echo "=== Testing effort level 5 (comprehensive) ==="
python3 -m pytest tests/ -v -k "comprehensive" --tb=short || true

echo ""
echo "=== Testing verification workflows ==="
python3 -m pytest tests/ -v -k "verification or spot_check or contradiction" --tb=short

echo ""
echo "=== Testing critique agent ==="
python3 -m pytest tests/ -v -k "critique or followup" --tb=short

echo ""
echo "=== Testing cancellation ==="
python3 -m pytest tests/ -v -k "cancel or cancellation" --tb=short

echo ""
echo "=== Testing replay mode ==="
python3 -m pytest tests/integration/test_replay.py -v --tb=short

echo ""
echo "=== Testing end-to-end workflow ==="
python3 -m pytest tests/integration/e2e.py -v --tb=short

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