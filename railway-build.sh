#!/bin/bash
# Railway build script - optimizes installation

set -e

echo "Starting optimized build..."

# Install dependencies without cache to save space
pip install --no-cache-dir --upgrade pip
pip install --no-cache-dir -r requirements.txt

echo "Build completed successfully!"

