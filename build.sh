#!/bin/bash
# SimpleNES-py Build Script
# Supports building executable files on Windows (via WSL or Git Bash), macOS, and Linux

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "SimpleNES-py Cross-Platform Build Tool"
echo "======================================"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: python3 not found. Please install Python 3 first." >&2
    exit 1
fi

# Check if dependencies need to be installed
if [ ! -f "requirements.txt" ] || [ ! "$(pip list | grep pyinstaller)" ]; then
    echo "Installing build dependencies..."
    pip3 install -r requirements.txt
    pip3 install pyinstaller
fi

# Execute build
echo "Starting to build executable file..."
python3 build.py

echo "Build completed!"
echo "Executable file is located in the dist/ directory"