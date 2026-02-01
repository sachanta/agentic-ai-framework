#!/bin/bash

# Script to generate TypeScript types from FastAPI OpenAPI schema

API_URL=${VITE_API_URL:-http://localhost:8000}
OUTPUT_FILE="src/types/api.ts"

echo "Fetching OpenAPI schema from ${API_URL}/openapi.json..."

# Generate types using openapi-typescript
npx openapi-typescript "${API_URL}/openapi.json" -o "${OUTPUT_FILE}"

if [ $? -eq 0 ]; then
    echo "API types successfully generated at ${OUTPUT_FILE}"
else
    echo "Failed to generate API types. Make sure the backend is running at ${API_URL}"
    exit 1
fi
