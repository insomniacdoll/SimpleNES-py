"""
Memory Bus System for SimpleNES-py
Handles memory access and I/O operations
"""
from typing import Dict, Callable, Optional
from ..cartridge.cartridge import Cartridge
from ..cartridge.mapper import Mapper

# I/O Register addresses
PPUCTRL = 0x2000
PPUMASK = 0x2001
PPUSTATUS = 0x2002
OAMADDR = 0x2003
OAMDATA = 0x2004
PPUSCROL = 0x2005
PPUADDR = 0x2006
PPUDATA = 0x2007
OAMDMA = 0x4014
JOY1 = 0x4016
JOY2 = 0x4017

class MainBus:
    def __init__(self):
        # CPU RAM: 2KB (0x800 bytes)
        self.ram = [0] * 0x800
        
        # Mapper for cartridge
        self.mapper: Optional[Mapper] = None
        
        # I/O callbacks
        self.write_callbacks: Dict[int, Callable[[int], None]] = {}
        self.read_callbacks: Dict[int, Callable[[], int]] = {}
    
    def set_mapper(self, mapper: Mapper) -> bool:
        """Set the cartridge mapper"""
        self.mapper = mapper
        return True
    
    def set_write_callback(self, reg: int, callback: Callable[[int], None]) -> bool:
        """Set a callback for writing to an I/O register"""
        self.write_callbacks[reg] = callback
        return True
    
    def set_read_callback(self, reg: int, callback: Callable[[], int]) -> bool:
        """Set a callback for reading from an I/O register"""
        self.read_callbacks[reg] = callback
        return True
    
    def read(self, addr: int) -> int:
        """Read a byte from memory"""
        if addr < 0x2000:
            # CPU RAM (mirrored every 0x800 bytes)
            return self.ram[addr & 0x7FF]
        elif addr < 0x4000:
            # PPU registers (mirrored every 8 bytes)
            reg = 0x2000 + (addr & 0x7)
            if reg in self.read_callbacks:
                return self.read_callbacks[reg]()
            return 0  # Default return value
        elif addr < 0x4018:
            # APU registers and I/O registers
            if addr in self.read_callbacks:
                return self.read_callbacks[addr]()
            return 0
        elif addr < 0x6000:
            # Expansion ROM (not supported)
            return 0
        elif addr < 0x8000:
            # PRG-RAM: delegate to mapper
            if self.mapper:
                return self.mapper.read_prg(addr)
            return 0
        else:
            # PRG-ROM: delegate to mapper
            if self.mapper:
                return self.mapper.read_prg(addr)
            else:
                return 0
    
    def write(self, addr: int, value: int):
        """Write a byte to memory"""
        if addr < 0x2000:
            # CPU RAM (mirrored every 0x800 bytes)
            self.ram[addr & 0x7FF] = value
        elif addr < 0x4000:
            # PPU registers (mirrored every 8 bytes)
            reg = 0x2000 + (addr & 0x7)
            if reg in self.write_callbacks:
                self.write_callbacks[reg](value)
        elif addr < 0x4018:
            # APU registers and I/O registers
            if addr in self.write_callbacks:
                self.write_callbacks[addr](value)
        elif addr < 0x6000:
            # Expansion ROM (not supported)
            pass
        elif addr < 0x8000:
            # PRG-RAM: delegate to mapper
            if self.mapper:
                self.mapper.write_prg(addr, value)
        else:
            # PRG-ROM registers: delegate to mapper
            if self.mapper:
                self.mapper.write_prg(addr, value)
    
    def get_page_ptr(self, page: int) -> Optional[bytes]:
        """Get a pointer to a 256-byte page of memory (for DMA)"""
        addr = page << 8
        if addr < 0x2000:
            # RAM pages
            return bytes(self.ram[addr & 0x7FF:(addr & 0x7FF) + 0x100])
        elif addr < 0x4020:
            # Register address - cannot DMA
            return None
        elif addr < 0x6000:
            # Expansion ROM - unsupported
            return None
        elif addr < 0x8000:
            # PRG-RAM: delegate to mapper or use cartridge ext_ram
            if self.mapper and self.mapper.has_extended_ram():
                # Use mapper's PRG-RAM access
                page_data = []
                for i in range(0x100):
                    page_data.append(self.mapper.read_prg(addr + i))
                return bytes(page_data)
            return None
        else:
            # PRG-ROM - cannot DMA
            return None