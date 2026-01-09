#!/usr/bin/env python3
"""
Main entry point for SimpleNES-py
NES emulator written in Python
"""

import sys
import os
import argparse
from simple_nes.emulator.emulator import Emulator
from simple_nes.util.logging import init_logging, info, error

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="SimpleNES-py: A Python NES emulator"
    )
    parser.add_argument(
        'rom_path',
        nargs='?',
        help='Path to the ROM file to load'
    )
    parser.add_argument(
        '-s', '--scale',
        type=float,
        default=3.0,
        help='Set video scale (default: 3)'
    )
    parser.add_argument(
        '-w', '--width',
        type=int,
        help='Set the width of the emulation screen'
    )
    parser.add_argument(
        '-H', '--height',
        type=int,
        help='Set the height of the emulation screen'
    )
    parser.add_argument(
        '-c', '--config',
        type=str,
        default='config.json',
        help='Path to the configuration file (default: config.json)'
    )
    
    return parser.parse_args()

def main():
    """Main function"""
    args = parse_arguments()
    
    # Initialize logging system
    init_logging()
    info("SimpleNES-py emulator starting up...")
    
    # Create emulator instance with config
    emulator = Emulator(config_path=args.config)
    
    # Set video parameters
    if args.scale:
        emulator.set_video_scale(args.scale)
    if args.width:
        emulator.set_video_width(args.width)
    if args.height:
        emulator.set_video_height(args.height)
    
    # Check if ROM path provided
    if not args.rom_path:
        error("No ROM file provided. Usage: python main.py [-s scale] [-w width] [-H height] [-c config] <rom_path>")
        # For testing purposes, you could load a default ROM if available
        # rom_path = "test_rom.nes"
        return
    
    # Verify ROM file exists
    if not os.path.exists(args.rom_path):
        error(f"ROM file not found: {args.rom_path}")
        return
    
    # Run the emulator
    info(f"Starting emulator with ROM: {args.rom_path}")
    emulator.run(args.rom_path)

if __name__ == "__main__":
    main()