# SimpleNES-py Packaging Guide

## Overview
This project provides a set of cross-platform build scripts that can package SimpleNES-py into standalone executable files for Windows, macOS, and Linux using PyInstaller.

## Build Script Descriptions

### build.py
- Main build script, uses PyInstaller to package the project into executable files
- Works on all platforms (Windows, macOS, Linux)
- Generates a single executable file containing all dependencies
- Supports customization through command-line arguments

### build_executable.py
- Alternative build script, provides a simplified build process
- Also uses PyInstaller for packaging
- Useful for quick builds with minimal configuration

### build.sh
- Convenience build script for Unix systems (macOS/Linux)
- Automatically installs dependencies and runs the build
- Makes the build process easier on Unix-like systems

### hook-pygame.py
- PyInstaller hook file for Pygame
- Ensures Pygame resources are properly included in the executable
- Handles Pygame's hidden imports and data files

## Prerequisites

### System Requirements
- **Python**: 3.7 or higher
- **Disk Space**: At least 500 MB free space for build artifacts
- **Operating System**: Windows, macOS, or Linux

### Python Dependencies
The build process requires the following packages (listed in requirements.txt):
- pygame >= 2.0.0
- numpy >= 1.21.0
- Pillow >= 8.0.0
- pyinstaller >= 5.0.0

### Platform-Specific Dependencies

#### Windows
- No additional system dependencies required
- Python installer available from python.org

#### macOS
- Optional: Homebrew for easy Python installation
  ```bash
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
  brew install python3
  ```

#### Linux
- May need to install SDL libraries:
  ```bash
  # Ubuntu/Debian
  sudo apt-get install python3-dev libsdl2-dev
  
  # Fedora
  sudo dnf install python3-devel SDL2-devel
  
  # Arch Linux
  sudo pacman -S python sdl2
  ```

## Build Steps

### Step 1: Set Up Virtual Environment (Recommended)

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# Linux/macOS:
source venv/bin/activate

# Windows:
venv\Scripts\activate
```

### Step 2: Install Dependencies

```bash
# Install all required packages
pip install -r requirements.txt

# Verify PyInstaller is installed
pip show pyinstaller
```

### Step 3: Run Build

#### Method 1: Using build.py (Recommended)

```bash
python build.py
```

#### Method 2: Using build_executable.py

```bash
python build_executable.py
```

#### Method 3: Using build.sh (Unix Only)

```bash
# Make script executable
chmod +x build.sh

# Run build
./build.sh
```

## Build Process Details

The build process performs the following steps:

1. **Analysis**: PyInstaller analyzes the Python code and its dependencies
2. **Collection**: Gathers all required Python modules and libraries
3. **Packaging**: Bundles everything into a single executable
4. **Optimization**: Optimizes the executable for the target platform
5. **Output**: Produces the final executable in the `dist/` directory

## Output Files

After building, the executable file will be located in the `dist/` directory:

### Windows
- **Location**: `dist/SimpleNES.exe`
- **Size**: Typically 50-100 MB
- **Dependencies**: None (embedded in executable)

### macOS
- **Location**: `dist/SimpleNES`
- **Size**: Typically 60-120 MB
- **Dependencies**: None (embedded in executable)
- **Note**: May need to grant execution permissions on first run

### Linux
- **Location**: `dist/SimpleNES`
- **Size**: Typically 50-100 MB
- **Dependencies**: None (embedded in executable)
- **Note**: May need to grant execution permissions:
  ```bash
  chmod +x dist/SimpleNES
  ```

## Usage

The built executable file can be used in several ways:

### 1. Command Line Usage
```bash
# Windows
SimpleNES.exe <rom_file.nes> [options]

# macOS/Linux
./SimpleNES <rom_file.nes> [options]
```

### 2. Drag and Drop
- Drag a ROM file (.nes) onto the executable
- The emulator will automatically launch with that ROM

### 3. Double Click
- On Windows: Double-click the executable, then select a ROM file
- On macOS/Linux: May need to set executable permissions first

### Command Line Options
- `-s, --scale`: Set display scale factor (default: 3.0)
- `-w, --width`: Set display width
- `-H, --height`: Set display height
- `-c, --config`: Path to configuration file (default: config.json)

## Platform-Specific Notes

### Windows
- **Building**: Requires a Windows system to build Windows version
- **Antivirus**: May trigger false positives on first run
- **Compatibility**: Works on Windows 7 and later
- **Dependencies**: None required for the executable

### macOS
- **Building**: Requires a macOS system to build macOS version
- **Code Signing**: Unsigned executables may show security warnings
- **Gatekeeper**: May need to bypass Gatekeeper on first run:
  ```bash
  xattr -cr dist/SimpleNES
  ```
- **Apple Silicon**: Builds are universal binaries (Intel + ARM)

### Linux
- **Building**: Requires a Linux system to build Linux version
- **Dependencies**: Executable is self-contained
- **Desktop Integration**: Can create desktop entry for easy access
- **Wayland**: May need to run with XWayland for full compatibility

## Advanced Configuration

### Custom Build Options

#### 1. Modify build.py
Edit the `build.py` file to customize:
- Application name
- Icon settings
- Version information
- Additional data files
- Exclusion of unnecessary modules

#### 2. Create Custom Spec File
Create a `SimpleNES.spec` file in the project root:

```python
# SimpleNES.spec
a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('config.json', '.'),
        # Add other data files here
    ],
    hiddenimports=[
        'pygame',
        'numpy',
        'PIL',
    ],
    hookspath=['.'],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=None)
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
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
```

#### 3. Use PyInstaller Directly
```bash
# Basic command
pyinstaller --onefile --name SimpleNES main.py

# With icon (Windows/macOS)
pyinstaller --onefile --icon=icon.ico --name SimpleNES main.py

# With data files
pyinstaller --onefile --add-data "config.json:." --name SimpleNES main.py
```

### Adding Icons

#### Windows
```bash
# Use .ico file
pyinstaller --onefile --icon=appicon.ico --name SimpleNES main.py
```

#### macOS
```bash
# Use .icns file
pyinstaller --onefile --icon=appicon.icns --name SimpleNES main.py
```

#### Linux
```bash
# Use .png file (will be converted)
pyinstaller --onefile --icon=appicon.png --name SimpleNES main.py
```

## Troubleshooting

### Common Issues

#### 1. Import Errors
**Problem**: ModuleNotFoundError when running executable
**Solution**:
- Ensure all dependencies are listed in requirements.txt
- Add missing modules to hiddenimports in build.py
- Check PyInstaller logs in `build/` directory

#### 2. Large File Size
**Problem**: Executable is too large (>200 MB)
**Solution**:
- Exclude unnecessary modules in build.py
- Use UPX compression (enabled by default)
- Remove debug symbols with `--strip` option

#### 3. Runtime Errors
**Problem**: Application crashes on startup
**Solution**:
- Run from command line to see error messages
- Check if all data files are included
- Verify Pygame resources are bundled correctly

#### 4. macOS Gatekeeper Issues
**Problem**: "App is damaged and can't be opened"
**Solution**:
```bash
# Remove extended attributes
xattr -cr dist/SimpleNES

# Or temporarily disable Gatekeeper (not recommended)
sudo spctl --master-disable
```

#### 5. Windows Antivirus Detection
**Problem**: Antivirus flags executable as malware
**Solution**:
- Submit to VirusTotal for analysis
- Add to antivirus exclusion list
- Consider code signing for production releases

### Debug Mode

To enable debug mode for troubleshooting:

```bash
# Build with debug symbols
pyinstaller --onefile --debug all --name SimpleNES main.py

# Run with console output
pyinstaller --onefile --console --name SimpleNES main.py
```

### Clean Build

To perform a clean build:

```bash
# Remove build artifacts
rm -rf build/ dist/

# Rebuild
python build.py
```

## Performance Optimization

### 1. Reduce Startup Time
- Use `--strip` to remove debug symbols
- Exclude unnecessary modules
- Pre-compile Python modules

### 2. Reduce File Size
- Enable UPX compression (default)
- Exclude unused dependencies
- Use one-file mode (already default)

### 3. Improve Runtime Performance
- Profile the application to identify bottlenecks
- Optimize NumPy operations
- Consider using PyPy for JIT compilation

## Distribution

### Creating Installers

#### Windows (NSIS)
```bash
# Install NSIS
# Create installer script
# Build installer with makensis
```

#### macOS (DMG)
```bash
# Create DMG
hdiutil create -volname SimpleNES -srcfolder dist/ SimpleNES.dmg
```

#### Linux (AppImage)
```bash
# Use appimage-builder or linuxdeploy
# Create AppImage for easy distribution
```

## Additional Resources

- [PyInstaller Documentation](https://pyinstaller.org/)
- [Pygame Documentation](https://www.pygame.org/docs/)
- [Python Packaging Guide](https://packaging.python.org/)

## Support

For issues related to:
- **Building**: Check this guide and PyInstaller documentation
- **Emulation**: See README.md and PROJECT_SUMMARY.md
- **Bugs**: Report issues on GitHub repository

## License

This project is based on the original SimpleNES project's license. See the LICENSE file for details.