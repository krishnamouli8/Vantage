"""
Unit tests for timing utilities.
"""

import pytest
import time
from vantage_agent.utils.timing import Timer


class TestTimer:
    """Tests for Timer class."""
    
    def test_timer_basic(self):
        """Test basic timer functionality."""
        timer = Timer()
        timer.start()
        time.sleep(0.1)  # Sleep for 100ms
        elapsed = timer.stop()
        
        # Should be approximately 100ms (with some tolerance)
        assert 90 <= elapsed <= 150
    
    def test_timer_context_manager(self):
        """Test timer as context manager."""
        with Timer() as timer:
            time.sleep(0.05)  # Sleep for 50ms
        
        # Should be approximately 50ms
        assert 40 <= timer.elapsed_ms <= 100
    
    def test_elapsed_ms_property(self):
        """Test elapsed_ms property."""
        timer = Timer()
        timer.start()
        time.sleep(0.02)  # Sleep for 20ms
        
        # Check elapsed time without stopping
        elapsed = timer.elapsed_ms
        assert 15 <= elapsed <= 50
        
        # Stop and check again
        timer.stop()
        final_elapsed = timer.elapsed_ms
        assert final_elapsed >= elapsed
    
    def test_elapsed_seconds_property(self):
        """Test elapsed_seconds property."""
        timer = Timer()
        timer.start()
        time.sleep(0.1)  # Sleep for 100ms
        timer.stop()
        
        elapsed_seconds = timer.elapsed_seconds
        # Should be approximately 0.1 seconds
        assert 0.09 <= elapsed_seconds <= 0.15
    
    def test_timer_not_started(self):
        """Test timer behavior when not started."""
        timer = Timer()
        
        with pytest.raises(RuntimeError, match="Timer was not started"):
            timer.stop()
    
    def test_timer_reset(self):
        """Test resetting the timer."""
        timer = Timer()
        timer.start()
        time.sleep(0.01)
        timer.stop()
        
        # Reset
        timer.reset()
        
        # elapsed_ms should be 0 after reset
        assert timer.elapsed_ms == 0.0
    
    def test_multiple_measurements(self):
        """Test taking multiple measurements."""
        timer = Timer()
        
        # First measurement
        timer.start()
        time.sleep(0.01)
        elapsed1 = timer.stop()
        
        # Second measurement
        timer.start()
        time.sleep(0.02)
        elapsed2 = timer.stop()
        
        # Second measurement should be longer
        assert elapsed2 > elapsed1
