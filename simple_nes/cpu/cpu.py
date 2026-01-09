"""
CPU Emulator for SimpleNES-py
Implements Ricoh 2A03 CPU (based on 6502)
"""
import numpy as np
from typing import Callable, Optional
from ..util.logging import error, debug

# Define common types
Byte = np.uint8
Word = np.uint16
Address = Word

# Interrupt vectors
NMIVector = 0xfffa
ResetVector = 0xfffc
IRQVector = 0xfffe

class CPU:
    def __init__(self, memory_bus):
        self.memory = memory_bus
        
        # Registers
        self.r_PC = Address(0)  # Program Counter
        self.r_SP = Byte(0)     # Stack Pointer
        self.r_A = Byte(0)      # Accumulator
        self.r_X = Byte(0)      # X Register
        self.r_Y = Byte(0)      # Y Register
        
        # Status flags
        self.f_C = False  # Carry
        self.f_Z = False  # Zero
        self.f_I = False  # Interrupt Disable
        self.f_D = False  # Decimal Mode
        self.f_V = False  # Overflow
        self.f_N = False  # Negative
        
        # Internal state
        self.m_skipCycles = 0
        self.m_cycles = 0
        
        # Interrupt flags
        self.m_pendingNMI = False
        self.m_pendingIRQ = False
        
        # Initialize CPU
        self.reset()
    
    def reset(self, start_addr: Optional[Address] = None):
        """Reset CPU to initial state"""
        if start_addr is None:
            # Read reset vector from memory
            lo = self.memory.read(ResetVector)
            hi = self.memory.read(ResetVector + 1)
            start_addr = int((hi << 8) | lo)
        
        self.r_PC = Address(start_addr)
        self.r_SP = Byte(0xFD)
        self.r_A = Byte(0)
        self.r_X = Byte(0)
        self.r_Y = Byte(0)
        
        self.f_I = True  # Interrupts disabled after reset
        self.f_D = False  # Decimal mode off
        
        self.m_skipCycles = 0
        self.m_cycles = 0
        self.m_pendingNMI = False
        self.m_pendingIRQ = False
    
    def step(self):
        """Execute a single CPU instruction"""
        self.m_cycles += 1
        
        # Handle cycle skipping (for DMA, etc.)
        if self.m_skipCycles > 1:
            self.m_skipCycles -= 1
            return 1
        
        self.m_skipCycles = 0
        
        # NMI has higher priority, check for it first
        if self.m_pendingNMI:
            self._interrupt_sequence('NMI')
            self.m_pendingNMI = False
            self.m_pendingIRQ = False
            return 7  # NMI takes 7 cycles
        
        elif self.m_pendingIRQ:
            if not self.f_I:  # Only process IRQ if interrupt flag is clear
                self._interrupt_sequence('IRQ')
                self.m_pendingNMI = False
                self.m_pendingIRQ = False
                return 7  # IRQ takes 7 cycles
            else:
                self.m_pendingIRQ = False
        
        # Fetch opcode
        opcode = self.memory.read(self.r_PC)
        self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
        
        # Execute instruction based on opcode
        cycles = self.execute_opcode(opcode)
        
        return cycles
    
    def execute_opcode(self, opcode: Byte):
        """Execute a single opcode"""
        # Fetch operands based on addressing mode
        cycles = 0
        
        # This is a simplified implementation with a few opcodes
        # A complete implementation would handle all 6502 opcodes
        
        if opcode == 0x00:  # BRK
            # Push PC+2, push flags, set interrupt flag, jump to IRQ vector
            pc = self.r_PC
            self.push_stack((pc >> 8) & 0xFF)
            self.push_stack(pc & 0xFF)
            
            flag_byte = (self.f_C | (self.f_Z << 1) | (self.f_I << 2) | 
                         (self.f_D << 3) | 0x04 | (self.f_V << 6) | (self.f_N << 7))
            self.push_stack(flag_byte)
            
            self.f_I = True
            lo = self.memory.read(IRQVector)
            hi = self.memory.read(IRQVector + 1)
            self.r_PC = Address((hi << 8) | lo)
            cycles = 7
        
        elif opcode == 0x4C:  # JMP absolute
            lo = int(self.memory.read(self.r_PC))
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            hi = int(self.memory.read(self.r_PC))
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            self.r_PC = Address((hi << 8) | lo)
            cycles = 3
        
        elif opcode == 0x6C:  # JMP indirect
            addr_lo = int(self.memory.read(self.r_PC))
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            addr_hi = int(self.memory.read(self.r_PC))
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            addr = Address((addr_hi << 8) | addr_lo)
            
            # Handle page boundary bug
            lo = self.memory.read(addr)
            hi_addr = Address((addr & 0xFF00) | ((addr + 1) & 0x00FF))
            hi = self.memory.read(hi_addr)
            
            self.r_PC = Address((hi << 8) | lo)
            cycles = 5
        
        elif opcode == 0xA9:  # LDA immediate
            value = int(self.memory.read(self.r_PC))
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            self.r_A = Byte(value)
            self.set_flags_ZN(self.r_A)
            cycles = 2
        
        elif opcode == 0xA5:  # LDA zero page
            addr = int(self.memory.read(self.r_PC))
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            self.r_A = self.memory.read(addr)
            self.set_flags_ZN(self.r_A)
            cycles = 3
        
        elif opcode == 0xB5:  # LDA zero page, X
            addr = (int(self.memory.read(self.r_PC)) + int(self.r_X)) & 0xFF
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            self.r_A = self.memory.read(addr)
            self.set_flags_ZN(self.r_A)
            cycles = 4
        
        elif opcode == 0xAD:  # LDA absolute
            lo = int(self.memory.read(self.r_PC))
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            hi = int(self.memory.read(self.r_PC))
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            addr = int((hi << 8) | lo)
            self.r_A = self.memory.read(addr)
            self.set_flags_ZN(self.r_A)
            cycles = 4
        
        elif opcode == 0xBD:  # LDA absolute, X
            lo = int(self.memory.read(self.r_PC))
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            hi = int(self.memory.read(self.r_PC))
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            base_addr = int((hi << 8) | lo)
            addr = Address(int(base_addr) + int(self.r_X))
            
            # Check for page boundary crossing
            if (base_addr & 0xFF00) != (addr & 0xFF00):
                cycles = 5  # Extra cycle for page crossing
            else:
                cycles = 4
            
            self.r_A = self.memory.read(addr)
            self.set_flags_ZN(self.r_A)
        
        elif opcode == 0xB9:  # LDA absolute, Y
            lo = int(self.memory.read(self.r_PC))
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            hi = int(self.memory.read(self.r_PC))
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            base_addr = int((hi << 8) | lo)
            addr = Address(int(base_addr) + int(self.r_Y))
            
            # Check for page boundary crossing
            if (base_addr & 0xFF00) != (addr & 0xFF00):
                cycles = 5  # Extra cycle for page crossing
            else:
                cycles = 4
            
            self.r_A = self.memory.read(addr)
            self.set_flags_ZN(self.r_A)
        
        elif opcode == 0xA1:  # LDA Indirect X
            zero_addr = (int(self.memory.read(self.r_PC)) + int(self.r_X)) & 0xFF
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            # Read the 16-bit address from zero page
            lo = self.memory.read(zero_addr & 0xFF)
            hi = self.memory.read((zero_addr + 1) & 0xFF)
            addr = int((hi << 8) | lo)
            self.r_A = self.memory.read(addr)
            self.set_flags_ZN(self.r_A)
            cycles = 6  # 6 cycles for indirect X addressing
        
        elif opcode == 0xB1:  # LDA Indirect Y
            zero_addr = int(self.memory.read(self.r_PC))
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            # Read the 16-bit address from zero page
            lo = self.memory.read(zero_addr & 0xFF)
            hi = self.memory.read((zero_addr + 1) & 0xFF)
            base_addr = int((hi << 8) | lo)
            addr = Address(int(base_addr) + int(self.r_Y))
            # Check for page boundary crossing
            if (base_addr & 0xFF00) != (addr & 0xFF00):
                cycles = 6  # Extra cycle for page crossing
            else:
                cycles = 5
            self.r_A = self.memory.read(addr)
            self.set_flags_ZN(self.r_A)
        
        elif opcode == 0x25:  # AND Zero Page
            addr = int(self.memory.read(self.r_PC))
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            value = self.memory.read(addr)
            self.r_A = Byte(self.r_A & value)
            self.set_flags_ZN(self.r_A)
            cycles = 3
        
        elif opcode == 0x45:  # EOR Zero Page
            addr = int(self.memory.read(self.r_PC))
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            value = self.memory.read(addr)
            self.r_A = Byte(self.r_A ^ value)
            self.set_flags_ZN(self.r_A)
            cycles = 3
        
        elif opcode == 0x65:  # ADC Zero Page
            addr = int(self.memory.read(self.r_PC))
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            value = self.memory.read(addr)
            sum_val = int(self.r_A) + int(value) + (1 if self.f_C else 0)
            self.f_C = (sum_val & 0x100) != 0
            self.f_V = ((int(self.r_A) ^ sum_val) & (int(value) ^ sum_val) & 0x80) != 0
            self.r_A = Byte(sum_val & 0xFF)
            self.set_flags_ZN(self.r_A)
            cycles = 3
        
        elif opcode == 0xE9:  # SBC Immediate
            value = int(self.memory.read(self.r_PC))
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            diff = int(self.r_A) - int(value) - (1 - int(self.f_C))
            self.f_C = not bool(diff & 0x100)
            self.f_V = ((int(self.r_A) ^ diff) & ((0xFF ^ int(value)) ^ diff) & 0x80) != 0
            self.r_A = Byte(diff & 0xFF)
            self.set_flags_ZN(self.r_A)
            cycles = 2
        
        elif opcode == 0xE5:  # SBC Zero Page
            addr = int(self.memory.read(self.r_PC))
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            value = self.memory.read(addr)
            diff = int(self.r_A) - int(value) - (1 - int(self.f_C))
            self.f_C = not bool(diff & 0x100)
            self.f_V = ((int(self.r_A) ^ diff) & ((0xFF ^ int(value)) ^ diff) & 0x80) != 0
            self.r_A = Byte(diff & 0xFF)
            self.set_flags_ZN(self.r_A)
            cycles = 3
        
        elif opcode == 0xC5:  # CMP Zero Page
            addr = int(self.memory.read(self.r_PC))
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            value = self.memory.read(addr)
            result = int(self.r_A) - int(value)
            self.f_C = result >= 0
            self.set_flags_ZN(Byte(result & 0xFF))
            cycles = 3
        
        elif opcode == 0x85:  # STA Zero Page
            addr = int(self.memory.read(self.r_PC))
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            self.memory.write(addr, self.r_A)
            cycles = 3
        
        elif opcode == 0xA0:  # LDY Immediate
            value = int(self.memory.read(self.r_PC))
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            self.r_Y = Byte(value)
            self.set_flags_ZN(self.r_Y)
            cycles = 2
        
        elif opcode == 0xA4:  # LDY Zero Page
            addr = int(self.memory.read(self.r_PC))
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            self.r_Y = self.memory.read(addr)
            self.set_flags_ZN(self.r_Y)
            cycles = 3
        
        elif opcode == 0xB4:  # LDY Zero Page X
            addr = (int(self.memory.read(self.r_PC)) + int(self.r_X)) & 0xFF
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            self.r_Y = self.memory.read(addr)
            self.set_flags_ZN(self.r_Y)
            cycles = 4
        
        elif opcode == 0xA2:  # LDX Immediate
            value = int(self.memory.read(self.r_PC))
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            self.r_X = Byte(value)
            self.set_flags_ZN(self.r_X)
            cycles = 2
        
        elif opcode == 0xA6:  # LDX Zero Page
            addr = int(self.memory.read(self.r_PC))
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            self.r_X = self.memory.read(addr)
            self.set_flags_ZN(self.r_X)
            cycles = 3
        
        elif opcode == 0xB6:  # LDX Zero Page Y
            addr = (int(self.memory.read(self.r_PC)) + int(self.r_Y)) & 0xFF
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            self.r_X = self.memory.read(addr)
            self.set_flags_ZN(self.r_X)
            cycles = 4
        
        elif opcode == 0xB5:  # LDA zero page, X
            addr = (int(self.memory.read(self.r_PC)) + int(self.r_X)) & 0xFF
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            self.r_A = self.memory.read(addr)
            self.set_flags_ZN(self.r_A)
            cycles = 4
        
        elif opcode == 0xAD:  # LDA absolute
            lo = int(self.memory.read(self.r_PC))
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            hi = int(self.memory.read(self.r_PC))
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            addr = int((hi << 8) | lo)
            self.r_A = self.memory.read(addr)
            self.set_flags_ZN(self.r_A)
            cycles = 4
        
        elif opcode == 0xBD:  # LDA absolute, X
            lo = int(self.memory.read(self.r_PC))
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            hi = int(self.memory.read(self.r_PC))
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            base_addr = int((hi << 8) | lo)
            addr = Address(int(base_addr) + int(self.r_X))
            
            # Check for page boundary crossing
            if (base_addr & 0xFF00) != (addr & 0xFF00):
                cycles = 5  # Extra cycle for page crossing
            else:
                cycles = 4
            
            self.r_A = self.memory.read(addr)
            self.set_flags_ZN(self.r_A)
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
        
        elif opcode == 0xA2:  # LDX immediate
            value = int(self.memory.read(self.r_PC))
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            self.r_X = Byte(value)
            self.set_flags_ZN(self.r_X)
            cycles = 2
        
        elif opcode == 0xA0:  # LDY immediate
            value = int(self.memory.read(self.r_PC))
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            self.r_Y = Byte(value)
            self.set_flags_ZN(self.r_Y)
            cycles = 2
        
        elif opcode == 0x85:  # STA zero page
            addr = int(self.memory.read(self.r_PC))
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            self.memory.write(addr, self.r_A)
            cycles = 3
        
        elif opcode == 0x8D:  # STA absolute
            lo = int(self.memory.read(self.r_PC))
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            hi = int(self.memory.read(self.r_PC))
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            addr = int((hi << 8) | lo)
            self.memory.write(addr, self.r_A)
            cycles = 4
        
        elif opcode == 0x91:  # STA Indirect Y
            zero_addr = int(self.memory.read(self.r_PC))
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            # Read the 16-bit address from zero page
            lo = self.memory.read(zero_addr & 0xFF)
            hi = self.memory.read((zero_addr + 1) & 0xFF)
            base_addr = int((hi << 8) | lo)
            addr = Address(int(base_addr) + int(self.r_Y))
            self.memory.write(addr, self.r_A)
            cycles = 6  # 6 cycles for indirect Y addressing
        
        elif opcode == 0xEA:  # NOP
            cycles = 2
        
        elif opcode == 0x18:  # CLC
            self.f_C = False
            cycles = 2
        
        elif opcode == 0x38:  # SEC
            self.f_C = True
            cycles = 2
        
        elif opcode == 0xD8:  # CLD
            self.f_D = False
            cycles = 2
        
        elif opcode == 0xF8:  # SED
            self.f_D = True
            cycles = 2
        
        elif opcode == 0x58:  # CLI
            self.f_I = False
            cycles = 2
        
        elif opcode == 0x78:  # SEI
            self.f_I = True
            cycles = 2
        
        elif opcode == 0xB8:  # CLV
            self.f_V = False
            cycles = 2
        
        elif opcode == 0xC9:  # CMP immediate
            value = int(self.memory.read(self.r_PC))
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            result = int(self.r_A) - int(value)
            self.f_C = result >= 0
            self.set_flags_ZN(Byte(result & 0xFF))
            cycles = 2
        
        elif opcode == 0xE8:  # INX
            self.r_X = Byte(self.r_X + 1)
            self.set_flags_ZN(self.r_X)
            cycles = 2
        
        elif opcode == 0xC8:  # INY
            self.r_Y = Byte(self.r_Y + 1)
            self.set_flags_ZN(self.r_Y)
            cycles = 2
        
        elif opcode == 0xCA:  # DEX
            self.r_X = Byte((int(self.r_X) - 1) & 0xFF)
            self.set_flags_ZN(self.r_X)
            cycles = 2
        
        elif opcode == 0x88:  # DEY
            self.r_Y = Byte((int(self.r_Y) - 1) & 0xFF)
            self.set_flags_ZN(self.r_Y)
            cycles = 2
        
        elif opcode == 0x05:  # ORA zero page
            addr = int(self.memory.read(self.r_PC))
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            value = self.memory.read(addr)
            self.r_A = Byte(self.r_A | value)
            self.set_flags_ZN(self.r_A)
            cycles = 3
        
        elif opcode == 0x01:  # ORA Indirect X
            zero_addr = (int(self.memory.read(self.r_PC)) + int(self.r_X)) & 0xFF
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            # Read the 16-bit address from zero page
            lo = self.memory.read(zero_addr & 0xFF)
            hi = self.memory.read((zero_addr + 1) & 0xFF)
            addr = int((hi << 8) | lo)
            value = self.memory.read(addr)
            self.r_A = Byte(self.r_A | value)
            self.set_flags_ZN(self.r_A)
            cycles = 6  # 6 cycles for indirect X addressing
        
        elif opcode == 0x11:  # ORA Indirect Y
            zero_addr = int(self.memory.read(self.r_PC))
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            # Read the 16-bit address from zero page
            lo = self.memory.read(zero_addr & 0xFF)
            hi = self.memory.read((zero_addr + 1) & 0xFF)
            base_addr = int((hi << 8) | lo)
            addr = Address(int(base_addr) + int(self.r_Y))
            # Check for page boundary crossing
            if (base_addr & 0xFF00) != (addr & 0xFF00):
                cycles = 6  # Extra cycle for page crossing
            else:
                cycles = 5
            value = self.memory.read(addr)
            self.r_A = Byte(self.r_A | value)
            self.set_flags_ZN(self.r_A)
        
        elif opcode == 0x1A:  # ORA Indirect X
            zero_addr = (int(self.memory.read(self.r_PC)) + int(self.r_X)) & 0xFF
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            lo = self.memory.read(zero_addr & 0xFF)
            hi = self.memory.read((zero_addr + 1) & 0xFF)
            addr = int((hi << 8) | lo)
            value = self.memory.read(addr)
            self.r_A = Byte(self.r_A | value)
            self.set_flags_ZN(self.r_A)
            cycles = 6
        
        elif opcode == 0x1C:  # ORA Absolute X
            lo = int(self.memory.read(self.r_PC))
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            hi = int(self.memory.read(self.r_PC))
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            base_addr = int((hi << 8) | lo)
            addr = int(base_addr + int(self.r_X))
            if (base_addr & 0xFF00) != (addr & 0xFF00):
                cycles = 5
            else:
                cycles = 4
            value = self.memory.read(addr)
            self.r_A = Byte(self.r_A | value)
            self.set_flags_ZN(self.r_A)
        
        elif opcode == 0x1D:  # ORA Absolute X
            lo = int(self.memory.read(self.r_PC))
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            hi = int(self.memory.read(self.r_PC))
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            base_addr = int((hi << 8) | lo)
            addr = int(base_addr + int(self.r_X))
            # Check for page boundary crossing
            if (base_addr & 0xFF00) != (addr & 0xFF00):
                cycles = 5  # Extra cycle for page crossing
            else:
                cycles = 4
            value = self.memory.read(addr)
            self.r_A = Byte(self.r_A | value)
            self.set_flags_ZN(self.r_A)
        
        elif opcode == 0x19:  # ORA Absolute Y
            lo = int(self.memory.read(self.r_PC))
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            hi = int(self.memory.read(self.r_PC))
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            base_addr = int((hi << 8) | lo)
            addr = int(base_addr + int(self.r_Y))
            # Check for page boundary crossing
            if (base_addr & 0xFF00) != (addr & 0xFF00):
                cycles = 5  # Extra cycle for page crossing
            else:
                cycles = 4
            value = self.memory.read(addr)
            self.r_A = Byte(self.r_A | value)
            self.set_flags_ZN(self.r_A)
        
        elif opcode == 0x15:  # ORA Zero Page X
            addr = (int(self.memory.read(self.r_PC)) + int(self.r_X)) & 0xFF
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            value = self.memory.read(addr)
            self.r_A = Byte(self.r_A | value)
            self.set_flags_ZN(self.r_A)
            cycles = 4
        
        elif opcode == 0x29:  # AND Immediate
            value = int(self.memory.read(self.r_PC))
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            self.r_A = Byte(self.r_A & value)
            self.set_flags_ZN(self.r_A)
            cycles = 2
        
        elif opcode == 0x2D:  # AND Absolute
            lo = int(self.memory.read(self.r_PC))
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            hi = int(self.memory.read(self.r_PC))
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            addr = int((hi << 8) | lo)
            value = self.memory.read(addr)
            self.r_A = Byte(self.r_A & value)
            self.set_flags_ZN(self.r_A)
            cycles = 4
        
        elif opcode == 0x3D:  # AND Absolute X
            lo = int(self.memory.read(self.r_PC))
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            hi = int(self.memory.read(self.r_PC))
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            base_addr = int((hi << 8) | lo)
            addr = Address(int(base_addr) + int(self.r_X))
            if (base_addr & 0xFF00) != (addr & 0xFF00):
                cycles = 5
            else:
                cycles = 4
            value = self.memory.read(addr)
            self.r_A = Byte(self.r_A & value)
            self.set_flags_ZN(self.r_A)
        
        elif opcode == 0x39:  # AND Absolute Y
            lo = int(self.memory.read(self.r_PC))
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            hi = int(self.memory.read(self.r_PC))
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            base_addr = int((hi << 8) | lo)
            addr = Address(int(base_addr) + int(self.r_Y))
            if (base_addr & 0xFF00) != (addr & 0xFF00):
                cycles = 5
            else:
                cycles = 4
            value = self.memory.read(addr)
            self.r_A = Byte(self.r_A & value)
            self.set_flags_ZN(self.r_A)
        
        elif opcode == 0x35:  # AND Zero Page X
            addr = (int(self.memory.read(self.r_PC)) + int(self.r_X)) & 0xFF
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            value = self.memory.read(addr)
            self.r_A = Byte(self.r_A & value)
            self.set_flags_ZN(self.r_A)
            cycles = 4
        
        elif opcode == 0x31:  # AND Indirect Y
            zero_addr = int(self.memory.read(self.r_PC))
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            lo = self.memory.read(zero_addr & 0xFF)
            hi = self.memory.read((zero_addr + 1) & 0xFF)
            base_addr = int((hi << 8) | lo)
            addr = Address(int(base_addr) + int(self.r_Y))
            if (base_addr & 0xFF00) != (addr & 0xFF00):
                cycles = 6
            else:
                cycles = 5
            value = self.memory.read(addr)
            self.r_A = Byte(self.r_A & value)
            self.set_flags_ZN(self.r_A)
        
        elif opcode == 0x21:  # AND Indirect X
            zero_addr = (int(self.memory.read(self.r_PC)) + int(self.r_X)) & 0xFF
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            lo = self.memory.read(zero_addr & 0xFF)
            hi = self.memory.read((zero_addr + 1) & 0xFF)
            addr = int((hi << 8) | lo)
            value = self.memory.read(addr)
            self.r_A = Byte(self.r_A & value)
            self.set_flags_ZN(self.r_A)
            cycles = 6
        
        elif opcode == 0x49:  # EOR Immediate
            value = int(self.memory.read(self.r_PC))
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            self.r_A = Byte(self.r_A ^ value)
            self.set_flags_ZN(self.r_A)
            cycles = 2
        
        elif opcode == 0x4D:  # EOR Absolute
            lo = int(self.memory.read(self.r_PC))
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            hi = int(self.memory.read(self.r_PC))
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            addr = int((hi << 8) | lo)
            value = self.memory.read(addr)
            self.r_A = Byte(self.r_A ^ value)
            self.set_flags_ZN(self.r_A)
            cycles = 4
        
        elif opcode == 0x5D:  # EOR Absolute X
            lo = int(self.memory.read(self.r_PC))
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            hi = int(self.memory.read(self.r_PC))
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            base_addr = int((hi << 8) | lo)
            addr = Address(int(base_addr) + int(self.r_X))
            if (base_addr & 0xFF00) != (addr & 0xFF00):
                cycles = 5
            else:
                cycles = 4
            value = self.memory.read(addr)
            self.r_A = Byte(self.r_A ^ value)
            self.set_flags_ZN(self.r_A)
        
        elif opcode == 0x59:  # EOR Absolute Y
            lo = int(self.memory.read(self.r_PC))
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            hi = int(self.memory.read(self.r_PC))
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            base_addr = int((hi << 8) | lo)
            addr = Address(int(base_addr) + int(self.r_Y))
            if (base_addr & 0xFF00) != (addr & 0xFF00):
                cycles = 5
            else:
                cycles = 4
            value = self.memory.read(addr)
            self.r_A = Byte(self.r_A ^ value)
            self.set_flags_ZN(self.r_A)
        
        elif opcode == 0x55:  # EOR Zero Page X
            addr = (int(self.memory.read(self.r_PC)) + int(self.r_X)) & 0xFF
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            value = self.memory.read(addr)
            self.r_A = Byte(self.r_A ^ value)
            self.set_flags_ZN(self.r_A)
            cycles = 4
        
        elif opcode == 0x51:  # EOR Indirect Y
            zero_addr = int(self.memory.read(self.r_PC))
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            lo = self.memory.read(zero_addr & 0xFF)
            hi = self.memory.read((zero_addr + 1) & 0xFF)
            base_addr = int((hi << 8) | lo)
            addr = Address(int(base_addr) + int(self.r_Y))
            if (base_addr & 0xFF00) != (addr & 0xFF00):
                cycles = 6
            else:
                cycles = 5
            value = self.memory.read(addr)
            self.r_A = Byte(self.r_A ^ value)
            self.set_flags_ZN(self.r_A)
        
        elif opcode == 0x41:  # EOR Indirect X
            zero_addr = (int(self.memory.read(self.r_PC)) + int(self.r_X)) & 0xFF
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            lo = self.memory.read(zero_addr & 0xFF)
            hi = self.memory.read((zero_addr + 1) & 0xFF)
            addr = int((hi << 8) | lo)
            value = self.memory.read(addr)
            self.r_A = Byte(self.r_A ^ value)
            self.set_flags_ZN(self.r_A)
            cycles = 6
        
        elif opcode == 0x69:  # ADC Immediate
            value = int(self.memory.read(self.r_PC))
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            sum_val = int(self.r_A) + int(value) + (1 if self.f_C else 0)
            self.f_C = (sum_val & 0x100) != 0
            self.f_V = ((int(self.r_A) ^ sum_val) & (int(value) ^ sum_val) & 0x80) != 0
            self.r_A = Byte(sum_val & 0xFF)
            self.set_flags_ZN(self.r_A)
            cycles = 2
        
        elif opcode == 0x6D:  # ADC Absolute
            lo = int(self.memory.read(self.r_PC))
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            hi = int(self.memory.read(self.r_PC))
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            addr = int((hi << 8) | lo)
            value = self.memory.read(addr)
            sum_val = int(self.r_A) + int(value) + (1 if self.f_C else 0)
            self.f_C = (sum_val & 0x100) != 0
            self.f_V = ((int(self.r_A) ^ sum_val) & (int(value) ^ sum_val) & 0x80) != 0
            self.r_A = Byte(sum_val & 0xFF)
            self.set_flags_ZN(self.r_A)
            cycles = 4
        
        elif opcode == 0x7D:  # ADC Absolute X
            lo = int(self.memory.read(self.r_PC))
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            hi = int(self.memory.read(self.r_PC))
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            base_addr = int((hi << 8) | lo)
            addr = Address(int(base_addr) + int(self.r_X))
            if (base_addr & 0xFF00) != (addr & 0xFF00):
                cycles = 5
            else:
                cycles = 4
            value = self.memory.read(addr)
            sum_val = int(self.r_A) + int(value) + (1 if self.f_C else 0)
            self.f_C = (sum_val & 0x100) != 0
            self.f_V = ((int(self.r_A) ^ sum_val) & (int(value) ^ sum_val) & 0x80) != 0
            self.r_A = Byte(sum_val & 0xFF)
            self.set_flags_ZN(self.r_A)
        
        elif opcode == 0x79:  # ADC Absolute Y
            lo = int(self.memory.read(self.r_PC))
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            hi = int(self.memory.read(self.r_PC))
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            base_addr = int((hi << 8) | lo)
            addr = Address(int(base_addr) + int(self.r_Y))
            if (base_addr & 0xFF00) != (addr & 0xFF00):
                cycles = 5
            else:
                cycles = 4
            value = self.memory.read(addr)
            sum_val = int(self.r_A) + int(value) + (1 if self.f_C else 0)
            self.f_C = (sum_val & 0x100) != 0
            self.f_V = ((int(self.r_A) ^ sum_val) & (int(value) ^ sum_val) & 0x80) != 0
            self.r_A = Byte(sum_val & 0xFF)
            self.set_flags_ZN(self.r_A)
        
        elif opcode == 0x75:  # ADC Zero Page X
            addr = (int(self.memory.read(self.r_PC)) + int(self.r_X)) & 0xFF
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            value = self.memory.read(addr)
            sum_val = int(self.r_A) + int(value) + (1 if self.f_C else 0)
            self.f_C = (sum_val & 0x100) != 0
            self.f_V = ((int(self.r_A) ^ sum_val) & (int(value) ^ sum_val) & 0x80) != 0
            self.r_A = Byte(sum_val & 0xFF)
            self.set_flags_ZN(self.r_A)
            cycles = 4
        
        elif opcode == 0x71:  # ADC Indirect Y
            zero_addr = int(self.memory.read(self.r_PC))
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            lo = self.memory.read(zero_addr & 0xFF)
            hi = self.memory.read((zero_addr + 1) & 0xFF)
            base_addr = int((hi << 8) | lo)
            addr = Address(int(base_addr) + int(self.r_Y))
            if (base_addr & 0xFF00) != (addr & 0xFF00):
                cycles = 6
            else:
                cycles = 5
            value = self.memory.read(addr)
            sum_val = int(self.r_A) + int(value) + (1 if self.f_C else 0)
            self.f_C = (sum_val & 0x100) != 0
            self.f_V = ((int(self.r_A) ^ sum_val) & (int(value) ^ sum_val) & 0x80) != 0
            self.r_A = Byte(sum_val & 0xFF)
            self.set_flags_ZN(self.r_A)
        
        elif opcode == 0x61:  # ADC Indirect X
            zero_addr = (int(self.memory.read(self.r_PC)) + int(self.r_X)) & 0xFF
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            lo = self.memory.read(zero_addr & 0xFF)
            hi = self.memory.read((zero_addr + 1) & 0xFF)
            addr = int((hi << 8) | lo)
            value = self.memory.read(addr)
            sum_val = int(self.r_A) + int(value) + (1 if self.f_C else 0)
            self.f_C = (sum_val & 0x100) != 0
            self.f_V = ((int(self.r_A) ^ sum_val) & (int(value) ^ sum_val) & 0x80) != 0
            self.r_A = Byte(sum_val & 0xFF)
            self.set_flags_ZN(self.r_A)
            cycles = 6
        
        elif opcode == 0xCD:  # CMP Absolute
            lo = int(self.memory.read(self.r_PC))
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            hi = int(self.memory.read(self.r_PC))
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            addr = int((hi << 8) | lo)
            value = self.memory.read(addr)
            result = int(self.r_A) - int(value)
            self.f_C = result >= 0
            self.set_flags_ZN(Byte(result & 0xFF))
            cycles = 4
        
        elif opcode == 0xDD:  # CMP Absolute X
            lo = int(self.memory.read(self.r_PC))
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            hi = int(self.memory.read(self.r_PC))
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            base_addr = int((hi << 8) | lo)
            addr = Address(int(base_addr) + int(self.r_X))
            if (base_addr & 0xFF00) != (addr & 0xFF00):
                cycles = 5
            else:
                cycles = 4
            value = self.memory.read(addr)
            result = int(self.r_A) - int(value)
            self.f_C = result >= 0
            self.set_flags_ZN(Byte(result & 0xFF))
        
        elif opcode == 0xD9:  # CMP Absolute Y
            lo = int(self.memory.read(self.r_PC))
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            hi = int(self.memory.read(self.r_PC))
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            base_addr = int((hi << 8) | lo)
            addr = Address(int(base_addr) + int(self.r_Y))
            if (base_addr & 0xFF00) != (addr & 0xFF00):
                cycles = 5
            else:
                cycles = 4
            value = self.memory.read(addr)
            result = int(self.r_A) - int(value)
            self.f_C = result >= 0
            self.set_flags_ZN(Byte(result & 0xFF))
        
        elif opcode == 0xD5:  # CMP Zero Page X
            addr = (int(self.memory.read(self.r_PC)) + int(self.r_X)) & 0xFF
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            value = self.memory.read(addr)
            result = int(self.r_A) - int(value)
            self.f_C = result >= 0
            self.set_flags_ZN(Byte(result & 0xFF))
            cycles = 4
        
        elif opcode == 0xD1:  # CMP Indirect Y
            zero_addr = int(self.memory.read(self.r_PC))
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            lo = self.memory.read(zero_addr & 0xFF)
            hi = self.memory.read((zero_addr + 1) & 0xFF)
            base_addr = int((hi << 8) | lo)
            addr = Address(int(base_addr) + int(self.r_Y))
            if (base_addr & 0xFF00) != (addr & 0xFF00):
                cycles = 6
            else:
                cycles = 5
            value = self.memory.read(addr)
            result = int(self.r_A) - int(value)
            self.f_C = result >= 0
            self.set_flags_ZN(Byte(result & 0xFF))
        
        elif opcode == 0xC1:  # CMP Indirect X
            zero_addr = (int(self.memory.read(self.r_PC)) + int(self.r_X)) & 0xFF
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            lo = self.memory.read(zero_addr & 0xFF)
            hi = self.memory.read((zero_addr + 1) & 0xFF)
            addr = int((hi << 8) | lo)
            value = self.memory.read(addr)
            result = int(self.r_A) - int(value)
            self.f_C = result >= 0
            self.set_flags_ZN(Byte(result & 0xFF))
            cycles = 6
        
        elif opcode == 0x95:  # STA Zero Page X
            addr = (int(self.memory.read(self.r_PC)) + int(self.r_X)) & 0xFF
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            self.memory.write(addr, self.r_A)
            cycles = 4
        
        elif opcode == 0x9D:  # STA Absolute X
            lo = int(self.memory.read(self.r_PC))
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            hi = int(self.memory.read(self.r_PC))
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            addr = int((hi << 8) | lo)
            addr = Address(addr + self.r_X)
            self.memory.write(addr, self.r_A)
            cycles = 5
        
        elif opcode == 0x99:  # STA Absolute Y
            lo = int(self.memory.read(self.r_PC))
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            hi = int(self.memory.read(self.r_PC))
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            addr = int((hi << 8) | lo)
            addr = Address(addr + self.r_Y)
            self.memory.write(addr, self.r_A)
            cycles = 5
        
        elif opcode == 0x84:  # STY Zero Page
            addr = int(self.memory.read(self.r_PC))
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            self.memory.write(addr, self.r_Y)
            cycles = 3
        
        elif opcode == 0x8C:  # STY Absolute
            lo = int(self.memory.read(self.r_PC))
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            hi = int(self.memory.read(self.r_PC))
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            addr = int((hi << 8) | lo)
            self.memory.write(addr, self.r_Y)
            cycles = 4
        
        elif opcode == 0x94:  # STY Zero Page X
            addr = (int(self.memory.read(self.r_PC)) + int(self.r_X)) & 0xFF
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            self.memory.write(addr, self.r_Y)
            cycles = 4
        
        elif opcode == 0xA4:  # LDY Zero Page
            addr = int(self.memory.read(self.r_PC))
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            self.r_Y = self.memory.read(addr)
            self.set_flags_ZN(self.r_Y)
            cycles = 3
        
        elif opcode == 0xAC:  # LDY Absolute
            lo = int(self.memory.read(self.r_PC))
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            hi = int(self.memory.read(self.r_PC))
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            addr = int((hi << 8) | lo)
            self.r_Y = self.memory.read(addr)
            self.set_flags_ZN(self.r_Y)
            cycles = 4
        
        elif opcode == 0xBC:  # LDY Absolute X
            lo = int(self.memory.read(self.r_PC))
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            hi = int(self.memory.read(self.r_PC))
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            base_addr = int((hi << 8) | lo)
            addr = Address(int(base_addr) + int(self.r_X))
            if (base_addr & 0xFF00) != (addr & 0xFF00):
                cycles = 5
            else:
                cycles = 4
            self.r_Y = self.memory.read(addr)
            self.set_flags_ZN(self.r_Y)
        
        elif opcode == 0xB4:  # LDY Zero Page X
            addr = (int(self.memory.read(self.r_PC)) + int(self.r_X)) & 0xFF
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            self.r_Y = self.memory.read(addr)
            self.set_flags_ZN(self.r_Y)
            cycles = 4
        
        elif opcode == 0xA6:  # LDX Zero Page
            addr = int(self.memory.read(self.r_PC))
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            self.r_X = self.memory.read(addr)
            self.set_flags_ZN(self.r_X)
            cycles = 3
        
        elif opcode == 0xAE:  # LDX Absolute
            lo = int(self.memory.read(self.r_PC))
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            hi = int(self.memory.read(self.r_PC))
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            addr = int((hi << 8) | lo)
            self.r_X = self.memory.read(addr)
            self.set_flags_ZN(self.r_X)
            cycles = 4
        
        elif opcode == 0xBE:  # LDX Absolute Y
            lo = int(self.memory.read(self.r_PC))
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            hi = int(self.memory.read(self.r_PC))
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            base_addr = int((hi << 8) | lo)
            addr = Address(int(base_addr) + int(self.r_Y))
            if (base_addr & 0xFF00) != (addr & 0xFF00):
                cycles = 5
            else:
                cycles = 4
            self.r_X = self.memory.read(addr)
            self.set_flags_ZN(self.r_X)
        
        elif opcode == 0xB6:  # LDX Zero Page Y
            addr = (int(self.memory.read(self.r_PC)) + int(self.r_Y)) & 0xFF
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            self.r_X = self.memory.read(addr)
            self.set_flags_ZN(self.r_X)
            cycles = 4
        
        elif opcode == 0xE4:  # CPX Zero Page
            addr = int(self.memory.read(self.r_PC))
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            value = self.memory.read(addr)
            result = int(self.r_X) - int(value)
            self.f_C = result >= 0
            self.set_flags_ZN(Byte(result & 0xFF))
            cycles = 3
        
        elif opcode == 0xEC:  # CPX Absolute
            lo = int(self.memory.read(self.r_PC))
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            hi = int(self.memory.read(self.r_PC))
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            addr = int((hi << 8) | lo)
            value = self.memory.read(addr)
            result = int(self.r_X) - int(value)
            self.f_C = result >= 0
            self.set_flags_ZN(Byte(result & 0xFF))
            cycles = 4
        
        elif opcode == 0xC4:  # CPY Zero Page
            addr = int(self.memory.read(self.r_PC))
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            value = self.memory.read(addr)
            result = int(self.r_Y) - int(value)
            self.f_C = result >= 0
            self.set_flags_ZN(Byte(result & 0xFF))
            cycles = 3
        
        elif opcode == 0xFD:  # SBC Absolute X
            lo = int(self.memory.read(self.r_PC))
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            hi = int(self.memory.read(self.r_PC))
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            base_addr = int((hi << 8) | lo)
            addr = Address(int(base_addr) + int(self.r_X))
            if (base_addr & 0xFF00) != (addr & 0xFF00):
                cycles = 5
            else:
                cycles = 4
            value = self.memory.read(addr)
            diff = int(self.r_A) - int(value) - (1 - int(self.f_C))
            self.f_C = not bool(diff & 0x100)
            self.f_V = ((int(self.r_A) ^ diff) & ((0xFF ^ int(value)) ^ diff) & 0x80) != 0
            self.r_A = Byte(diff & 0xFF)
            self.set_flags_ZN(self.r_A)
        
        elif opcode == 0xF9:  # SBC Absolute Y
            lo = int(self.memory.read(self.r_PC))
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            hi = int(self.memory.read(self.r_PC))
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            base_addr = int((hi << 8) | lo)
            addr = Address(int(base_addr) + int(self.r_Y))
            if (base_addr & 0xFF00) != (addr & 0xFF00):
                cycles = 5
            else:
                cycles = 4
            value = self.memory.read(addr)
            diff = int(self.r_A) - int(value) - (1 - int(self.f_C))
            self.f_C = not bool(diff & 0x100)
            self.f_V = ((int(self.r_A) ^ diff) & ((0xFF ^ int(value)) ^ diff) & 0x80) != 0
            self.r_A = Byte(diff & 0xFF)
            self.set_flags_ZN(self.r_A)
        
        elif opcode == 0xF5:  # SBC Zero Page X
            addr = (int(self.memory.read(self.r_PC)) + int(self.r_X)) & 0xFF
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            value = self.memory.read(addr)
            diff = int(self.r_A) - int(value) - (1 - int(self.f_C))
            self.f_C = not bool(diff & 0x100)
            self.f_V = ((int(self.r_A) ^ diff) & ((0xFF ^ int(value)) ^ diff) & 0x80) != 0
            self.r_A = Byte(diff & 0xFF)
            self.set_flags_ZN(self.r_A)
            cycles = 4
        
        elif opcode == 0xF1:  # SBC Indirect Y
            zero_addr = int(self.memory.read(self.r_PC))
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            lo = self.memory.read(zero_addr & 0xFF)
            hi = self.memory.read((zero_addr + 1) & 0xFF)
            base_addr = int((hi << 8) | lo)
            addr = Address(int(base_addr) + int(self.r_Y))
            if (base_addr & 0xFF00) != (addr & 0xFF00):
                cycles = 6
            else:
                cycles = 5
            value = self.memory.read(addr)
            diff = int(self.r_A) - int(value) - (1 - int(self.f_C))
            self.f_C = not bool(diff & 0x100)
            self.f_V = ((int(self.r_A) ^ diff) & ((0xFF ^ int(value)) ^ diff) & 0x80) != 0
            self.r_A = Byte(diff & 0xFF)
            self.set_flags_ZN(self.r_A)
        
        elif opcode == 0xE1:  # SBC Indirect X
            zero_addr = (int(self.memory.read(self.r_PC)) + int(self.r_X)) & 0xFF
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            lo = self.memory.read(zero_addr & 0xFF)
            hi = self.memory.read((zero_addr + 1) & 0xFF)
            addr = int((hi << 8) | lo)
            value = self.memory.read(addr)
            diff = int(self.r_A) - int(value) - (1 - int(self.f_C))
            self.f_C = not bool(diff & 0x100)
            self.f_V = ((int(self.r_A) ^ diff) & ((0xFF ^ int(value)) ^ diff) & 0x80) != 0
            self.r_A = Byte(diff & 0xFF)
            self.set_flags_ZN(self.r_A)
            cycles = 6
        
        elif opcode == 0x24:  # BIT Zero Page
            addr = int(self.memory.read(self.r_PC))
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            value = self.memory.read(addr)
            self.f_Z = not (self.r_A & value)
            self.f_V = (value & 0x40) != 0
            self.f_N = (value & 0x80) != 0
            cycles = 3
        
        elif opcode == 0x2C:  # BIT Absolute
            lo = int(self.memory.read(self.r_PC))
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            hi = int(self.memory.read(self.r_PC))
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            addr = int((hi << 8) | lo)
            value = self.memory.read(addr)
            self.f_Z = not (self.r_A & value)
            self.f_V = (value & 0x40) != 0
            self.f_N = (value & 0x80) != 0
            cycles = 4
        
        elif opcode == 0x08:  # PHP - Push Processor Status
            flag_byte = (self.f_C | (self.f_Z << 1) | (self.f_I << 2) | 
                         (self.f_D << 3) | 0x10 | 0x04 | (self.f_V << 6) | (self.f_N << 7))
            self.push_stack(flag_byte)
            cycles = 3
        
        elif opcode == 0x28:  # PLP - Pull Processor Status
            flag_byte = self.pull_stack()
            self.f_N = (flag_byte & 0x80) != 0
            self.f_V = (flag_byte & 0x40) != 0
            self.f_D = (flag_byte & 0x08) != 0
            self.f_I = (flag_byte & 0x04) != 0
            self.f_Z = (flag_byte & 0x02) != 0
            self.f_C = (flag_byte & 0x01) != 0
            cycles = 4
        
        elif opcode == 0x48:  # PHA - Push Accumulator
            self.push_stack(self.r_A)
            cycles = 3
        
        elif opcode == 0x68:  # PLA - Pull Accumulator
            self.r_A = self.pull_stack()
            self.set_flags_ZN(self.r_A)
            cycles = 4
        
        elif opcode == 0xAA:  # TAX - Transfer A to X
            self.r_X = self.r_A
            self.set_flags_ZN(self.r_X)
            cycles = 2
        
        elif opcode == 0xA8:  # TAY - Transfer A to Y
            self.r_Y = self.r_A
            self.set_flags_ZN(self.r_Y)
            cycles = 2
        
        elif opcode == 0xBA:  # TSX - Transfer SP to X
            self.r_X = self.r_SP
            self.set_flags_ZN(self.r_X)
            cycles = 2
        
        elif opcode == 0x8A:  # TXA - Transfer X to A
            self.r_A = self.r_X
            self.set_flags_ZN(self.r_A)
            cycles = 2
        
        elif opcode == 0x98:  # TYA - Transfer Y to A
            self.r_A = self.r_Y
            self.set_flags_ZN(self.r_A)
            cycles = 2
        
        elif opcode == 0x4A:  # LSR - Logical Shift Right Accumulator
            self.f_C = (self.r_A & 0x01) != 0
            self.r_A = Byte(int(self.r_A) >> 1)
            self.set_flags_ZN(self.r_A)
            cycles = 2
        
        elif opcode == 0x46:  # LSR Zero Page
            addr = int(self.memory.read(self.r_PC))
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            value = self.memory.read(addr)
            self.f_C = (value & 0x01) != 0
            result = Byte(int(value) >> 1)
            self.memory.write(addr, result)
            self.set_flags_ZN(result)
            cycles = 5
        
        elif opcode == 0x4E:  # LSR Absolute
            lo = int(self.memory.read(self.r_PC))
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            hi = int(self.memory.read(self.r_PC))
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            addr = int((hi << 8) | lo)
            value = self.memory.read(addr)
            self.f_C = (value & 0x01) != 0
            result = Byte(int(value) >> 1)
            self.memory.write(addr, result)
            self.set_flags_ZN(result)
            cycles = 6
        
        elif opcode == 0x56:  # LSR Zero Page X
            addr = (int(self.memory.read(self.r_PC)) + int(self.r_X)) & 0xFF
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            value = self.memory.read(addr)
            self.f_C = (value & 0x01) != 0
            result = Byte(int(value) >> 1)
            self.memory.write(addr, result)
            self.set_flags_ZN(result)
            cycles = 6
        
        elif opcode == 0x5E:  # LSR Absolute X
            lo = int(self.memory.read(self.r_PC))
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            hi = int(self.memory.read(self.r_PC))
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            base_addr = int((hi << 8) | lo)
            addr = Address(int(base_addr) + int(self.r_X))
            value = self.memory.read(addr)
            self.f_C = (value & 0x01) != 0
            result = Byte(int(value) >> 1)
            self.memory.write(addr, result)
            self.set_flags_ZN(result)
            cycles = 7
        
        elif opcode == 0x6A:  # ROR - Rotate Right Accumulator
            prev_c = self.f_C
            self.f_C = (self.r_A & 0x01) != 0
            self.r_A = Byte((int(self.r_A) >> 1) | (prev_c << 7))
            self.set_flags_ZN(self.r_A)
            cycles = 2
        
        elif opcode == 0x66:  # ROR Zero Page
            addr = int(self.memory.read(self.r_PC))
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            value = self.memory.read(addr)
            prev_c = self.f_C
            self.f_C = (value & 0x01) != 0
            result = Byte((int(value) >> 1) | (prev_c << 7))
            self.memory.write(addr, result)
            self.set_flags_ZN(result)
            cycles = 5
        
        elif opcode == 0x6E:  # ROR Absolute
            lo = int(self.memory.read(self.r_PC))
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            hi = int(self.memory.read(self.r_PC))
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            addr = int((hi << 8) | lo)
            value = self.memory.read(addr)
            prev_c = self.f_C
            self.f_C = (value & 0x01) != 0
            result = Byte((int(value) >> 1) | (prev_c << 7))
            self.memory.write(addr, result)
            self.set_flags_ZN(result)
            cycles = 6
        
        elif opcode == 0x76:  # ROR Zero Page X
            addr = (int(self.memory.read(self.r_PC)) + int(self.r_X)) & 0xFF
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            value = self.memory.read(addr)
            prev_c = self.f_C
            self.f_C = (value & 0x01) != 0
            result = Byte((int(value) >> 1) | (prev_c << 7))
            self.memory.write(addr, result)
            self.set_flags_ZN(result)
            cycles = 6
        
        elif opcode == 0x7E:  # ROR Absolute X
            lo = int(self.memory.read(self.r_PC))
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            hi = int(self.memory.read(self.r_PC))
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            base_addr = int((hi << 8) | lo)
            addr = Address(int(base_addr) + int(self.r_X))
            value = self.memory.read(addr)
            prev_c = self.f_C
            self.f_C = (value & 0x01) != 0
            result = Byte((int(value) >> 1) | (prev_c << 7))
            self.memory.write(addr, result)
            self.set_flags_ZN(result)
            cycles = 7
        
        elif opcode == 0x2A:  # ROL - Rotate Left Accumulator
            prev_c = self.f_C
            self.f_C = (self.r_A & 0x80) != 0
            self.r_A = Byte(((int(self.r_A) << 1) & 0xFF) | (1 if prev_c else 0))
            self.set_flags_ZN(self.r_A)
            cycles = 2
        
        elif opcode == 0x26:  # ROL Zero Page
            addr = int(self.memory.read(self.r_PC))
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            value = self.memory.read(addr)
            prev_c = self.f_C
            self.f_C = (value & 0x80) != 0
            result = Byte(((int(value) << 1) & 0xFF) | (1 if prev_c else 0))
            self.memory.write(addr, result)
            self.set_flags_ZN(result)
            cycles = 5
        
        elif opcode == 0x2E:  # ROL Absolute
            lo = int(self.memory.read(self.r_PC))
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            hi = int(self.memory.read(self.r_PC))
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            addr = int((hi << 8) | lo)
            value = self.memory.read(addr)
            prev_c = self.f_C
            self.f_C = (value & 0x80) != 0
            result = Byte(((int(value) << 1) & 0xFF) | (1 if prev_c else 0))
            self.memory.write(addr, result)
            self.set_flags_ZN(result)
            cycles = 6
        
        elif opcode == 0x36:  # ROL Zero Page X
            addr = (int(self.memory.read(self.r_PC)) + int(self.r_X)) & 0xFF
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            value = self.memory.read(addr)
            prev_c = self.f_C
            self.f_C = (value & 0x80) != 0
            result = Byte(((int(value) << 1) & 0xFF) | (1 if prev_c else 0))
            self.memory.write(addr, result)
            self.set_flags_ZN(result)
            cycles = 6
        
        elif opcode == 0x3E:  # ROL Absolute X
            lo = int(self.memory.read(self.r_PC))
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            hi = int(self.memory.read(self.r_PC))
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            base_addr = int((hi << 8) | lo)
            addr = Address(int(base_addr) + int(self.r_X))
            value = self.memory.read(addr)
            prev_c = self.f_C
            self.f_C = (value & 0x80) != 0
            result = Byte(((int(value) << 1) & 0xFF) | (1 if prev_c else 0))
            self.memory.write(addr, result)
            self.set_flags_ZN(result)
            cycles = 7
        
        elif opcode == 0xC6:  # DEC Zero Page
            addr = int(self.memory.read(self.r_PC))
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            value = self.memory.read(addr)
            result = Byte((int(value) - 1) & 0xFF)
            self.memory.write(addr, result)
            self.set_flags_ZN(result)
            cycles = 5
        
        elif opcode == 0xCE:  # DEC Absolute
            lo = int(self.memory.read(self.r_PC))
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            hi = int(self.memory.read(self.r_PC))
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            addr = int((hi << 8) | lo)
            value = self.memory.read(addr)
            result = Byte((int(value) - 1) & 0xFF)
            self.memory.write(addr, result)
            self.set_flags_ZN(result)
            cycles = 6
        
        elif opcode == 0xD6:  # DEC Zero Page X
            addr = (int(self.memory.read(self.r_PC)) + int(self.r_X)) & 0xFF
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            value = self.memory.read(addr)
            result = Byte((int(value) - 1) & 0xFF)
            self.memory.write(addr, result)
            self.set_flags_ZN(result)
            cycles = 6
        
        elif opcode == 0xDE:  # DEC Absolute X
            lo = int(self.memory.read(self.r_PC))
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            hi = int(self.memory.read(self.r_PC))
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            base_addr = int((hi << 8) | lo)
            addr = Address(int(base_addr) + int(self.r_X))
            value = self.memory.read(addr)
            result = Byte((int(value) - 1) & 0xFF)
            self.memory.write(addr, result)
            self.set_flags_ZN(result)
            cycles = 7
        
        elif opcode == 0xE6:  # INC Zero Page
            addr = int(self.memory.read(self.r_PC))
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            value = self.memory.read(addr)
            result = Byte((int(value) + 1) & 0xFF)
            self.memory.write(addr, result)
            self.set_flags_ZN(result)
            cycles = 5
        
        elif opcode == 0xFE:  # INC Absolute X
            lo = int(self.memory.read(self.r_PC))
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            hi = int(self.memory.read(self.r_PC))
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            base_addr = int((hi << 8) | lo)
            addr = Address(int(base_addr) + int(self.r_X))
            value = self.memory.read(addr)
            result = Byte((int(value) + 1) & 0xFF)
            self.memory.write(addr, result)
            self.set_flags_ZN(result)
            cycles = 7
        
        elif opcode == 0x25:  # AND zero page
            addr = int(self.memory.read(self.r_PC))
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            value = self.memory.read(addr)
            self.r_A = Byte(self.r_A & value)
            self.set_flags_ZN(self.r_A)
            cycles = 3
        
        elif opcode == 0x45:  # EOR zero page
            addr = int(self.memory.read(self.r_PC))
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            value = self.memory.read(addr)
            self.r_A = Byte(self.r_A ^ value)
            self.set_flags_ZN(self.r_A)
            cycles = 3
        
        elif opcode == 0x9A:  # TXS - Transfer X to Stack Pointer
            self.r_SP = self.r_X
            cycles = 2
        
        elif opcode == 0x0A:  # ASL - Arithmetic Shift Left Accumulator
            # Shift accumulator left, shifting bit 7 to carry flag
            self.f_C = (self.r_A & 0x80) != 0  # Set carry to bit 7
            self.r_A = Byte((self.r_A << 1) & 0xFF)
            self.set_flags_ZN(self.r_A)
            cycles = 2
        
        elif opcode == 0x06:  # ASL - Arithmetic Shift Left Zero Page
            addr = int(self.memory.read(self.r_PC))
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            value = self.memory.read(addr)
            self.f_C = (value & 0x80) != 0  # Set carry to bit 7 before shift
            result = Byte((value << 1) & 0xFF)
            self.memory.write(addr, result)
            self.set_flags_ZN(result)
            cycles = 5  # 5 cycles for zero page addressing with read-modify-write
        
        elif opcode == 0x0E:  # ASL - Arithmetic Shift Left Absolute
            lo = int(self.memory.read(self.r_PC))
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            hi = int(self.memory.read(self.r_PC))
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            addr = int((hi << 8) | lo)
            value = self.memory.read(addr)
            self.f_C = (value & 0x80) != 0  # Set carry to bit 7 before shift
            result = Byte((value << 1) & 0xFF)
            self.memory.write(addr, result)
            self.set_flags_ZN(result)
            cycles = 6  # 6 cycles for absolute addressing with read-modify-write
        
        elif opcode == 0x16:  # ASL - Arithmetic Shift Left Zero Page X
            addr = (int(self.memory.read(self.r_PC)) + int(self.r_X)) & 0xFF
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            value = self.memory.read(addr)
            self.f_C = (value & 0x80) != 0  # Set carry to bit 7 before shift
            result = Byte((value << 1) & 0xFF)
            self.memory.write(addr, result)
            self.set_flags_ZN(result)
            cycles = 6  # 6 cycles for zero page X addressing with read-modify-write
        
        elif opcode == 0x1E:  # ASL - Arithmetic Shift Left Absolute X
            lo = int(self.memory.read(self.r_PC))
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            hi = int(self.memory.read(self.r_PC))
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            base_addr = int((hi << 8) | lo)
            addr = Address(int(base_addr) + int(self.r_X))
            value = self.memory.read(addr)
            self.f_C = (value & 0x80) != 0  # Set carry to bit 7 before shift
            result = Byte((value << 1) & 0xFF)
            self.memory.write(addr, result)
            self.set_flags_ZN(result)
            cycles = 7  # 7 cycles for absolute X addressing with read-modify-write
        
        elif opcode == 0x10:  # BPL - Branch if Plus (Negative flag clear)
            offset = self.memory.read(self.r_PC)
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            if not self.f_N:  # If negative flag is clear, branch
                # Calculate target address with sign extension
                if offset & 0x80:  # If offset is negative (signed)
                    # Convert to signed 8-bit (-128 to 127) then add to PC
                    signed_offset = offset - 0x100  # Convert unsigned byte to signed value
                    target = Address((int(self.r_PC) + signed_offset) & 0xFFFF)
                else:
                    target = Address((int(self.r_PC) + offset) & 0xFFFF)
                # Page boundary check: extra cycle if crossing page boundary
                if (self.r_PC & 0xFF00) != (target & 0xFF00):
                    cycles = 4  # Extra cycle for page crossing
                else:
                    cycles = 3  # Base cycles
                self.r_PC = target
            else:
                cycles = 2  # 2 cycles if branch not taken
        
        elif opcode == 0xB0:  # BCS - Branch if Carry Set
            offset = self.memory.read(self.r_PC)
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            if self.f_C:  # If carry flag is set, branch
                # Calculate target address with sign extension
                if offset & 0x80:  # If offset is negative (signed)
                    # Convert to signed 8-bit (-128 to 127) then add to PC
                    signed_offset = offset - 0x100  # Convert unsigned byte to signed value
                    target = Address((int(self.r_PC) + signed_offset) & 0xFFFF)
                else:
                    target = Address((int(self.r_PC) + offset) & 0xFFFF)
                # Page boundary check: extra cycle if crossing page boundary
                if (self.r_PC & 0xFF00) != (target & 0xFF00):
                    cycles = 4  # Extra cycle for page crossing
                else:
                    cycles = 3  # Base cycles
                self.r_PC = target
            else:
                cycles = 2  # 2 cycles if branch not taken
        
        elif opcode == 0xD0:  # BNE - Branch if Not Equal (Zero flag clear)
            offset = self.memory.read(self.r_PC)
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            if not self.f_Z:  # If zero flag is clear, branch
                # Calculate target address with sign extension
                if offset & 0x80:  # If offset is negative (signed)
                    # Convert to signed 8-bit (-128 to 127) then add to PC
                    signed_offset = offset - 0x100  # Convert unsigned byte to signed value
                    target = Address((int(self.r_PC) + signed_offset) & 0xFFFF)
                else:
                    target = Address((int(self.r_PC) + offset) & 0xFFFF)
                # Page boundary check: extra cycle if crossing page boundary
                if (self.r_PC & 0xFF00) != (target & 0xFF00):
                    cycles = 4  # Extra cycle for page crossing
                else:
                    cycles = 3  # Base cycles
                self.r_PC = target
            else:
                cycles = 2  # 2 cycles if branch not taken
        
        elif opcode == 0x20:  # JSR - Jump to Subroutine
            # Get the target address (2 bytes)
            lo = int(self.memory.read(self.r_PC))
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            hi = int(self.memory.read(self.r_PC))
            target = Address((hi << 8) | lo)
            
            # Push return address (PC-1) onto the stack (JSR's last byte address)
            # When RTS executes, it will pull this address and increment it by 1
            return_addr = self.r_PC - 1  # Address of the last byte of JSR instruction
            self.push_stack(Byte((return_addr >> 8) & 0xFF))  # Push high byte as Byte
            self.push_stack(Byte(return_addr & 0xFF))        # Push low byte as Byte
            
            # Jump to target address
            self.r_PC = target
            cycles = 6  # JSR takes 6 cycles
        
        elif opcode == 0x40:  # RTI - Return from Interrupt
            # Pull processor status from stack
            flag_byte = self.pull_stack()
            self.f_N = (flag_byte & 0x80) != 0
            self.f_V = (flag_byte & 0x40) != 0
            self.f_D = (flag_byte & 0x08) != 0
            self.f_I = (flag_byte & 0x04) != 0
            self.f_Z = (flag_byte & 0x02) != 0
            self.f_C = (flag_byte & 0x01) != 0
            # Pull return address from stack
            lo = self.pull_stack()
            hi = self.pull_stack()
            self.r_PC = Address((hi << 8) | lo)
            cycles = 6  # RTI takes 6 cycles
        
        elif opcode == 0x60:  # RTS - Return from Subroutine
            # Pull return address from stack and add 1
            lo = self.pull_stack()
            hi = self.pull_stack()
            self.r_PC = Address((hi << 8) | lo)
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)  # Add 1 to return address
            cycles = 6  # RTS takes 6 cycles
        
        elif opcode == 0xCC:  # CPY - Compare Y Register Absolute
            lo = int(self.memory.read(self.r_PC))
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            hi = int(self.memory.read(self.r_PC))
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            addr = int((hi << 8) | lo)
            value = self.memory.read(addr)
            
            result = int(self.r_Y) - int(value)
            self.f_C = result >= 0  # Set carry if Y >= value
            self.set_flags_ZN(Byte(result & 0xFF))
            cycles = 4  # 4 cycles for absolute addressing
        
        elif opcode == 0xC0:  # CPY - Compare Y Register Immediate
            value = int(self.memory.read(self.r_PC))
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            
            result = int(self.r_Y) - int(value)
            self.f_C = result >= 0  # Set carry if Y >= value
            self.set_flags_ZN(Byte(result & 0xFF))
            cycles = 2  # 2 cycles for immediate addressing
        
        elif opcode == 0xE0:  # CPX - Compare X Register Immediate
            value = int(self.memory.read(self.r_PC))
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            
            result = int(self.r_X) - int(value)
            self.f_C = result >= 0  # Set carry if X >= value
            self.set_flags_ZN(Byte(result & 0xFF))
            cycles = 2  # 2 cycles for immediate addressing
        
        elif opcode == 0x90:  # BCC - Branch if Carry Clear
            offset = self.memory.read(self.r_PC)
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            if not self.f_C:  # If carry flag is clear, branch
                # Calculate target address with sign extension
                if offset & 0x80:  # If offset is negative (signed)
                    # Convert to signed 8-bit (-128 to 127) then add to PC
                    signed_offset = offset - 0x100  # Convert unsigned byte to signed value
                    target = Address((int(self.r_PC) + signed_offset) & 0xFFFF)
                else:
                    target = Address((int(self.r_PC) + offset) & 0xFFFF)
                # Page boundary check: extra cycle if crossing page boundary
                if (self.r_PC & 0xFF00) != (target & 0xFF00):
                    cycles = 4  # Extra cycle for page crossing
                else:
                    cycles = 3  # Base cycles
                self.r_PC = target
            else:
                cycles = 2  # 2 cycles if branch not taken
        
        elif opcode == 0xB0:  # BCS - Branch if Carry Set
            offset = self.memory.read(self.r_PC)
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            if self.f_C:  # If carry flag is set, branch
                # Calculate target address with sign extension
                if offset & 0x80:  # If offset is negative (signed)
                    # Convert to signed 8-bit (-128 to 127) then add to PC
                    signed_offset = offset - 0x100  # Convert unsigned byte to signed value
                    target = Address((int(self.r_PC) + signed_offset) & 0xFFFF)
                else:
                    target = Address((int(self.r_PC) + offset) & 0xFFFF)
                # Page boundary check: extra cycle if crossing page boundary
                if (self.r_PC & 0xFF00) != (target & 0xFF00):
                    cycles = 4  # Extra cycle for page crossing
                else:
                    cycles = 3  # Base cycles
                self.r_PC = target
            else:
                cycles = 2  # 2 cycles if branch not taken
        
        elif opcode == 0xF0:  # BEQ - Branch if Equal (Zero flag set)
            offset = self.memory.read(self.r_PC)
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            if self.f_Z:  # If zero flag is set, branch
                # Calculate target address with sign extension
                if offset & 0x80:  # If offset is negative (signed)
                    # Convert to signed 8-bit (-128 to 127) then add to PC
                    signed_offset = offset - 0x100  # Convert unsigned byte to signed value
                    target = Address((int(self.r_PC) + signed_offset) & 0xFFFF)
                else:
                    target = Address((int(self.r_PC) + offset) & 0xFFFF)
                # Page boundary check: extra cycle if crossing page boundary
                if (self.r_PC & 0xFF00) != (target & 0xFF00):
                    cycles = 4  # Extra cycle for page crossing
                else:
                    cycles = 3  # Base cycles
                self.r_PC = target
            else:
                cycles = 2  # 2 cycles if branch not taken
        
        elif opcode == 0x30:  # BMI - Branch if Minus (Negative flag set)
            offset = self.memory.read(self.r_PC)
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            if self.f_N:  # If negative flag is set, branch
                # Calculate target address with sign extension
                if offset & 0x80:  # If offset is negative (signed)
                    # Convert to signed 8-bit (-128 to 127) then add to PC
                    signed_offset = offset - 0x100  # Convert unsigned byte to signed value
                    target = Address((int(self.r_PC) + signed_offset) & 0xFFFF)
                else:
                    target = Address((int(self.r_PC) + offset) & 0xFFFF)
                # Page boundary check: extra cycle if crossing page boundary
                if (self.r_PC & 0xFF00) != (target & 0xFF00):
                    cycles = 4  # Extra cycle for page crossing
                else:
                    cycles = 3  # Base cycles
                self.r_PC = target
            else:
                cycles = 2  # 2 cycles if branch not taken
        
        elif opcode == 0x50:  # BVC - Branch if Overflow Clear
            offset = self.memory.read(self.r_PC)
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            if not self.f_V:  # If overflow flag is clear, branch
                # Calculate target address with sign extension
                if offset & 0x80:  # If offset is negative (signed)
                    # Convert to signed 8-bit (-128 to 127) then add to PC
                    signed_offset = offset - 0x100  # Convert unsigned byte to signed value
                    target = Address((int(self.r_PC) + signed_offset) & 0xFFFF)
                else:
                    target = Address((int(self.r_PC) + offset) & 0xFFFF)
                # Page boundary check: extra cycle if crossing page boundary
                if (self.r_PC & 0xFF00) != (target & 0xFF00):
                    cycles = 4  # Extra cycle for page crossing
                else:
                    cycles = 3  # Base cycles
                self.r_PC = target
            else:
                cycles = 2  # 2 cycles if branch not taken
        
        elif opcode == 0x70:  # BVS - Branch if Overflow Set
            offset = self.memory.read(self.r_PC)
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            if self.f_V:  # If overflow flag is set, branch
                # Calculate target address with sign extension
                if offset & 0x80:  # If offset is negative (signed)
                    # Convert to signed 8-bit (-128 to 127) then add to PC
                    signed_offset = offset - 0x100  # Convert unsigned byte to signed value
                    target = Address((int(self.r_PC) + signed_offset) & 0xFFFF)
                else:
                    target = Address((int(self.r_PC) + offset) & 0xFFFF)
                # Page boundary check: extra cycle if crossing page boundary
                if (self.r_PC & 0xFF00) != (target & 0xFF00):
                    cycles = 4  # Extra cycle for page crossing
                else:
                    cycles = 3  # Base cycles
                self.r_PC = target
            else:
                cycles = 2  # 2 cycles if branch not taken
        
        elif opcode == 0x8E:  # STX - Store X Absolute
            lo = int(self.memory.read(self.r_PC))
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            hi = int(self.memory.read(self.r_PC))
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            addr = int((hi << 8) | lo)
            self.memory.write(addr, self.r_X)
            cycles = 4  # 4 cycles for absolute addressing
        
        elif opcode == 0x86:  # STX - Store X Zero Page
            addr = int(self.memory.read(self.r_PC))
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            self.memory.write(addr, self.r_X)
            cycles = 3  # 3 cycles for zero page addressing
        
        elif opcode == 0xEE:  # INC - Increment Memory Absolute
            lo = int(self.memory.read(self.r_PC))
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            hi = int(self.memory.read(self.r_PC))
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            addr = int((hi << 8) | lo)
            value = self.memory.read(addr)
            result = Byte((value + 1) & 0xFF)
            self.memory.write(addr, result)
            self.set_flags_ZN(result)
            cycles = 6  # 6 cycles for absolute addressing with read-modify-write
        
        elif opcode == 0xF6:  # INC - Increment Memory Zero Page, X
            zp_addr = (int(self.memory.read(self.r_PC)) + int(self.r_X)) & 0xFF
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            value = self.memory.read(zp_addr)
            result = Byte((value + 1) & 0xFF)
            self.memory.write(zp_addr, result)
            self.set_flags_ZN(result)
            cycles = 6  # 6 cycles for zero page, X addressing with read-modify-write
        
        elif opcode == 0x19:  # SBC - Subtract with Carry Absolute, Y
            lo = int(self.memory.read(self.r_PC))
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            hi = int(self.memory.read(self.r_PC))
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            addr = int((hi << 8) | lo)
            addr_with_y = Address(addr + self.r_Y)
            
            value = self.memory.read(addr_with_y)
            # Check for page boundary crossing
            if (addr & 0xFF00) != (addr_with_y & 0xFF00):
                cycles = 5  # Extra cycle for page crossing (not counting the base cycles)
            else:
                cycles = 4  # Base cycles for absolute,Y addressing
            
            # SBC: A - M - (1 - C), following C++ implementation
            # High carry means "no borrow", thus negate and subtract
            diff = int(self.r_A) - int(value) - (1 - int(self.f_C))
            # if the ninth bit is 1, the resulting number is negative => borrow => low carry
            self.f_C = not bool(diff & 0x100)
            # Same as ADC, except instead of the subtrahend, substitute with it's one complement
            # Calculate overflow: (A^result) & (M^result) & 0x80 (for SBC it's (A^result) & (~M^result) & 0x80)
            # To avoid issues with Python's ~ operator with negative numbers, use 0xFF ^ value instead
            self.f_V = ((int(self.r_A) ^ diff) & ((0xFF ^ int(value)) ^ diff) & 0x80) != 0
            self.r_A = Byte(diff & 0xFF)
            self.set_flags_ZN(self.r_A)
        
        elif opcode == 0xED:  # SBC - Subtract with Carry Absolute
            lo = int(self.memory.read(self.r_PC))
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            hi = int(self.memory.read(self.r_PC))
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            addr = int((hi << 8) | lo)
            value = self.memory.read(addr)
            
            # SBC: A - M - (1 - C), following C++ implementation
            # High carry means "no borrow", thus negate and subtract
            diff = int(self.r_A) - int(value) - (1 - int(self.f_C))
            # if the ninth bit is 1, the resulting number is negative => borrow => low carry
            self.f_C = not bool(diff & 0x100)
            # Same as ADC, except instead of the subtrahend, substitute with it's one complement
            # Calculate overflow: (A^result) & (M^result) & 0x80 (for SBC it's (A^result) & (~M^result) & 0x80)
            # To avoid issues with Python's ~ operator with negative numbers, use 0xFF ^ value instead
            self.f_V = ((int(self.r_A) ^ diff) & ((0xFF ^ int(value)) ^ diff) & 0x80) != 0
            self.r_A = Byte(diff & 0xFF)  # Convert to unsigned 8-bit
            self.set_flags_ZN(self.r_A)
            cycles = 4  # 4 cycles for absolute addressing
        
        # Illegal opcodes implementations
        elif opcode == 0xFB:  # SBC - Illegal opcode (SBC immediate with 3 bytes)
            # Skip the immediate value (2 bytes)
            self.r_PC = Address((int(self.r_PC) + 2) & 0xFFFF)
            # Perform SBC with dummy value - similar to how illegal opcodes behave
            cycles = 2
        
        elif opcode == 0x0C:  # NOP - Illegal opcode (NOP with absolute addressing)
            # Skip 2 bytes of addressing
            self.r_PC = Address((int(self.r_PC) + 2) & 0xFFFF)
            cycles = 4  # Takes 4 cycles like absolute addressing
        
        elif opcode == 0x02 or opcode == 0x82 or opcode == 0x80:  # JAM - Illegal opcodes that lock up CPU
            # In real 6502, these would lock up the CPU, but for simulation we'll just advance PC
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            cycles = 2
        
        elif opcode == 0x74:  # NOP - Illegal opcode (NOP with zero page,X addressing)
            # Skip 1 byte of addressing
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            cycles = 4  # Takes 4 cycles like zero page,X addressing
        
        elif opcode == 0x07:  # SLO - Illegal opcode (Shift Left and OR)
            # Skip 1 byte of addressing (zero page)
            addr = int(self.memory.read(self.r_PC))
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            # Read, shift left, store back, then OR with accumulator
            value = self.memory.read(addr)
            self.f_C = (value & 0x80) != 0  # Set carry to bit 7 before shift
            result = Byte((value << 1) & 0xFF)
            self.memory.write(addr, result)
            self.r_A = Byte(self.r_A | result)
            self.set_flags_ZN(self.r_A)
            cycles = 5
        
        elif opcode == 0x09:  # NOP - Illegal opcode (NOP immediate)
            # Skip 1 byte of immediate value
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
            cycles = 2
        
        elif opcode == 0xFF:  # Illegal opcode - acts like NOP
            # 0xFF is an illegal opcode, but we'll treat it like a NOP
            # This is often found at the end of ROMs
            cycles = 2
        
        else:
            # For unimplemented opcodes, just advance PC and return default cycles
            # In a real implementation, we'd have to determine instruction length
            # based on the opcode, but for now we'll just return a default
            error(f"Unimplemented opcode: {hex(opcode)} at PC: {hex(self.r_PC - 1)}")
            cycles = 2
        
        return cycles
    
    def push_stack(self, value):
        """Push a value onto the stack"""
        # Ensure the value is within uint8 range
        value_byte = Byte(value & 0xFF)
        # Calculate stack address (0x0100-0x01FF)
        stack_addr = 0x0100 | int(self.r_SP)
        self.memory.write(stack_addr, value_byte)
        self.r_SP = Byte((int(self.r_SP) - 1) & 0xFF)
    
    def pull_stack(self) -> Byte:
        """Pull a value from the stack"""
        self.r_SP = Byte(self.r_SP + 1)
        stack_addr = 0x0100 | int(self.r_SP)
        return Byte(self.memory.read(stack_addr))
    
    def set_flags_ZN(self, value: Byte):
        """Set Zero and Negative flags based on value"""
        self.f_Z = (value == 0)
        self.f_N = ((value & 0x80) != 0)
    
    def get_PC(self) -> Address:
        """Get program counter"""
        return self.r_PC
    
    def interrupt(self, interrupt_type: str):
        """Set interrupt flag for NMI or IRQ"""
        if interrupt_type == 'NMI':
            self.m_pendingNMI = True
        elif interrupt_type == 'IRQ':
            self.m_pendingIRQ = True
    
    def _interrupt_sequence(self, interrupt_type: str):
        """Handle interrupt sequence (NMI, IRQ, or BRK)"""
        # Check if interrupts are disabled (not for NMI or BRK)
        if interrupt_type == 'IRQ' and self.f_I:
            return
        
        # Add one if BRK, a quirk of 6502
        if interrupt_type == 'BRK':
            self.r_PC = Address((int(self.r_PC) + 1) & 0xFFFF)
        
        # Push PC high byte
        self.push_stack((int(self.r_PC) >> 8) & 0xFF)
        # Push PC low byte
        self.push_stack(int(self.r_PC) & 0xFF)
        
        # Push status flags
        flags = (self.f_N << 7) | (self.f_V << 6) | (1 << 5) | ((1 if interrupt_type == 'BRK' else 0) << 4) | (self.f_D << 3) | (self.f_I << 2) | (self.f_Z << 1) | self.f_C
        self.push_stack(flags)
        
        # Set interrupt disable flag
        self.f_I = True
        
        # Jump to interrupt vector
        if interrupt_type == 'NMI':
            lo = self.memory.read(NMIVector)
            hi = self.memory.read(NMIVector + 1)
            self.r_PC = Address((hi << 8) | lo)
        else:  # IRQ or BRK
            lo = self.memory.read(IRQVector)
            hi = self.memory.read(IRQVector + 1)
            self.r_PC = Address((hi << 8) | lo)
    
    def skip_DMA_cycles(self):
        """Skip cycles after DMA operation"""
        self.m_skipCycles += 513
        if self.m_cycles & 0x0002:
            self.m_skipCycles += 1