"""
Test APU channel implementations
Tests for Pulse, Triangle, Noise, and DMC channels
"""
import pytest
from simple_nes.apu.apu import APU, PulseChannel, TriangleChannel, NoiseChannel, DMCChannel

class TestPulseChannel:
    def test_pulse_channel_initialization(self):
        """Test that PulseChannel initializes correctly"""
        channel = PulseChannel(0)
        assert channel.channel_num == 0
        assert channel.enabled == False
        assert channel.length_counter == 0
    
    def test_pulse_channel_sweep_unit(self):
        """Test PulseChannel sweep unit implementation"""
        channel = PulseChannel(1)  # Pulse2 (uses two's complement)
        
        # Set up sweep parameters
        channel.sweep_enabled = True
        channel.sweep_divider = 0
        channel.sweep_shift = 1
        channel.sweep_negate = True
        channel.timer_low = 0x00
        channel.timer_high = 0x01  # Period = 256
        
        # Calculate sweep target
        current_period = 256
        target_period = channel.calculate_sweep_target(current_period)
        
        # For Pulse2 with negate and shift=1: target = current - (current >> 1)
        # target = 256 - 128 = 128
        assert target_period == 128
    
    def test_pulse_channel_sweep_muting(self):
        """Test PulseChannel sweep muting logic"""
        channel = PulseChannel(0)
        
        # Test muting for high frequency (period < 8)
        assert channel.is_sweep_muted(5, 10) == True
        
        # Test muting for target > 0x7FF
        assert channel.is_sweep_muted(256, 0x800) == True
        
        # Test not muted
        assert channel.is_sweep_muted(256, 200) == False
    
    def test_pulse_channel_ones_complement(self):
        """Test that Pulse1 uses ones complement"""
        channel1 = PulseChannel(0)  # Pulse1
        channel2 = PulseChannel(1)  # Pulse2
        
        assert channel1.ones_complement == True
        assert channel2.ones_complement == False

class TestTriangleChannel:
    def test_triangle_channel_initialization(self):
        """Test that TriangleChannel initializes correctly"""
        channel = TriangleChannel()
        assert channel.enabled == False
        assert channel.linear_counter == 0
        assert channel.length_counter == 0
    
    def test_triangle_channel_linear_counter(self):
        """Test TriangleChannel linear counter implementation"""
        channel = TriangleChannel()
        
        # Set up linear counter
        channel.linear_counter_load = 100
        channel.length_counter_halt = True
        
        # Reload linear counter
        channel.linear_counter_reload = True
        channel.update_linear_counter()
        assert channel.linear_counter == 100
        
        # Verify reload flag is not cleared when length_counter_halt is True
        assert channel.linear_counter_reload == True
        
        # Set length_counter_halt to False
        channel.length_counter_halt = False
        channel.update_linear_counter()
        assert channel.linear_counter_reload == False
    
    def test_triangle_channel_linear_counter_control(self):
        """Test TriangleChannel linear counter control flag"""
        channel = TriangleChannel()
        
        # Write to register 0 ($4008)
        channel.write_register(0, 0x80)  # Set bit 7
        
        # Both length_counter_halt and linear_counter_control should be set
        assert channel.length_counter_halt == True
        assert channel.linear_counter_control == True
    
    def test_triangle_channel_reload_flag(self):
        """Test TriangleChannel reload flag on register write"""
        channel = TriangleChannel()
        
        # Write to register 3 ($400B) should set reload flag
        channel.write_register(3, 0x00)
        assert channel.linear_counter_reload == True

class TestNoiseChannel:
    def test_noise_channel_initialization(self):
        """Test that NoiseChannel initializes correctly"""
        channel = NoiseChannel()
        assert channel.enabled == False
        assert channel.shift_register == 1
        assert channel.length_counter == 0
    
    def test_noise_channel_shift_register(self):
        """Test NoiseChannel shift register implementation"""
        channel = NoiseChannel()
        
        # Set up for long mode
        channel.mode_flag = False
        channel.shift_register = 1
        
        # Clock the noise generator
        channel.clock()
        
        # Verify shift register has changed
        assert channel.shift_register != 1
    
    def test_noise_channel_muting(self):
        """Test NoiseChannel muting when bit 0 is set"""
        channel = NoiseChannel()
        channel.enabled = True
        channel.length_counter = 10
        
        # Set bit 0
        channel.shift_register = 0x01
        
        # Output should be muted
        assert channel.output() == 0.0
        
        # Clear bit 0
        channel.shift_register = 0x02
        
        # Output should not be muted (assuming volume > 0)
        assert channel.output() > 0.0 or channel.volume == 0

class TestDMCChannel:
    def test_dmc_channel_initialization(self):
        """Test that DMCChannel initializes correctly"""
        channel = DMCChannel()
        assert channel.enabled == False
        assert channel.length_counter == 0
        assert channel.irq_flag == False
    
    def test_dmc_channel_frequency_periods(self):
        """Test DMCChannel frequency periods"""
        channel = DMCChannel()
        
        # Verify frequency periods are set
        assert len(channel.dmc_periods) == 16
        assert channel.dmc_periods[0] == 428  # NTSC frequency
    
    def test_dmc_channel_sample_address(self):
        """Test DMCChannel sample address calculation"""
        channel = DMCChannel()
        
        # Write to register 2 ($4012)
        channel.write_register(2, 0x00)
        
        # Sample address should be 0xC000
        assert channel.sample_address == 0xC000
    
    def test_dmc_channel_sample_length(self):
        """Test DMCChannel sample length calculation"""
        channel = DMCChannel()
        
        # Write to register 3 ($4013)
        channel.write_register(3, 0x00)
        
        # Sample length should be 1 (0 * 16 + 1)
        assert channel.sample_length == 1
        
        # Write again
        channel.write_register(3, 0x01)
        
        # Sample length should be 17 (1 * 16 + 1)
        assert channel.sample_length == 17
    
    def test_dmc_channel_control(self):
        """Test DMCChannel control from APU status register"""
        channel = DMCChannel()
        
        # Enable DMC channel
        channel.control(0x10)
        
        assert channel.enabled == True
        
        # Disable DMC channel
        channel.control(0x00)
        
        assert channel.enabled == False
    
    def test_dmc_channel_irq_clear(self):
        """Test DMCChannel interrupt clearing"""
        channel = DMCChannel()
        channel.irq_flag = True
        
        # Clear interrupt
        channel.clear_interrupt()
        
        assert channel.irq_flag == False

class TestAPUIntegration:
    def test_apu_all_channels_initialized(self):
        """Test that APU initializes all channels"""
        apu = APU()
        
        assert hasattr(apu, 'pulse1')
        assert hasattr(apu, 'pulse2')
        assert hasattr(apu, 'triangle')
        assert hasattr(apu, 'noise')
        assert hasattr(apu, 'dmc')
    
    def test_apu_frame_counter_modes(self):
        """Test APU frame counter supports both modes"""
        apu = APU()
        
        # Write to frame counter register
        apu.write_register(0x4017, 0x00)  # 4-step mode
        assert apu.interrupt_inhibit == False
        
        apu.write_register(0x4017, 0x80)  # 5-step mode
        assert apu.interrupt_inhibit == True
    
    def test_apu_status_register(self):
        """Test APU status register read"""
        apu = APU()
        
        # Enable pulse1 and set length counter
        apu.write_register(0x4015, 0x01)  # Enable pulse1
        apu.pulse1.length_counter = 10  # Set length counter
        
        # Read status
        status = apu.read_register(0x4015)
        
        # Bit 0 should be set (pulse1 enabled and length counter > 0)
        assert (status & 0x01) == 1