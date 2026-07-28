#!/bin/bash
# Security Audit Script for Scam Detection App

echo "Starting Security Audit..."

# Check for hardcoded secrets in codebase
echo "Checking for hardcoded secrets..."
grep -rE "api_key|password|secret|token" . --exclude-dir=node_modules --exclude-dir=venv --exclude-dir=.git | grep -v "example"

# Check dependencies for known vulnerabilities (Backend)
if [ -f "requirements.txt" ]; then
    echo "Auditing Python dependencies..."
    pip install safety
    safety check -r requirements.txt
fi

# Check dependencies for known vulnerabilities (Frontend)
if [ -d "frontend" ]; then
    echo "Auditing Node.js dependencies..."
    cd frontend && npm audit
    cd ..
fi

# Check file permissions
echo "Checking file permissions..."
find . -type f -name ".env" -not -perm 600

echo "Security Audit Complete."
