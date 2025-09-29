#!/usr/bin/env python3
import pygame
import asyncio
import sys
import json
from pathlib import Path
from core.game_data import game_data, MLSubject
from core.educational_conversation import EducationalConversation
from core.conversation import SignalType
from core.ollama_service import Message
from ui.conversation_ui import ConversationUI


class MLEducationGame:
    def __init__(self):
        pygame.init()

        # Window setup
        self.width = 1024
        self.height = 768
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("ML Education with Local LLM")

        # Clock for FPS control
        self.clock = pygame.time.Clock()
        self.fps = 60
        self.running = True

        # Game components
        self.conversation = EducationalConversation()
        self.ui = ConversationUI(self.screen)

        # Load NPC backstory
        self.npc_backstory = self._load_npc_backstory()

        # Load response schema
        self.response_schema = self._load_response_schema()

        # State
        self.is_conversing = False
        self.awaiting_response = False

        # Register signal handlers
        self._register_signal_handlers()

    def _load_npc_backstory(self) -> str:
        """Load NPC backstory from file."""
        backstory_path = Path("data/npc_backstory.txt")
        if backstory_path.exists():
            return backstory_path.read_text()
        return "You are an ML educator helping students learn machine learning concepts."

    def _load_response_schema(self) -> dict:
        """Load response schema from file."""
        schema_path = Path("data/response_schema.json")
        if schema_path.exists():
            return json.loads(schema_path.read_text())
        return {}

    def _register_signal_handlers(self):
        """Register handlers for conversation signals."""
        self.conversation.register_signal_handler(
            SignalType.LEARNING_CHECKPOINT,
            self._handle_checkpoint
        )
        self.conversation.register_signal_handler(
            SignalType.TOPIC_COMPLETED,
            self._handle_topic_completed
        )
        self.conversation.register_signal_handler(
            SignalType.ASSESSMENT_QUESTION,
            self._handle_assessment
        )
        self.conversation.register_signal_handler(
            SignalType.ENCOURAGEMENT,
            self._handle_encouragement
        )

    def _handle_checkpoint(self, signal):
        """Handle learning checkpoint signal."""
        print(f"Checkpoint reached: {signal.data.get('learning_objective', 'Unknown')}")
        self.ui.add_message("system", f"🎯 Checkpoint: {signal.data.get('learning_objective', 'Progress saved')}")

    def _handle_topic_completed(self, signal):
        """Handle topic completion signal."""
        topic = signal.data.get('topic_name', 'Unknown topic')
        print(f"Topic completed: {topic}")
        self.ui.add_message("system", f"✅ Topic Completed: {topic}")

    def _handle_assessment(self, signal):
        """Handle assessment question signal."""
        print(f"Assessment: {signal.data.get('assessment_criteria', 'Evaluation in progress')}")
        self.ui.add_message("system", "📝 Assessment in progress...")

    def _handle_encouragement(self, signal):
        """Handle encouragement signal."""
        encouragement_type = signal.data.get('encouragement_type', 'progress_acknowledgment')
        messages = {
            'milestone_celebration': "🎉 Milestone achieved! Great work!",
            'progress_acknowledgment': "👍 Good progress!",
            'effort_recognition': "💪 Your effort is paying off!",
            'breakthrough_moment': "💡 Breakthrough moment!",
            'persistence_praise': "🌟 Your persistence is admirable!"
        }
        self.ui.add_message("system", messages.get(encouragement_type, "Keep going!"))

    def start_conversation(self):
        """Start a new educational conversation."""
        if not self.is_conversing:
            # Prepare system prompt with NPC backstory
            system_prompt = f"{self.npc_backstory}\n\n{self.conversation.get_subject_prompt()}"

            # Configure conversation with response schema
            self.conversation.state.messages.append(
                Message("system", system_prompt)
            )

            # Start the conversation
            self.conversation.start_educational_session()
            self.is_conversing = True

            # Display initial greeting
            greeting = self.conversation.get_initial_greeting()
            self.ui.add_message("assistant", greeting)

            # Update progress display
            self._update_progress_display()

    def _update_progress_display(self):
        """Update the progress display in UI."""
        progress = self.conversation.get_progress_summary()
        self.ui.update_progress({
            'sessions': progress['sessions'],
            'topics': progress['completed_topics'],
            'assessments': progress['assessments'],
            'checkpoints': progress['checkpoints']
        })

    async def process_user_input(self, user_input: str):
        """Process user input asynchronously."""
        if self.awaiting_response:
            return

        self.awaiting_response = True
        self.ui.add_message("user", user_input)

        try:
            # Generate response
            response = await self.conversation.process_educational_response(user_input)

            # Display response
            self.ui.add_message("assistant", response)

            # Update progress
            self._update_progress_display()

        except Exception as e:
            error_msg = f"Error: {str(e)}"
            self.ui.add_message("system", error_msg)
            print(error_msg)

        finally:
            self.awaiting_response = False

    def handle_events(self):
        """Handle pygame events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.is_conversing:
                        self.is_conversing = False
                        self.conversation.end_conversation()
                    else:
                        self.running = False

                elif event.key == pygame.K_F1:
                    # Show help
                    self.show_help()

                elif event.key == pygame.K_TAB:
                    # Switch subjects
                    self.switch_subject()

                elif event.key == pygame.K_SPACE and not self.is_conversing:
                    # Start conversation from menu
                    self.start_conversation()

            # Pass event to UI if conversing
            if self.is_conversing:
                user_input = self.ui.handle_event(event)
                if user_input and not self.awaiting_response:
                    # Create task for async processing
                    asyncio.create_task(self.process_user_input(user_input))

    def show_help(self):
        """Display help information."""
        help_text = """
Controls:
- Type your message and press Enter to send
- ESC: Exit conversation / Quit
- TAB: Switch ML topics
- F1: Show this help
- Arrow keys: Scroll conversation
- Page Up/Down: Fast scroll
        """
        self.ui.add_message("system", help_text)

    def switch_subject(self):
        """Switch to next ML subject."""
        current = game_data.educational_subject
        subjects = list(MLSubject)
        current_idx = subjects.index(current)
        next_idx = (current_idx + 1) % len(subjects)
        game_data.educational_subject = subjects[next_idx]
        game_data.save_settings()

        subject_name = game_data.get_subject_name()
        self.ui.add_message("system", f"Switched to: {subject_name}")

        # Restart conversation with new subject
        if self.is_conversing:
            self.conversation.end_conversation()
            self.conversation = EducationalConversation()
            self._register_signal_handlers()
            self.start_conversation()

    def draw_menu(self):
        """Draw the main menu."""
        self.screen.fill((30, 30, 40))

        font_large = pygame.font.Font(None, 48)
        font_medium = pygame.font.Font(None, 32)
        font_small = pygame.font.Font(None, 24)

        # Title
        title = font_large.render("ML Education with Local LLM", True, (220, 220, 230))
        title_rect = title.get_rect(center=(self.width // 2, 100))
        self.screen.blit(title, title_rect)

        # Current subject
        subject_text = f"Current Topic: {game_data.get_subject_name()}"
        subject = font_medium.render(subject_text, True, (180, 180, 200))
        subject_rect = subject.get_rect(center=(self.width // 2, 200))
        self.screen.blit(subject, subject_rect)

        # Instructions
        instructions = [
            "Press SPACE to start learning",
            "Press TAB to change topic",
            "Press S for settings",
            "Press ESC to quit"
        ]

        y = 300
        for instruction in instructions:
            text = font_small.render(instruction, True, (160, 160, 180))
            text_rect = text.get_rect(center=(self.width // 2, y))
            self.screen.blit(text, text_rect)
            y += 40

        # Ollama status
        if self.conversation.ollama_service.is_available():
            status_text = f"✓ Ollama connected at {game_data.ollama_host_url}"
            status_color = (100, 250, 100)
        else:
            status_text = f"✗ Ollama not available at {game_data.ollama_host_url}"
            status_color = (250, 100, 100)

        status = font_small.render(status_text, True, status_color)
        status_rect = status.get_rect(center=(self.width // 2, self.height - 50))
        self.screen.blit(status, status_rect)

    def update(self, dt):
        """Update game state."""
        if self.is_conversing:
            self.ui.update(dt)

    def draw(self):
        """Draw the game."""
        if self.is_conversing:
            self.ui.draw()
        else:
            self.draw_menu()

        pygame.display.flip()

    async def run(self):
        """Main game loop."""
        # Check for Ollama on startup
        if not self.conversation.ollama_service.is_available():
            print(f"Warning: Ollama not available at {game_data.ollama_host_url}")
            print("Please ensure Ollama is running and the gemma3n model is installed.")
            print("Run: ollama pull gemma3n:e4b")

        while self.running:
            dt = self.clock.tick(self.fps) / 1000.0

            self.handle_events()
            self.update(dt)
            self.draw()

            # Allow async tasks to run
            await asyncio.sleep(0)

        pygame.quit()
        game_data.save_settings()


async def main():
    """Entry point."""
    game = MLEducationGame()
    await game.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nGame interrupted by user")
        sys.exit(0)