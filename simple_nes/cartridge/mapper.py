"""
Mapper implementations for SimpleNES-py
Handles different NES cartridge mapper types
"""
from abc import ABC, abstractmethod
from typing import List, Callable
from .cartridge import Cartridge
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

    def __init__(self, cart: Cartridge, mapper_type: int):
        self.cartridge = cart
        self.type = mapper_type

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
                     interrupt_cb: Callable[[], None] = None,
                     nmi_cb: Callable[[], None] = None,
                     mirroring_cb: Callable[[], None] = None) -> 'Mapper':
        """Factory method to create appropriate mapper instance"""
        if mapper_type == Mapper.Type.NROM:
            return NROM(cart)
        elif mapper_type == Mapper.Type.UxROM:
            return UxROM(cart)
        elif mapper_type == Mapper.Type.CNROM:
            return CNROM(cart)
        elif mapper_type == Mapper.Type.MMC3:
            return MMC3(cart, interrupt_cb)
        elif mapper_type == Mapper.Type.AxROM:
            return AxROM(cart)
        elif mapper_type == Mapper.Type.ColorDreams:
            return ColorDreams(cart)
        elif mapper_type == Mapper.Type.GxROM:
            return GxROM(cart)
        elif mapper_type == Mapper.Type.SxROM:
            return SxROM(cart)
        else:
            warning(f"Unsupported mapper type: {mapper_type}, using NROM")
            return NROM(cart)


class NROM(Mapper):
    """Mapper 0 - NROM: No mapper, simple PRG/CHR ROM"""
    def __init__(self, cart: Cartridge):
        super().__init__(cart, Mapper.Type.NROM)
        self.prg_banks = len(cart.get_rom()) // 0x4000  # 16KB banks

    def write_prg(self, addr: int, value: int):
        # NROM has no writable registers in PRG space
        pass

    def read_prg(self, addr: int) -> int:
        # NROM maps PRG-ROM directly
        if addr >= 0x8000:
            # PRG ROM space
            effective_addr = addr - 0x8000
            if self.prg_banks == 1:
                # If only 1 bank, mirror it
                effective_addr = effective_addr % len(self.cartridge.get_rom())
            else:
                # 2 or more banks
                effective_addr = effective_addr % len(self.cartridge.get_rom())
            if effective_addr < len(self.cartridge.get_rom()):
                return self.cartridge.get_rom()[effective_addr]
        elif addr >= 0x6000:
            # PRG RAM space
            # This is handled by the main bus for save RAM
            pass
        return 0

    def read_chr(self, addr: int) -> int:
        chr_rom = self.cartridge.get_vrom()
        if addr < len(chr_rom):
            return chr_rom[addr]
        return 0

    def write_chr(self, addr: int, value: int):
        # For CHR ROM, ignore writes
        # For CHR RAM, we would write to the RAM
        pass


class UxROM(Mapper):
    """Mapper 2 - UNROM: Simple bank switching for PRG ROM"""
    def __init__(self, cart: Cartridge):
        super().__init__(cart, Mapper.Type.UxROM)
        self.prg_banks = len(cart.get_rom()) // 0x4000
        self.prg_bank_select = 0

    def write_prg(self, addr: int, value: int):
        if addr >= 0x8000:
            # Bank select register
            self.prg_bank_select = value & (self.prg_banks - 1)

    def read_prg(self, addr: int) -> int:
        if 0x8000 <= addr < 0xC000:
            # First 16KB of PRG ROM (switchable)
            bank_offset = (self.prg_bank_select * 0x4000) + (addr - 0x8000)
            rom_data = self.cartridge.get_rom()
            if bank_offset < len(rom_data):
                return rom_data[bank_offset]
        elif 0xC000 <= addr <= 0xFFFF:
            # Last 16KB of PRG ROM (fixed to last bank)
            last_bank = self.prg_banks - 1
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
        # For CHR ROM, ignore writes
        pass


class CNROM(Mapper):
    """Mapper 3 - CNROM: Simple bank switching for CHR ROM"""
    def __init__(self, cart: Cartridge):
        super().__init__(cart, Mapper.Type.CNROM)
        self.chr_bank_select = 0

    def write_prg(self, addr: int, value: int):
        if addr >= 0x8000:
            # Bank select register for CHR ROM
            self.chr_bank_select = (value & 0x03)  # Upper bits ignored

    def read_prg(self, addr: int) -> int:
        # NROM-style fixed PRG mapping
        if addr >= 0x8000:
            effective_addr = addr - 0x8000
            rom_data = self.cartridge.get_rom()
            if effective_addr < len(rom_data):
                return rom_data[effective_addr]
        return 0

    def read_chr(self, addr: int) -> int:
        chr_rom = self.cartridge.get_vrom()
        # Each bank is 8KB
        bank_offset = (self.chr_bank_select * 0x2000) + addr
        if bank_offset < len(chr_rom):
            return chr_rom[bank_offset]
        return 0

    def write_chr(self, addr: int, value: int):
        # For CHR ROM, ignore writes
        pass


class MMC3(Mapper):
    """Mapper 4 - MMC3: Advanced bank switching and IRQ"""
    def __init__(self, cart: Cartridge, interrupt_cb: Callable[[], None]):
        super().__init__(cart, Mapper.Type.MMC3)
        self.irq_counter = 0
        self.irq_latch = 0
        self.irq_enabled = False
        self.irq_reload = False
        self.irq_next = False
        self.interrupt_cb = interrupt_cb
        
        # Bank select registers
        self.registers = [0] * 8
        self.bank_select = 0
        
        # PRG and CHR bank registers
        self.prg_banks = len(cart.get_rom()) // 0x2000  # 8KB banks
        self.chr_banks = len(cart.get_vrom()) // 0x400  # 1KB banks

    def write_prg(self, addr: int, value: int):
        if 0x8000 <= addr <= 0x9FFF:
            if addr & 0x01:
                # Bank data register
                self.registers[self.bank_select & 0x07] = value
            else:
                # Bank select register
                self.bank_select = value

        elif 0xA000 <= addr <= 0xBFFF:
            if addr & 0x01:
                # Mirroring control
                pass
            else:
                # PRG RAM protect/write
                pass

        elif 0xC000 <= addr <= 0xDFFF:
            if addr & 0x01:
                # IRQ latch
                self.irq_latch = value
            else:
                # IRQ counter
                self.irq_counter = 0

        elif 0xE000 <= addr <= 0xFFFF:
            if addr & 0x01:
                # IRQ enable
                self.irq_enabled = True
            else:
                # IRQ disable
                self.irq_enabled = False
                self.irq_counter = 0

    def read_prg(self, addr: int) -> int:
        if 0x8000 <= addr <= 0xFFFF:
            if addr < 0xA000:
                # First 8KB bank
                bank_reg = self.registers[6] & 0xFE
                bank_offset = (bank_reg * 0x2000) + (addr & 0x1FFF)
                rom_data = self.cartridge.get_rom()
                if bank_offset < len(rom_data):
                    return rom_data[bank_offset]
            elif addr < 0xC000:
                # Second 8KB bank
                bank_reg = self.registers[7]
                bank_offset = (bank_reg * 0x2000) + (addr & 0x1FFF)
                rom_data = self.cartridge.get_rom()
                if bank_offset < len(rom_data):
                    return rom_data[bank_offset]
            elif addr < 0xE000:
                # Second to last 8KB bank (fixed)
                bank_offset = ((self.prg_banks - 2) * 0x2000) + (addr & 0x1FFF)
                rom_data = self.cartridge.get_rom()
                if bank_offset < len(rom_data):
                    return rom_data[bank_offset]
            else:
                # Last 8KB bank (fixed)
                bank_offset = ((self.prg_banks - 1) * 0x2000) + (addr & 0x1FFF)
                rom_data = self.cartridge.get_rom()
                if bank_offset < len(rom_data):
                    return rom_data[bank_offset]
        return 0

    def read_chr(self, addr: int) -> int:
        # Handle MMC3 CHR bank switching
        rom_data = self.cartridge.get_vrom()
        
        # Determine which register to use based on addr and mirroring
        if addr < 0x800:
            # First 1KB
            reg_idx = 0 if (self.registers[0] & 0x80) else 2
        elif addr < 0x1000:
            # Second 1KB
            reg_idx = 1 if (self.registers[0] & 0x80) else 3
        elif addr < 0x1400:
            # Third 1KB
            reg_idx = 2 if (self.registers[0] & 0x80) else 0
        elif addr < 0x1800:
            # Fourth 1KB
            reg_idx = 3 if (self.registers[0] & 0x80) else 1
        elif addr < 0x1C00:
            # Fifth 1KB
            reg_idx = 4
        else:
            # Sixth 1KB
            reg_idx = 5
        
        bank_reg = self.registers[reg_idx]
        bank_offset = (bank_reg * 0x400) + (addr & 0x3FF)
        
        if bank_offset < len(rom_data):
            return rom_data[bank_offset]
        return 0

    def write_chr(self, addr: int, value: int):
        # For CHR ROM, ignore writes
        # For CHR RAM, we would write to the RAM
        pass

    def scanline_irq(self):
        """Handle scanline-based IRQ for MMC3"""
        zero_transition = False
        
        if self.irq_counter == 0 or self.irq_reload:
            self.irq_counter = self.irq_latch
            self.irq_reload = False
        else:
            self.irq_counter -= 1
            zero_transition = self.irq_counter == 0
        
        if zero_transition and self.irq_enabled:
            if self.interrupt_cb:
                self.interrupt_cb()


class AxROM(Mapper):
    """Mapper 7 - ANROM: Simple bank switching for PRG and mirroring"""
    def __init__(self, cart: Cartridge):
        super().__init__(cart, Mapper.Type.AxROM)
        self.prg_bank_select = 0

    def write_prg(self, addr: int, value: int):
        if addr >= 0x8000:
            # Bank select and mirroring
            self.prg_bank_select = (value >> 4) & 0x0F
            # Mirroring handled by changing nametable setup

    def read_prg(self, addr: int) -> int:
        if addr >= 0x8000:
            # Switchable 32KB bank
            bank_offset = (self.prg_bank_select * 0x8000) + (addr - 0x8000)
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
        # For CHR ROM, ignore writes
        pass


class ColorDreams(Mapper):
    """Mapper 11 - Color Dreams: PRG and CHR bank switching"""
    def __init__(self, cart: Cartridge):
        super().__init__(cart, Mapper.Type.ColorDreams)
        self.prg_bank_select = 0
        self.chr_bank_select = 0

    def write_prg(self, addr: int, value: int):
        if addr >= 0x8000:
            # Bank select register for both PRG and CHR
            self.prg_bank_select = (value >> 4) & 0x03
            self.chr_bank_select = value & 0x03

    def read_prg(self, addr: int) -> int:
        if addr >= 0x8000:
            bank_size = len(self.cartridge.get_rom()) // 4  # Assuming 4 banks
            bank_offset = (self.prg_bank_select * bank_size) + (addr - 0x8000)
            rom_data = self.cartridge.get_rom()
            if bank_offset < len(rom_data):
                return rom_data[bank_offset]
        return 0

    def read_chr(self, addr: int) -> int:
        chr_rom = self.cartridge.get_vrom()
        bank_size = len(chr_rom) // 4  # Assuming 4 banks
        bank_offset = (self.chr_bank_select * bank_size) + addr
        if bank_offset < len(chr_rom):
            return chr_rom[bank_offset]
        return 0

    def write_chr(self, addr: int, value: int):
        # For CHR ROM, ignore writes
        pass


class GxROM(Mapper):
    """Mapper 66 - GxROM: PRG and CHR bank switching"""
    def __init__(self, cart: Cartridge):
        super().__init__(cart, Mapper.Type.GxROM)
        self.prg_bank_select = 0
        self.chr_bank_select = 0

    def write_prg(self, addr: int, value: int):
        if addr >= 0x8000:
            # Bank select register
            self.prg_bank_select = (value >> 4) & 0x0F
            self.chr_bank_select = value & 0x0F

    def read_prg(self, addr: int) -> int:
        if addr >= 0x8000:
            bank_size = len(self.cartridge.get_rom()) // 0x8000  # 32KB banks
            bank_offset = (self.prg_bank_select * 0x8000) + (addr - 0x8000)
            rom_data = self.cartridge.get_rom()
            if bank_offset < len(rom_data):
                return rom_data[bank_offset]
        return 0

    def read_chr(self, addr: int) -> int:
        chr_rom = self.cartridge.get_vrom()
        bank_size = len(chr_rom) // 0x2000  # 8KB banks
        bank_offset = (self.chr_bank_select * 0x2000) + addr
        if bank_offset < len(chr_rom):
            return chr_rom[bank_offset]
        return 0

    def write_chr(self, addr: int, value: int):
        # For CHR ROM, ignore writes
        pass


class SxROM(Mapper):
    """Mapper 1 - MMC1: The most common mapper"""
    def __init__(self, cart: Cartridge):
        super().__init__(cart, Mapper.Type.SxROM)
        self.shift_register = 0x10
        self.control = 0x0C  # Reset state
        self.chr_bank_0 = 0
        self.chr_bank_1 = 0
        self.prg_bank = 0

    def write_prg(self, addr: int, value: int):
        if addr >= 0x8000:
            # MMC1 uses a shift register to write 5-bit values
            if value & 0x80:
                # Reset shift register
                self.shift_register = 0x10
                self.control |= 0x0C  # Ensure 32KB mode is set appropriately
            else:
                # Shift in bit 0
                complete = bool(self.shift_register & 0x01)
                self.shift_register >>= 1
                self.shift_register |= (value & 0x01) << 4
                
                if complete:
                    # Write complete, process the 5-bit value to the register
                    reg_select = (addr >> 13) & 0x03  # Use bits 14-13 to select register
                    val = self.shift_register & 0x1F
                    
                    if reg_select == 0:
                        # Control register
                        self.control = val
                    elif reg_select == 1:
                        # CHR bank 0
                        self.chr_bank_0 = val
                    elif reg_select == 2:
                        # CHR bank 1
                        self.chr_bank_1 = val
                    elif reg_select == 3:
                        # PRG bank
                        self.prg_bank = val
                    
                    # Reset shift register after use
                    self.shift_register = 0x10

    def read_prg(self, addr: int) -> int:
        if addr >= 0x8000:
            rom_data = self.cartridge.get_rom()
            prg_size = len(rom_data)
            
            # Determine PRG banking mode
            prg_mode = (self.control >> 2) & 0x03
            
            if prg_mode == 0 or prg_mode == 1:
                # 32KB mode
                bank_size = 0x8000  # 32KB
                bank_offset = (self.prg_bank & 0x0E) * bank_size + (addr - 0x8000)
            elif prg_mode == 2:
                # Fix first bank at $8000, switch second bank at $C000
                if addr < 0xC000:
                    bank_offset = 0  # Fixed first bank
                else:
                    bank_offset = (self.prg_bank & 0x0F) * 0x4000 + (addr - 0xC000)
            else:  # prg_mode == 3
                # Switch first bank at $8000, fix second bank at $C000
                if addr < 0xC000:
                    bank_offset = (self.prg_bank & 0x0F) * 0x4000 + (addr - 0x8000)
                else:
                    bank_offset = (prg_size - 0x4000) + (addr - 0xC000)  # Last bank
            
            if bank_offset < len(rom_data):
                return rom_data[bank_offset]
        return 0

    def read_chr(self, addr: int) -> int:
        chr_rom = self.cartridge.get_vrom()
        
        # Determine CHR banking mode
        chr_mode = (self.control >> 4) & 0x01
        
        if chr_mode == 0:
            # 8KB mode
            bank_size = 0x2000  # 8KB
            bank_offset = (self.chr_bank_0 & 0x1E) * 0x400 + addr
        else:
            # 4KB mode
            if addr < 0x1000:
                # First 4KB bank
                bank_offset = (self.chr_bank_0 & 0x1F) * 0x400 + addr
            else:
                # Second 4KB bank
                bank_offset = (self.chr_bank_1 & 0x1F) * 0x400 + (addr - 0x1000)
        
        if bank_offset < len(chr_rom):
            return chr_rom[bank_offset]
        return 0

    def write_chr(self, addr: int, value: int):
        # For CHR ROM, ignore writes
        pass