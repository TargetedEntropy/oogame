"""
Conversation module tests.
Tests conversation management, signal handling, and educational features.
"""

import unittest
import sys
import os
from unittest.mock import Mock, patch, MagicMock

test_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(test_dir)
sys.path.insert(0, parent_dir)

from core.conversation import (
    SignalType, ConversationSignal, ConversationState, Conversation
)
from core.educational_conversation import EducationalConversation
from core.ollama_service import Message


class TestSignalType(unittest.TestCase):
    """Test SignalType enum."""

    def test_signal_type_values(self):
        """Test SignalType enum values."""
        self.assertEqual(SignalType.LEARNING_CHECKPOINT.value, "learning_checkpoint")
        self.assertEqual(SignalType.TOPIC_COMPLETED.value, "topic_completed")
        self.assertEqual(SignalType.ASSESSMENT_QUESTION.value, "assessment_question")


class TestConversationSignal(unittest.TestCase):
    """Test ConversationSignal dataclass."""

    def test_signal_creation(self):
        """Test ConversationSignal creation."""
        signal = ConversationSignal(
            type=SignalType.LEARNING_CHECKPOINT,
            data={"topic": "navigation", "progress": 50}
        )

        self.assertEqual(signal.type, SignalType.LEARNING_CHECKPOINT)
        self.assertEqual(signal.data["topic"], "navigation")
        self.assertEqual(signal.data["progress"], 50)

    def test_signal_default_data(self):
        """Test ConversationSignal with default data."""
        signal = ConversationSignal(type=SignalType.ENCOURAGEMENT)

        self.assertEqual(signal.type, SignalType.ENCOURAGEMENT)
        self.assertEqual(signal.data, {})


class TestConversationState(unittest.TestCase):
    """Test ConversationState dataclass."""

    def test_state_creation(self):
        """Test ConversationState creation."""
        state = ConversationState()

        self.assertEqual(state.messages, [])
        self.assertFalse(state.is_active)
        self.assertFalse(state.is_processing)
        self.assertIsNone(state.current_topic)
        self.assertEqual(state.session_count, 0)

    def test_state_with_data(self):
        """Test ConversationState with initial data."""
        messages = [Message("user", "Hello")]
        state = ConversationState(
            messages=messages,
            is_active=True,
            current_topic="navigation",
            session_count=3
        )

        self.assertEqual(state.messages, messages)
        self.assertTrue(state.is_active)
        self.assertEqual(state.current_topic, "navigation")
        self.assertEqual(state.session_count, 3)


class TestConversation(unittest.TestCase):
    """Test Conversation class."""

    @patch('core.conversation.OllamaService')
    @patch('core.conversation.game_data')
    def setUp(self, mock_game_data, mock_ollama_service):
        """Set up test fixtures."""
        mock_game_data.ollama_host_url = "http://localhost:11434"
        mock_ollama_service.return_value = Mock()

        self.conversation = Conversation()

    def test_initialization(self):
        """Test Conversation initialization."""
        self.assertIsNotNone(self.conversation.ollama_service)
        self.assertIsInstance(self.conversation.state, ConversationState)
        self.assertEqual(self.conversation.max_history, 20)
        self.assertEqual(len(self.conversation.signal_handlers), len(SignalType))

    def test_register_signal_handler(self):
        """Test signal handler registration."""
        handler = Mock()
        self.conversation.register_signal_handler(SignalType.LEARNING_CHECKPOINT, handler)

        self.assertIn(handler, self.conversation.signal_handlers[SignalType.LEARNING_CHECKPOINT])

    def test_emit_signal(self):
        """Test signal emission."""
        handler = Mock()
        self.conversation.register_signal_handler(SignalType.ENCOURAGEMENT, handler)

        signal = ConversationSignal(SignalType.ENCOURAGEMENT, {"message": "Great job!"})
        self.conversation._emit_signal(signal)

        handler.assert_called_once_with(signal)

    def test_start_session(self):
        """Test session start."""
        self.conversation.start_session()

        self.assertTrue(self.conversation.state.is_active)
        self.assertEqual(self.conversation.state.session_count, 1)

    def test_end_session(self):
        """Test session end."""
        self.conversation.state.is_active = True
        self.conversation.state.messages = [Message("user", "test")]

        self.conversation.end_session()

        self.assertFalse(self.conversation.state.is_active)
        self.assertFalse(self.conversation.state.is_processing)

    def test_add_message(self):
        """Test message addition."""
        message = Message("user", "Test message")
        self.conversation.add_message(message)

        self.assertIn(message, self.conversation.state.messages)

    def test_get_conversation_history(self):
        """Test conversation history retrieval."""
        messages = [Message("user", f"Message {i}") for i in range(25)]
        self.conversation.state.messages = messages

        history = self.conversation.get_conversation_history()

        # Should limit to max_history
        self.assertEqual(len(history), self.conversation.max_history)


class TestEducationalConversation(unittest.TestCase):
    """Test EducationalConversation class."""

    @patch('core.educational_conversation.OllamaService')
    @patch('core.educational_conversation.game_data')
    def setUp(self, mock_game_data, mock_ollama_service):
        """Set up test fixtures."""
        mock_game_data.ollama_host_url = "http://localhost:11434"
        mock_ollama_service.return_value = Mock()

        self.educational_conversation = EducationalConversation()

    def test_initialization(self):
        """Test EducationalConversation initialization."""
        self.assertIsNotNone(self.educational_conversation)
        self.assertIsInstance(self.educational_conversation.state, ConversationState)

    @patch('core.educational_conversation.asyncio.create_task')
    def test_send_message_async(self, mock_create_task):
        """Test asynchronous message sending."""
        mock_create_task.return_value = Mock()

        self.educational_conversation.send_message("Test question")

        mock_create_task.assert_called_once()
        self.assertTrue(self.educational_conversation.state.is_processing)

    def test_set_response_schema(self):
        """Test response schema setting."""
        schema = {"type": "object", "properties": {"response": {"type": "string"}}}
        self.educational_conversation.set_response_schema(schema)

        # Should not crash
        self.assertIsNotNone(self.educational_conversation)

    def test_signal_detection(self):
        """Test signal detection in responses."""
        response_with_signal = {
            "response": "Great work!",
            "signals": [{"type": "encouragement", "data": {"level": "high"}}]
        }

        signals = self.educational_conversation._detect_signals(response_with_signal)

        self.assertEqual(len(signals), 1)
        self.assertEqual(signals[0].type.value, "encouragement")


class TestConversationIntegration(unittest.TestCase):
    """Test conversation integration and edge cases."""

    @patch('core.conversation.OllamaService')
    @patch('core.conversation.game_data')
    def test_conversation_creation_without_crash(self, mock_game_data, mock_ollama_service):
        """Test that conversation can be created without crashing."""
        mock_game_data.ollama_host_url = "http://localhost:11434"
        mock_ollama_service.return_value = Mock()

        try:
            conversation = Conversation()
            self.assertIsNotNone(conversation)
        except Exception as e:
            self.fail(f"Conversation creation should not crash: {e}")

    def test_message_type_validation(self):
        """Test Message type validation."""
        message = Message("user", "Test content")

        self.assertEqual(message.role, "user")
        self.assertEqual(message.content, "Test content")


if __name__ == '__main__':
    unittest.main(verbosity=2)