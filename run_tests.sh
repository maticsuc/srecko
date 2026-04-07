#!/bin/bash
#
# Srečko Test Runner with Logging
#
# Usage:
#   ./run_tests.sh              # Run all tests, show results
#   ./run_tests.sh --quick      # Quick mode (skip RAG)
#   ./run_tests.sh --json       # Output JSON only
#   ./run_tests.sh --verbose    # Verbose output
#

set -e

# Configuration
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$PROJECT_DIR/venv"
LOG_DIR="$PROJECT_DIR/logs"
TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")

# Create logs directory if needed
mkdir -p "$LOG_DIR"

# Check if venv exists
if [ ! -d "$VENV_DIR" ]; then
    echo "✗ Virtual environment not found at $VENV_DIR"
    echo "  Run: python -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# Activate venv
source "$VENV_DIR/bin/activate"

# Run tests with passed arguments
echo "Running Srečko tests..."
echo "Timestamp: $TIMESTAMP"
echo ""

# Capture results
if [ "$1" == "--json" ]; then
    # JSON output only
    python "$PROJECT_DIR/tests/test_srecko.py" "$@" > "$LOG_DIR/results_$TIMESTAMP.json"
    cat "$LOG_DIR/results_$TIMESTAMP.json"
elif [ "$1" == "--store" ]; then
    # Store results and show summary
    RESULT_FILE="$LOG_DIR/results_$TIMESTAMP.txt"
    python "$PROJECT_DIR/tests/test_srecko.py" --quick > "$RESULT_FILE" 2>&1
    cat "$RESULT_FILE"
    echo ""
    echo "Results stored: $RESULT_FILE"
else
    # Normal execution
    python "$PROJECT_DIR/tests/test_srecko.py" "$@"
fi

EXIT_CODE=$?

# Print summary
echo ""
if [ $EXIT_CODE -eq 0 ]; then
    echo "✓ Tests passed"
else
    echo "✗ Tests failed (exit code: $EXIT_CODE)"
fi

exit $EXIT_CODE
