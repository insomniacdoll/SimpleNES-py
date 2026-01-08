#!/bin/bash
# SimpleNES-py startup script

# Check if in virtual environment
if [ -z "$VIRTUAL_ENV" ]; then
    echo "Activating virtual environment..."
    if [ -d "venv" ]; then
        source venv/bin/activate
    else
        echo "Error: Virtual environment 'venv' not found. Please run: python3 -m venv venv"
        exit 1
    fi
fi

# Check arguments
if [ $# -eq 0 ]; then
    echo "Usage: $0 <rom_file> [options]"
    echo "Example: $0 SuperMarioBros.nes -s 3"
    echo ""
    echo "Options:"
    echo "  -s, --scale SCALE    Set display scale (default: 3)"
    echo "  -w, --width WIDTH    Set window width"
    echo "  -H, --height HEIGHT  Set window height"
    echo "  -h, --help          Show help"
    exit 1
fi

# Run emulator
python main.py "$@"