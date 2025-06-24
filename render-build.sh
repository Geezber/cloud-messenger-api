#!/bin/bash
# render-build.sh
set -ex  # Enable debug output and exit on error

echo "=== Starting build process ==="
echo "Current directory: $(pwd)"
echo "Files in directory:"
ls -la

echo "=== Updating pip ==="
python -m pip install --upgrade pip

echo "=== Installing wheel ==="
pip install wheel

echo "=== Installing requirements ==="
pip install -r requirements.txt

echo "=== Installed packages ==="
pip freeze
