from tmr.pomodoro import App, SessionType
from unittest.mock import patch, MagicMock
import pytest

class TestApp:
    def test_init(self):
        app = App(25, 5, 15, 4)
        assert app.work_time == 25
        assert app.break_time == 5
        assert app.long_break_time == 15
        assert app.cycles == 4
        assert app.current_session_type == SessionType.WORK
        
    def test_cycle_generator(self):
        """Test cycle logic with shortened time using generator."""
        app = App(1, 1, 1, 2)
        app.SECs_PER_MIN = 0.01 # Speed up time
        
        # Iterate through the generator
        gen = app.cycle_generator(0, 1)
        
        first_remaining, total = next(gen)
        assert total > 0
        assert first_remaining <= total
        
        last_remaining = 0
        for remaining, _ in gen:
            last_remaining = remaining
            
        assert last_remaining == 0

    def test_session_type_enum(self):
        assert SessionType.WORK.name == "WORK"
        assert SessionType.BREAK.name == "BREAK"
        
    def test_notify(self):
        app = App(25, 5, 15, 4)
        with patch('tmr.pomodoro.subprocess.run') as mock_run:
            with patch('tmr.pomodoro.shutil.which', return_value=True):
                app.notify("Test", "Msg")
                mock_run.assert_called_once()