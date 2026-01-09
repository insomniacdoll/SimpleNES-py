# SimpleNES-py Project Summary

## Project Overview

SimpleNES-py is an NES (Nintendo Entertainment System) emulator implemented in Python, based on the original SimpleNES C++ project. This project aims to provide a fully functional NES emulator capable of running classic NES games.

## Architecture Design

### Core Components

1. **CPU Module (simple_nes/cpu/cpu.py)**
   - Implements Ricoh 2A03 CPU (based on 6502 processor)
   - Supports complete 6502 instruction set
   - Includes registers, flags, and interrupt handling (NMI, IRQ)

2. **PPU Module (simple_nes/ppu/ppu.py)**
   - Implements NES PPU (Picture Processing Unit, RP2C02)
   - Handles graphics rendering, scanlines, and frame synchronization
   - Supports sprite and background rendering
   - Implements OAM (Object Attribute Memory) for sprite management

3. **Virtual Screen (simple_nes/emulator/emulator.py)**
   - Virtual screen buffer for PPU rendering
   - Uses NumPy arrays for efficient pixel storage
   - Resolution: 256x240 pixels (NES native resolution)

4. **Memory Bus System (simple_nes/bus/mainbus.py)**
   - Implements CPU memory mapping
   - Handles memory read/write and I/O operations
   - Manages memory mirroring and external device communication
   - Supports callback-based I/O register handling

5. **Picture Bus (simple_nes/ppu/renderer.py)**
   - Separate memory bus for PPU graphics memory
   - Handles CHR ROM/RAM access
   - Supports nametable mirroring

6. **Cartridge and Mapper System (simple_nes/cartridge/)**
   - Supports iNES format ROM loading
   - Implements multiple common mappers (NROM, UxROM, CNROM, MMC3, AxROM, ColorDreams, GxROM, SxROM)
   - Handles PRG/CHR ROM mapping and bank switching
   - Supports mapper-specific features (IRQ, mirroring control)

7. **Controller System (simple_nes/controller/controller.py)**
   - Implements NES controller input
   - Supports keyboard mapping via configuration file
   - Handles controller state and strobe-based sequential reading
   - Supports two players simultaneously

8. **Audio System (simple_nes/apu/apu.py)**
   - Implements NES APU (Audio Processing Unit)
   - Includes two pulse channels, triangle wave channel, noise channel, and DMC channel
   - Supports sound effects and music playback
   - Runs at CPU frequency

9. **Rendering System (simple_nes/ppu/renderer.py)**
   - Uses Pygame for graphics rendering
   - Handles PPU output to screen conversion
   - Supports adjustable display scaling
   - Converts virtual screen buffer to display surface

10. **Configuration System (simple_nes/util/config.py)**
    - JSON-based configuration management
    - Supports logging configuration
    - Supports controller key mapping configuration

11. **Logging System (simple_nes/util/logging.py)**
    - Comprehensive logging for debugging and monitoring
    - Supports multiple log levels (DEBUG, INFO, WARNING, ERROR)
    - Console and file output support
    - Configurable log format

### Dependencies

- **Pygame** (>= 2.0.0): For graphics rendering, audio, and input processing
- **NumPy** (>= 1.21.0): For numerical calculations and buffer processing
- **Pillow** (>= 8.0.0): For image processing
- **PyInstaller** (>= 5.0.0): For building standalone executables

## File Structure

```
SimpleNES-py/
├── main.py                 # Main program entry point
├── requirements.txt        # Python dependencies
├── pyproject.toml         # Project configuration file
├── config.json            # Default configuration file
├── README.md              # Project description
├── PROJECT_SUMMARY.md     # Project summary documentation
├── BUILDING.md            # Build documentation
├── run.sh                 # Run script
├── build.py               # Build script
├── build_executable.py    # Alternative build script
├── build.sh               # Unix build script
├── hook-pygame.py         # PyInstaller hook for Pygame
├── simple_nes/            # Main source code package
│   ├── __init__.py
│   ├── apu/               # Audio Processing Unit
│   │   ├── __init__.py
│   │   └── apu.py         # APU emulator
│   ├── bus/               # Memory bus system
│   │   ├── __init__.py
│   │   └── mainbus.py     # Memory bus implementation
│   ├── cartridge/         # Cartridge system
│   │   ├── __init__.py
│   │   ├── cartridge.py   # Cartridge loading
│   │   └── mapper.py      # Mapper implementation
│   ├── controller/        # Controller system
│   │   ├── __init__.py
│   │   └── controller.py  # Controller implementation
│   ├── cpu/               # CPU system
│   │   ├── __init__.py
│   │   └── cpu.py         # CPU emulator
│   ├── emulator/          # Emulator core
│   │   ├── __init__.py
│   │   └── emulator.py    # Main emulator loop
│   ├── ppu/               # Picture Processing Unit
│   │   ├── __init__.py
│   │   ├── ppu.py         # PPU emulator
│   │   └── renderer.py    # Rendering system
│   └── util/              # Utility modules
│       ├── __init__.py
│       ├── config.py      # Configuration management
│       └── logging.py     # Logging system
├── tests/                 # Test files directory
│   ├── __init__.py
│   ├── test_basic_cpu.py
│   ├── test_opcode_fixes.py
│   └── unit/              # Unit tests
│       ├── __init__.py
│       ├── test_basic_imports_mocked.py
│       ├── test_basic_imports.py
│       ├── test_components.py
│       ├── test_integration.py
│       ├── test_module_functionality.py
│       └── test_ppu.py
├── venv/                  # Python virtual environment
└── __init__.py
```

## Usage

### Install Dependencies

```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
```

### Run Emulator

```bash
# Activate virtual environment
source venv/bin/activate

# Run emulator
python main.py [options] <rom_path>

# Example
python main.py -s 3 SuperMarioBros.nes
```

### Command Line Options

- `-h, --help`: Show help information
- `-s, --scale`: Set display scale (default: 3)
- `-w, --width`: Set window width
- `-H, --height`: Set window height
- `-c, --config`: Path to configuration file (default: config.json)

### Configuration

The emulator uses a JSON configuration file (`config.json` by default) for:

1. **Logging Configuration**
   - Log level (DEBUG, INFO, WARNING, ERROR)
   - Log file path
   - Console and file output toggles
   - Log format customization

2. **Controller Configuration**
   - Keyboard mapping for Player 1 and Player 2
   - Customizable button assignments

### Default Controls

**Player 1**
- A: J
- B: K
- Select: Right Shift
- Start: Enter
- Up: W
- Down: S
- Left: A
- Right: D

**Player 2**
- A: Numpad 5
- B: Numpad 6
- Select: Numpad 8
- Start: Numpad 9
- Up: Up Arrow
- Down: Down Arrow
- Left: Left Arrow
- Right: Right Arrow

**System Controls**
- ESC: Exit emulator

## Implementation Features

- **CPU Simulation**: Complete 6502 instruction set with proper interrupt handling
- **Graphics Rendering**: Full PPU functionality with background and sprite rendering, scanline-based timing
- **Audio Processing**: Complete APU implementation with all five sound channels
- **ROM Support**: iNES format ROM support with multiple mapper types
- **Input Processing**: Keyboard-based controls supporting two players, configurable via JSON
- **Memory Management**: Proper memory mapping with mirroring support
- **I/O Handling**: Callback-based I/O register system for flexible device communication
- **Logging**: Comprehensive logging system for debugging and monitoring
- **Configuration**: JSON-based configuration for easy customization
- **Extensibility**: Modular design, easy to add new features and mappers

## Emulation Details

### Timing
- CPU: ~1.79 MHz (NTSC)
- PPU: ~5.37 MHz (3x CPU frequency)
- APU: ~1.79 MHz (same as CPU)
- Frame rate: 60 FPS (NTSC)

### Video
- Resolution: 256x240 pixels
- Color palette: NES native colors
- Scaling: Adjustable via command line

### Audio
- Channels: 2 pulse, 1 triangle, 1 noise, 1 DMC
- Sample rate: Configurable via Pygame
- Support for both sound effects and music

## Current Status

SimpleNES-py has implemented the core functionality of an NES emulator, including CPU, PPU, memory system, cartridge mappers, controllers, audio system, and rendering. The emulator provides a solid foundation for running NES games and can be extended with additional features.

## Future Development Suggestions

1. **Complete CPU Instructions**: Ensure all 6502 instructions and precise timing
2. **Enhance PPU**: Implement full sprite 0 collision detection, scroll registers, etc.
3. **Optimize Performance**: Further optimize rendering and audio processing with NumPy
4. **Add Debugging Tools**: Memory viewer, CPU trace, PPU viewer, and other functionality
5. **Support More Mappers**: Implement more complex mapper types (MMC1, MMC5, etc.)
6. **Save States**: Implement game save and replay functionality
7. **Cheats**: Add Game Genie/Action Replay cheat code support
8. **Netplay**: Add network multiplayer support

## License

This project is based on the original SimpleNES project's license. See the LICENSE file for details.