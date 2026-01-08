"""
Cartridge and Mapper implementations for SimpleNES-py
Handles ROM loading and mapper logic
"""
from typing import List, Optional, Callable
import os

# Name table mirroring types
class NameTableMirroring:
    Horizontal = 0
    Vertical = 1
    FourScreen = 8
    OneScreenLower = 9
    OneScreenHigher = 10

class Cartridge:
    def __init__(self):
        self.prg_rom = []  # Program ROM
        self.chr_rom = []  # Character ROM
        self.name_table_mirroring = NameTableMirroring.Horizontal
        self.mapper_number = 0
        self.extended_ram = False
        self.chr_ram = False
    
    def load_from_file(self, path: str) -> bool:
        """Load ROM from file"""
        if not os.path.exists(path):
            print(f"ROM file not found: {path}")
            return False
        
        try:
            with open(path, 'rb') as f:
                rom_data = list(f.read())
            
            # Check for iNES header (16 bytes)
            if len(rom_data) < 16:
                print("Invalid ROM file: too small")
                return False
            
            # Validate header signature
            if rom_data[0] != 0x4E or rom_data[1] != 0x45 or rom_data[2] != 0x53 or rom_data[3] != 0x1A:
                print("Invalid ROM file: wrong header")
                return False
            
            # Extract header information
            prg_rom_size = rom_data[4] * 16384  # 16KB units
            chr_rom_size = rom_data[5] * 8192   # 8KB units
            flags_6 = rom_data[6]
            flags_7 = rom_data[7]
            prg_ram_size = rom_data[8] or 1     # If 0, use 1 page (8KB)
            flags_9 = rom_data[9]
            flags_10 = rom_data[10]
            
            # Extract mapper number
            self.mapper_number = ((flags_6 >> 4) | (flags_7 & 0xF0))
            
            # Extract mirroring type
            if flags_6 & 0x01:
                self.name_table_mirroring = NameTableMirroring.Vertical
            else:
                self.name_table_mirroring = NameTableMirroring.Horizontal
            
            # Check for four-screen mirroring
            if flags_6 & 0x08:
                self.name_table_mirroring = NameTableMirroring.FourScreen
            
            # Check for extended RAM
            self.extended_ram = bool(flags_6 & 0x02)
            
            # Check for CHR RAM (if no CHR ROM)
            self.chr_ram = (chr_rom_size == 0)
            
            # Extract ROM data
            header_size = 16
            trainer_size = 512 if (flags_6 & 0x04) else 0
            
            start_offset = header_size + trainer_size
            
            # Load PRG ROM
            self.prg_rom = rom_data[start_offset:start_offset + prg_rom_size]
            start_offset += prg_rom_size
            
            # Load CHR ROM
            if not self.chr_ram:
                self.chr_rom = rom_data[start_offset:start_offset + chr_rom_size]
            else:
                # Initialize CHR RAM if needed
                self.chr_rom = [0] * 8192  # 8KB of CHR RAM
            
            print(f"Loaded ROM: {os.path.basename(path)}")
            print(f"  Mapper: {self.mapper_number}")
            print(f"  PRG ROM: {prg_rom_size} bytes")
            print(f"  CHR ROM: {chr_rom_size} bytes")
            print(f"  Mirroring: {self.name_table_mirroring}")
            
            return True
        except Exception as e:
            print(f"Error loading ROM: {e}")
            return False
    
    def get_rom(self) -> List[int]:
        """Get PRG ROM data"""
        return self.prg_rom
    
    def get_vrom(self) -> List[int]:
        """Get CHR ROM data"""
        return self.chr_rom
    
    def get_mapper(self) -> int:
        """Get mapper number"""
        return self.mapper_number
    
    def get_name_table_mirroring(self) -> int:
        """Get name table mirroring type"""
        return self.name_table_mirroring
    
    def has_extended_ram(self) -> bool:
        """Check if cartridge has extended RAM"""
        return self.extended_ram