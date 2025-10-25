#!/bin/bash
# Script to run tests with various options

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Default options
COVERAGE=false
VERBOSE=false
SPECIFIC_TEST=""
FAILFAST=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --coverage|-c)
            COVERAGE=true
            shift
            ;;
        --verbose|-v)
            VERBOSE=true
            shift
            ;;
        --failfast|-x)
            FAILFAST=true
            shift
            ;;
        --test|-t)
            SPECIFIC_TEST="$2"
            shift 2
            ;;
        --help|-h)
            echo "Usage: ./scripts/run-tests.sh [options]"
            echo ""
            echo "Options:"
            echo "  -c, --coverage     Run tests with coverage reporting"
            echo "  -v, --verbose      Run tests in verbose mode"
            echo "  -x, --failfast     Stop on first test failure"
            echo "  -t, --test FILE    Run specific test file or test"
            echo "  -h, --help         Show this help message"
            echo ""
            echo "Examples:"
            echo "  ./scripts/run-tests.sh --coverage"
            echo "  ./scripts/run-tests.sh --test back/tests/test_auth_unit.py"
            echo "  ./scripts/run-tests.sh --verbose --failfast"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

# Build pytest command
PYTEST_CMD="uv run python -m pytest"

# Add test path
if [ -n "$SPECIFIC_TEST" ]; then
    PYTEST_CMD="$PYTEST_CMD $SPECIFIC_TEST"
else
    PYTEST_CMD="$PYTEST_CMD back/tests/"
fi

# Add coverage options
if [ "$COVERAGE" = true ]; then
    PYTEST_CMD="$PYTEST_CMD --cov=back/api --cov-report=term --cov-report=html"
    echo -e "${GREEN}Running tests with coverage...${NC}"
else
    echo -e "${GREEN}Running tests...${NC}"
fi

# Add verbose option
if [ "$VERBOSE" = true ]; then
    PYTEST_CMD="$PYTEST_CMD -v"
fi

# Add failfast option
if [ "$FAILFAST" = true ]; then
    PYTEST_CMD="$PYTEST_CMD -x"
fi

# Run tests
echo -e "${YELLOW}Command: $PYTEST_CMD${NC}"
eval $PYTEST_CMD

# Show coverage report location if coverage was run
if [ "$COVERAGE" = true ]; then
    echo ""
    echo -e "${GREEN}Coverage HTML report generated at: htmlcov/index.html${NC}"
    echo -e "${YELLOW}Open with: open htmlcov/index.html${NC}"
fi
