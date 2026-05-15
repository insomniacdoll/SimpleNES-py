"""
Mapper implementations for SimpleNES-py
Handles different NES cartridge mapper types
"""
from abc import ABC, abstractmethod
from typing import List, Callable
from .cartridge import Cartridge, NameTableMirroring
from ..util.logging import warning

class Mapper(ABC):
    class Type:
        NROM = 0
        SxROM = 1  # MMC1
        UxROM = 2  # UNROM
        CNROM = 3  # CNROM
        MMC3 = 4   # MMC3
        AxROM = 7  # ANROM
        ColorDreams = 11
        GxROM = 66

    def __init__(self, cart: Cartridge, mapper_type: int,
                 irq_cb: Callable[[], None] = None,
                 mirroring_cb: Callable[[], None] = None):
        self.cartridge = cart
        self.type = mapper_type
        self.irq_callback = irq_cb
        self.mirroring_callback = mirroring_cb

    @abstractmethod
    def write_prg(self, addr: int, value: int):
        """Write to PRG ROM address space"""
        pass

    @abstractmethod
    def read_prg(self, addr: int) -> int:
        """Read from PRG ROM address space"""
        pass

    @abstractmethod
    def read_chr(self, addr: int) -> int:
        """Read from CHR ROM address space"""
        pass

    @abstractmethod
    def write_chr(self, addr: int, value: int):
        """Write to CHR ROM address space"""
        pass

    def get_name_table_mirroring(self) -> int:
        """Get the nametable mirroring type for this mapper"""
        return self.cartridge.get_name_table_mirroring()

    def has_extended_ram(self) -> bool:
        """Check if cartridge has extended RAM"""
        return self.cartridge.has_extended_ram()

    def scanline_irq(self):
        """Called at each scanline for mappers that support IRQ"""
        pass

    @staticmethod
    def create_mapper(mapper_type: int, cart: Cartridge, 
                      irq_cb: Callable[[], None] = None,
                      mirroring_cb: Callable[[], None] = None) -> 'Mapper':
        """Factory method to create appropriate mapper instance"""
        if mapper_type == Mapper.Type.NROM:
            return NROM(cart, mirroring_cb=mirroring_cb)
        elif mapper_type == Mapper.Type.UxROM:
            return UxROM(cart, mirroring_cb=mirroring_cb)
        elif mapper_type == Mapper.Type.CNROM:
            return CNROM(cart, mirroring_cb=mirroring_cb)
        elif mapper_type == Mapper.Type.MMC3:
            return MMC3(cart, irq_cb=irq_cb, mirroring_cb=mirroring_cb)
        elif mapper_type == Mapper.Type.AxROM:
            return AxROM(cart, mirroring_cb=mirroring_cb)
        elif mapper_type == Mapper.Type.ColorDreams:
            return ColorDreams(cart, mirroring_cb=mirroring_cb)
        elif mapper_type == Mapper.Type.GxROM:
            return GxROM(cart, mirroring_cb=mirroring_cb)
        elif mapper_type == Mapper.Type.SxROM:
            return SxROM(cart, mirroring_cb=mirroring_cb)
        else:
            warning(f"Unsupported mapper type: {mapper_type}, using NROM")
            return NROM(cart, mirroring_cb=mirroring_cb)


class NROM(Mapper):
    """Mapper 0 - NROM: No mapper, simple PRG/CHR ROM"""
    
    def __init__(self, cart: Cartridge, mirroring_cb: Callable[[], None] = None):
        super().__init__(cart, Mapper.Type.NROM, mirroring_cb=mirroring_cb)
        self.prg_banks = len(cart.get_rom()) // 0x4000  # 16KB banks
    
    def write_prg(self, addr: int, value: int):
        """Single write_prg handling PRG-RAM and ROM space"""
        if 0x6000 <= addr < 0x8000:
            # PRG-RAM write
            if self.has_extended_ram():
                ext_ram = self.cartridge.get_ext_ram()
                ext_ram[addr - 0x6000] = value
        # NROM has no writable registers in $8000-$FFFF
    
    def read_prg(self, addr: int) -> int:
        """Single read_prg handling PRG-RAM and ROM"""
        if 0x6000 <= addr < 0x8000:
            # PRG-RAM read
            if self.has_extended_ram():
                ext_ram = self.cartridge.get_ext_ram()
                return ext_ram[addr - 0x6000]
            return 0
        elif addr >= 0x8000:
            # PRG ROM
            rom_data = self.cartridge.get_rom()
            if not rom_data:
                return 0
            effective_addr = addr - 0x8000
            if self.prg_banks == 1:
                # If only 1 bank, mirror it
                effective_addr = effective_addr % len(rom_data)
            else:
                # 2 or more banks
                effective_addr = effective_addr % len(rom_data)
            if effective_addr < len(rom_data):
                return rom_data[effective_addr]
        return 0
    
    def read_chr(self, addr: int) -> int:
        chr_rom = self.cartridge.get_vrom()
        if addr < len(chr_rom):
            return chr_rom[addr]
        return 0
    
    def write_chr(self, addr: int, value: int):
        """CHR-RAM write (if cartridge has CHR-RAM)"""
        if self.cartridge.has_chr_ram():
            chr_rom = self.cartridge.get_vrom()
            if addr < len(chr_rom):
                chr_rom[addr] = value


class UxROM(Mapper):
    """Mapper 2 - UNROM: Simple bank switching for PRG ROM"""
    
    def __init__(self, cart: Cartridge, mirroring_cb: Callable[[], None] = None):
        super().__init__(cart, Mapper.Type.UxROM, mirroring_cb=mirroring_cb)
        self.prg_banks = len(cart.get_rom()) // 0x4000
        self.prg_bank_select = 0
    
    def write_prg(self, addr: int, value: int):
        """Single write_prg handling PRG-RAM and bank select"""
        if 0x6000 <= addr < 0x8000:
            # PRG-RAM write
            if self.has_extended_ram():
                ext_ram = self.cartridge.get_ext_ram()
                ext_ram[addr - 0x6000] = value
        elif addr >= 0x8000:
            # Bank select register
            if self.prg_banks > 0:
                self.prg_bank_select = value & (self.prg_banks - 1)
            else:
                self.prg_bank_select = 0
    
    def read_prg(self, addr: int) -> int:
        if 0x6000 <= addr < 0x8000:
            if self.has_extended_ram():
                ext_ram = self.cartridge.get_ext_ram()
                return ext_ram[addr - 0x6000]
            return 0
        elif 0x8000 <= addr < 0xC000:
            # First 16KB (switchable)
            bank_offset = (self.prg_bank_select * 0x4000) + (addr - 0x8000)
            rom_data = self.cartridge.get_rom()
            if bank_offset < len(rom_data):
                return rom_data[bank_offset]
        elif 0xC000 <= addr <= 0xFFFF:
            # Last 16KB (fixed)
            last_bank = self.prg_banks - 1 if self.prg_banks > 0 else 0
            bank_offset = (last_bank * 0x4000) + (addr - 0xC000)
            rom_data = self.cartridge.get_rom()
            if bank_offset < len(rom_data):
                return rom_data[bank_offset]
        return 0
    
    def read_chr(self, addr: int) -> int:
        chr_rom = self.cartridge.get_vrom()
        if addr < len(chr_rom):
            return chr_rom[addr]
        return 0
    
    def write_chr(self, addr: int, value: int):
        if self.cartridge.has_chr_ram():
            chr_rom = self.cartridge.get_vrom()
            if addr < len(chr_rom):
                chr_rom[addr] = value


class CNROM(Mapper):
    """Mapper 3 - CNROM: Simple bank switching for CHR ROM"""
    
    def __init__(self, cart: Cartridge, mirroring_cb: Callable[[], None] = None):
        super().__init__(cart, Mapper.Type.CNROM, mirroring_cb=mirroring_cb)
        self.chr_bank_select = 0
    
    def write_prg(self, addr: int, value: int):
        """Single write_prg handling PRG-RAM and CHR bank select"""
        if 0x6000 <= addr < 0x8000:
            if self.has_extended_ram():
                ext_ram = self.cartridge.get_ext_ram()
                ext_ram[addr - 0x6000] = value
        elif addr >= 0x8000:
            # CHR bank select
            self.chr_bank_select = value & 0x03
    
    def read_prg(self, addr: int) -> int:
        if 0x6000 <= addr < 0x8000:
            if self.has_extended_ram():
                ext_ram = self.cartridge.get_ext_ram()
                return ext_ram[addr - 0x6000]
            return 0
        elif addr >= 0x8000:
            effective_addr = addr - 0x8000
            rom_data = self.cartridge.get_rom()
            if effective_addr < len(rom_data):
                return rom_data[effective_addr]
        return 0
    
    def read_chr(self, addr: int) -> int:
        chr_rom = self.cartridge.get_vrom()
        bank_offset = (self.chr_bank_select * 0x2000) + addr
        if bank_offset < len(chr_rom):
            return chr_rom[bank_offset]
        return 0
    
    def write_chr(self, addr: int, value: int):
        if self.cartridge.has_chr_ram():
            chr_rom = self.cartridge.get_vrom()
            bank_offset = (self.chr_bank_select * 0x2000) + addr
            if bank_offset < len(chr_rom):
                chr_rom[bank_offset] = value


class MMC3(Mapper):
    """
    Mapper 4 - MMC3: Advanced bank switching and IRQ
    
    IRQ Implementation Note (Temporary Callback Model):
    
    This implementation uses edge-triggered callback, NOT the C++ IRQ line
    pull/release model. Test scope must be limited to:
    
    - $C000: Set IRQ latch value
    - $C001: Reload counter (set to 0, mark reload pending)
    - $E000: Disable IRQ (clear irq_enabled, no callback trigger)
    - $E001: Enable IRQ (set irq_enabled, does NOT trigger immediately)
    - Counter decrement: When counter goes from 1 to 0, trigger callback
    
    DO NOT test:
    - IRQ release semantics (belongs to future IRQLine model)
    - Multiple IRQ sources sharing same line
    - IRQ line state persistence
    
    Future: Should migrate to IRQHandler.pull()/release() with IRQLine model.
    """
    
    def __init__(self, cart: Cartridge, irq_cb: Callable[[], None] = None,
                 mirroring_cb: Callable[[], None] = None):
        super().__init__(cart, Mapper.Type.MMC3, irq_cb=irq_cb, mirroring_cb=mirroring_cb)
        
        # Bank registers
        self.target_register = 0
        self.prg_bank_mode = False
        self.chr_inversion = False
        self.bank_registers = [0] * 8
        
        # CHR banks (8 x 1KB)
        self.chr_banks = [0] * 8
        
        # PRG banks (4 x 8KB)
        self.prg_banks = [0, 0, 0, 0]
        
        # IRQ (temporary implementation)
        self.irq_counter = 0
        self.irq_latch = 0
        self.irq_enabled = False
        self.irq_reload = False
        
        # PRG-RAM (32KB, managed by MMC3)
        self.prg_ram = [0] * 0x8000
        
        # Mirroring RAM (4KB for four-screen mode)
        self.mirroring_ram = [0] * 0x1000
        self.mirroring = NameTableMirroring.Horizontal
        
        self._initialize_banks()
    
    def _initialize_banks(self):
        rom_data = self.cartridge.get_rom()
        rom_size = len(rom_data)
        chr_data = self.cartridge.get_vrom()
        chr_size = len(chr_data) if chr_data else 0
        
        # PRG: Initialize all 4 banks to last two 8KB banks (C++ parity)
        # Banks 0,1 are switchable but should have valid initial values
        # Banks 2,3 are fixed to last two banks
        self.prg_banks[0] = max(0, rom_size - 0x4000)
        self.prg_banks[1] = max(0, rom_size - 0x2000)
        self.prg_banks[2] = max(0, rom_size - 0x4000)
        self.prg_banks[3] = max(0, rom_size - 0x2000)
        
        # CHR: initialize to last 1KB banks
        if chr_size > 0:
            for i in range(8):
                self.chr_banks[i] = max(0, chr_size - 0x400)
            self.chr_banks[0] = max(0, chr_size - 0x800)
            self.chr_banks[3] = max(0, chr_size - 0x800)
    
    def has_extended_ram(self) -> bool:
        """MMC3 always has PRG-RAM"""
        return True
    
    def write_prg(self, addr: int, value: int):
        """Single write_prg handling PRG-RAM and all registers"""
        if 0x6000 <= addr <= 0x7FFF:
            # PRG-RAM write
            self.prg_ram[addr & 0x1FFF] = value
        
        elif 0x8000 <= addr <= 0x9FFF:
            if addr & 0x01 == 0:  # Bank select ($8000)
                self.target_register = value & 0x07
                self.prg_bank_mode = bool(value & 0x40)
                self.chr_inversion = bool(value & 0x80)
            else:  # Bank data ($8001)
                self.bank_registers[self.target_register] = value
                self._update_banks()
        
        elif 0xA000 <= addr <= 0xBFFF:
            if addr & 0x01 == 0:  # Mirroring ($A000)
                if self.cartridge.get_name_table_mirroring() & 0x08:
                    self.mirroring = NameTableMirroring.FourScreen
                elif value & 0x01:
                    self.mirroring = NameTableMirroring.Horizontal
                else:
                    self.mirroring = NameTableMirroring.Vertical
                if self.mirroring_callback:
                    self.mirroring_callback()
        
        elif 0xC000 <= addr <= 0xDFFF:
            if addr & 0x01 == 0:  # IRQ latch ($C000)
                self.irq_latch = value
            else:  # IRQ reload ($C001)
                self.irq_counter = 0
                self.irq_reload = True
        
        elif 0xE000 <= addr <= 0xFFFF:
            if addr & 0x01 == 0:  # IRQ disable ($E000)
                self.irq_enabled = False
            else:  # IRQ enable ($E001)
                self.irq_enabled = True
    
    def _update_banks(self):
        rom_data = self.cartridge.get_rom()
        rom_size = len(rom_data)
        chr_data = self.cartridge.get_vrom()
        chr_size = len(chr_data) if chr_data else 0
        
        # CHR bank update
        if not self.chr_inversion:
            self.chr_banks[0] = (self.bank_registers[0] & 0xFE) * 0x400
            self.chr_banks[1] = self.chr_banks[0] + 0x400
            self.chr_banks[2] = (self.bank_registers[1] & 0xFE) * 0x400
            self.chr_banks[3] = self.chr_banks[2] + 0x400
            self.chr_banks[4] = self.bank_registers[2] * 0x400
            self.chr_banks[5] = self.bank_registers[3] * 0x400
            self.chr_banks[6] = self.bank_registers[4] * 0x400
            self.chr_banks[7] = self.bank_registers[5] * 0x400
        else:
            self.chr_banks[0] = self.bank_registers[2] * 0x400
            self.chr_banks[1] = self.bank_registers[3] * 0x400
            self.chr_banks[2] = self.bank_registers[4] * 0x400
            self.chr_banks[3] = self.bank_registers[5] * 0x400
            self.chr_banks[4] = (self.bank_registers[0] & 0xFE) * 0x400
            self.chr_banks[5] = self.chr_banks[4] + 0x400
            self.chr_banks[6] = (self.bank_registers[1] & 0xFE) * 0x400
            self.chr_banks[7] = self.chr_banks[6] + 0x400
        
        # Clamp CHR offsets (defensive handling for empty/invalid ROM)
        for i in range(8):
            if chr_size > 0:
                self.chr_banks[i] = min(self.chr_banks[i], chr_size - 0x400)
            else:
                self.chr_banks[i] = 0
        
        # PRG bank update
        if not self.prg_bank_mode:
            self.prg_banks[0] = (self.bank_registers[6] & 0x3F) * 0x2000
            self.prg_banks[1] = (self.bank_registers[7] & 0x3F) * 0x2000
            self.prg_banks[2] = max(0, rom_size - 0x4000)
            self.prg_banks[3] = max(0, rom_size - 0x2000)
        else:
            self.prg_banks[0] = max(0, rom_size - 0x4000)
            self.prg_banks[1] = (self.bank_registers[7] & 0x3F) * 0x2000
            self.prg_banks[2] = (self.bank_registers[6] & 0x3F) * 0x2000
            self.prg_banks[3] = max(0, rom_size - 0x2000)
        
        # Clamp PRG offsets (defensive handling)
        for i in range(4):
            self.prg_banks[i] = min(self.prg_banks[i], max(0, rom_size - 0x2000))
    
    def read_prg(self, addr: int) -> int:
        if 0x6000 <= addr <= 0x7FFF:
            return self.prg_ram[addr & 0x1FFF]
        
        elif 0x8000 <= addr <= 0x9FFF:
            offset = self.prg_banks[0] + (addr & 0x1FFF)
        elif 0xA000 <= addr <= 0xBFFF:
            offset = self.prg_banks[1] + (addr & 0x1FFF)
        elif 0xC000 <= addr <= 0xDFFF:
            offset = self.prg_banks[2] + (addr & 0x1FFF)
        elif 0xE000 <= addr <= 0xFFFF:
            offset = self.prg_banks[3] + (addr & 0x1FFF)
        else:
            return 0
        
        rom_data = self.cartridge.get_rom()
        if offset < len(rom_data):
            return rom_data[offset]
        return 0
    
    def read_chr(self, addr: int) -> int:
        """Read CHR including mirroring RAM for four-screen mode"""
        if addr <= 0x1FFF:
            # Pattern table
            bank_select = addr >> 10
            offset = self.chr_banks[bank_select] + (addr & 0x3FF)
            chr_data = self.cartridge.get_vrom()
            if chr_data and offset < len(chr_data):
                return chr_data[offset]
        elif addr <= 0x2FFF:
            # Mirroring RAM (four-screen mode)
            return self.mirroring_ram[addr - 0x2000]
        return 0
    
    def write_chr(self, addr: int, value: int):
        """Write CHR including mirroring RAM"""
        if 0x2000 <= addr <= 0x2FFF:
            # Mirroring RAM
            self.mirroring_ram[addr - 0x2000] = value
    
    def scanline_irq(self):
        """MMC3 scanline IRQ (temporary callback implementation)"""
        zero_transition = False
        
        if self.irq_counter == 0 or self.irq_reload:
            self.irq_counter = self.irq_latch
            self.irq_reload = False
        else:
            self.irq_counter -= 1
            zero_transition = (self.irq_counter == 0)
        
        if zero_transition and self.irq_enabled:
            if self.irq_callback:
                self.irq_callback()
    
    def get_name_table_mirroring(self) -> int:
        return self.mirroring


class AxROM(Mapper):
    """Mapper 7 - AxROM: 32KB PRG bank switching with mirroring control"""
    
    def __init__(self, cart: Cartridge, mirroring_cb: Callable[[], None] = None):
        super().__init__(cart, Mapper.Type.AxROM, mirroring_cb=mirroring_cb)
        self.prg_bank_select = 0
        self.mirroring = NameTableMirroring.OneScreenLower
    
    def write_prg(self, addr: int, value: int):
        """Single write_prg handling PRG-RAM and bank/mirroring select"""
        if 0x6000 <= addr < 0x8000:
            # PRG-RAM write
            if self.has_extended_ram():
                ext_ram = self.cartridge.get_ext_ram()
                ext_ram[addr - 0x6000] = value
        elif addr >= 0x8000:
            # Bank select and mirroring (C++: value & 0x07 for bank, bit4 for mirroring)
            self.prg_bank_select = value & 0x07
            self.mirroring = (NameTableMirroring.OneScreenHigher 
                             if (value & 0x10) 
                             else NameTableMirroring.OneScreenLower)
            if self.mirroring_callback:
                self.mirroring_callback()
    
    def read_prg(self, addr: int) -> int:
        if 0x6000 <= addr < 0x8000:
            if self.has_extended_ram():
                ext_ram = self.cartridge.get_ext_ram()
                return ext_ram[addr - 0x6000]
            return 0
        elif addr >= 0x8000:
            # 32KB switchable bank
            bank_offset = (self.prg_bank_select * 0x8000) + (addr - 0x8000)
            rom_data = self.cartridge.get_rom()
            if bank_offset < len(rom_data):
                return rom_data[bank_offset]
        return 0
    
    def read_chr(self, addr: int) -> int:
        # AxROM uses CHR-RAM (8KB)
        chr_rom = self.cartridge.get_vrom()
        if addr < len(chr_rom):
            return chr_rom[addr]
        return 0
    
    def write_chr(self, addr: int, value: int):
        """CHR-RAM write - only write if cartridge has CHR-RAM"""
        # AxROM typically uses CHR-RAM, but check to avoid modifying CHR-ROM
        if self.cartridge.has_chr_ram():
            chr_rom = self.cartridge.get_vrom()
            if addr < len(chr_rom):
                chr_rom[addr] = value
    
    def get_name_table_mirroring(self) -> int:
        return self.mirroring


class ColorDreams(Mapper):
    """Mapper 11 - ColorDreams: PRG and CHR bank switching"""
    
    def __init__(self, cart: Cartridge, mirroring_cb: Callable[[], None] = None):
        super().__init__(cart, Mapper.Type.ColorDreams, mirroring_cb=mirroring_cb)
        self.prg_bank_select = 0
        self.chr_bank_select = 0
        self.mirroring = NameTableMirroring.Vertical
    
    def write_prg(self, addr: int, value: int):
        """Single write_prg handling PRG-RAM and bank select"""
        if 0x6000 <= addr < 0x8000:
            if self.has_extended_ram():
                ext_ram = self.cartridge.get_ext_ram()
                ext_ram[addr - 0x6000] = value
        elif addr >= 0x8000:
            # C++: prgbank = value & 0x3; chrbank = (value >> 4) & 0xF
            self.prg_bank_select = value & 0x03
            self.chr_bank_select = (value >> 4) & 0x0F
    
    def read_prg(self, addr: int) -> int:
        if 0x6000 <= addr < 0x8000:
            if self.has_extended_ram():
                ext_ram = self.cartridge.get_ext_ram()
                return ext_ram[addr - 0x6000]
            return 0
        elif addr >= 0x8000:
            bank_offset = (self.prg_bank_select * 0x8000) + (addr & 0x7FFF)
            rom_data = self.cartridge.get_rom()
            if bank_offset < len(rom_data):
                return rom_data[bank_offset]
        return 0
    
    def read_chr(self, addr: int) -> int:
        if addr <= 0x1FFF:
            chr_rom = self.cartridge.get_vrom()
            bank_offset = (self.chr_bank_select * 0x2000) + addr
            if bank_offset < len(chr_rom):
                return chr_rom[bank_offset]
        return 0
    
    def write_chr(self, addr: int, value: int):
        # ColorDreams typically uses CHR-ROM
        pass
    
    def get_name_table_mirroring(self) -> int:
        return self.mirroring


class GxROM(Mapper):
    """Mapper 66 - GxROM: PRG and CHR bank switching
    
    Note: Bank selection uses modulo for defensive bounds checking.
    This is a Python compatibility enhancement to prevent index overflow
    when bank select exceeds available banks. Strict C++ parity would
    not use modulo and rely on ROM having correct bank count.
    """
    
    def __init__(self, cart: Cartridge, mirroring_cb: Callable[[], None] = None):
        super().__init__(cart, Mapper.Type.GxROM, mirroring_cb=mirroring_cb)
        self.prg_bank_select = 0
        self.chr_bank_select = 0
    
    def write_prg(self, addr: int, value: int):
        """Single write_prg handling PRG-RAM and bank select"""
        if 0x6000 <= addr < 0x8000:
            if self.has_extended_ram():
                ext_ram = self.cartridge.get_ext_ram()
                ext_ram[addr - 0x6000] = value
        elif addr >= 0x8000:
            # C++: prgbank = (value >> 4) & 0x03; chrbank = value & 0x03
            self.prg_bank_select = (value >> 4) & 0x03
            self.chr_bank_select = value & 0x03
    
    def read_prg(self, addr: int) -> int:
        if 0x6000 <= addr < 0x8000:
            if self.has_extended_ram():
                ext_ram = self.cartridge.get_ext_ram()
                return ext_ram[addr - 0x6000]
            return 0
        elif addr >= 0x8000:
            rom_data = self.cartridge.get_rom()
            num_banks = len(rom_data) // 0x8000
            if num_banks > 0:
                # Defensive: use modulo to prevent overflow
                # (Python compatibility enhancement, not strict C++ parity)
                bank_idx = self.prg_bank_select % num_banks
                bank_offset = bank_idx * 0x8000 + (addr & 0x7FFF)
                if bank_offset < len(rom_data):
                    return rom_data[bank_offset]
        return 0
    
    def read_chr(self, addr: int) -> int:
        chr_rom = self.cartridge.get_vrom()
        num_banks = len(chr_rom) // 0x2000 if chr_rom else 0
        if num_banks > 0 and addr <= 0x1FFF:
            # Defensive: use modulo to prevent overflow
            bank_idx = self.chr_bank_select % num_banks
            bank_offset = bank_idx * 0x2000 + addr
            if bank_offset < len(chr_rom):
                return chr_rom[bank_offset]
        return 0
    
    def write_chr(self, addr: int, value: int):
        if self.cartridge.has_chr_ram():
            chr_rom = self.cartridge.get_vrom()
            if addr < len(chr_rom):
                chr_rom[addr] = value


class SxROM(Mapper):
    """Mapper 1 - MMC1: The most common mapper with shift register"""
    
    def __init__(self, cart: Cartridge, mirroring_cb: Callable[[], None] = None):
        super().__init__(cart, Mapper.Type.SxROM, mirroring_cb=mirroring_cb)
        
        # Shift register state (C++ model)
        self.temp_register = 0
        self.write_counter = 0
        
        # Control registers
        self.control = 0x0C
        self.chr_reg_0 = 0
        self.chr_reg_1 = 0
        self.prg_reg = 0
        
        # Internal state
        self.mirroring = NameTableMirroring.Horizontal
        self.chr_mode = 0  # 0=8KB, 1=4KBx2
        self.prg_mode = 3  # 0-1=32KB, 2=fix first, 3=fix last
        
        # Bank offsets (using 4KB granularity for CHR)
        self.first_bank_prg_offset = 0
        self.second_bank_prg_offset = len(cart.get_rom()) - 0x4000 if cart.get_rom() else 0
        self.first_bank_chr_offset = 0
        self.second_bank_chr_offset = 0
        
        self._calculate_chr_banks()
    
    def write_prg(self, addr: int, value: int):
        """Single write_prg handling PRG-RAM and shift register"""
        if 0x6000 <= addr < 0x8000:
            # PRG-RAM write
            if self.has_extended_ram():
                ext_ram = self.cartridge.get_ext_ram()
                ext_ram[addr - 0x6000] = value
        elif addr >= 0x8000:
            # Shift register protocol
            if value & 0x80:  # Reset bit
                self.temp_register = 0
                self.write_counter = 0
                self.prg_mode = 3
                self._calculate_prg_banks()
            else:
                self.temp_register = (self.temp_register >> 1) | ((value & 1) << 4)
                self.write_counter += 1
                
                if self.write_counter == 5:
                    self._process_register(addr, self.temp_register)
                    self.temp_register = 0
                    self.write_counter = 0
    
    def _process_register(self, addr: int, value: int):
        """Process accumulated 5-bit value"""
        if addr <= 0x9FFF:  # Control register
            self.control = value
            
            # Mirroring from bits 0-1
            mirroring_map = {
                0: NameTableMirroring.OneScreenLower,
                1: NameTableMirroring.OneScreenHigher,
                2: NameTableMirroring.Vertical,
                3: NameTableMirroring.Horizontal
            }
            self.mirroring = mirroring_map[value & 0x03]
            if self.mirroring_callback:
                self.mirroring_callback()
            
            self.chr_mode = (value >> 4) & 0x01
            self.prg_mode = (value >> 2) & 0x03
            
            self._calculate_prg_banks()
            self._calculate_chr_banks()
        
        elif addr <= 0xBFFF:  # CHR reg 0
            self.chr_reg_0 = value
            self._calculate_chr_banks()
        
        elif addr <= 0xDFFF:  # CHR reg 1
            self.chr_reg_1 = value
            if self.chr_mode == 1:
                self._calculate_chr_banks()
        
        else:  # PRG reg
            self.prg_reg = value & 0x0F
            self._calculate_prg_banks()
    
    def _calculate_prg_banks(self):
        rom_data = self.cartridge.get_rom()
        rom_size = len(rom_data)
        
        if self.prg_mode <= 1:  # 32KB mode
            bank = (self.prg_reg & 0x0E) * 0x4000
            self.first_bank_prg_offset = bank
            self.second_bank_prg_offset = bank + 0x4000
        elif self.prg_mode == 2:  # Fix first bank
            self.first_bank_prg_offset = 0
            self.second_bank_prg_offset = self.prg_reg * 0x4000
        else:  # Fix last bank (mode 3)
            self.first_bank_prg_offset = self.prg_reg * 0x4000
            self.second_bank_prg_offset = rom_size - 0x4000 if rom_size > 0 else 0
    
    def _calculate_chr_banks(self):
        """Calculate CHR bank offsets using 4KB (0x1000) granularity"""
        if self.chr_mode == 0:  # 8KB mode
            base = (self.chr_reg_0 & 0x1E) * 0x1000  # 4KB granularity, ignore LSB
            self.first_bank_chr_offset = base
            self.second_bank_chr_offset = base + 0x1000
        else:  # 4KB mode
            self.first_bank_chr_offset = self.chr_reg_0 * 0x1000  # 4KB granularity
            self.second_bank_chr_offset = self.chr_reg_1 * 0x1000
    
    def read_prg(self, addr: int) -> int:
        if 0x6000 <= addr < 0x8000:
            if self.has_extended_ram():
                ext_ram = self.cartridge.get_ext_ram()
                return ext_ram[addr - 0x6000]
            return 0
        elif addr < 0xC000:
            offset = self.first_bank_prg_offset + (addr & 0x3FFF)
        else:
            offset = self.second_bank_prg_offset + (addr & 0x3FFF)
        
        rom_data = self.cartridge.get_rom()
        if offset < len(rom_data):
            return rom_data[offset]
        return 0
    
    def read_chr(self, addr: int) -> int:
        if addr < 0x1000:
            offset = self.first_bank_chr_offset + addr
        else:
            offset = self.second_bank_chr_offset + (addr & 0xFFF)
        
        chr_data = self.cartridge.get_vrom()
        if offset < len(chr_data):
            return chr_data[offset]
        return 0
    
    def write_chr(self, addr: int, value: int):
        """CHR-RAM write"""
        if self.cartridge.has_chr_ram():
            chr_data = self.cartridge.get_vrom()
            if addr < 0x1000:
                offset = self.first_bank_chr_offset + addr
            else:
                offset = self.second_bank_chr_offset + (addr & 0xFFF)
            if offset < len(chr_data):
                chr_data[offset] = value
    
    def get_name_table_mirroring(self) -> int:
        return self.mirroring