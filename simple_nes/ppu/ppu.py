"""
Picture Processing Unit (PPU) for SimpleNES-py
Implements the NES PPU (RP2C02) based on SimpleNES C++ implementation
"""
import numpy as np
from typing import Callable, Optional, List
from ..util.logging import info

# PPU Constants
ScanlineCycleLength = 341
ScanlineEndCycle = 340
VisibleScanlines = 240
ScanlineVisibleDots = 256
FrameEndScanline = 261
AttributeOffset = 0x3C0

# NES Color Palette (from C++ PaletteColors.h)
COLORS = [
    (84, 84, 84), (0, 30, 116), (8, 16, 144), (48, 0, 136),
    (68, 0, 100), (92, 0, 48), (84, 4, 0), (60, 24, 0),
    (32, 42, 0), (8, 58, 0), (0, 64, 0), (0, 60, 0),
    (0, 50, 60), (0, 0, 0), (0, 0, 0), (0, 0, 0),
    (152, 150, 152), (8, 76, 196), (48, 50, 236), (92, 30, 228),
    (136, 20, 176), (160, 20, 100), (152, 34, 32), (120, 60, 0),
    (84, 90, 0), (40, 114, 0), (8, 124, 0), (0, 118, 40),
    (0, 102, 120), (0, 0, 0), (0, 0, 0), (0, 0, 0),
    (236, 238, 236), (76, 154, 236), (120, 124, 236), (176, 98, 236),
    (228, 84, 236), (236, 88, 180), (236, 106, 100), (212, 136, 32),
    (160, 170, 0), (116, 196, 0), (76, 208, 32), (56, 204, 108),
    (56, 180, 204), (60, 60, 60), (0, 0, 0), (0, 0, 0),
    (236, 238, 236), (168, 204, 236), (188, 188, 236), (212, 178, 236),
    (236, 174, 236), (236, 174, 212), (236, 180, 176), (228, 196, 144),
    (204, 210, 120), (180, 222, 120), (168, 226, 144), (152, 226, 180),
    (160, 214, 228), (160, 162, 160), (0, 0, 0), (0, 0, 0)
]

class PPU:
    def __init__(self, picture_bus, screen):
        self.bus = picture_bus
        self.screen = screen
        
        # Timing and state
        self.pipeline_state = 0  # 0=PreRender, 1=Render, 2=PostRender, 3=VerticalBlank
        self.cycle = 0
        self.scanline = 0
        self.even_frame = True
        
        # Control flags
        self.vblank = False
        self.spr_zero_hit = False
        self.sprite_overflow = False
        
        # Registers
        self.data_address = int(0)
        self.temp_address = int(0)
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
        self.bg_page = 0  # 0=Low, 1=High
        self.spr_page = 0  # 0=Low, 1=High
        self.data_addr_increment = 1
        
        # Internal buffers
        self.sprite_memory = [0] * (64 * 4)  # 64 sprites * 4 bytes each
        self.scanline_sprites = []  # List of sprite indices on current scanline
        self.picture_buffer = np.zeros((ScanlineVisibleDots, VisibleScanlines, 3), dtype=np.uint8)
        
        # Callback for VBlank interrupt
        self.vblank_callback: Optional[Callable] = None
        
        self.reset()
    
    def reset(self):
        """Reset PPU to initial state"""
        self.long_sprites = False
        self.generate_interrupt = False
        self.greyscale_mode = False
        self.vblank = False
        self.spr_zero_hit = False
        self.sprite_overflow = False
        self.show_background = True
        self.show_sprites = True
        self.even_frame = True
        self.first_write = True
        self.bg_page = 0
        self.spr_page = 0
        self.data_address = int(0)
        self.cycle = 0
        self.scanline = 0
        self.sprite_data_address = 0
        self.fine_x_scroll = 0
        self.temp_address = int(0)
        self.data_addr_increment = 1
        self.pipeline_state = 0  # PreRender
        self.scanline_sprites = []
    
    def set_interrupt_callback(self, callback: Callable):
        """Set callback for VBlank interrupt"""
        self.vblank_callback = callback
    
    def do_DMA(self, page_ptr: List[int]):
        """Perform DMA operation"""
        # DMA transfers 256 bytes from CPU page to PPU OAM
        for i in range(256 - self.sprite_data_address):
            self.sprite_memory[self.sprite_data_address + i] = page_ptr[i]
        if self.sprite_data_address > 0:
            for i in range(self.sprite_data_address):
                self.sprite_memory[i] = page_ptr[256 - self.sprite_data_address + i]
    
    def step(self):
        """Execute a single PPU step"""
        old_state = self.pipeline_state
        
        if self.pipeline_state == 0:  # PreRender
            if self.cycle == 1:
                self.vblank = False
                self.spr_zero_hit = False
            elif self.cycle == ScanlineVisibleDots + 2 and self.show_background and self.show_sprites:
                # Set bits related to horizontal position
                self.data_address = int(self.data_address & ~0x41f)  # Unset horizontal bits
                self.data_address = int(self.data_address | (self.temp_address & 0x41f))  # Copy
            elif self.cycle > 280 and self.cycle <= 304 and self.show_background and self.show_sprites:
                # Set vertical bits
                self.data_address = int(self.data_address & ~0x7be0)  # Unset bits related to horizontal
                self.data_address = int(self.data_address | (self.temp_address & 0x7be0))  # Copy
            
            # If rendering is on, every other frame is one cycle shorter
            skip_cycle = (not self.even_frame) and self.show_background and self.show_sprites
            
            # Add IRQ support for MMC3 - check BEFORE state transition
            if self.cycle == 260 and self.show_background and self.show_sprites:
                if hasattr(self.bus, 'scanline_irq'):
                    self.bus.scanline_irq()
            
            if self.cycle >= ScanlineEndCycle - (1 if skip_cycle else 0):
                self.pipeline_state = 1  # Render
                self.cycle = 0
                self.scanline = 0
                self.cycle += 1  # Increment cycle after state transition
            else:
                self.cycle += 1
            return
        
        elif self.pipeline_state == 1:  # Render
            if self.cycle > 0 and self.cycle <= ScanlineVisibleDots:
                bg_color = 0
                spr_color = 0
                bg_opaque = False
                spr_opaque = True
                sprite_foreground = False
                
                x = self.cycle - 1
                y = self.scanline
                
                if self.show_background:
                    x_fine = (self.fine_x_scroll + x) % 8
                    if not self.hide_edge_background or x >= 8:
                        # Fetch tile
                        addr = 0x2000 | (self.data_address & 0x0FFF)
                        tile = self._read(addr)
                        
                        # Fetch pattern
                        addr = (tile * 16) + ((self.data_address >> 12) & 0x7)
                        addr |= self.bg_page << 12
                        pattern0 = self._read(addr)
                        pattern1 = self._read(addr + 8)
                        bg_color = (pattern0 >> (7 ^ x_fine)) & 1
                        bg_color |= ((pattern1 >> (7 ^ x_fine)) & 1) << 1
                        
                        bg_opaque = bool(bg_color)
                        
                        # Fetch attribute and calculate higher two bits of palette
                        addr = 0x23C0 | (self.data_address & 0x0C00) | ((self.data_address >> 4) & 0x38) | ((self.data_address >> 2) & 0x07)
                        attribute = self._read(addr)
                        shift = ((self.data_address >> 4) & 4) | (self.data_address & 2)
                        bg_color |= ((attribute >> shift) & 0x3) << 2
                    
                    # Increment/wrap coarse X
                    if x_fine == 7:
                        if (self.data_address & 0x001F) == 31:
                            self.data_address = int(self.data_address & ~0x001F)
                            self.data_address = int(self.data_address ^ 0x0400)
                        else:
                            self.data_address = int(self.data_address + 1)
                
                if self.show_sprites and (not self.hide_edge_sprites or x >= 8):
                    for i in self.scanline_sprites:
                        spr_x = self.sprite_memory[i * 4 + 3]
                        
                        if 0 > x - spr_x or x - spr_x >= 8:
                            continue
                        
                        spr_y = self.sprite_memory[i * 4 + 0] + 1
                        tile = self.sprite_memory[i * 4 + 1]
                        attribute = self.sprite_memory[i * 4 + 2]
                        
                        length = 16 if self.long_sprites else 8
                        
                        x_shift = (x - spr_x) % 8
                        y_offset = (y - spr_y) % length
                        
                        if (attribute & 0x40) == 0:
                            x_shift ^= 7
                        if (attribute & 0x80) != 0:
                            y_offset ^= (length - 1)
                        
                        addr = 0
                        if not self.long_sprites:
                            addr = tile * 16 + y_offset
                            if self.spr_page == 1:
                                addr += 0x1000
                        else:
                            y_offset = (y_offset & 7) | ((y_offset & 8) << 1)
                            addr = (tile >> 1) * 32 + y_offset
                            addr |= (tile & 1) << 12
                        
                        spr_color |= (self._read(addr) >> x_shift) & 1
                        spr_color |= ((self._read(addr + 8) >> x_shift) & 1) << 1
                        
                        if not (spr_opaque := bool(spr_color)):
                            spr_color = 0
                            continue
                        
                        spr_color |= 0x10
                        spr_color |= (attribute & 0x3) << 2
                        
                        sprite_foreground = not bool(attribute & 0x20)
                        
                        # Sprite-0 hit detection (matching C++ implementation)
                        # Only detect hit if:
                        # 1. Background is being rendered
                        # 2. This is sprite 0
                        # 3. Both sprite and background are opaque
                        # 4. Sprite is not hidden at edge (or x >= 8)
                        # 5. Background is not hidden at edge (or x >= 8)
                        if (not self.spr_zero_hit and 
                            self.show_background and 
                            i == 0 and 
                            spr_opaque and 
                            bg_opaque and
                            (not self.hide_edge_sprites or x >= 8) and
                            (not self.hide_edge_background or x >= 8)):
                            self.spr_zero_hit = True
                        
                        break
                
                palette_addr = bg_color
                
                if (not bg_opaque and spr_opaque) or (bg_opaque and spr_opaque and sprite_foreground):
                    palette_addr = spr_color
                elif not bg_opaque and not spr_opaque:
                    palette_addr = 0
                
                color_idx = self.bus.read_palette(palette_addr)
                self.picture_buffer[x, y] = COLORS[color_idx]
            
            elif self.cycle == ScanlineVisibleDots + 1 and self.show_background:
                # Shamelessly copied from nesdev wiki
                if (self.data_address & 0x7000) != 0x7000:
                    self.data_address = int(self.data_address + 0x1000)
                else:
                    self.data_address = int(self.data_address & ~0x7000)
                    y = (self.data_address & 0x03E0) >> 5
                    if y == 29:
                        y = 0
                        self.data_address = int(self.data_address ^ 0x0800)
                    elif y == 31:
                        y = 0
                    else:
                        y += 1
                    self.data_address = int((self.data_address & ~0x03E0) | (y << 5))
            
            elif self.cycle == ScanlineVisibleDots + 2 and self.show_background and self.show_sprites:
                # Copy bits related to horizontal position
                self.data_address = int(self.data_address & ~0x41f)
                self.data_address = int(self.data_address | (self.temp_address & 0x41f))
            
            # Add IRQ support for MMC3
            if self.cycle == 260 and self.show_background and self.show_sprites:
                if hasattr(self.bus, 'scanline_irq'):
                    self.bus.scanline_irq()
            
            if self.cycle >= ScanlineEndCycle:
                # Find and index sprites that are on the next Scanline
                self.scanline_sprites = []
                
                range_val = 16 if self.long_sprites else 8
                
                j = 0
                for i in range(self.sprite_data_address // 4, 64):
                    diff = self.scanline - self.sprite_memory[i * 4]
                    if 0 <= diff < range_val:
                        if j >= 8:
                            self.sprite_overflow = True
                            break
                        self.scanline_sprites.append(i)
                        j += 1
                
                self.scanline += 1
                self.cycle = 0
                
                # Check if we've finished rendering all visible scanlines
                if self.scanline >= VisibleScanlines:
                    self.pipeline_state = 2  # PostRender
                self.cycle += 1  # Increment cycle after scanline completion
            else:
                self.cycle += 1
            return
        
        elif self.pipeline_state == 2:  # PostRender
            if self.cycle >= ScanlineEndCycle:
                self.scanline += 1
                self.cycle = 0
                self.pipeline_state = 3  # VerticalBlank
                
                # Copy picture buffer to screen at the end of PostRender
                # Note: picture_buffer shape is (ScanlineVisibleDots, VisibleScanlines, 3)
                # Indexed as [x, y, channel]
                for x in range(self.picture_buffer.shape[0]):
                    for y in range(self.picture_buffer.shape[1]):
                        color = self.picture_buffer[x, y]
                        self.screen.set_pixel(x, y, color)
                self.cycle += 1  # Increment cycle after state transition
            else:
                self.cycle += 1
            return
        
        elif self.pipeline_state == 3:  # VerticalBlank
            # Set vblank flag at cycle 1 of scanline 241 (VisibleScanlines + 1)
            if self.cycle == 1 and self.scanline == VisibleScanlines + 1:
                self.vblank = True
                if self.generate_interrupt and self.vblank_callback:
                    self.vblank_callback()
            
            if self.cycle >= ScanlineEndCycle:
                self.scanline += 1
                self.cycle = 0
                
                if self.scanline >= FrameEndScanline:
                    self.pipeline_state = 0  # PreRender
                    self.scanline = 0
                    self.even_frame = not self.even_frame
                    info(f"PPU: VerticalBlank -> PreRender (scanline={self.scanline}, cycle={self.cycle})")
                self.cycle += 1  # Increment cycle after state transition
            else:
                self.cycle += 1
            return
    
    def _read(self, addr: int) -> int:
        """Read from PPU address space"""
        return self.bus.read(addr)
    
    def _read_oam(self, addr: int) -> int:
        """Read from OAM memory"""
        return self.sprite_memory[addr]
    
    def _write_oam(self, addr: int, value: int):
        """Write to OAM memory"""
        self.sprite_memory[addr] = value
    
    # PPU register access methods
    def control(self, ctrl: int):
        """Write to PPUCTRL register (0x2000)"""
        self.generate_interrupt = bool(ctrl & 0x80)
        self.long_sprites = bool(ctrl & 0x20)
        self.bg_page = 1 if (ctrl & 0x10) else 0
        self.spr_page = 1 if (ctrl & 0x08) else 0
        if ctrl & 0x04:
            self.data_addr_increment = 0x20
        else:
            self.data_addr_increment = 1
        
        # Set the nametable in the temp address
        self.temp_address = int(self.temp_address & ~0xc00)
        self.temp_address = int(self.temp_address | ((ctrl & 0x3) << 10))
    
    def set_mask(self, mask: int):
        """Write to PPUMASK register (0x2001)"""
        self.greyscale_mode = bool(mask & 0x1)
        self.hide_edge_background = not bool(mask & 0x2)
        self.hide_edge_sprites = not bool(mask & 0x4)
        self.show_background = bool(mask & 0x8)
        self.show_sprites = bool(mask & 0x10)
    
    def get_status(self) -> int:
        """Read from PPUSTATUS register (0x2002)"""
        status = (self.sprite_overflow << 5) | (self.spr_zero_hit << 6) | (self.vblank << 7)
        self.vblank = False
        self.first_write = True
        return status
    
    def set_data_address(self, addr: int):
        """Write to PPUADDR register (0x2006)"""
        if self.first_write:
            self.temp_address = int(self.temp_address & ~0xff00)
            self.temp_address = int(self.temp_address | ((addr & 0x3f) << 8))
            self.first_write = False
        else:
            self.temp_address = int(self.temp_address & ~0xff)
            self.temp_address = int(self.temp_address | addr)
            self.data_address = int(self.temp_address)
            self.first_write = True
    
    def get_data(self) -> int:
        """Read from PPUDATA register (0x2007)"""
        # Check if current address is in palette range before reading
        is_palette = self.data_address >= 0x3f00
        
        data = self.bus.read(self.data_address)
        self.data_address = int(self.data_address + self.data_addr_increment)
        
        # Reads are delayed by one byte/read when address is NOT in palette range
        if not is_palette:
            # Return from the data buffer and store the current value in the buffer
            data, self.data_buffer = self.data_buffer, data
        
        return data
    
    def set_oam_address(self, addr: int):
        """Write to OAMADDR register (0x2003)"""
        self.sprite_data_address = addr
    
    def get_oam_data(self) -> int:
        """Read from OAMDATA register (0x2004)"""
        return self._read_oam(self.sprite_data_address)
    
    def set_oam_data(self, value: int):
        """Write to OAMDATA register (0x2004)"""
        self._write_oam(self.sprite_data_address, value)
        self.sprite_data_address = (self.sprite_data_address + 1) & 0xFF
    
    def set_data(self, data: int):
        """Write to PPUDATA register (0x2007)"""
        self.bus.write(self.data_address, data)
        self.data_address = int(self.data_address + self.data_addr_increment)
    
    def set_scroll(self, scroll: int):
        """Write to PPUSCROL register (0x2005)"""
        if self.first_write:
            self.temp_address = int(self.temp_address & ~0x1f)
            self.temp_address = int(self.temp_address | ((scroll >> 3) & 0x1f))
            self.fine_x_scroll = scroll & 0x7
            self.first_write = False
        else:
            self.temp_address = int(self.temp_address & ~0x73e0)
            self.temp_address = int(self.temp_address | (((scroll & 0x7) << 12) | ((scroll & 0xf8) << 2)))
            self.first_write = True
    
