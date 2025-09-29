import json
import re
from typing import List, Dict, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
from core.ollama_service import OllamaService, Message
from core.game_data import game_data


class SignalType(Enum):
    LEARNING_CHECKPOINT = "learning_checkpoint"
    TOPIC_COMPLETED = "topic_completed"
    ASSESSMENT_QUESTION = "assessment_question"
    ENCOURAGEMENT = "encouragement"
    DIFFICULTY_ADJUSTMENT = "difficulty_adjustment"
    OBSERVATION_PROMPT = "observation_prompt"
    REFLECTION_MOMENT = "reflection_moment"
    PRACTICE_EXERCISE = "practice_exercise"
    KNOWLEDGE_UNLOCKED = "knowledge_unlocked"


@dataclass
class ConversationSignal:
    type: SignalType
    data: Dict = field(default_factory=dict)


@dataclass
class ConversationState:
    messages: List[Message] = field(default_factory=list)
    is_active: bool = False
    is_processing: bool = False
    current_topic: Optional[str] = None
    session_count: int = 0
    completed_topics: List[str] = field(default_factory=list)
    assessment_count: int = 0
    checkpoint_count: int = 0


class Conversation:
    def __init__(self):
        self.ollama_service = OllamaService(game_data.ollama_host_url)
        self.state = ConversationState()
        self.signal_handlers: Dict[SignalType, List[Callable]] = {
            signal_type: [] for signal_type in SignalType
        }
        self.max_history = 20  # Keep last N messages for context

    def register_signal_handler(self, signal_type: SignalType, handler: Callable):
        """Register a handler for a specific signal type."""
        if signal_type in self.signal_handlers:
            self.signal_handlers[signal_type].append(handler)

    def emit_signal(self, signal: ConversationSignal):
        """Emit a signal to all registered handlers."""
        if signal.type in self.signal_handlers:
            for handler in self.signal_handlers[signal.type]:
                try:
                    handler(signal)
                except Exception as e:
                    print(f"Error in signal handler: {e}")

    def start_conversation(self, initial_message: str = None):
        """Start a new conversation."""
        self.state.is_active = True
        self.state.session_count += 1

        if initial_message:
            self.state.messages.append(Message("system", initial_message))

    def end_conversation(self):
        """End the current conversation."""
        self.state.is_active = False
        self.state.is_processing = False

    def add_user_message(self, content: str):
        """Add a user message to the conversation."""
        if not self.state.is_active:
            return

        self.state.messages.append(Message("user", content))
        self._trim_history()

    def add_assistant_message(self, content: str):
        """Add an assistant message to the conversation."""
        self.state.messages.append(Message("assistant", content))
        self._trim_history()

    def _trim_history(self):
        """Trim conversation history to prevent context overflow."""
        if len(self.state.messages) > self.max_history:
            # Keep system message if present
            system_msgs = [m for m in self.state.messages if m.role == "system"]
            other_msgs = [m for m in self.state.messages if m.role != "system"]

            # Keep most recent messages
            trimmed = system_msgs + other_msgs[-(self.max_history - len(system_msgs)):]
            self.state.messages = trimmed

    def process_response(self, response: str) -> Optional[ConversationSignal]:
        """Process LLM response and extract signal if present."""
        try:
            # Try to extract JSON from response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                data = json.loads(json_str)

                if 'signal' in data:
                    signal_data = data['signal']
                    signal_type_str = signal_data.get('type', '')

                    # Convert string to SignalType enum
                    for signal_type in SignalType:
                        if signal_type.value == signal_type_str:
                            return ConversationSignal(
                                type=signal_type,
                                data=signal_data.get('data', {})
                            )

                # Return the message content
                if 'message' in data:
                    return data['message']

        except (json.JSONDecodeError, KeyError) as e:
            # If not valid JSON or missing expected fields, treat as plain text
            pass

        return response

    def format_message_for_display(self, message: Message) -> str:
        """Format a message for display with role indicators."""
        role_colors = {
            "user": "[You]",
            "assistant": "[ML Tutor]",
            "system": "[System]"
        }

        prefix = role_colors.get(message.role, f"[{message.role}]")
        return f"{prefix} {message.content}"

    def get_conversation_history(self) -> List[str]:
        """Get formatted conversation history for display."""
        return [self.format_message_for_display(msg) for msg in self.state.messages
                if msg.role != "system"]

    def update_progress(self, signal: ConversationSignal):
        """Update progress based on signal type."""
        if signal.type == SignalType.TOPIC_COMPLETED:
            topic = signal.data.get('topic_name', '')
            if topic and topic not in self.state.completed_topics:
                self.state.completed_topics.append(topic)

        elif signal.type == SignalType.ASSESSMENT_QUESTION:
            self.state.assessment_count += 1

        elif signal.type == SignalType.LEARNING_CHECKPOINT:
            self.state.checkpoint_count += 1

    def get_progress_summary(self) -> Dict:
        """Get a summary of learning progress."""
        return {
            "sessions": self.state.session_count,
            "completed_topics": len(self.state.completed_topics),
            "assessments": self.state.assessment_count,
            "checkpoints": self.state.checkpoint_count,
            "current_topic": self.state.current_topic
        }

    async def generate_response(self, user_input: str) -> str:
        """Generate AI response for user input."""
        if self.state.is_processing:
            return "Please wait for the current response to complete."

        self.state.is_processing = True
        self.add_user_message(user_input)

        try:
            model = game_data.get_model_name()
            response_parts = []

            # Use async generator or run in executor to prevent blocking
            import asyncio
            import concurrent.futures

            def get_full_response():
                parts = []
                for chunk in self.ollama_service.chat(
                    model=model,
                    messages=self.state.messages,
                    stream=True
                ):
                    parts.append(chunk)
                return ''.join(parts)

            # Run the blocking operation in a thread pool
            loop = asyncio.get_event_loop()
            with concurrent.futures.ThreadPoolExecutor() as executor:
                full_response = await loop.run_in_executor(executor, get_full_response)

            # Process response for signals
            processed = self.process_response(full_response)

            if isinstance(processed, ConversationSignal):
                self.emit_signal(processed)
                self.update_progress(processed)
                # Extract message from signal data if available
                message = processed.data.get('message', full_response)
            else:
                message = processed if isinstance(processed, str) else full_response

            self.add_assistant_message(message)
            return message

        except Exception as e:
            error_msg = f"Error generating response: {str(e)}"
            print(error_msg)
            return error_msg
        finally:
            self.state.is_processing = False