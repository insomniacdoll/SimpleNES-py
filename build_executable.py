#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SimpleNES-py Build Script
Used to package SimpleNES-py into cross-platform executable files
Supports Windows, macOS, and Linux
"""

import os
import sys
import platform
import subprocess
import shutil

def install_pyinstaller():
    """Install PyInstaller"""
    print("Installing PyInstaller...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
    print("PyInstaller installation complete!")

def build_executable():
    """Build executable file"""
    system = platform.system().lower()
    print("Detected system: {0}".format(system))
    
    # Ensure PyInstaller is installed
    try:
        import PyInstaller
    except ImportError:
        install_pyinstaller()
    
    # Project root directory
    project_root = os.path.dirname(os.path.abspath(__file__))
    dist_dir = os.path.join(project_root, "dist")
    
    # Remove dist directory if it exists
    if os.path.exists(dist_dir):
        shutil.rmtree(dist_dir)
    
    # Build command arguments
    build_args = [
        "pyinstaller",
        "--onefile",           # Package into a single executable file
        "--windowed",          # Don't show console window (for GUI apps)
        "--name=SimpleNES",    # Executable name
        "--add-data=src;src",  # Add src directory to package
        "--collect-all=pygame", # Collect all pygame dependencies
        "--clean",             # Clean temporary files
        "main.py"              # Main entry file
    ]
    
    # Adjust parameters based on different platforms
    if system == "windows":
        executable_name = "SimpleNES.exe"
        build_args[4] = "--add-data=src;src"  # Windows uses ; separator
    else:
        executable_name = "SimpleNES"
        build_args[4] = "--add-data=src:src"  # Linux/macOS uses : separator
    
    print("Starting to build executable...")
    print("Executing command: {0}".format(' '.join(build_args)))
    
    try:
        subprocess.check_call(build_args)
        print("Build successful! Executable located at: {0}".format(os.path.join(dist_dir, executable_name)))
        
        # Provide usage instructions
        print("\nUsage instructions:")
        print("1. Drag and drop NES ROM file onto {0} to run".format(executable_name))
        print("2. Or run from command line: ./{0} <rom_file.nes>".format(executable_name))
        print("3. Available parameters: -s <scale>, -w <width>, -H <height>")
        
    except subprocess.CalledProcessError as e:
        print("Build failed: {0}".format(e))
        sys.exit(1)

def build_for_distribution():
    """Build executable for distribution (needs to run separately on each platform)"""
    system = platform.system()
    print("Building executable for {0}...".format(system))
    build_executable()

if __name__ == "__main__":
    print("SimpleNES-py Cross-platform Build Tool")
    print("="*40)
    
    build_for_distribution()
