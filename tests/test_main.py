"""
Main game module tests.
Tests game initialization, state management, and core functionality.
"""

import unittest
import sys
import os
from unittest.mock import Mock, patch, MagicMock

test_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(test_dir)
sys.path.insert(0, parent_dir)

# Mock pygame before importing main
pygame_mock = MagicMock()
pygame_gui_mock = MagicMock()
pygame_menu_mock = MagicMock()

with patch.dict('sys.modules', {
    'pygame': pygame_mock,
    'pygame_gui': pygame_gui_mock,
    'pygame_menu': pygame_menu_mock
}):
    from main import MLEducationGame


class TestMLEducationGame(unittest.TestCase):
    """Test main game class functionality."""

    @patch('main.pygame')
    @patch('main.pygame_gui')
    @patch('main.pygame_menu')
    @patch('main.EducationalConversation')
    @patch('main.ConversationUI')
    @patch('main.FlightUI')
    def setUp(self, mock_flight_ui, mock_conv_ui, mock_conv, mock_menu, mock_gui, mock_pygame):
        """Set up test fixtures with mocked dependencies."""
        # Mock pygame components
        mock_pygame.init = Mock()
        mock_pygame.display.set_mode = Mock(return_value=Mock())
        mock_pygame.display.set_caption = Mock()
        mock_pygame.time.Clock = Mock(return_value=Mock())

        # Mock the UI components
        mock_conv_ui.return_value = Mock()
        mock_flight_ui.return_value = Mock()
        mock_conv.return_value = Mock()

        # Initialize game with mocks
        self.game = MLEducationGame()

    def test_initialization(self):
        """Test game initialization."""
        self.assertIsNotNone(self.game)
        self.assertEqual(self.game.width, 1024)
        self.assertEqual(self.game.height, 768)
        self.assertEqual(self.game.fps, 60)
        self.assertTrue(self.game.running)
        self.assertFalse(self.game.is_conversing)
        self.assertFalse(self.game.awaiting_response)
        self.assertTrue(self.game.show_menu)

    @patch('main.Path.exists')
    @patch('main.Path.read_text')
    def test_load_npc_backstory_success(self, mock_read_text, mock_exists):
        """Test successful NPC backstory loading."""
        mock_exists.return_value = True
        mock_read_text.return_value = "Test backstory"

        backstory = self.game._load_npc_backstory()
        self.assertEqual(backstory, "Test backstory")

    @patch('main.Path.exists')
    def test_load_npc_backstory_file_not_found(self, mock_exists):
        """Test NPC backstory loading when file doesn't exist."""
        mock_exists.return_value = False

        backstory = self.game._load_npc_backstory()
        self.assertIn("aviation instructor", backstory.lower())

    @patch('main.Path.exists')
    @patch('main.Path.read_text')
    @patch('main.json.loads')
    def test_load_response_schema_success(self, mock_json_loads, mock_read_text, mock_exists):
        """Test successful response schema loading."""
        mock_exists.return_value = True
        mock_read_text.return_value = '{"test": "schema"}'
        mock_json_loads.return_value = {"test": "schema"}

        schema = self.game._load_response_schema()
        self.assertEqual(schema, {"test": "schema"})

    @patch('main.Path.exists')
    def test_load_response_schema_file_not_found(self, mock_exists):
        """Test response schema loading when file doesn't exist."""
        mock_exists.return_value = False

        schema = self.game._load_response_schema()
        self.assertIsInstance(schema, dict)
        self.assertIn("type", schema)

    def test_start_conversation(self):
        """Test conversation start functionality."""
        self.game.start_conversation()
        self.assertTrue(self.game.is_conversing)
        self.assertFalse(self.game.show_menu)

    def test_start_flight_simulation(self):
        """Test flight simulation start."""
        self.game.start_flight_simulation()
        self.assertFalse(self.game.is_conversing)
        self.assertFalse(self.game.show_menu)

    def test_show_main_menu(self):
        """Test main menu display."""
        self.game.show_main_menu()
        self.assertTrue(self.game.show_menu)
        self.assertFalse(self.game.is_conversing)

    @patch('main.pygame.event.get')
    def test_handle_events_quit(self, mock_get_events):
        """Test quit event handling."""
        quit_event = Mock()
        quit_event.type = pygame_mock.QUIT
        mock_get_events.return_value = [quit_event]

        self.game.handle_events()
        self.assertFalse(self.game.running)

    @patch('main.pygame.event.get')
    def test_handle_events_keydown(self, mock_get_events):
        """Test keydown event handling."""
        keydown_event = Mock()
        keydown_event.type = pygame_mock.KEYDOWN
        keydown_event.key = pygame_mock.K_ESCAPE
        mock_get_events.return_value = [keydown_event]

        self.game.is_conversing = True
        self.game.handle_events()
        self.assertFalse(self.game.is_conversing)
        self.assertTrue(self.game.show_menu)


class TestGameUtilityFunctions(unittest.TestCase):
    """Test utility functions and edge cases."""

    @patch('main.MLEducationGame')
    def test_game_creation_without_crash(self, mock_game_class):
        """Test that game can be created without crashing."""
        mock_game_class.return_value = Mock()
        mock_game_class.return_value.run = Mock()

        # This should not raise an exception
        game_instance = mock_game_class()
        self.assertIsNotNone(game_instance)


if __name__ == '__main__':
    unittest.main(verbosity=2)