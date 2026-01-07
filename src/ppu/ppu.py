"""
Picture Processing Unit (PPU) for SimpleNES-py
Implements the NES PPU (RP2C02)
"""
import numpy as np
from typing import Callable, Optional

# PPU Constants
ScanlineCycleLength = 341
ScanlineEndCycle = 340
VisibleScanlines = 240
ScanlineVisibleDots = 256
FrameEndScanline = 261
AttributeOffset = 0x3C0

# Palette colors (simplified)
PALETTE_COLORS = [
    0x696969, 0x002492, 0x0000db, 0x6d49dd,
    0xab00a2, 0xb70021, 0xb30000, 0x7b0800,
    0x411c00, 0x002d00, 0x003b00, 0x003b00,
    0x002e6e, 0x000000, 0x000000, 0x000000,
    # ... more colors would be defined here
]

class PPU:
    def __init__(self, picture_bus, screen):
        self.bus = picture_bus
        self.screen = screen
        
        # Timing and state
        self.pipeline_state = "PreRender"  # PreRender, Render, PostRender, VerticalBlank
        self.cycle = 0
        self.scanline = 0
        self.even_frame = False
        
        # Control flags
        self.vblank = False
        self.spr_zero_hit = False
        self.sprite_overflow = False
        
        # Registers
        self.data_address = 0
        self.temp_address = 0
        self.fine_x_scroll = 0
        self.first_write = True
        self.data_buffer = 0
        
        self.sprite_data_address = 0
        
        # Setup flags
        self.long_sprites = False
        self.generate_interrupt = False
        self.greyscale_mode = False
        self.show_sprites = True
        self.show_background = True
        self.hide_edge_sprites = False
        self.hide_edge_background = False
        self.bg_page = "Low"  # Low, High
        self.spr_page = "Low"  # Low, High
        self.data_addr_increment = 1
        
        # Internal buffers
        self.sprite_memory = [0] * 256
        self.scanline_sprites = [0] * 16
        self.picture_buffer = np.zeros((240, 256, 3), dtype=np.uint8)
        
        # Callback for VBlank interrupt
        self.vblank_callback: Optional[Callable] = None
        
        self.reset()
    
    def reset(self):
        """Reset PPU to initial state"""
        self.cycle = 0
        self.scanline = 0
        self.even_frame = False
        self.vblank = False
        self.spr_zero_hit = False
        self.sprite_overflow = False
        self.first_write = True
        
        # Reset registers
        self.data_address = 0
        self.temp_address = 0
        self.fine_x_scroll = 0
        self.data_buffer = 0
        self.sprite_data_address = 0
        
        # Reset control flags
        self.long_sprites = False
        self.generate_interrupt = False
        self.greyscale_mode = False
        self.show_sprites = True
        self.show_background = True
        self.hide_edge_sprites = False
        self.hide_edge_background = False
        self.bg_page = "Low"
        self.spr_page = "Low"
        self.data_addr_increment = 1
        
        # Initialize pipeline state
        self.pipeline_state = "PreRender"
    
    def step(self):
        """Execute a single PPU step"""
        # Update timing
        self.cycle += 1
        
        if self.cycle > ScanlineCycleLength:
            self.cycle = 0
            self.scanline += 1
            
            if self.scanline > FrameEndScanline:
                self.scanline = -1
                self.even_frame = not self.even_frame
                self.pipeline_state = "PreRender"
            elif self.scanline == -1:
                self.pipeline_state = "PreRender"
                self.vblank = False
                self.spr_zero_hit = False
                self.sprite_overflow = False
            elif self.scanline < VisibleScanlines:
                self.pipeline_state = "Render"
            elif self.scanline == VisibleScanlines:
                self.pipeline_state = "PostRender"
            elif self.scanline == 241:
                self.pipeline_state = "VerticalBlank"
                self.vblank = True
                if self.generate_interrupt and self.vblank_callback:
                    self.vblank_callback()
        
        # Render current pixel if in visible scanline and render is enabled
        if (self.scanline >= 0 and 
            self.scanline < VisibleScanlines and 
            self.cycle < ScanlineVisibleDots and 
            self.show_background):
            
            # Calculate pixel position
            pixel_x = self.cycle
            pixel_y = self.scanline
            
            # Simplified background rendering
            # In a full implementation, we would:
            # 1. Determine which tile needs to be rendered
            # 2. Fetch tile pattern and attributes
            # 3. Apply palette lookup
            # 4. Handle scrolling and mirroring
            
            # For now, create a simple pattern based on tile coordinates
            tile_x = pixel_x // 8
            tile_y = pixel_y // 8
            
            # Create a checkerboard pattern of tiles
            if (tile_x + tile_y) % 2 == 0:
                # Even tiles - light blue
                color = [135, 206, 235]  # Light blue
            else:
                # Odd tiles - dark blue  
                color = [0, 0, 139]  # Dark blue
            
            # Apply greyscale if enabled
            if self.greyscale_mode:
                # Convert to greyscale by averaging the color
                grey = int(0.299 * color[0] + 0.587 * color[1] + 0.114 * color[2])
                color = [grey, grey, grey]
            
            self.picture_buffer[pixel_y, pixel_x] = color
    
    def set_interrupt_callback(self, callback: Callable):
        """Set callback for VBlank interrupt"""
        self.vblank_callback = callback
    
    def do_DMA(self, page_ptr):
        """Perform DMA operation"""
        # DMA transfers 256 bytes from CPU page to PPU OAM
        pass
    
    # PPU register access methods
    def control(self, ctrl):
        """Write to PPUCTRL register (0x2000)"""
        self.temp_address = (self.temp_address & 0xF3FF) | ((ctrl & 0x03) << 10)
        self.bg_page = "High" if (ctrl & 0x10) else "Low"
        self.spr_page = "High" if (ctrl & 0x08) else "Low"
        self.long_sprites = bool(ctrl & 0x20)
        self.generate_interrupt = bool(ctrl & 0x80)
        
        # Update address increment
        self.data_addr_increment = 32 if (ctrl & 0x04) else 1
    
    def set_mask(self, mask):
        """Write to PPUMASK register (0x2001)"""
        self.greyscale_mode = bool(mask & 0x01)
        self.show_background = bool(mask & 0x08)
        self.show_sprites = bool(mask & 0x10)
        self.hide_edge_background = bool(mask & 0x02)
        self.hide_edge_sprites = bool(mask & 0x04)
    
    def set_oam_address(self, addr):
        """Write to OAMADDR register (0x2003)"""
        self.sprite_data_address = addr
    
    def set_data_address(self, addr):
        """Write to PPUADDR register (0x2006)"""
        if self.first_write:
            self.temp_address = (self.temp_address & 0x80FF) | ((addr & 0x3F) << 8)
            self.first_write = False
        else:
            self.temp_address = (self.temp_address & 0xFF00) | addr
            self.data_address = self.temp_address
            self.first_write = True
    
    def set_scroll(self, scroll):
        """Write to PPUSCROL register (0x2005)"""
        if self.first_write:
            self.temp_address = (self.temp_address & 0xFFE0) | (scroll >> 3)
            self.fine_x_scroll = scroll & 0x07
            self.first_write = False
        else:
            self.temp_address = (self.temp_address & 0x8FFF) | ((scroll & 0x07) << 12)
            self.temp_address = (self.temp_address & 0xFC1F) | ((scroll & 0xF8) << 2)
            self.first_write = True
    
    def set_data(self, data):
        """Write to PPUDATA register (0x2007)"""
        # Write to PPU memory at current address
        self.bus.write(self.data_address, data)
        
        # Increment address based on control register
        self.data_address += self.data_addr_increment
        self.data_address &= 0xFFFF
    
    def get_status(self):
        """Read from PPUSTATUS register (0x2002)"""
        result = 0
        if self.vblank:
            result |= 0x80
        if self.spr_zero_hit:
            result |= 0x40
        if self.sprite_overflow:
            result |= 0x20
        
        # Reading status resets the write toggle and vblank flag
        self.first_write = True
        self.vblank = False
        
        return result
    
    def get_data(self):
        """Read from PPUDATA register (0x2007)"""
        # Reading returns buffered value and reads next value
        result = self.data_buffer
        self.data_buffer = self.bus.read(self.data_address)
        
        # Increment address based on control register
        self.data_address += self.data_addr_increment
        self.data_address &= 0xFFFF
        
        return result
    
    def get_oam_data(self):
        """Read from OAMDATA register (0x2004)"""
        return self.sprite_memory[self.sprite_data_address]
    
    def set_oam_data(self, value):
        """Write to OAMDATA register (0x2004)"""
        self.sprite_memory[self.sprite_data_address] = value
        self.sprite_data_address = (self.sprite_data_address + 1) & 0xFF