# SimpleNES-py

A Python implementation of an NES emulator.

## Overview

SimpleNES-py is a Nintendo Entertainment System (NES) emulator written in Python. It aims to accurately emulate the NES hardware including the CPU, PPU (graphics processor), and memory systems to run classic NES games.

## Features

- CPU emulation (Ricoh 6502 processor)
- PPU emulation (picture processing unit)
- Memory bus system
- Cartridge/mapper support
- Controller input handling
- Graphical display using Pygame
- Support for various NES mappers

## Requirements

- Python 3.7+
- pygame
- numpy
- Pillow

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
python main.py [options] rom-file
```

## Supported Options

- `-h, --help`: Print help text and exit
- `-s, --scale`: Set video scale (default: 3)
- `-w, --width`: Set the width of the emulation screen
- `-H, --height`: Set the height of the emulation screen

## Project Structure

- `src/cpu/`: CPU emulation logic
- `src/ppu/`: Picture Processing Unit emulation
- `src/bus/`: Memory bus and I/O handling
- `src/cartridge/`: ROM loading and mapper implementations
- `src/controller/`: Input controller handling
- `src/emulator/`: Main emulator logic
