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
from pathlib import Path

def install_pyinstaller():
    """Install PyInstaller"""
    print("Installing PyInstaller...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller", "pygame", "numpy", "Pillow"])
    print("PyInstaller installation complete!")

def build_executable():
    """Build executable file"""
    system = platform.system().lower()
    print("Detected system: {0}".format(system))
    
    # Ensure PyInstaller is installed
    try:
        import PyInstaller
        import pygame
        import numpy
        import PIL
    except ImportError:
        install_pyinstaller()
    
    # Project root directory
    project_root = Path(__file__).parent
    dist_dir = project_root / "dist"
    build_dir = project_root / "build"
    
    # Clean old build files
    for dir_path in [dist_dir, build_dir]:
        if dir_path.exists():
            print("Cleaning old build directory: {0}".format(dir_path))
            shutil.rmtree(dir_path)
    
    # Create spec file for precise control
    spec_content = '''# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('simple_nes', 'simple_nes'),  # Include source code directory
    ],
    hiddenimports=[
        'simple_nes',
        'simple_nes.bus',
        'simple_nes.cartridge', 
        'simple_nes.controller',
        'simple_nes.cpu',
        'simple_nes.emulator',
        'simple_nes.ppu',
        'simple_nes.apu',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='SimpleNES',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Set to False to not show console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Can add icon path here
)
'''
    
    # Write spec file
    spec_file = project_root / "SimpleNES.spec"
    with open(spec_file, 'w', encoding='utf-8') as f:
        f.write(spec_content)
    
    # Build command
    build_cmd = ["pyinstaller", "--clean", str(spec_file)]
    
    print("Starting to build executable...")
    print("Executing build command: {0}".format(' '.join(build_cmd)))
    
    try:
        subprocess.run(build_cmd, check=True)
        print("Build successful!")
        
        # Show results
        output_path = os.path.join(dist_dir, "SimpleNES")
        if system == "windows":
            output_path = os.path.join(dist_dir, "SimpleNES.exe")
        
        if os.path.exists(output_path):
            size_mb = os.path.getsize(output_path) / (1024 * 1024)
            print("Executable size: {0:.2f} MB".format(size_mb))
            print("Executable location: {0}".format(output_path))
        else:
            print("Warning: Expected executable not found: {0}".format(output_path))
        
        return True
        
    except subprocess.CalledProcessError as e:
        print("Build failed: {0}".format(e))
        return False
    finally:
        # Clean up spec file
        if spec_file.exists():
            spec_file.unlink()

def build_for_distribution():
    """Build executable for distribution (needs to run separately on each platform)"""
    system = platform.system()
    print("Building executable for {0}...".format(system))
    success = build_executable()
    
    if success:
        print("\nBuild completed!")
        print("Usage:")
        print("1. Double-click the executable to run")
        print("2. Or run from command line: ./SimpleNES <rom_file.nes>")
        print("3. Supported options: -s <scale> -w <width> -H <height>")
    else:
        print("\nBuild failed, please check error messages.")
        sys.exit(1)

if __name__ == "__main__":
    print("SimpleNES-py Cross-platform Build Tool")
    print("="*40)
    
    build_for_distribution()
