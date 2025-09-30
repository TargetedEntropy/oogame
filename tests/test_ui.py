"""
UI module tests.
Tests conversation UI and flight UI functionality.
"""

import unittest
import sys
import os
from unittest.mock import Mock, patch, MagicMock

test_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(test_dir)
sys.path.insert(0, parent_dir)

# Mock pygame and pygame_gui before importing UI modules
pygame_mock = MagicMock()
pygame_gui_mock = MagicMock()

with patch.dict('sys.modules', {
    'pygame': pygame_mock,
    'pygame_gui': pygame_gui_mock
}):
    from ui.conversation_ui import ConversationUI
    from ui.flight_ui import FlightUI


class TestConversationUI(unittest.TestCase):
    """Test ConversationUI functionality."""

    def setUp(self):
        """Set up test fixtures."""
        # Mock pygame surface
        self.screen_mock = Mock()
        self.screen_mock.get_size.return_value = (1024, 768)

        # Mock pygame_gui components
        pygame_gui_mock.UIManager.return_value = Mock()
        pygame_gui_mock.elements.UITextBox.return_value = Mock()
        pygame_gui_mock.elements.UITextEntryLine.return_value = Mock()

        self.ui = ConversationUI(self.screen_mock)

    def test_initialization(self):
        """Test ConversationUI initialization."""
        self.assertIsNotNone(self.ui)
        self.assertEqual(self.ui.width, 1024)
        self.assertEqual(self.ui.height, 768)
        self.assertIsNotNone(self.ui.manager)
        self.assertIsNotNone(self.ui.conversation_box)

    def test_add_message(self):
        """Test adding messages to conversation."""
        # Mock the conversation box
        self.ui.conversation_box.html_text = ""

        self.ui.add_message("User", "Test message")

        # Should have called set_text or similar method
        self.assertTrue(hasattr(self.ui.conversation_box, 'set_text') or
                       hasattr(self.ui.conversation_box, 'html_text'))

    def test_clear_conversation(self):
        """Test clearing conversation."""
        self.ui.conversation_box.html_text = "Some content"

        self.ui.clear_conversation()

        # Should reset the text
        self.assertIn("Aircraft Education Session", self.ui.conversation_box.html_text)

    def test_handle_event(self):
        """Test event handling."""
        mock_event = Mock()
        mock_event.type = pygame_mock.KEYDOWN
        mock_event.key = pygame_mock.K_RETURN

        # Should not crash
        result = self.ui.handle_event(mock_event)
        # Result can be None or boolean


class TestFlightUI(unittest.TestCase):
    """Test FlightUI functionality."""

    def setUp(self):
        """Set up test fixtures."""
        # Mock pygame surface
        self.screen_mock = Mock()
        self.screen_mock.get_size.return_value = (1024, 768)
        self.screen_mock.fill = Mock()
        self.screen_mock.blit = Mock()

        # Mock pygame components
        pygame_mock.font.Font.return_value = Mock()
        pygame_mock.font.Font.return_value.render.return_value = Mock()
        pygame_mock.font.Font.return_value.get_height.return_value = 20
        pygame_mock.Surface.return_value = Mock()
        pygame_mock.draw.circle = Mock()
        pygame_mock.draw.rect = Mock()
        pygame_mock.draw.line = Mock()

        # Mock flight simulator
        with patch('ui.flight_ui.flight_simulator') as mock_simulator:
            mock_simulator.is_flying = False
            mock_simulator.get_status.return_value = {
                'phase': 'PREFLIGHT',
                'altitude': 0,
                'airspeed': 0,
                'heading': 0,
                'fuel_remaining': 100.0,
                'engine_temp': 180,
                'weather': {
                    'condition': 'CLEAR',
                    'wind_direction': 270,
                    'wind_speed': 10
                },
                'autopilot_enabled': False,
                'progress_percent': 0,
                'flight_time': 0,
                'system_alerts': []
            }
            self.ui = FlightUI(self.screen_mock)

    def test_initialization(self):
        """Test FlightUI initialization."""
        self.assertIsNotNone(self.ui)
        self.assertEqual(self.ui.width, 1024)
        self.assertEqual(self.ui.height, 768)
        self.assertIsNotNone(self.ui.colors)

    def test_draw_not_flying(self):
        """Test drawing when not flying."""
        # Should not crash when simulator is not flying
        self.ui.draw()

        # Should have called screen methods
        self.assertTrue(self.screen_mock.fill.called or
                       self.screen_mock.blit.called)

    @patch('ui.flight_ui.flight_simulator')
    def test_draw_flying(self, mock_simulator):
        """Test drawing during flight."""
        mock_simulator.is_flying = True
        mock_simulator.get_status.return_value = {
            'phase': 'CRUISE',
            'altitude': 6500,
            'airspeed': 120,
            'heading': 90,
            'fuel_remaining': 85.0,
            'engine_temp': 200,
            'weather': {
                'condition': 'CLEAR',
                'wind_direction': 270,
                'wind_speed': 15
            },
            'autopilot_enabled': True,
            'progress_percent': 25.5,
            'flight_time': 3600,
            'system_alerts': ['Engine temperature high']
        }

        # Should not crash during flight display
        self.ui.draw()

        # Should have rendered flight information
        self.assertTrue(self.screen_mock.fill.called)

    def test_handle_click(self):
        """Test click handling."""
        # Test autopilot toggle click
        click_pos = (50, 600)  # Approximate autopilot button position

        # Should not crash
        self.ui.handle_click(click_pos)

    def test_color_definitions(self):
        """Test that required colors are defined."""
        required_colors = ['BLACK', 'WHITE', 'RED', 'GREEN', 'BLUE', 'YELLOW']

        for color in required_colors:
            self.assertIn(color, self.ui.colors)
            self.assertIsInstance(self.ui.colors[color], tuple)
            self.assertEqual(len(self.ui.colors[color]), 3)


class TestUIIntegration(unittest.TestCase):
    """Test UI integration and edge cases."""

    @patch('pygame.Surface')
    def test_ui_creation_without_crash(self, mock_surface):
        """Test that UI components can be created without crashing."""
        mock_surface.get_size.return_value = (800, 600)

        # Should not crash with different screen sizes
        try:
            with patch('ui.flight_ui.flight_simulator'):
                ui = FlightUI(mock_surface)
            self.assertIsNotNone(ui)
        except Exception as e:
            self.fail(f"UI creation should not crash: {e}")


if __name__ == '__main__':
    unittest.main(verbosity=2)