"""
CPU Emulator for SimpleNES-py
Implements Ricoh 2A03 CPU (based on 6502)
"""
import numpy as np
from typing import Callable, Optional

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
            start_addr = Address((hi << 8) | lo)
        
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
        # Fetch opcode
        opcode = self.memory.read(self.r_PC)
        self.r_PC = Address(self.r_PC + 1)
        
        # Execute instruction based on opcode
        cycles = self.execute_opcode(opcode)
        
        # Update cycle count
        self.m_cycles += cycles
        
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
            lo = self.memory.read(self.r_PC)
            self.r_PC = Address(self.r_PC + 1)
            hi = self.memory.read(self.r_PC)
            self.r_PC = Address(self.r_PC + 1)
            self.r_PC = Address((hi << 8) | lo)
            cycles = 3
        
        elif opcode == 0x6C:  # JMP indirect
            addr_lo = self.memory.read(self.r_PC)
            self.r_PC = Address(self.r_PC + 1)
            addr_hi = self.memory.read(self.r_PC)
            self.r_PC = Address(self.r_PC + 1)
            addr = Address((addr_hi << 8) | addr_lo)
            
            # Handle page boundary bug
            lo = self.memory.read(addr)
            hi_addr = Address((addr & 0xFF00) | ((addr + 1) & 0x00FF))
            hi = self.memory.read(hi_addr)
            
            self.r_PC = Address((hi << 8) | lo)
            cycles = 5
        
        elif opcode == 0xA9:  # LDA immediate
            value = self.memory.read(self.r_PC)
            self.r_PC = Address(self.r_PC + 1)
            self.r_A = Byte(value)
            self.set_flags_ZN(self.r_A)
            cycles = 2
        
        elif opcode == 0xA5:  # LDA zero page
            addr = self.memory.read(self.r_PC)
            self.r_PC = Address(self.r_PC + 1)
            self.r_A = self.memory.read(addr)
            self.set_flags_ZN(self.r_A)
            cycles = 3
        
        elif opcode == 0xB5:  # LDA zero page, X
            addr = (self.memory.read(self.r_PC) + self.r_X) & 0xFF
            self.r_PC = Address(self.r_PC + 1)
            self.r_A = self.memory.read(addr)
            self.set_flags_ZN(self.r_A)
            cycles = 4
        
        elif opcode == 0xAD:  # LDA absolute
            lo = self.memory.read(self.r_PC)
            self.r_PC = Address(self.r_PC + 1)
            hi = self.memory.read(self.r_PC)
            self.r_PC = Address(self.r_PC + 1)
            addr = Address((hi << 8) | lo)
            self.r_A = self.memory.read(addr)
            self.set_flags_ZN(self.r_A)
            cycles = 4
        
        elif opcode == 0xBD:  # LDA absolute, X
            lo = self.memory.read(self.r_PC)
            self.r_PC = Address(self.r_PC + 1)
            hi = self.memory.read(self.r_PC)
            self.r_PC = Address(self.r_PC + 1)
            base_addr = Address((hi << 8) | lo)
            addr = Address(base_addr + self.r_X)
            
            # Check for page boundary crossing
            if (base_addr & 0xFF00) != (addr & 0xFF00):
                cycles = 5  # Extra cycle for page crossing
            else:
                cycles = 4
            
            self.r_A = self.memory.read(addr)
            self.set_flags_ZN(self.r_A)
            self.r_PC = Address(self.r_PC + 1)
        
        elif opcode == 0xA2:  # LDX immediate
            value = self.memory.read(self.r_PC)
            self.r_PC = Address(self.r_PC + 1)
            self.r_X = Byte(value)
            self.set_flags_ZN(self.r_X)
            cycles = 2
        
        elif opcode == 0xA0:  # LDY immediate
            value = self.memory.read(self.r_PC)
            self.r_PC = Address(self.r_PC + 1)
            self.r_Y = Byte(value)
            self.set_flags_ZN(self.r_Y)
            cycles = 2
        
        elif opcode == 0x85:  # STA zero page
            addr = self.memory.read(self.r_PC)
            self.r_PC = Address(self.r_PC + 1)
            self.memory.write(addr, self.r_A)
            cycles = 3
        
        elif opcode == 0x8D:  # STA absolute
            lo = self.memory.read(self.r_PC)
            self.r_PC = Address(self.r_PC + 1)
            hi = self.memory.read(self.r_PC)
            self.r_PC = Address(self.r_PC + 1)
            addr = Address((hi << 8) | lo)
            self.memory.write(addr, self.r_A)
            cycles = 4
        
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
            value = self.memory.read(self.r_PC)
            self.r_PC = Address(self.r_PC + 1)
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
            self.r_X = Byte(self.r_X - 1)
            self.set_flags_ZN(self.r_X)
            cycles = 2
        
        elif opcode == 0x88:  # DEY
            self.r_Y = Byte(self.r_Y - 1)
            self.set_flags_ZN(self.r_Y)
            cycles = 2
        
        elif opcode == 0x05:  # ORA zero page
            addr = self.memory.read(self.r_PC)
            self.r_PC = Address(self.r_PC + 1)
            value = self.memory.read(addr)
            self.r_A = Byte(self.r_A | value)
            self.set_flags_ZN(self.r_A)
            cycles = 3
        
        elif opcode == 0x25:  # AND zero page
            addr = self.memory.read(self.r_PC)
            self.r_PC = Address(self.r_PC + 1)
            value = self.memory.read(addr)
            self.r_A = Byte(self.r_A & value)
            self.set_flags_ZN(self.r_A)
            cycles = 3
        
        elif opcode == 0x45:  # EOR zero page
            addr = self.memory.read(self.r_PC)
            self.r_PC = Address(self.r_PC + 1)
            value = self.memory.read(addr)
            self.r_A = Byte(self.r_A ^ value)
            self.set_flags_ZN(self.r_A)
            cycles = 3
        
        else:
            # For unimplemented opcodes, just advance PC and return default cycles
            # In a real implementation, we'd have to determine instruction length
            # based on the opcode, but for now we'll just return a default
            print(f"Unimplemented opcode: {hex(opcode)} at PC: {hex(self.r_PC - 1)}")
            cycles = 2
        
        return cycles
    
    def push_stack(self, value: Byte):
        """Push a value onto the stack"""
        self.memory.write(0x0100 | self.r_SP, value)
        self.r_SP = Byte(self.r_SP - 1)
    
    def pull_stack(self) -> Byte:
        """Pull a value from the stack"""
        self.r_SP = Byte(self.r_SP + 1)
        return self.memory.read(0x0100 | self.r_SP)
    
    def set_flags_ZN(self, value: Byte):
        """Set Zero and Negative flags based on value"""
        self.f_Z = (value == 0)
        self.f_N = ((value & 0x80) != 0)
    
    def get_PC(self) -> Address:
        """Get program counter"""
        return self.r_PC
    
    def skip_DMA_cycles(self):
        """Skip cycles after DMA operation"""
        self.m_skipCycles += 513
        if self.m_cycles & 0x0002:
            self.m_skipCycles += 1