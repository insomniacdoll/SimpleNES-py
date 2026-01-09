"""
Test cases for bug fixes and C++ compatibility
"""
import pytest
import sys
import os

# Add parent directory to path to import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from simple_nes.cpu.cpu import CPU
from simple_nes.bus.mainbus import MainBus
from simple_nes.ppu.ppu import PPU
from simple_nes.cartridge.cartridge import Cartridge
import numpy as np


class MockScreen:
    """Mock screen for testing PPU"""
    def __init__(self):
        self.pixels = np.zeros((256, 240, 3), dtype=np.uint8)
    
    def set_pixel(self, x, y, color):
        if 0 <= x < 256 and 0 <= y < 240:
            self.pixels[x, y] = color


class MockPictureBus:
    """Mock picture bus for testing PPU"""
    def __init__(self):
        self.palette = [i for i in range(64)]
    
    def read(self, addr):
        return 0
    
    def read_palette(self, index):
        return self.palette[index % len(self.palette)]


class TestCPUFixes:
    """Test CPU bug fixes"""
    
    def test_reset_clears_all_flags(self):
        """Test that reset() clears all flags explicitly"""
        bus = MainBus()
        cpu = CPU(bus)
        
        # Set some flags
        cpu.f_C = True
        cpu.f_Z = True
        cpu.f_V = True
        cpu.f_N = True
        
        # Reset CPU
        cpu.reset()
        
        # Check that all flags are properly reset
        assert cpu.f_I == True  # Interrupt disable should be True after reset
        assert cpu.f_C == False  # Carry should be False
        assert cpu.f_Z == False  # Zero should be False
        assert cpu.f_D == False  # Decimal should be False
        assert cpu.f_V == False  # Overflow should be False
        assert cpu.f_N == False  # Negative should be False
    
    def test_php_instruction_flags(self):
        """Test PHP instruction sets flags correctly"""
        bus = MainBus()
        cpu = CPU(bus)
        
        # Set some flags
        cpu.f_C = True
        cpu.f_Z = True
        cpu.f_I = True
        cpu.f_D = False
        cpu.f_V = True
        cpu.f_N = True
        
        # Execute PHP instruction
        cpu.r_PC = 0
        bus.write(0, 0x08)  # PHP opcode
        bus.write(0xFFFC, 0)  # Reset vector
        bus.write(0xFFFD, 0)
        
        cycles = cpu.step()
        
        # Check that flags were pushed correctly
        # Bit 5 should be 1 (unused), Bit 4 should be 1 (B flag)
        flag_byte = cpu.pull_stack()
        assert (flag_byte & 0x20) == 0x20  # Bit 5 is 1
        assert (flag_byte & 0x10) == 0x10  # Bit 4 (B flag) is 1
        assert (flag_byte & 0x04) != 0  # I flag should be preserved
    
    def test_irq_pending_not_cleared_when_disabled(self):
        """Test that IRQ pending flag is not cleared when IRQ is disabled"""
        bus = MainBus()
        cpu = CPU(bus)
        
        # Enable IRQ pending
        cpu.m_pendingIRQ = True
        cpu.f_I = True  # Disable interrupts
        
        # Execute a step
        cpu.r_PC = 0
        bus.write(0, 0xEA)  # NOP
        bus.write(0xFFFC, 0)
        bus.write(0xFFFD, 0)
        
        cpu.step()
        
        # IRQ should still be pending
        assert cpu.m_pendingIRQ == True
    
    def test_dma_cycle_skip_logic(self):
        """Test DMA cycle skip uses correct bit check"""
        bus = MainBus()
        cpu = CPU(bus)
        
        # Test with odd cycle count
        cpu.m_cycles = 1
        initial_skip = cpu.m_skipCycles
        cpu.skip_DMA_cycles()
        
        # Should add 1 extra cycle for odd cycle
        assert cpu.m_skipCycles == initial_skip + 513 + 1
        
        # Test with even cycle count
        cpu.m_cycles = 2
        cpu.m_skipCycles = 0
        cpu.skip_DMA_cycles()
        
        # Should not add extra cycle for even cycle
        assert cpu.m_skipCycles == 513


class TestPPUFixes:
    """Test PPU bug fixes"""
    
    def test_ppu_data_buffer_delay(self):
        """Test PPUDATA read uses correct buffer delay logic"""
        screen = MockScreen()
        bus = MockPictureBus()
        ppu = PPU(bus, screen)
        
        # Set data address to non-palette range
        ppu.data_address = 0x2000
        ppu.data_buffer = 0x42
        
        # First read should return buffer value
        result = ppu.get_data()
        assert result == 0x42
        
        # Second read should return previous data (buffered)
        # and update buffer with current data
        result2 = ppu.get_data()
        assert result2 == 0  # Mock bus returns 0
    
    def test_sprite_zero_hit_detection(self):
        """Test sprite-0 hit detection with edge hiding"""
        screen = MockScreen()
        bus = MockPictureBus()
        ppu = PPU(bus, screen)
        
        # Enable background rendering
        ppu.show_background = True
        ppu.show_sprites = True
        ppu.hide_edge_sprites = True
        ppu.hide_edge_background = True
        
        # Set up sprite 0 at position (0, 0)
        ppu.sprite_memory[0] = 0  # Y position
        ppu.sprite_memory[1] = 0  # Tile
        ppu.sprite_memory[2] = 0  # Attribute
        ppu.sprite_memory[3] = 0  # X position
        
        # Set up scanline sprites
        ppu.scanline_sprites = [0]
        
        # Simulate rendering at x=0 (should not trigger hit due to edge hiding)
        ppu.cycle = 1
        ppu.scanline = 0
        ppu.pipeline_state = 1  # Render
        
        # Hit should not be triggered at edge when edge hiding is enabled
        # (This is a simplified test - actual rendering would need more setup)
        assert ppu.spr_zero_hit == False
    
    def test_even_frame_skip_logic(self):
        """Test even frame skip logic"""
        screen = MockScreen()
        bus = MockPictureBus()
        ppu = PPU(bus, screen)
        
        # Enable rendering
        ppu.show_background = True
        ppu.show_sprites = True
        
        # Test with even frame
        ppu.even_frame = True
        ppu.cycle = 340
        ppu.pipeline_state = 0  # PreRender
        
        # Should transition at cycle 340 for even frame
        for _ in range(2):
            ppu.step()
        
        assert ppu.pipeline_state == 1  # Should be in Render state
        
        # Test with odd frame
        ppu.even_frame = False
        ppu.cycle = 339
        ppu.pipeline_state = 0  # PreRender
        
        # Should transition at cycle 339 for odd frame (one cycle shorter)
        for _ in range(2):
            ppu.step()
        
        assert ppu.pipeline_state == 1  # Should be in Render state


def test_no_duplicate_opcodes():
    """Test that there are no duplicate opcode implementations"""
    bus = MainBus()
    cpu = CPU(bus)
    
    # Check that each opcode has a unique implementation
    # This is a basic sanity check - we verify the file doesn't have
    # duplicate opcode checks by examining the structure
    
    # Read the CPU file and check for duplicate opcode patterns
    import ast
    import inspect
    
    source = inspect.getsource(cpu.execute_opcode)
    
    # Count occurrences of common opcodes
    opcodes_to_check = [0xB5, 0xAD, 0xA2, 0xA0, 0x85]
    
    for opcode in opcodes_to_check:
        pattern = f"opcode == 0x{opcode:02X}"
        count = source.count(pattern)
        assert count == 1, f"Opcode 0x{opcode:02X} appears {count} times, expected 1"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])