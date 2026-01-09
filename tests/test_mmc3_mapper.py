"""
Test MMC3 Mapper functionality
Tests for MMC3 Mapper including scanline IRQ logic
"""
import pytest
from simple_nes.cartridge.cartridge import Cartridge
from simple_nes.cartridge.mapper import Mapper
from unittest.mock import MagicMock

class TestMMC3Mapper:
    def test_mmc3_scanline_irq_reload(self):
        """Test MMC3 scanline IRQ reload logic"""
        # Create a mock cartridge
        cartridge = Cartridge()
        cartridge.prg_rom = [0] * (32 * 1024)  # 32KB PRG ROM
        cartridge.chr_rom = [0] * (8 * 1024)   # 8KB CHR ROM
        
        # Create mock interrupt callback
        interrupt_cb = MagicMock()
        
        # Create MMC3 mapper
        mapper = Mapper.create_mapper(
            Mapper.Type.MMC3,
            cartridge,
            interrupt_cb,
            MagicMock()
        )
        
        # Set up IRQ parameters
        mapper.irq_latch = 10
        mapper.irq_enabled = True
        
        # Test reload on first call
        mapper.irq_reload = True
        mapper.scanline_irq()
        
        # Counter should be reloaded
        assert mapper.irq_counter == 10
        # Reload flag should be cleared
        assert mapper.irq_reload == False
        # IRQ should not be triggered (counter was reloaded, not decremented)
        assert interrupt_cb.call_count == 0
    
    def test_mmc3_scanline_irq_decrement(self):
        """Test MMC3 scanline IRQ decrement logic"""
        # Create a mock cartridge
        cartridge = Cartridge()
        cartridge.prg_rom = [0] * (32 * 1024)
        cartridge.chr_rom = [0] * (8 * 1024)
        
        # Create mock interrupt callback
        interrupt_cb = MagicMock()
        
        # Create MMC3 mapper
        mapper = Mapper.create_mapper(
            Mapper.Type.MMC3,
            cartridge,
            interrupt_cb,
            MagicMock()
        )
        
        # Set up IRQ parameters
        mapper.irq_latch = 10
        mapper.irq_counter = 5
        mapper.irq_enabled = True
        mapper.irq_reload = False
        
        # Call scanline_irq
        mapper.scanline_irq()
        
        # Counter should be decremented
        assert mapper.irq_counter == 4
        # IRQ should not be triggered (counter != 0 after decrement)
        assert interrupt_cb.call_count == 0
    
    def test_mmc3_scanline_irq_trigger(self):
        """Test MMC3 scanline IRQ trigger logic"""
        # Create a mock cartridge
        cartridge = Cartridge()
        cartridge.prg_rom = [0] * (32 * 1024)
        cartridge.chr_rom = [0] * (8 * 1024)
        
        # Create mock interrupt callback
        interrupt_cb = MagicMock()
        
        # Create MMC3 mapper
        mapper = Mapper.create_mapper(
            Mapper.Type.MMC3,
            cartridge,
            interrupt_cb,
            MagicMock()
        )
        
        # Set up IRQ parameters
        mapper.irq_latch = 10
        mapper.irq_counter = 1
        mapper.irq_enabled = True
        mapper.irq_reload = False
        
        # Call scanline_irq
        mapper.scanline_irq()
        
        # Counter should be 0 after decrement
        assert mapper.irq_counter == 0
        # IRQ should be triggered (counter reached 0 after decrement)
        assert interrupt_cb.call_count == 1
    
    def test_mmc3_scanline_irq_no_trigger_when_disabled(self):
        """Test MMC3 scanline IRQ does not trigger when disabled"""
        # Create a mock cartridge
        cartridge = Cartridge()
        cartridge.prg_rom = [0] * (32 * 1024)
        cartridge.chr_rom = [0] * (8 * 1024)
        
        # Create mock interrupt callback
        interrupt_cb = MagicMock()
        
        # Create MMC3 mapper
        mapper = Mapper.create_mapper(
            Mapper.Type.MMC3,
            cartridge,
            interrupt_cb,
            MagicMock()
        )
        
        # Set up IRQ parameters but disable IRQ
        mapper.irq_latch = 10
        mapper.irq_counter = 1
        mapper.irq_enabled = False
        mapper.irq_reload = False
        
        # Call scanline_irq
        mapper.scanline_irq()
        
        # Counter should be 0 after decrement
        assert mapper.irq_counter == 0
        # IRQ should NOT be triggered (irq_enabled is False)
        assert interrupt_cb.call_count == 0
    
    def test_mmc3_scanline_irq_zero_counter_reload(self):
        """Test MMC3 scanline IRQ reload when counter is zero"""
        # Create a mock cartridge
        cartridge = Cartridge()
        cartridge.prg_rom = [0] * (32 * 1024)
        cartridge.chr_rom = [0] * (8 * 1024)
        
        # Create mock interrupt callback
        interrupt_cb = MagicMock()
        
        # Create MMC3 mapper
        mapper = Mapper.create_mapper(
            Mapper.Type.MMC3,
            cartridge,
            interrupt_cb,
            MagicMock()
        )
        
        # Set up IRQ parameters with counter = 0
        mapper.irq_latch = 10
        mapper.irq_counter = 0
        mapper.irq_enabled = True
        mapper.irq_reload = False
        
        # Call scanline_irq
        mapper.scanline_irq()
        
        # Counter should be reloaded
        assert mapper.irq_counter == 10
        # IRQ should not be triggered (counter was reloaded, not decremented)
        assert interrupt_cb.call_count == 0
    
    def test_mmc3_scanline_irq_multiple_calls(self):
        """Test MMC3 scanline IRQ with multiple calls"""
        # Create a mock cartridge
        cartridge = Cartridge()
        cartridge.prg_rom = [0] * (32 * 1024)
        cartridge.chr_rom = [0] * (8 * 1024)
        
        # Create mock interrupt callback
        interrupt_cb = MagicMock()
        
        # Create MMC3 mapper
        mapper = Mapper.create_mapper(
            Mapper.Type.MMC3,
            cartridge,
            interrupt_cb,
            MagicMock()
        )
        
        # Set up IRQ parameters
        mapper.irq_latch = 3
        mapper.irq_counter = 3
        mapper.irq_enabled = True
        mapper.irq_reload = False
        
        # Call scanline_irq 3 times
        mapper.scanline_irq()
        assert mapper.irq_counter == 2
        assert interrupt_cb.call_count == 0
        
        mapper.scanline_irq()
        assert mapper.irq_counter == 1
        assert interrupt_cb.call_count == 0
        
        mapper.scanline_irq()
        assert mapper.irq_counter == 0
        assert interrupt_cb.call_count == 1  # IRQ triggered on 3rd call
    
    def test_mmc3_scanline_irq_reload_priority(self):
        """Test MMC3 scanline IRQ reload has priority over decrement"""
        # Create a mock cartridge
        cartridge = Cartridge()
        cartridge.prg_rom = [0] * (32 * 1024)
        cartridge.chr_rom = [0] * (8 * 1024)
        
        # Create mock interrupt callback
        interrupt_cb = MagicMock()
        
        # Create MMC3 mapper
        mapper = Mapper.create_mapper(
            Mapper.Type.MMC3,
            cartridge,
            interrupt_cb,
            MagicMock()
        )
        
        # Set up IRQ parameters with both reload and counter > 0
        mapper.irq_latch = 10
        mapper.irq_counter = 5
        mapper.irq_enabled = True
        mapper.irq_reload = True
        
        # Call scanline_irq
        mapper.scanline_irq()
        
        # Counter should be reloaded (reload has priority)
        assert mapper.irq_counter == 10
        # Reload flag should be cleared
        assert mapper.irq_reload == False
        # IRQ should not be triggered
        assert interrupt_cb.call_count == 0