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
        # CPU RAM: 2KB mirrored to fill 0x0000-0x1FFF
        self.ram = [0] * 0x800  # 2KB of actual RAM
        self.ram.extend(self.ram)  # Mirror to 0x1000
        self.ram.extend(self.ram)  # Mirror to 0x1800
        self.ram.extend(self.ram)  # Mirror to 0x2000
        
        # Extended RAM (for cartridges that support it)
        self.ext_ram = [0] * 0x2000  # 8KB extended RAM
        
        # Mapper for cartridge
        self.mapper: Optional[Mapper] = None
        
        # I/O callbacks
        self.write_callbacks: Dict[int, Callable[[int], None]] = {}
        self.read_callbacks: Dict[int, Callable[[], int]] = {}
        
        # APU registers placeholder
        self.apu_regs = [0] * (0x4014 - 0x4000)
    
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
        elif addr < 0x4014:
            # APU registers and I/O registers
            if addr == JOY1:
                # Placeholder for controller 1
                return 0xFF
            elif addr == JOY2:
                # Placeholder for controller 2
                return 0xFF
            else:
                # Return APU register value
                return self.apu_regs[addr - 0x4000]
        elif addr == OAMDMA:
            # DMA register - handled by write only
            return 0
        elif addr < 0x6000:
            # APU registers and I/O (0x4014-0x401F)
            if addr == OAMDMA:
                return 0
            else:
                return 0
        elif addr < 0x8000:
            # Save RAM
            return self.ext_ram[addr - 0x6000]
        else:
            # Cartridge ROM/PRG-ROM space
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
        elif addr < 0x4014:
            # APU registers and I/O registers
            if addr in self.write_callbacks:
                self.write_callbacks[addr](value)
            else:
                # Store in APU registers array
                if 0x4000 <= addr < 0x4014:
                    self.apu_regs[addr - 0x4000] = value
        elif addr == OAMDMA:
            # DMA - trigger DMA transfer
            if self.write_callbacks.get(OAMDMA):
                self.write_callbacks[OAMDMA](value)
        elif addr < 0x6000:
            # APU registers and I/O (0x4014-0x401F)
            if addr in self.write_callbacks:
                self.write_callbacks[addr](value)
        elif addr < 0x8000:
            # Save RAM
            self.ext_ram[addr - 0x6000] = value
        else:
            # Cartridge ROM/PRG-ROM space
            if self.mapper:
                self.mapper.write_prg(addr, value)
    
    def get_page_ptr(self, page: int) -> Optional[bytes]:
        """Get a pointer to a 256-byte page of memory (for DMA)"""
        if page < 0x20:
            # RAM pages
            start_idx = (page * 0x100) % 0x800
            return bytes(self.ram[start_idx:start_idx + 0x100])
        else:
            # For other pages, return from cartridge if available
            if self.mapper:
                # This is a simplified approach - in a real implementation
                # we'd need to handle PRG-ROM pages
                return bytes([self.mapper.read_prg(page * 0x100 + i) for i in range(0x100)])
            return None