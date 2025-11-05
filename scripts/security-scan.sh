#!/bin/bash
# Security scanning script for SMTPy
# Run security checks on dependencies and code

set -e

echo "🔒 SMTPy Security Scan"
echo "====================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if we're in the project root
if [ ! -f "README.md" ]; then
    echo "❌ Error: Please run this script from the project root directory"
    exit 1
fi

echo "📦 Scanning Backend Dependencies..."
echo "-----------------------------------"

# Backend Python dependencies
if [ -d "back" ]; then
    cd back

    # Check if pip-audit is installed
    if ! command -v pip-audit &> /dev/null; then
        echo "Installing pip-audit..."
        pip install pip-audit
    fi

    echo "Running pip-audit on Python dependencies..."
    pip-audit --format json > ../security-reports/backend-vulnerabilities.json 2>&1 || true
    pip-audit || echo -e "${YELLOW}⚠️  Found vulnerabilities in Python dependencies${NC}"

    cd ..
else
    echo "Backend directory not found, skipping..."
fi

echo ""
echo "📦 Scanning Frontend Dependencies..."
echo "------------------------------------"

# Frontend npm dependencies
if [ -d "front" ]; then
    cd front

    echo "Running npm audit on JavaScript dependencies..."
    npm audit --json > ../security-reports/frontend-vulnerabilities.json 2>&1 || true
    npm audit || echo -e "${YELLOW}⚠️  Found vulnerabilities in JavaScript dependencies${NC}"

    cd ..
else
    echo "Frontend directory not found, skipping..."
fi

echo ""
echo "🔍 Scanning Code for Security Issues..."
echo "---------------------------------------"

# Backend code scanning with bandit
if [ -d "back" ]; then
    if ! command -v bandit &> /dev/null; then
        echo "Installing bandit..."
        pip install bandit
    fi

    echo "Running bandit security linter on Python code..."
    bandit -r back/ -ll -f json -o security-reports/backend-code-scan.json 2>&1 || true
    bandit -r back/ -ll || echo -e "${YELLOW}⚠️  Found security issues in Python code${NC}"
fi

echo ""
echo "🔐 Checking for Secrets in Code..."
echo "----------------------------------"

# Check for potential secrets (basic check)
if command -v grep &> /dev/null; then
    echo "Scanning for potential exposed secrets..."

    # Create reports directory if it doesn't exist
    mkdir -p security-reports

    # Patterns to search for
    patterns=(
        "password.*=.*['\"].*['\"]"
        "api[_-]?key.*=.*['\"].*['\"]"
        "secret.*=.*['\"].*['\"]"
        "token.*=.*['\"].*['\"]"
        "aws[_-]?access"
        "stripe[_-]?key"
    )

    found_secrets=0
    for pattern in "${patterns[@]}"; do
        results=$(grep -rniI "$pattern" --exclude-dir={node_modules,.git,dist,build,__pycache__,.pytest_cache,htmlcov} --exclude="*.{min.js,bundle.js,lock}" . 2>/dev/null || true)
        if [ ! -z "$results" ]; then
            echo -e "${RED}⚠️  Potential secret found matching pattern: $pattern${NC}"
            echo "$results" | head -5
            found_secrets=$((found_secrets + 1))
        fi
    done

    if [ $found_secrets -eq 0 ]; then
        echo -e "${GREEN}✅ No obvious secrets found in code${NC}"
    else
        echo -e "${RED}❌ Found $found_secrets potential secret patterns${NC}"
        echo "Review the findings and ensure no real secrets are committed"
    fi
fi

echo ""
echo "📊 Security Scan Summary"
echo "========================"
echo ""

# Count vulnerabilities
backend_vulns=0
frontend_vulns=0

if [ -f "security-reports/backend-vulnerabilities.json" ]; then
    backend_vulns=$(cat security-reports/backend-vulnerabilities.json | grep -o '"vulnerabilities"' | wc -l || echo "0")
fi

if [ -f "security-reports/frontend-vulnerabilities.json" ]; then
    frontend_vulns=$(cat security-reports/frontend-vulnerabilities.json | grep -o '"severity"' | wc -l || echo "0")
fi

echo "Backend Vulnerabilities: $backend_vulns"
echo "Frontend Vulnerabilities: $frontend_vulns"
echo ""

if [ $backend_vulns -eq 0 ] && [ $frontend_vulns -eq 0 ]; then
    echo -e "${GREEN}✅ No critical vulnerabilities found!${NC}"
    echo ""
    echo "Recommendations:"
    echo "  - Keep dependencies updated regularly"
    echo "  - Enable Dependabot for automated updates"
    echo "  - Review security advisories weekly"
    exit 0
else
    echo -e "${YELLOW}⚠️  Vulnerabilities found. Review and fix before production.${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Review security-reports/ directory for details"
    echo "  2. Update vulnerable dependencies"
    echo "  3. Run: npm audit fix (for frontend)"
    echo "  4. Run: pip install -U package-name (for backend)"
    echo "  5. Re-run this scan to verify fixes"
    exit 1
fi
