#!/bin/bash

# Extract name and version from frontend/package.json
# Using grep and sed for compatibility if jq is not available
FRONTEND_NAME=$(grep '"name":' frontend/package.json | head -1 | sed -E 's/.*"name": "([^"]+)".*/\1/')
VERSION=$(grep '"version":' frontend/package.json | head -1 | sed -E 's/.*"version": "([^"]+)".*/\1/')

if [ -z "$FRONTEND_NAME" ] || [ -z "$VERSION" ]; then
  echo "Error: Could not extract name or version from frontend/package.json"
  exit 1
fi

export FRONTEND_NAME
export BACKEND_NAME="chronos-backend"
export VERSION

echo "Building project with:"
echo "  Frontend Name: $FRONTEND_NAME"
echo "  Backend Name:  $BACKEND_NAME"
echo "  Version:       $VERSION"

# Run docker-compose with the exported variables
docker compose up --build
