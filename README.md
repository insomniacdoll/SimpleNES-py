# SimpleNES-py

A Python implementation of an NES emulator.

## Overview

SimpleNES-py is a Nintendo Entertainment System (NES) emulator written in Python. It aims to accurately emulate the NES hardware including the CPU, PPU (graphics processor), APU (audio processing unit), and memory systems to run classic NES games.

## Features

- **CPU emulation**: Ricoh 2A03 processor (based on 6502) with complete instruction set
- **PPU emulation**: Picture Processing Unit with background and sprite rendering
- **APU emulation**: Audio Processing Unit with pulse, triangle, noise, and DMC channels
- **Memory bus system**: Complete memory mapping and I/O handling
- **Cartridge/mapper support**: Support for multiple mapper types (NROM, UxROM, CNROM, MMC3, AxROM, ColorDreams, GxROM, SxROM)
- **Controller input handling**: Support for two players with keyboard mapping
- **Graphical display**: Pygame-based rendering with adjustable scaling
- **Configurable system**: JSON-based configuration for logging and controller mapping
- **Logging system**: Comprehensive logging for debugging and monitoring

## Requirements

- Python 3.7+
- pygame >= 2.0.0
- numpy >= 1.21.0
- Pillow >= 8.0.0

## Installation

```bash
# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
```

## Usage

```bash
python main.py [options] <rom_path>
```

### Command Line Options

- `-h, --help`: Print help text and exit
- `-s, --scale`: Set video scale (default: 3)
- `-w, --width`: Set the width of the emulation screen
- `-H, --height`: Set the height of the emulation screen
- `-c, --config`: Path to the configuration file (default: config.json)

### Configuration

The emulator uses a `config.json` file for configuration:

```json
{
  "logging": {
    "level": "INFO",
    "file_path": "simple_nes.log",
    "console_output": true,
    "file_output": true,
    "format": "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s"
  },
  "controller": {
    "player1": {
      "A": "K_j",
      "B": "K_k",
      "SELECT": "K_RSHIFT",
      "START": "K_RETURN",
      "UP": "K_w",
      "DOWN": "K_s",
      "LEFT": "K_a",
      "RIGHT": "K_d"
    },
    "player2": {
      "A": "K_KP5",
      "B": "K_KP6",
      "SELECT": "K_KP8",
      "START": "K_KP9",
      "UP": "K_UP",
      "DOWN": "K_DOWN",
      "LEFT": "K_LEFT",
      "RIGHT": "K_RIGHT"
    }
  }
}
```

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

**Other Controls**
- ESC: Exit emulator

### Example Usage

```bash
# Run with default settings
python main.py SuperMarioBros.nes

# Run with custom scale
python main.py -s 4 SuperMarioBros.nes

# Run with custom window size
python main.py -w 800 -H 600 SuperMarioBros.nes

# Run with custom config
python main.py -c my_config.json SuperMarioBros.nes
```

## Project Structure

- `simple_nes/`: Main package directory
  - `simple_nes/cpu/`: CPU emulation logic (Ricoh 2A03)
  - `simple_nes/ppu/`: Picture Processing Unit emulation
  - `simple_nes/apu/`: Audio Processing Unit implementation
  - `simple_nes/bus/`: Memory bus and I/O handling
  - `simple_nes/cartridge/`: ROM loading and mapper implementations
  - `simple_nes/controller/`: Input controller handling
  - `simple_nes/emulator/`: Main emulator logic and game loop
  - `simple_nes/util/`: Utility functions (logging, configuration)
- `tests/`: Unit and integration tests
- `main.py`: Main program entry point
- `requirements.txt`: Python dependencies
- `pyproject.toml`: Project configuration
- `config.json`: Default configuration file
- `run.sh`: Convenience script for running the emulator
- `build.py`: Build script for creating executable
- `build_executable.py`: Alternative build script
- `build.sh`: Unix build script
- `BUILDING.md`: Building instructions
- `PROJECT_SUMMARY.md`: Detailed project documentation

## Building Executable

See `BUILDING.md` for detailed instructions on building standalone executables for Windows, macOS, and Linux.

## Supported Mappers

- Mapper 0: NROM
- Mapper 1: SxROM (MMC1)
- Mapper 2: UxROM (UNROM)
- Mapper 3: CNROM
- Mapper 4: MMC3
- Mapper 7: AxROM (ANROM)
- Mapper 11: ColorDreams
- Mapper 66: GxROM

## License

This project is based on the original SimpleNES project. See the LICENSE file for details.
