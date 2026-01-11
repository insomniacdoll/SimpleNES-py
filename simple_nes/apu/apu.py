"""
Audio system for SimpleNES-py
Implements NES APU (Audio Processing Unit)
"""
import pygame
import numpy as np
from typing import Callable

class APU:
    def __init__(self, irq_callback: Callable[[], None] = None):
        # IRQ callback for frame counter interrupts
        self.irq_callback = irq_callback
        
        # Check if pygame mixer module is available
        self.mixer_available = hasattr(pygame, 'mixer')
        if self.mixer_available:
            try:
                pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
            except (NotImplementedError, ModuleNotFoundError):
                self.mixer_available = False
        
        # APU channels
        self.pulse1 = PulseChannel(0)  # $4000-$4003
        self.pulse2 = PulseChannel(1)  # $4004-$4007
        self.triangle = TriangleChannel()  # $4008-$400B
        self.noise = NoiseChannel()  # $400C-$400F
        self.dmc = DMCChannel()  # $4010-$4013
        
        # Frame counter
        self.frame_counter = 0
        self.frame_interrupt = False
        self.interrupt_inhibit = False
        self.frame_counter_mode = 0  # 0=4-step, 1=5-step
        
        # Status register
        self.status = 0
        
        # Audio buffer and playback
        self.sample_rate = 44100
        self.audio_buffer = []
        
        # Setup mixer channel for audio output if available
        if self.mixer_available:
            self.audio_channel = pygame.mixer.Channel(0)
        else:
            self.audio_channel = None
    
    def write_register(self, addr: int, value: int):
        """Write to APU register"""
        if 0x4000 <= addr <= 0x4003:
            self.pulse1.write_register(addr - 0x4000, value)
        elif 0x4004 <= addr <= 0x4007:
            self.pulse2.write_register(addr - 0x4004, value)
        elif 0x4008 <= addr <= 0x400B:
            self.triangle.write_register(addr - 0x4008, value)
        elif 0x400C <= addr <= 0x400F:
            self.noise.write_register(addr - 0x400C, value)
        elif 0x4010 <= addr <= 0x4013:
            self.dmc.write_register(addr - 0x4010, value)
        elif addr == 0x4015:
            # Status register
            self.status = value
            # Enable/disable channels based on bits
            self.pulse1.enabled = bool(value & 0x01)
            self.pulse2.enabled = bool(value & 0x02)
            self.triangle.enabled = bool(value & 0x04)
            self.noise.enabled = bool(value & 0x08)
            self.dmc.enabled = bool(value & 0x10)
        elif addr == 0x4017:
            # Frame counter register
            self.frame_counter_mode = (value >> 7) & 0x01  # Bit 7: mode (0=4-step, 1=5-step)
            self.interrupt_inhibit = bool(value >> 6)  # Bit 6: interrupt inhibit
            # Reset frame counter
            self.frame_counter = 0
            # Clear frame interrupt if inhibit is set
            if self.interrupt_inhibit:
                self.frame_interrupt = False
    
    def read_register(self, addr: int) -> int:
        """Read from APU register"""
        if addr == 0x4015:
            # Status register
            result = 0
            # Bit 0-3: Channel length counter status (1 if not muted)
            # A channel is not muted if enabled and length counter > 0
            if self.pulse1.enabled and self.pulse1.length_counter > 0:
                result |= 0x01
            if self.pulse2.enabled and self.pulse2.length_counter > 0:
                result |= 0x02
            if self.triangle.enabled and self.triangle.length_counter > 0:
                result |= 0x04
            if self.noise.enabled and self.noise.length_counter > 0:
                result |= 0x08
            # Bit 4: DMC active
            if self.dmc.length_counter > 0 or self.dmc.loop_flag:
                result |= 0x10
            # Bit 6: Frame interrupt
            if self.frame_interrupt:
                result |= 0x40
            # Bit 7: DMC interrupt
            if self.dmc.irq_flag:
                result |= 0x80
            
            # Clear frame interrupt flag
            self.frame_interrupt = False
            return result
        return 0
    
    def step(self):
        """Execute one APU step - this would run at CPU frequency"""
        # In a real implementation, APU runs at CPU frequency
        # and generates audio samples periodically
        
        # Update frame counter (NTSC)
        # Using constants from C++ implementation
        Q1 = 7457
        Q2 = 14913
        Q3 = 22371
        Q4 = 29829
        Q5 = 37281
        seq4step_length = Q4 + 1
        seq5step_length = Q5 + 1
        
        self.frame_counter += 1
        
        # The frame counter generates 4 or 5 step clocking signals per frame
        # depending on bit 7 of $4017
        if not self.interrupt_inhibit:
            # 4-step mode (default)
            if self.frame_counter == Q1:
                self._quarter_frame_update()
            elif self.frame_counter == Q2:
                self._quarter_frame_update()
                self._half_frame_update()
            elif self.frame_counter == Q3:
                self._quarter_frame_update()
            elif self.frame_counter == Q4:
                self._quarter_frame_update()
                self._half_frame_update()
                self.frame_interrupt = True  # Generate interrupt
                # Trigger IRQ if not inhibited and callback is set
                # Temporarily disabled for testing
                # if not self.interrupt_inhibit and self.irq_callback:
                #     self.irq_callback()
            elif self.frame_counter == seq4step_length:
                self.frame_counter = 0  # Reset counter
        else:
            # 5-step mode (interrupts inhibited)
            if self.frame_counter == Q1:
                self._quarter_frame_update()
            elif self.frame_counter == Q2:
                self._quarter_frame_update()
                self._half_frame_update()
            elif self.frame_counter == Q3:
                self._quarter_frame_update()
            elif self.frame_counter == Q5:
                self._quarter_frame_update()
                self._half_frame_update()
            elif self.frame_counter == seq5step_length:
                self.frame_counter = 0  # Reset counter
    
    def _quarter_frame_update(self):
        """Update quarter-frame counters for channels"""
        self.pulse1.update_envelope()
        self.pulse2.update_envelope()
        self.triangle.update_linear_counter()
        self.noise.update_envelope()
    
    def _half_frame_update(self):
        """Update half-frame counters for channels"""
        self.pulse1.update_sweep()
        self.pulse2.update_sweep()
        self.triangle.update_length_counter()
        self.noise.update_length_counter()
        self.dmc.update_length_counter()
    
    def generate_audio(self):
        """Generate audio samples for playback"""
        # Get output from each channel
        pulse1_output = self.pulse1.output()
        pulse2_output = self.pulse2.output()
        triangle_output = self.triangle.output()
        noise_output = self.noise.output()
        dmc_output = self.dmc.output()
        
        # Mix the channels using the correct non-linear formula (matching C++ implementation)
        # Pulse channels: 95.88 / ((8128.0 / (pulse1 + pulse2)) + 100.0)
        pulse_out = 0.0
        if pulse1_output + pulse2_output != 0:
            pulse_out = 95.88 / ((8128.0 / (pulse1_output + pulse2_output)) + 100.0)
        
        # TND channels: 159.79 / (1.0 / ((triangle / 8227.0) + (noise / 12241.0) + (dmc / 22638.0)) + 100.0)
        tnd_out = 0.0
        if triangle_output + noise_output + dmc_output != 0:
            tnd_sum = (triangle_output / 8227.0) + (noise_output / 12241.0) + (dmc_output / 22638.0)
            tnd_out = 159.79 / (1.0 / tnd_sum + 100.0)
        
        # Combine all channels
        total_output = pulse_out + tnd_out
        
        # Clamp to valid range [-1.0, 1.0]
        total_output = max(-1.0, min(1.0, total_output))
        
        # Convert to 16-bit signed integer
        sample = int(total_output * 32767)
        
        return sample
    
    def play_sample(self, sample_data):
        """Play audio sample if mixer is available"""
        if self.mixer_available and self.audio_channel:
            # Convert sample data to a pygame sound object and play it
            # For now, we just skip if mixer is not available
            try:
                sound = pygame.sndarray.make_sound(sample_data)
                self.audio_channel.play(sound)
            except:
                # If there's an error playing the sound, ignore it
                pass
        # If mixer is not available, just ignore the audio

class PulseChannel:
    def __init__(self, channel_num: int):
        self.channel_num = channel_num
        
        # Channel registers
        self.duty_cycle = 0  # $00:0-1
        self.length_counter_halt = False  # $00:6
        self.constant_volume = False  # $00:7
        self.envelope_divider = 0  # $00:0-3
        self.envelope_loop = False  # $00:5
        self.volume = 0  # $00:0-3 or constant volume
        
        self.sweep_enabled = False  # $01:7
        self.sweep_divider = 0  # $01:4-6
        self.sweep_negate = False  # $01:3
        self.sweep_shift = 0  # $01:0-2
        
        self.timer_low = 0  # $02:0-7
        self.timer_high = 0  # $03:0-2
        self.length_counter_load = 0  # $03:3-7
        
        # Internal state
        self.timer = 0
        self.envelope_volume = 0
        self.length_counter = 0
        self.enabled = False
        
        # Waveform position
        self.waveform_pos = 0
        
        # Duty cycle waveforms (out of 8 steps)
        self.duty_cycles = [
            [0, 1, 0, 0, 0, 0, 0, 0],  # 12.5%
            [0, 1, 1, 0, 0, 0, 0, 0],  # 25%
            [0, 1, 1, 1, 1, 0, 0, 0],  # 50%
            [1, 0, 0, 1, 1, 1, 1, 1]   # 25% negated
        ]
        
        # Sweep unit internal state
        self.sweep_reload = False
        self.sweep_divider_counter = 0
        self.sweep_target_period = 0
        self.ones_complement = (channel_num == 0)  # Pulse1 uses ones complement
    
    def write_register(self, reg: int, value: int):
        """Write to pulse channel register"""
        if reg == 0:
            self.duty_cycle = (value >> 6) & 0x03
            self.length_counter_halt = bool(value & 0x20)
            self.constant_volume = bool(value & 0x10)
            self.volume = value & 0x0F
            self.envelope_loop = bool(value & 0x20)
        elif reg == 1:
            self.sweep_enabled = bool(value & 0x80)
            self.sweep_divider = (value >> 4) & 0x07
            self.sweep_negate = bool(value & 0x08)
            self.sweep_shift = value & 0x07
        elif reg == 2:
            self.timer_low = value
        elif reg == 3:
            self.timer_high = value & 0x07
            self.length_counter_load = (value >> 3) & 0x1F
            if self.enabled:
                self.length_counter = self.length_counter_load
    
    def update_envelope(self):
        """Update envelope divider"""
        if not self.constant_volume:
            if self.envelope_divider == 0:
                self.envelope_divider = 15
                if self.envelope_volume > 0:
                    self.envelope_volume -= 1
                elif self.envelope_loop:
                    self.envelope_volume = 15
            else:
                self.envelope_divider -= 1
    
    def update_sweep(self):
        """Update sweep unit"""
        # Reload sweep divider
        if self.sweep_reload:
            self.sweep_divider_counter = self.sweep_divider
            self.sweep_reload = False
            return
        
        # If sweep is disabled, don't update
        if not self.sweep_enabled:
            return
        
        # Decrement sweep divider
        if self.sweep_divider_counter > 0:
            self.sweep_divider_counter -= 1
            return
        
        # Reset sweep divider
        self.sweep_divider_counter = self.sweep_divider
        
        # Update period if shift > 0
        if self.sweep_shift > 0:
            current_period = (self.timer_high << 8) | self.timer_low
            target_period = self.calculate_sweep_target(current_period)
            
            if not self.is_sweep_muted(current_period, target_period):
                self.timer_low = target_period & 0xFF
                self.timer_high = (target_period >> 8) & 0x07
    
    def calculate_sweep_target(self, current_period: int) -> int:
        """Calculate sweep target period"""
        amount = current_period >> self.sweep_shift
        
        if not self.sweep_negate:
            return current_period + amount
        elif self.ones_complement:
            # Ones complement (for Pulse2)
            return max(0, current_period - amount - 1)
        else:
            # Two's complement (for Pulse1)
            return max(0, current_period - amount)
    
    def is_sweep_muted(self, current_period: int, target_period: int) -> bool:
        """Check if sweep is muted"""
        # Mute if target period > 0x7FF
        if target_period > 0x7FF:
            return True
        
        # Mute if current period < 8 (too high frequency)
        if current_period < 8:
            return True
        
        return False
    
    def output(self) -> float:
        """Get the current output value for this channel"""
        if not self.enabled or self.length_counter == 0:
            return 0.0
        
        # Calculate timer value
        timer = (self.timer_high << 8) | self.timer_low
        
        # Check if muted by sweep
        if self.sweep_enabled:
            target_period = self.calculate_sweep_target(timer)
            if self.is_sweep_muted(timer, target_period):
                return 0.0
        
        # Update waveform position
        self.waveform_pos = (self.waveform_pos + 1) % 8
        
        # Get the current duty cycle pattern
        pattern = self.duty_cycles[self.duty_cycle]
        duty_value = pattern[self.waveform_pos]
        
        # Calculate volume
        volume = self.volume if self.constant_volume else self.envelope_volume
        
        # Return amplitude based on duty cycle and volume
        return duty_value * (volume / 15.0) if timer > 0 else 0.0

class TriangleChannel:
    def __init__(self):
        # Channel registers
        self.linear_counter_load = 0  # $4008:0-6
        self.length_counter_halt = False  # $4008:7
        
        self.timer_low = 0  # $400A:0-7
        self.timer_high = 0  # $400B:0-2
        self.length_counter_load_reg = 0  # $400B:3-7
        
        # Internal state
        self.linear_counter = 0
        self.length_counter = 0
        self.timer = 0
        self.enabled = False
        
        # Waveform position
        self.waveform_pos = 0
        self.waveform_direction = 1  # 1 for up, -1 for down
        
        # Triangle waveform: 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0
        self.triangle_wave = list(range(16)) + list(range(15, -1, -1))
        
        # Linear counter control flags
        self.linear_counter_control = False
        self.linear_counter_reload = False
    
    def write_register(self, reg: int, value: int):
        """Write to triangle channel register"""
        if reg == 0:
            self.linear_counter_load = value & 0x7F
            self.length_counter_halt = bool(value & 0x80)
            self.linear_counter_control = bool(value & 0x80)  # Same bit is used for both
        elif reg == 2:
            self.timer_low = value
        elif reg == 3:
            self.timer_high = value & 0x07
            self.length_counter_load_reg = (value >> 3) & 0x1F
            if self.enabled:
                self.length_counter = self.length_counter_load_reg
            self.linear_counter_reload = True
    
    def update_linear_counter(self):
        """Update linear counter"""
        if self.linear_counter_reload:
            self.linear_counter = self.linear_counter_load
        elif self.linear_counter > 0:
            self.linear_counter -= 1
        
        # Clear reload flag
        if not self.length_counter_halt:
            self.linear_counter_reload = False
    
    def update_length_counter(self):
        """Update length counter"""
        if not self.length_counter_halt and self.length_counter > 0:
            self.length_counter -= 1
    
    def output(self) -> float:
        """Get the current output value for this channel"""
        if not self.enabled or self.length_counter == 0 or self.linear_counter == 0:
            return 0.0
        
        # Update waveform position
        if self.timer == 0:
            self.waveform_pos = (self.waveform_pos + 1) % len(self.triangle_wave)
        
        # Calculate timer value
        self.timer -= 1
        if self.timer <= 0:
            timer = (self.timer_high << 8) | self.timer_low
            self.timer = timer + 1
        
        # Get triangle value and scale to -1.0 to 1.0
        triangle_value = self.triangle_wave[self.waveform_pos]
        return (triangle_value - 15.0) / 15.0  # Normalize to -1.0 to 1.0

class NoiseChannel:
    def __init__(self):
        # Channel registers
        self.mode_flag = False  # $400C:6 (0=32767 bits, 1=93 bits)
        self.length_counter_halt = False  # $400C:5
        self.constant_volume = False  # $400C:4
        self.volume = 0  # $400C:0-3
        
        self.frequency_index = 0  # $400E:0-3
        self.length_counter_load = 0  # $400F:3-7
        
        # Internal state
        self.envelope_volume = 0
        self.length_counter = 0
        self.enabled = False
        
        # Noise generation
        self.shift_register = 1  # Start with bit 0 set
        self.period = 0
        self.timer = 0
    
    def write_register(self, reg: int, value: int):
        """Write to noise channel register"""
        if reg == 0:
            self.length_counter_halt = bool(value & 0x20)
            self.constant_volume = bool(value & 0x10)
            self.volume = value & 0x0F
        elif reg == 2:
            self.mode_flag = bool(value & 0x80)
            self.frequency_index = value & 0x0F
            # Update period based on frequency index
            noise_periods = [4, 8, 16, 32, 64, 96, 128, 160, 202, 254, 380, 508, 762, 1016, 2034, 4068]
            self.period = noise_periods[self.frequency_index]
        elif reg == 3:
            self.length_counter_load = (value >> 3) & 0x1F
            if self.enabled:
                self.length_counter = self.length_counter_load
    
    def update_envelope(self):
        """Update envelope divider"""
        if not self.constant_volume:
            if self.envelope_volume == 0:
                self.envelope_volume = 15
            elif self.envelope_volume > 0:
                self.envelope_volume -= 1
    
    def update_length_counter(self):
        """Update length counter"""
        if not self.length_counter_halt and self.length_counter > 0:
            self.length_counter -= 1
    
    def output(self) -> float:
        """Get the current output value for this channel"""
        if not self.enabled or self.length_counter == 0:
            return 0.0
        
        # Check if bit 0 is set (if set, output is muted)
        if self.shift_register & 0x01:
            return 0.0
        
        # Calculate volume
        volume = self.volume if self.constant_volume else self.envelope_volume
        return volume / 15.0
    
    def clock(self):
        """Clock the noise generator (called at APU rate)"""
        self.timer -= 1
        if self.timer <= 0:
            self.timer = self.period
            
            # Shift register with XOR feedback
            if self.mode_flag:
                # Short mode (93 bits): use bit 0 and bit 6
                feedback = (self.shift_register & 1) ^ ((self.shift_register >> 6) & 1)
            else:
                # Long mode (32767 bits): use bit 0 and bit 1
                feedback = (self.shift_register & 1) ^ ((self.shift_register >> 1) & 1)
            
            self.shift_register >>= 1
            self.shift_register |= (feedback << 14)  # 15-bit shift register

class DMCChannel:
    def __init__(self):
        # Channel registers
        self.irq_enabled = False  # $4010:7
        self.loop_flag = False  # $4010:6
        self.frequency_index = 0  # $4010:0-3
        
        self.direct_load = 0  # $4011:0-6
        self.sample_address = 0  # $4012:0-7
        self.sample_length = 0  # $4013:0-7
        
        # Internal state
        self.enabled = False
        self.irq_flag = False
        self.length_counter = 0
        self.address_counter = 0
        self.dac = 0
        self.timer = 0
        
        # DMC sampling state
        self.sample_buffer = 0
        self.sample_buffer_empty = True
        self.bits_remaining = 0
        self.shift_register = 0
        
        # DMA callback
        self.dma_callback = None
        
        # DMC frequency periods (in CPU cycles)
        self.dmc_periods = [428, 380, 340, 320, 254, 254, 170, 170, 127, 127, 114, 114, 107, 107, 98, 98]
    
    def set_dma_callback(self, callback):
        """Set the DMA callback for reading samples"""
        self.dma_callback = callback
    
    def write_register(self, reg: int, value: int):
        """Write to DMC channel register"""
        if reg == 0:
            self.irq_enabled = bool(value & 0x80)
            self.loop_flag = bool(value & 0x40)
            self.frequency_index = value & 0x0F
        elif reg == 1:
            self.direct_load = value & 0x7F
            self.dac = self.direct_load
        elif reg == 2:
            self.sample_address = 0xC000 + (value * 0x40)
            self.address_counter = self.sample_address
        elif reg == 3:
            self.sample_length = (value * 0x10) + 1
            if self.enabled:
                self.length_counter = self.sample_length
    
    def control(self, value: int):
        """Control DMC channel (from APU status register)"""
        self.enabled = bool(value & 0x10)
        if self.enabled and self.length_counter == 0:
            self.length_counter = self.sample_length
            self.address_counter = self.sample_address
    
    def update_length_counter(self):
        """Update length counter"""
        if self.length_counter > 0:
            self.length_counter -= 1
            if self.length_counter == 0:
                if self.loop_flag:
                    self.length_counter = self.sample_length
                    self.address_counter = self.sample_address
                elif self.irq_enabled:
                    self.irq_flag = True
    
    def clear_interrupt(self):
        """Clear DMC interrupt flag"""
        self.irq_flag = False
    
    def has_more_samples(self) -> bool:
        """Check if DMC has more samples to play"""
        return self.length_counter > 0 or self.loop_flag
    
    def clock(self):
        """Clock the DMC channel"""
        # Update timer
        self.timer -= 1
        if self.timer > 0:
            return
        
        # Reset timer
        self.timer = self.dmc_periods[self.frequency_index]
        
        # Load sample buffer if empty
        if self.sample_buffer_empty and self.length_counter > 0:
            if self.dma_callback:
                self.sample_buffer = self.dma_callback(self.address_counter >> 6)
            self.sample_buffer_empty = False
            self.address_counter = (self.address_counter + 1) | 0x8000
            self.length_counter -= 1
            if self.length_counter == 0:
                if self.loop_flag:
                    self.length_counter = self.sample_length
                    self.address_counter = self.sample_address
                elif self.irq_enabled:
                    self.irq_flag = True
        
        # Output sample
        if self.bits_remaining == 0:
            if not self.sample_buffer_empty:
                self.shift_register = self.sample_buffer
                self.sample_buffer_empty = True
                self.bits_remaining = 8
            else:
                self.shift_register = 0
                self.bits_remaining = 8
        
        # Update DAC
        if self.shift_register & 0x01:
            if self.dac <= 125:
                self.dac += 2
        else:
            if self.dac >= 2:
                self.dac -= 2
        
        self.shift_register >>= 1
        self.bits_remaining -= 1
    
    def output(self) -> float:
        """Get the current output value for this channel"""
        return self.dac / 127.0  # Normalize to 0.0-1.0