#!/bin/bash
# Script to validate .env file before running Docker

set -e

ENV_FILE=".env"

if [ ! -f "$ENV_FILE" ]; then
    echo "❌ Error: .env file not found in $(pwd)"
    echo "Please create a .env file with required environment variables."
    exit 1
fi

echo "🔍 Validating .env file..."

# Check for required variables
MISSING_VARS=()

if ! grep -q "^DATABASE_PASSWORD=" "$ENV_FILE" || grep -q "^DATABASE_PASSWORD=$" "$ENV_FILE" || grep -q "^DATABASE_PASSWORD=CHANGE_THIS_PASSWORD" "$ENV_FILE"; then
    MISSING_VARS+=("DATABASE_PASSWORD")
fi

if ! grep -q "^JWT_SECRET_KEY=" "$ENV_FILE" || grep -q "^JWT_SECRET_KEY=$" "$ENV_FILE" || grep -q "^JWT_SECRET_KEY=CHANGE_THIS_TO_A_STRONG_RANDOM_SECRET" "$ENV_FILE"; then
    MISSING_VARS+=("JWT_SECRET_KEY")
fi

if [ ${#MISSING_VARS[@]} -gt 0 ]; then
    echo "❌ Error: Missing or using placeholder values for required variables:"
    for var in "${MISSING_VARS[@]}"; do
        echo "   - $var"
    done
    echo ""
    echo "Please update your .env file with actual values:"
    echo "  - DATABASE_PASSWORD: Set a strong database password"
    echo "  - JWT_SECRET_KEY: Generate with: openssl rand -hex 32"
    exit 1
fi

echo "✅ .env file validation passed!"
echo "   All required variables are set."

