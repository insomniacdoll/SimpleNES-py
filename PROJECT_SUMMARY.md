# SimpleNES-py Project Summary

## Project Overview

SimpleNES-py is an NES (Nintendo Entertainment System) emulator implemented in Python, based on the original SimpleNES C++ project. This project aims to provide a fully functional NES emulator capable of running classic NES games.

## Architecture Design

### Core Components

1. **CPU Module (simple_nes/cpu/cpu.py)**
   - Implements Ricoh 2A03 CPU (based on 6502 processor)
   - Supports complete 6502 instruction set
   - Includes registers, flags, and interrupt handling

2. **PPU Module (simple_nes/ppu/ppu.py)**
   - Implements NES PPU (Picture Processing Unit, RP2C02)
   - Handles graphics rendering, scanlines, and frame synchronization
   - Supports sprite and background rendering

3. **Memory Bus System (simple_nes/bus/mainbus.py)**
   - Implements CPU memory mapping
   - Handles memory read/write and I/O operations
   - Manages memory mirroring and external device communication

4. **Cartridge and Mapper System (simple_nes/cartridge/)**
   - Supports iNES format ROM loading
   - Implements multiple common mappers (NROM, UxROM, CNROM, MMC3, AxROM, ColorDreams, GxROM, SxROM)
   - Handles PRG/CHR ROM mapping and bank switching

5. **Controller System (simple_nes/controller/controller.py)**
   - Implements NES controller input
   - Supports keyboard mapping and gamepad input
   - Handles controller state and sequence reading

6. **Audio System (simple_nes/apu/apu.py)**
   - Implements NES APU (Audio Processing Unit)
   - Includes two pulse channels, triangle wave channel, noise channel, and DMC channel
   - Supports sound effects and music playback

7. **Rendering System (simple_nes/ppu/renderer.py)**
   - Uses Pygame for graphics rendering
   - Handles PPU output to screen conversion
   - Supports adjustable display scaling

### Dependencies

- **Pygame**: For graphics rendering, audio, and input processing
- **NumPy**: For numerical calculations and buffer processing
- **Pillow**: For image processing (optional)

## File Structure

```
SimpleNES-py/
├── main.py                 # Main program entry point
├── requirements.txt        # Python dependencies
├── pyproject.toml         # Project configuration file
├── README.md              # Project description
├── PROJECT_SUMMARY.md     # Project summary documentation
├── BUILDING.md            # Build documentation
├── run.sh                 # Run script
├── build.py               # Build script
├── build_executable.py    # Alternative build script
├── build.sh               # Unix build script
├── simple_nes/            # Main source code package
│   ├── __init__.py
│   ├── apu/               # Audio Processing Unit
│   │   ├── __init__.py
│   │   ├── apu.py         # APU emulator
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
│   │   ├── emulator.py    # Main emulator loop
│   │   └── apu.py         # Audio Processing Unit
│   └── ppu/               # Picture Processing Unit
│       ├── __init__.py
│       ├── ppu.py         # PPU emulator
│       └── renderer.py    # Rendering system
├── tests/                 # Test files directory
│   ├── __init__.py
│   └── unit/              # Unit tests
│       ├── __init__.py
│       ├── test_basic_imports_mocked.py
│       ├── test_basic_imports.py
│       ├── test_components.py
│       ├── test_integration.py
│       └── test_module_functionality.py
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

## Implementation Features

- **CPU Simulation**: Supports most of 6502 instruction set
- **Graphics Rendering**: Basic PPU functionality, supports background and sprite rendering
- **Audio Processing**: Implements complete APU, including all sound channels
- **ROM Support**: Supports iNES format ROM, compatible with multiple mappers
- **Input Processing**: Keyboard controls, supports two players
- **Extensibility**: Modular design, easy to add new features

## Current Status

SimpleNES-py has implemented the core functionality of an NES emulator, including CPU, PPU, memory system, cartridge mappers, controllers, and audio system. While it cannot yet run all NES games (as some advanced features are still under development), it has built a complete framework that can be extended and improved.

## Future Development Suggestions

1. **Complete CPU Instructions**: Implement all 6502 instructions and precise timing
2. **Enhance PPU**: Implement full sprite 0 collision detection, mask controls, etc.
3. **Optimize Performance**: Use NumPy to optimize rendering and audio processing
4. **Add Debugging Tools**: Memory viewer, CPU trace, and other functionality
5. **Support More Mappers**: Implement more complex mapper types
6. **Save States**: Implement game save and replay functionality

## License

This project is based on the original SimpleNES project's license. See the LICENSE file for details.