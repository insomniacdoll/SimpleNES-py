# SimpleNES-py Packaging Guide

## Overview
This project provides a set of cross-platform build scripts that can package SimpleNES-py into standalone executable files for Windows, macOS, and Linux.

## Build Script Descriptions

### build.py
- Main build script, uses PyInstaller to package the project into executable files
- Works on all platforms
- Generates a single executable file containing all dependencies

### build_executable.py
- Alternative build script, provides a simplified build process
- Also uses PyInstaller for packaging

### build.sh
- Convenience build script for Unix systems (macOS/Linux)
- Automatically installs dependencies and runs the build

## Build Steps

### General Build Method (Recommended)
1. Ensure Python 3.7+ is installed
2. Activate the project virtual environment (if present):
   ```bash
   source venv/bin/activate  # Linux/macOS
   # or
   venv\Scripts\activate     # Windows
   ```
3. Run build: `python build.py`

### Platform-Specific Methods

#### Windows
```cmd
# Activate virtual environment
venv\Scripts\activate

# Run build
python build.py
```

#### macOS/Linux
```bash
# Activate virtual environment
source venv/bin/activate

# Use convenience script
chmod +x build.sh
./build.sh

# Or run build script directly
python build.py
```

## Output Files
After building, the executable file will be located in the `dist/` directory:
- Windows: `dist/SimpleNES.exe`
- macOS: `dist/SimpleNES`
- Linux: `dist/SimpleNES`

## Usage
The built executable file can be:
1. Run directly by double-clicking
2. Run by dragging a ROM file onto the executable
3. Used from command line: `./SimpleNES <rom_file.nes> [options]`

Supported command line options:
- `-s, --scale`: Set display scale factor (default: 3.0)
- `-w, --width`: Set display width
- `-H, --height`: Set display height

## Cross-Platform Build Notes

### Windows
- Requires a Windows system to build Windows version (.exe)
- Can install Python and Git Bash to run shell scripts

### macOS
- Requires a macOS system to build macOS version
- Recommended to use Homebrew to install Python

### Linux
- Requires a Linux system to build Linux version
- May need to install additional system dependencies, such as SDL libraries

## Notes
1. The build process may take several minutes depending on system performance
2. The generated executable file contains the Python interpreter and all dependencies, so it is relatively large
3. On first run, it may be flagged by security software as a false positive; please add to trust list
4. For best performance and compatibility, it is recommended to build on the same platform as the target
5. The built executable is standalone and does not require Python or other dependencies to be installed

## Advanced Configuration
To customize build options (such as icons, version information, etc.), you can:
1. Modify the spec file content in `build.py`
2. Create a `SimpleNES.spec` file in the project root for advanced configuration
3. Use PyInstaller's command-line parameters for customization

## Troubleshooting
- If encountering dependency issues, ensure you are using the project's virtual environment
- If build fails, check PyInstaller logs in the `build/` directory
- For code signing issues on macOS, you may need to temporarily disable it to test the executable