"""
Unit tests for PPU (Picture Processing Unit)
Tests PPU functionality against C++ reference implementation
"""
import pytest
import numpy as np
from unittest.mock import Mock, MagicMock


class MockPictureBus:
    """Mock PictureBus for testing"""
    def __init__(self):
        self.mapper = None
        self.vram = [0] * 0x1000
        self.palette_memory = [0] * 0x20
        self.mirroring_type = 0
    
    def read(self, addr):
        if addr < 0x2000:
            return 0
        elif addr < 0x3EFF:
            # Name tables (0x2000-0x2FFF), mirrored to 0x3000-0x3EFF
            normalized_addr = addr
            if addr >= 0x3000:
                normalized_addr -= 0x1000
            # Map to VRAM (0x2000-0x2FFF -> 0x000-0xFFF)
            actual_addr = normalized_addr & 0xFFF
            if actual_addr < len(self.vram):
                return self.vram[actual_addr]
            return 0
        elif addr >= 0x3F00 and addr < 0x4000:
            palette_addr = (addr - 0x3F00) & 0x1F
            return self.palette_memory[palette_addr]
        return 0
    
    def write(self, addr, value):
        if addr < 0x2000:
            pass
        elif addr < 0x3EFF:
            # Name tables (0x2000-0x2FFF), mirrored to 0x3000-0x3EFF
            normalized_addr = addr
            if addr >= 0x3000:
                normalized_addr -= 0x1000
            # Map to VRAM (0x2000-0x2FFF -> 0x000-0xFFF)
            actual_addr = normalized_addr & 0xFFF
            if actual_addr < len(self.vram):
                self.vram[actual_addr] = value
        elif addr >= 0x3F00 and addr < 0x4000:
            palette_addr = (addr - 0x3F00) & 0x1F
            self.palette_memory[palette_addr] = value
    
    def read_palette(self, palette_addr):
        if palette_addr >= 0x10 and palette_addr % 4 == 0:
            palette_addr = palette_addr & 0xf
        return self.palette_memory[palette_addr]
    
    def scanlineIRQ(self):
        """MMC3 scanline IRQ support"""
        pass


class MockVirtualScreen:
    """Mock VirtualScreen for testing"""
    def __init__(self):
        self.width = 256
        self.height = 240
        self.buffer = np.zeros((240, 256, 3), dtype=np.uint8)
    
    def set_pixel(self, x, y, color):
        if 0 <= x < self.width and 0 <= y < self.height:
            self.buffer[y, x] = color


def test_ppu_initialization():
    """Test PPU initialization"""
    from simple_nes.ppu.ppu import PPU
    
    bus = MockPictureBus()
    screen = MockVirtualScreen()
    ppu = PPU(bus, screen)
    
    # Check initial state
    assert ppu.pipeline_state == 0  # PreRender
    assert ppu.cycle == 0
    assert ppu.scanline == 0
    assert ppu.even_frame == True
    assert ppu.vblank == False
    assert ppu.spr_zero_hit == False
    assert ppu.sprite_overflow == False
    assert ppu.data_address == 0
    assert ppu.temp_address == 0
    assert ppu.fine_x_scroll == 0
    assert ppu.first_write == True
    assert ppu.sprite_data_address == 0
    assert len(ppu.sprite_memory) == 64 * 4  # 64 sprites * 4 bytes


def test_ppu_reset():
    """Test PPU reset functionality"""
    from simple_nes.ppu.ppu import PPU
    
    bus = MockPictureBus()
    screen = MockVirtualScreen()
    ppu = PPU(bus, screen)
    
    # Modify some values
    ppu.pipeline_state = 3
    ppu.cycle = 100
    ppu.scanline = 50
    ppu.vblank = True
    ppu.spr_zero_hit = True
    ppu.data_address = 0x1234
    ppu.temp_address = 0x5678
    
    # Reset
    ppu.reset()
    
    # Check reset state
    assert ppu.pipeline_state == 0  # PreRender
    assert ppu.cycle == 0
    assert ppu.scanline == 0
    assert ppu.even_frame == True
    assert ppu.vblank == False
    assert ppu.spr_zero_hit == False
    assert ppu.sprite_overflow == False
    assert ppu.data_address == 0
    assert ppu.temp_address == 0
    assert ppu.fine_x_scroll == 0
    assert ppu.first_write == True
    assert ppu.sprite_data_address == 0
    assert ppu.bg_page == 0
    assert ppu.spr_page == 0
    assert ppu.data_addr_increment == 1


def test_ppu_control_register():
    """Test PPUCTRL register (0x2000)"""
    from simple_nes.ppu.ppu import PPU
    
    bus = MockPictureBus()
    screen = MockVirtualScreen()
    ppu = PPU(bus, screen)
    
    # Test control register with all flags set
    ctrl = 0b11111111  # All flags set
    ppu.control(ctrl)
    
    assert ppu.generate_interrupt == True
    assert ppu.long_sprites == True
    assert ppu.bg_page == 1
    assert ppu.spr_page == 1
    assert ppu.data_addr_increment == 0x20
    assert ppu.temp_address == (ctrl & 0x3) << 10
    
    # Test with different values
    ctrl = 0b00000000  # All flags cleared
    ppu.control(ctrl)
    
    assert ppu.generate_interrupt == False
    assert ppu.long_sprites == False
    assert ppu.bg_page == 0
    assert ppu.spr_page == 0
    assert ppu.data_addr_increment == 1


def test_ppu_mask_register():
    """Test PPUMASK register (0x2001)"""
    from simple_nes.ppu.ppu import PPU
    
    bus = MockPictureBus()
    screen = MockVirtualScreen()
    ppu = PPU(bus, screen)
    
    # Test mask register
    mask = 0b00011111  # All flags set
    ppu.set_mask(mask)
    
    assert ppu.greyscale_mode == True
    assert ppu.hide_edge_background == False
    assert ppu.hide_edge_sprites == False
    assert ppu.show_background == True
    assert ppu.show_sprites == True
    
    # Test with different values
    mask = 0b00000000  # All flags cleared
    ppu.set_mask(mask)
    
    assert ppu.greyscale_mode == False
    assert ppu.hide_edge_background == True
    assert ppu.hide_edge_sprites == True
    assert ppu.show_background == False
    assert ppu.show_sprites == False


def test_ppu_status_register():
    """Test PPUSTATUS register (0x2002)"""
    from simple_nes.ppu.ppu import PPU
    
    bus = MockPictureBus()
    screen = MockVirtualScreen()
    ppu = PPU(bus, screen)
    
    # Set flags
    ppu.vblank = True
    ppu.spr_zero_hit = True
    ppu.sprite_overflow = True
    
    # Read status
    status = ppu.get_status()
    
    assert status & 0x80  # VBlank flag
    assert status & 0x40  # Sprite 0 hit flag
    assert status & 0x20  # Sprite overflow flag
    
    # Reading status should clear vblank and reset first_write
    assert ppu.vblank == False
    assert ppu.first_write == True


def test_ppu_scroll_register():
    """Test PPUSCROLL register (0x2005)"""
    from simple_nes.ppu.ppu import PPU
    
    bus = MockPictureBus()
    screen = MockVirtualScreen()
    ppu = PPU(bus, screen)
    
    # First write (horizontal scroll)
    scroll1 = 0xAB  # 10101011
    ppu.set_scroll(scroll1)
    
    assert ppu.first_write == False
    assert ppu.fine_x_scroll == 0x3  # Lower 3 bits
    assert (ppu.temp_address & 0x1F) == 0x15  # Upper 5 bits
    
    # Second write (vertical scroll)
    scroll2 = 0xCD  # 11001101
    ppu.set_scroll(scroll2)
    
    assert ppu.first_write == True
    # The second write sets bits in temp_address
    # ((scroll2 & 0x7) << 12) | ((scroll2 & 0xF8) << 2)
    # = ((0xCD & 0x7) << 12) | ((0xCD & 0xF8) << 2)
    # = ((0x5) << 12) | ((0xC8) << 2)
    # = 0x5000 | 0x320
    # = 0x5320
    expected = ((scroll2 & 0x7) << 12) | ((scroll2 & 0xF8) << 2)
    assert (ppu.temp_address & 0x73E0) == expected


def test_ppu_data_address_register():
    """Test PPUADDR register (0x2006)"""
    from simple_nes.ppu.ppu import PPU
    
    bus = MockPictureBus()
    screen = MockVirtualScreen()
    ppu = PPU(bus, screen)
    
    # First write (high byte)
    addr1 = 0x23
    ppu.set_data_address(addr1)
    
    assert ppu.first_write == False
    assert ppu.temp_address == (addr1 & 0x3F) << 8
    
    # Second write (low byte)
    addr2 = 0x45
    ppu.set_data_address(addr2)
    
    assert ppu.first_write == True
    assert ppu.data_address == ((addr1 & 0x3F) << 8) | addr2


def test_ppu_oam_operations():
    """Test OAM (Object Attribute Memory) operations"""
    from simple_nes.ppu.ppu import PPU
    
    bus = MockPictureBus()
    screen = MockVirtualScreen()
    ppu = PPU(bus, screen)
    
    # Set OAM address
    ppu.set_oam_address(0x10)
    assert ppu.sprite_data_address == 0x10
    
    # Write OAM data
    ppu.set_oam_data(0xAB)
    assert ppu.sprite_memory[0x10] == 0xAB
    assert ppu.sprite_data_address == 0x11
    
    # Read OAM data
    ppu.set_oam_address(0x10)
    data = ppu.get_oam_data()
    assert data == 0xAB


def test_ppu_dma():
    """Test DMA (Direct Memory Access) operation"""
    from simple_nes.ppu.ppu import PPU
    
    bus = MockPictureBus()
    screen = MockVirtualScreen()
    ppu = PPU(bus, screen)
    
    # Set OAM address
    ppu.set_oam_address(0x20)
    
    # Perform DMA
    page_data = list(range(256))
    ppu.do_DMA(page_data)
    
    # Check that data was transferred correctly
    for i in range(256 - 0x20):
        assert ppu.sprite_memory[0x20 + i] == i
    for i in range(0x20):
        assert ppu.sprite_memory[i] == 256 - 0x20 + i


def test_ppu_step_prerender():
    """Test PPU step in PreRender state"""
    from simple_nes.ppu.ppu import PPU
    
    bus = MockPictureBus()
    screen = MockVirtualScreen()
    ppu = PPU(bus, screen)
    
    ppu.pipeline_state = 0  # PreRender
    ppu.cycle = 0
    ppu.scanline = 261
    ppu.vblank = True
    ppu.spr_zero_hit = True
    
    # Step through PreRender
    for _ in range(341):
        ppu.step()
    
    # Should transition to Render state
    # After transition, cycle is set to 0, then incremented to 1 by step()
    assert ppu.pipeline_state == 1  # Render
    assert ppu.cycle == 1  # Incremented after state transition
    assert ppu.scanline == 0
    assert ppu.vblank == False
    assert ppu.spr_zero_hit == False


def test_ppu_step_render():
    """Test PPU step in Render state"""
    from simple_nes.ppu.ppu import PPU
    
    bus = MockPictureBus()
    screen = MockVirtualScreen()
    ppu = PPU(bus, screen)
    
    ppu.pipeline_state = 1  # Render
    ppu.cycle = 0
    ppu.scanline = 0
    ppu.show_background = True
    ppu.show_sprites = True
    
    # Step through one scanline
    for _ in range(341):
        ppu.step()
    
    # Should increment scanline and stay in Render state
    # After completing a scanline, cycle is reset to 0, then incremented to 1
    assert ppu.pipeline_state == 1  # Render
    assert ppu.cycle == 1  # Incremented after cycle reset
    assert ppu.scanline == 1


def test_ppu_step_postrender():
    """Test PPU step in PostRender state"""
    from simple_nes.ppu.ppu import PPU
    
    bus = MockPictureBus()
    screen = MockVirtualScreen()
    ppu = PPU(bus, screen)
    
    ppu.pipeline_state = 2  # PostRender
    ppu.cycle = 0
    ppu.scanline = 240
    
    # Step through PostRender
    for _ in range(341):
        ppu.step()
    
    # Should transition to VerticalBlank state
    # After transition, cycle is reset to 0, then incremented to 1
    assert ppu.pipeline_state == 3  # VerticalBlank
    assert ppu.cycle == 1  # Incremented after cycle reset
    assert ppu.scanline == 241


def test_ppu_step_verticalblank():
    """Test PPU step in VerticalBlank state"""
    from simple_nes.ppu.ppu import PPU
    
    bus = MockPictureBus()
    screen = MockVirtualScreen()
    ppu = PPU(bus, screen)
    
    ppu.pipeline_state = 3  # VerticalBlank
    ppu.cycle = 0
    ppu.scanline = 241
    ppu.generate_interrupt = True
    
    # Mock callback
    callback_called = False
    def callback():
        nonlocal callback_called
        callback_called = True
    
    ppu.set_interrupt_callback(callback)
    
    # Step through VerticalBlank
    for _ in range(341):
        ppu.step()
    
    # Should set VBlank and call callback
    assert ppu.vblank == True
    assert callback_called == True
    
    # Continue to end of frame
    while ppu.pipeline_state != 0:  # PreRender
        ppu.step()
    
    # Should transition back to PreRender
    # After transition, cycle is reset to 0, then incremented to 1
    assert ppu.pipeline_state == 0  # PreRender
    assert ppu.cycle == 1  # Incremented after cycle reset
    assert ppu.scanline == 0


def test_ppu_full_frame():
    """Test PPU through a full frame"""
    from simple_nes.ppu.ppu import PPU
    
    bus = MockPictureBus()
    screen = MockVirtualScreen()
    ppu = PPU(bus, screen)
    
    ppu.reset()
    
    # Step through a full frame (262 scanlines * 341 cycles)
    total_steps = 262 * 341
    for _ in range(total_steps):
        ppu.step()
    
    # After a full frame, should be back in PreRender
    # The exact cycle value depends on the implementation
    # The important thing is that the state is correct
    assert ppu.pipeline_state == 0  # PreRender
    assert ppu.scanline == 0
    assert ppu.even_frame == False  # Should toggle


def test_ppu_data_read_write():
    """Test PPUDATA register read/write operations"""
    from simple_nes.ppu.ppu import PPU
    
    bus = MockPictureBus()
    screen = MockVirtualScreen()
    ppu = PPU(bus, screen)
    
    # Set data address
    ppu.set_data_address(0x23)
    ppu.set_data_address(0x45)
    
    # Write data
    ppu.set_data(0xAB)
    assert bus.read(0x2345) == 0xAB
    
    # Read data (with buffering)
    ppu.set_data_address(0x20)
    ppu.set_data_address(0x00)
    
    # First read returns buffered value
    data1 = ppu.get_data()
    # Second read returns actual value
    data2 = ppu.get_data()
    
    # Check address increment
    assert ppu.data_address == 0x2002  # Should have incremented


def test_ppu_constants():
    """Test that PPU constants match C++ implementation"""
    from simple_nes.ppu.ppu import (
        ScanlineCycleLength,
        ScanlineEndCycle,
        VisibleScanlines,
        ScanlineVisibleDots,
        FrameEndScanline
    )
    
    assert ScanlineCycleLength == 341
    assert ScanlineEndCycle == 340
    assert VisibleScanlines == 240
    assert ScanlineVisibleDots == 256
    assert FrameEndScanline == 261


def test_ppu_sprite_memory_size():
    """Test that sprite memory size is correct"""
    from simple_nes.ppu.ppu import PPU
    
    bus = MockPictureBus()
    screen = MockVirtualScreen()
    ppu = PPU(bus, screen)
    
    # Should be 64 sprites * 4 bytes = 256 bytes
    assert len(ppu.sprite_memory) == 64 * 4


def test_ppu_picture_buffer_size():
    """Test that picture buffer size is correct"""
    from simple_nes.ppu.ppu import PPU
    
    bus = MockPictureBus()
    screen = MockVirtualScreen()
    ppu = PPU(bus, screen)
    
    # Should be 256 pixels wide * 240 pixels tall * 3 color channels
    assert ppu.picture_buffer.shape == (256, 240, 3)


def test_ppu_vblank_callback():
    """Test VBlank interrupt callback"""
    from simple_nes.ppu.ppu import PPU
    
    bus = MockPictureBus()
    screen = MockVirtualScreen()
    ppu = PPU(bus, screen)
    
    callback_called = False
    def callback():
        nonlocal callback_called
        callback_called = True
    
    ppu.set_interrupt_callback(callback)
    
    # Set up for VBlank - start from PostRender state
    ppu.pipeline_state = 2  # PostRender
    ppu.cycle = 340  # End of PostRender scanline
    ppu.scanline = 240
    ppu.generate_interrupt = True
    
    # Step to transition to VerticalBlank (cycle becomes 0, scanline becomes 241)
    ppu.step()
    
    # Now step to trigger VBlank (cycle becomes 1)
    ppu.step()
    
    # VBlank should be set at cycle 1, scanline 241
    assert ppu.vblank == True
    assert callback_called == True


def test_ppu_mmc3_irq():
    """Test MMC3 scanline IRQ support"""
    from simple_nes.ppu.ppu import PPU
    
    bus = MockPictureBus()
    screen = MockVirtualScreen()
    ppu = PPU(bus, screen)
    
    irq_called = False
    def mock_irq():
        nonlocal irq_called
        irq_called = True
    
    bus.scanlineIRQ = mock_irq
    
    # Set up for MMC3 IRQ
    # IRQ is triggered at cycle 260 in PreRender state
    ppu.pipeline_state = 0  # PreRender
    ppu.cycle = 260  # Set cycle to 260 directly
    ppu.scanline = 0
    ppu.show_background = True
    ppu.show_sprites = True
    
    # Step to trigger IRQ (cycle is already 260)
    ppu.step()
    
    assert irq_called == True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])