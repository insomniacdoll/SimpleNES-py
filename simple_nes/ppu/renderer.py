"""
Rendering system for SimpleNES-py
Handles converting PPU output to Pygame display
"""
import pygame
import numpy as np
from simple_nes.ppu.ppu import PPU
from ..bus.mainbus import MainBus
from ..cartridge.mapper import Mapper

class Renderer:
    def __init__(self, virtual_screen, screen_width: int = 256, screen_height: int = 240):
        self.virtual_screen = virtual_screen
        self.screen_width = screen_width
        self.screen_height = screen_height
        
        # Initialize pygame display surface
        self.display_surface = pygame.Surface((screen_width, screen_height))
        
        # Palette mapping (simplified)
        # In a real implementation, this would use the NES color palette
        self.palette = self._generate_nes_palette()
    
    def _generate_nes_palette(self):
        """Generate a simplified NES color palette"""
        # This is a simplified palette - a full implementation would use the
        # exact NES color values
        palette = []
        for i in range(64):  # NES has 64 colors in its palette
            if i < 16:
                # First 16 colors are grays and blacks
                val = int(i * 16)
                palette.append((val, val, val))
            elif i < 32:
                # Next 16 are various colors
                palette.append((255, 0, 0))  # Red
            elif i < 48:
                # Next 16 are more colors
                palette.append((0, 255, 0))  # Green
            else:
                # Last 16
                palette.append((0, 0, 255))  # Blue
        return palette
    
    def render_frame(self):
        """Render a complete frame from virtual screen data"""
        # Get the buffer from virtual screen
        screen_buffer = self.virtual_screen.buffer
        
        # Convert the screen buffer to a pygame surface
        # Create a temporary surface to hold the raw pixel data
        temp_surface = pygame.Surface((self.screen_width, self.screen_height))
        
        # Copy pixels from screen buffer to pygame surface
        for y in range(self.screen_height):
            for x in range(self.screen_width):
                # Get RGB values from screen buffer
                r, g, b = screen_buffer[y, x]
                color = (int(r), int(g), int(b))
                temp_surface.set_at((x, y), color)
        
        # Scale the surface to fit the display requirements
        return temp_surface
    
    def update_display(self, screen, scale_factor=1):
        """Update the display with the current frame"""
        # Render the current frame
        frame_surface = self.render_frame()
        
        # Scale the frame if needed
        if scale_factor != 1:
            frame_surface = pygame.transform.scale(
                frame_surface,
                (self.screen_width * scale_factor, self.screen_height * scale_factor)
            )
        
        # Blit to the main screen
        screen.blit(frame_surface, (0, 0))
        pygame.display.flip()

class PictureBus:
    """
    Picture Bus - handles communication between PPU and graphics memory
    Based on C++ implementation from SimpleNES
    """
    # Name table mirroring types (matching C++ implementation)
    HORIZONTAL = 0
    VERTICAL = 1
    ONE_SCREEN_LOWER = 9
    ONE_SCREEN_HIGHER = 10
    FOUR_SCREEN = 8
    
    def __init__(self, mapper):
        self.mapper = mapper
        self.vram = [0] * 0x800  # 2KB VRAM (matching C++ implementation)
        self.palette_memory = [0] * 0x20  # 32 bytes for palette
        self.mirroring_type = 0  # Default mirroring type
        
        # Nametable indices (matching C++ implementation)
        self.NameTable0 = 0
        self.NameTable1 = 0
        self.NameTable2 = 0
        self.NameTable3 = 0
        
        # Update mirroring if mapper is available
        if self.mapper:
            self.update_mirroring()
    
    def set_mapper(self, mapper):
        """Set the mapper and update mirroring"""
        self.mapper = mapper
        if self.mapper:
            self.update_mirroring()
        return True
    
    def update_mirroring(self):
        """Update nametable mirroring based on mapper configuration"""
        if not self.mapper:
            return
        
        mirroring = self.mapper.get_name_table_mirroring()
        
        if mirroring == self.HORIZONTAL:
            # Horizontal mirroring (vertical scrolling)
            self.NameTable0 = 0
            self.NameTable1 = 0
            self.NameTable2 = 0x400
            self.NameTable3 = 0x400
        elif mirroring == self.VERTICAL:
            # Vertical mirroring (horizontal scrolling)
            self.NameTable0 = 0
            self.NameTable1 = 0x400
            self.NameTable2 = 0
            self.NameTable3 = 0x400
        elif mirroring == self.ONE_SCREEN_LOWER:
            # Single screen with lower bank
            self.NameTable0 = 0
            self.NameTable1 = 0
            self.NameTable2 = 0
            self.NameTable3 = 0
        elif mirroring == self.ONE_SCREEN_HIGHER:
            # Single screen with higher bank
            self.NameTable0 = 0x400
            self.NameTable1 = 0x400
            self.NameTable2 = 0x400
            self.NameTable3 = 0x400
        elif mirroring == self.FOUR_SCREEN:
            # Four screen mirroring (uses mapper's CHR RAM)
            self.NameTable0 = len(self.vram)
        else:
            # Default to single screen lower
            self.NameTable0 = 0
            self.NameTable1 = 0
            self.NameTable2 = 0
            self.NameTable3 = 0
    
    def read(self, addr):
        """Read from picture memory"""
        # PictureBus is limited to 0x3fff
        addr = addr & 0x3FFF
        
        if addr < 0x2000:
            # Pattern table access - goes to cartridge CHR ROM/RAM
            if self.mapper:
                return self.mapper.read_chr(addr)
            else:
                return 0
        elif addr <= 0x3EFF:
            # Name tables up to 0x3000, then mirrored up to 0x3EFF
            index = addr & 0x3FF
            normalized_addr = addr
            
            if addr >= 0x3000:
                normalized_addr -= 0x1000
            
            # If nametable index is beyond VRAM size, use mapper's CHR
            if self.NameTable0 >= len(self.vram):
                if self.mapper:
                    return self.mapper.read_chr(normalized_addr)
                else:
                    return 0
            elif normalized_addr < 0x2400:  # NT0
                return self.vram[self.NameTable0 + index]
            elif normalized_addr < 0x2800:  # NT1
                return self.vram[self.NameTable1 + index]
            elif normalized_addr < 0x2C00:  # NT2
                return self.vram[self.NameTable2 + index]
            else:  # NT3
                return self.vram[self.NameTable3 + index]
        elif addr <= 0x3FFF:
            # Palette memory
            palette_addr = addr & 0x1F
            return self.read_palette(palette_addr)
        
        return 0
    
    def write(self, addr, value):
        """Write to picture memory"""
        # PictureBus is limited to 0x3fff
        addr = addr & 0x3FFF
        
        if addr < 0x2000:
            # Pattern table access - goes to cartridge CHR ROM/RAM
            if self.mapper:
                self.mapper.write_chr(addr, value)
        elif addr <= 0x3EFF:
            # Name tables up to 0x3000, then mirrored up to 0x3EFF
            index = addr & 0x3FF
            normalized_addr = addr
            
            if addr >= 0x3000:
                normalized_addr -= 0x1000
            
            # If nametable index is beyond VRAM size, use mapper's CHR
            if self.NameTable0 >= len(self.vram):
                if self.mapper:
                    self.mapper.write_chr(normalized_addr, value)
            elif normalized_addr < 0x2400:  # NT0
                self.vram[self.NameTable0 + index] = value
            elif normalized_addr < 0x2800:  # NT1
                self.vram[self.NameTable1 + index] = value
            elif normalized_addr < 0x2C00:  # NT2
                self.vram[self.NameTable2 + index] = value
            else:  # NT3
                self.vram[self.NameTable3 + index] = value
        elif addr <= 0x3FFF:
            # Palette memory
            palette_addr = addr & 0x1F
            # Addresses $3F10/$3F14/$3F18/$3F1C are mirrors of $3F00/$3F04/$3F08/$3F0C
            if palette_addr >= 0x10 and palette_addr % 4 == 0:
                palette_addr = palette_addr & 0x0F
            self.palette_memory[palette_addr] = value
    
    def read_palette(self, addr):
        """Read from palette memory"""
        # Addresses $3F10/$3F14/$3F18/$3F1C are mirrors of $3F00/$3F04/$3F08/$3F0C
        if addr >= 0x10 and addr % 4 == 0:
            addr = addr & 0x0F
        return self.palette_memory[addr]
    
    def scanline_irq(self):
        """Call mapper's scanline IRQ handler"""
        if self.mapper:
            self.mapper.scanline_irq()