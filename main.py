#!/usr/bin/env python3
import pygame
import pygame_gui
import pygame_menu
import asyncio
import sys
import json
from pathlib import Path
from typing import Optional

from core.game_data import game_data, AircraftType
from core.educational_conversation import EducationalConversation
from core.conversation import SignalType
from core.ollama_service import Message
from core.npc_system import npc_manager
from core.flight_simulator import flight_simulator
from ui.conversation_ui import ConversationUI
from ui.flight_ui import FlightUI


class MLEducationGame:
    def __init__(self):
        pygame.init()

        # Window setup
        self.width = 1024
        self.height = 768
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Aircraft Education with Local LLM")

        # Clock for FPS control
        self.clock = pygame.time.Clock()
        self.fps = 60
        self.running = True

        # Game components
        self.conversation = EducationalConversation()
        self.ui = ConversationUI(self.screen)
        self.flight_ui = FlightUI(self.screen)

        # Load NPC backstory
        self.npc_backstory = self._load_npc_backstory()

        # Load response schema
        self.response_schema = self._load_response_schema()

        # State
        self.is_conversing = False
        self.awaiting_response = False
        self.show_menu = True
        self.current_submenu = None  # Track which submenu is active
        self.is_flying = False  # Track flight simulation mode

        # Register signal handlers
        self._register_signal_handlers()

        # Check Ollama status before creating menu
        self.ollama_status = self._check_ollama_status()

        # Create main menu with pygame-menu
        self._create_menu()

    def _create_menu(self):
        """Create the main menu using pygame-menu."""
        # Custom theme based on our color scheme
        custom_theme = pygame_menu.themes.THEME_DARK.copy()
        custom_theme.background_color = (30, 30, 40)
        custom_theme.title_background_color = (45, 45, 60)
        custom_theme.widget_selection_color = (100, 150, 250)
        custom_theme.widget_font_color = (220, 220, 230)
        custom_theme.widget_font_size = 24
        custom_theme.title_font_size = 36

        # Create main menu
        self.menu = pygame_menu.Menu(
            title='Aircraft Education with Local LLM',
            width=self.width,
            height=self.height,
            theme=custom_theme
        )

        # Add menu items
        self.menu.add.label(f'Current Topic: {game_data.get_subject_name()}',
                           font_size=20,
                           font_color=(180, 180, 200))
        self.menu.add.vertical_margin(30)

        # Subject selector
        subjects = [(subject.name.replace('_', ' ').title(), subject)
                   for subject in AircraftType]
        self.subject_selector = self.menu.add.selector(
            'Select Topic: ',
            subjects,
            default=int(game_data.educational_subject),
            onchange=self._on_subject_change
        )

        self.menu.add.vertical_margin(20)

        # Player name input
        self.menu.add.text_input(
            'Your Name: ',
            default=game_data.player_name,
            onchange=self._on_name_change,
            maxchar=20
        )

        # Pronoun selector
        pronouns = [
            ('they/them', 'they/them'),
            ('she/her', 'she/her'),
            ('he/him', 'he/him')
        ]
        pronoun_index = next((i for i, (_, v) in enumerate(pronouns)
                             if v == game_data.player_pronouns), 0)
        self.menu.add.selector(
            'Pronouns: ',
            pronouns,
            default=pronoun_index,
            onchange=self._on_pronoun_change
        )

        self.menu.add.vertical_margin(30)

        # Action buttons
        self.menu.add.button('Start Learning', self._start_conversation_from_menu)
        self.menu.add.button('Travel to Airport', self._show_travel_menu)
        self.menu.add.button('Settings', self._show_settings)
        self.menu.add.button('Help', self._show_help_menu)
        self.menu.add.button('Quit', pygame_menu.events.EXIT)

        self.menu.add.vertical_margin(30)

        # Ollama status
        status_color = (100, 250, 100) if self.ollama_status else (250, 100, 100)
        status_text = '✓ Ollama Connected' if self.ollama_status else '✗ Ollama Not Available'
        self.menu.add.label(
            status_text,
            font_size=18,
            font_color=status_color
        )
        self.menu.add.label(
            f'Host: {game_data.ollama_host_url}',
            font_size=14,
            font_color=(160, 160, 180)
        )

        # Create settings menu
        self._create_settings_menu()

        # Create help menu
        self._create_help_menu()

        # Create travel menu
        self._create_travel_menu()

    def _create_settings_menu(self):
        """Create the settings menu."""
        # This method now does nothing - menu is created fresh each time
        pass

    def _create_help_menu(self):
        """Create the help menu."""
        # This method now does nothing - menu is created fresh each time
        pass

    def _create_travel_menu(self):
        """Create the travel menu for location selection."""
        # This method now does nothing - menu is created fresh each time
        pass

    def _travel_to_location(self, location_id: str):
        """Travel to selected location."""
        # Check if already at this location
        if npc_manager.current_location and npc_manager.current_location.id == location_id:
            self._show_message("Already at this location!")
            return

        # Get destination location
        destination = next((loc for loc in npc_manager.locations if loc.id == location_id), None)
        if not destination:
            self._show_message("Location not found!")
            return

        # Start flight if we have a current location
        if npc_manager.current_location:
            # Show flight planning dialog
            self._show_flight_planning_dialog(npc_manager.current_location, destination)
        else:
            # No current location, teleport directly
            location, npc = npc_manager.travel_to_location(location_id)
            if location and npc:
                self._show_message(f"Arrived at {location.name}! Met {npc.name}")
                self.current_submenu = None
                self.show_menu = False
                self.menu.disable()
                self.start_conversation()
            else:
                self._show_message("Travel failed - location not found")

    def _on_subject_change(self, value, subject):
        """Handle subject change in menu."""
        game_data.educational_subject = subject
        game_data.save_settings()

    def _on_name_change(self, value):
        """Handle name change in menu."""
        game_data.player_name = value
        game_data.save_settings()

    def _on_pronoun_change(self, value, pronouns):
        """Handle pronoun change in menu."""
        game_data.player_pronouns = pronouns
        game_data.save_settings()

    def _on_ollama_host_change(self, value):
        """Handle Ollama host URL change."""
        game_data.ollama_host_url = value

    def _on_model_change(self, value, use_latest):
        """Handle model selection change."""
        game_data.use_gemma3n_latest = use_latest

    def _save_settings(self):
        """Save settings and update connection."""
        game_data.save_settings()
        self.conversation.ollama_service.host_url = game_data.ollama_host_url
        self.ollama_status = self._check_ollama_status()
        self._update_menu_status()

    def _test_ollama_connection(self):
        """Test Ollama connection and show result."""
        self.conversation.ollama_service.host_url = game_data.ollama_host_url
        if self.conversation.ollama_service.is_available():
            models = self.conversation.ollama_service.list_models()
            if models:
                model_list = ', '.join(models[:5])  # Show first 5 models
                self._show_message(f"Connected! Models: {model_list}")
            else:
                self._show_message("Connected but no models found!")
        else:
            self._show_message("Connection failed! Check Ollama is running.")

    def _show_message(self, message: str):
        """Show a temporary message (would need a toast/notification system)."""
        print(message)  # For now, just print

    def _check_ollama_status(self) -> bool:
        """Check if Ollama is available."""
        return self.conversation.ollama_service.is_available()

    def _update_menu_status(self):
        """Update Ollama status in menu."""
        # This would need menu widget update support
        pass

    def _start_conversation_from_menu(self):
        """Start conversation from menu."""
        self.show_menu = False
        self.menu.disable()
        self.start_conversation()

    def _show_settings(self):
        """Show settings menu."""
        # Create a completely fresh menu each time to avoid state issues
        custom_theme = self.menu.get_theme().copy()

        self.settings_menu = pygame_menu.Menu(
            title='Settings',
            width=self.width,
            height=self.height,
            theme=custom_theme
        )

        # Ollama host URL input
        self.settings_menu.add.text_input(
            'Ollama Host: ',
            default=game_data.ollama_host_url,
            onchange=self._on_ollama_host_change,
            maxchar=50
        )

        # Model selection
        models = [
            ('Gemma 3n (e4b) - Larger', True),
            ('Gemma 3n (e2b) - Smaller', False)
        ]
        model_index = 0 if game_data.use_gemma3n_latest else 1
        self.settings_menu.add.selector(
            'Model: ',
            models,
            default=model_index,
            onchange=self._on_model_change
        )

        self.settings_menu.add.vertical_margin(30)

        # Save and back buttons
        self.settings_menu.add.button('Test Connection', self._test_ollama_connection)
        self.settings_menu.add.button('Save Settings', self._save_settings)
        self.settings_menu.add.button('Back', self._back_to_main_menu)

        # Set as current submenu instead of using mainloop
        self.current_submenu = self.settings_menu
        self.show_menu = False

    def _back_to_main_menu(self):
        """Return to main menu from submenu."""
        self.current_submenu = None
        self.show_menu = True
        self.menu.enable()

    def _end_flight(self):
        """End current flight and arrive at destination."""
        performance = flight_simulator.end_flight()

        if performance.get('completed', False) or performance.get('final_progress', 0) > 80:
            # Successful arrival - select NPC and start conversation
            if hasattr(flight_simulator, 'current_flight') and flight_simulator.current_flight:
                destination = flight_simulator.current_flight.destination
                location, npc = npc_manager.travel_to_location(destination.id)
                if location and npc:
                    self._show_message(f"Arrived at {location.name}! Met {npc.name}")
                    self.is_flying = False
                    self.flight_ui.hide()
                    self.start_conversation()
                    return

        # Failed flight or emergency landing - return to menu
        self._show_message("Flight ended. Returning to menu.")
        self.is_flying = False
        self.flight_ui.hide()
        self.show_menu = True
        self.menu.enable()

    def _show_flight_planning_dialog(self, departure, destination):
        """Show flight planning dialog before starting flight."""
        # Calculate flight plan
        aircraft_type = game_data.educational_subject.name
        flight_plan = flight_simulator.calculate_flight_plan(
            departure,
            destination,
            aircraft_type
        )

        # Create flight planning menu
        custom_theme = self.menu.get_theme().copy()

        self.flight_planning_menu = pygame_menu.Menu(
            title='Flight Planning',
            width=self.width,
            height=self.height,
            theme=custom_theme
        )

        # Flight information
        self.flight_planning_menu.add.label(f'From: {departure.name}', font_size=20)
        self.flight_planning_menu.add.label(f'To: {destination.name}', font_size=20)
        self.flight_planning_menu.add.vertical_margin(20)

        self.flight_planning_menu.add.label(f'Aircraft: {aircraft_type.replace("_", " ").title()}', font_size=18)
        self.flight_planning_menu.add.label(f'Distance: {flight_plan.distance_nm:.0f} nautical miles', font_size=16)
        self.flight_planning_menu.add.label(f'Estimated Flight Time: {flight_plan.estimated_time_minutes // 60}h {flight_plan.estimated_time_minutes % 60}m', font_size=16)
        self.flight_planning_menu.add.label(f'Cruise Altitude: {flight_plan.cruise_altitude:,} feet', font_size=16)
        self.flight_planning_menu.add.label(f'Cruise Speed: {flight_plan.cruise_speed} knots', font_size=16)
        self.flight_planning_menu.add.label(f'Fuel Required: {flight_plan.fuel_required:.1f} gallons', font_size=16)

        self.flight_planning_menu.add.vertical_margin(30)

        # Flight duration options
        duration_options = [
            ('Real-time flight (Desert Bus style)', 'real_time'),
            ('Accelerated flight (5x speed)', 'accelerated'),
            ('Quick travel (skip flight)', 'instant')
        ]

        self.flight_duration_selector = self.flight_planning_menu.add.selector(
            'Flight Mode: ',
            duration_options,
            default=1,  # Default to accelerated
            style="fancy"
        )

        self.flight_planning_menu.add.vertical_margin(20)

        # Action buttons
        self.flight_planning_menu.add.button('Start Flight', self._start_planned_flight, flight_plan)
        self.flight_planning_menu.add.button('Cancel', self._back_to_main_menu)

        # Set as current submenu
        self.current_submenu = self.flight_planning_menu
        self.show_menu = False

    def _start_planned_flight(self, flight_plan):
        """Start the planned flight based on selected options."""
        # Get selected flight mode
        duration_mode = self.flight_duration_selector.get_value()[0][1]

        if duration_mode == 'instant':
            # Skip flight simulation, arrive immediately
            location, npc = npc_manager.travel_to_location(flight_plan.destination.id)
            if location and npc:
                self._show_message(f"Arrived at {location.name}! Met {npc.name}")
                self.current_submenu = None
                self.show_menu = False
                self.menu.disable()
                self.start_conversation()
            return

        # Set time acceleration based on mode
        if duration_mode == 'accelerated':
            # Modify flight plan for accelerated flight (5x speed)
            flight_plan.estimated_time_minutes = flight_plan.estimated_time_minutes // 5

        # Start flight simulation
        if flight_simulator.start_flight(flight_plan):
            self._show_message(f"Flying to {flight_plan.destination.name}...")
            self.current_submenu = None
            self.show_menu = False
            self.is_flying = True
            self.flight_ui.show()
        else:
            self._show_message("Failed to start flight!")
            self._back_to_main_menu()

    def _show_help_menu(self):
        """Show help menu."""
        # Create a completely fresh menu each time to avoid state issues
        custom_theme = self.menu.get_theme().copy()

        self.help_menu = pygame_menu.Menu(
            title='Help',
            width=self.width,
            height=self.height,
            theme=custom_theme
        )

        help_text = [
            "CONTROLS:",
            "",
            "In Menu:",
            "  • Use ARROW KEYS to navigate",
            "  • ENTER to select",
            "  • ESC to go back",
            "",
            "In Conversation:",
            "  • Type your message and press ENTER to send",
            "  • ESC to return to menu",
            "  • TAB to switch topics",
            "  • F1 for help",
            "",
            "LEARNING TIPS:",
            "",
            "• Ask questions to explore concepts deeply",
            "• Request detailed explanations of aircraft systems",
            "• The instructor adapts to your aviation knowledge level",
            "• Aircraft types build on each other - start with basics",
            "",
            "REQUIREMENTS:",
            "",
            "• Ollama must be running locally",
            "• Gemma 3n model must be installed:",
            "  ollama pull gemma3n:e4b"
        ]

        for line in help_text:
            if line.startswith("  "):
                self.help_menu.add.label(line, font_size=16, font_color=(160, 160, 180))
            elif line == "":
                self.help_menu.add.vertical_margin(10)
            elif line.endswith(":"):
                self.help_menu.add.label(line, font_size=20, font_color=(220, 220, 230))
            else:
                self.help_menu.add.label(line, font_size=18, font_color=(200, 200, 210))

        self.help_menu.add.vertical_margin(30)
        self.help_menu.add.button('Back', self._back_to_main_menu)

        # Set as current submenu instead of using mainloop
        self.current_submenu = self.help_menu
        self.show_menu = False

    def _show_travel_menu(self):
        """Show travel menu."""
        # Create a completely fresh menu each time to avoid state issues
        custom_theme = self.menu.get_theme().copy()

        self.travel_menu = pygame_menu.Menu(
            title='Travel to Airport',
            width=self.width,
            height=self.height,
            theme=custom_theme
        )

        # Current location info
        if npc_manager.current_location:
            self.travel_menu.add.label(
                f'Current: {npc_manager.current_location.name}',
                font_size=20,
                font_color=(180, 220, 180)
            )
            if npc_manager.current_npc:
                self.travel_menu.add.label(
                    f'NPC: {npc_manager.current_npc.name}',
                    font_size=16,
                    font_color=(150, 150, 200)
                )
        else:
            self.travel_menu.add.label(
                'No current location',
                font_size=20,
                font_color=(180, 180, 180)
            )

        self.travel_menu.add.vertical_margin(20)

        # Add location buttons
        for location in npc_manager.locations:
            button_text = f"{location.name} ({location.country})"
            # Highlight current location differently
            if npc_manager.current_location and location.id == npc_manager.current_location.id:
                button_text = f"→ {button_text} (Current)"

            self.travel_menu.add.button(
                button_text,
                self._travel_to_location,
                location.id
            )

        self.travel_menu.add.vertical_margin(30)
        self.travel_menu.add.button('Back', self._back_to_main_menu)

        # Set as current submenu instead of using mainloop
        self.current_submenu = self.travel_menu
        self.show_menu = False

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
        self.ui.add_message("system", f"🎯 Checkpoint: {signal.data.get('learning_objective', 'Progress saved')}")

    def _handle_topic_completed(self, signal):
        """Handle topic completion signal."""
        topic = signal.data.get('topic_name', 'Unknown topic')
        self.ui.add_message("system", f"✅ Topic Completed: {topic}")

    def _handle_assessment(self, signal):
        """Handle assessment question signal."""
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
            # Update UI with current subject
            self.ui.update_subject(game_data.get_subject_name())
            self.ui.clear_messages()

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

            # Show conversation UI
            self.ui.show()

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

            # Handle menu events
            if self.show_menu:
                self.menu.update([event])
            elif self.current_submenu:
                # Handle submenu events
                self.current_submenu.update([event])
                # Handle ESC key to go back to main menu
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self._back_to_main_menu()
            elif self.is_flying:
                # Handle flight simulation events
                action = self.flight_ui.handle_event(event)
                if action == "end_flight":
                    self._end_flight()
                elif action == "course_correction":
                    pass  # Already handled by flight_ui
                elif action == "autopilot_toggle":
                    pass  # Already handled by flight_ui
            else:
                # Handle conversation events
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.is_conversing = False
                        self.conversation.end_conversation()
                        self.show_menu = True
                        self.menu.enable()
                        self.ui.hide()

                    elif event.key == pygame.K_TAB:
                        self.switch_subject()

                    elif event.key == pygame.K_F1:
                        self.show_help()

                # Pass event to UI
                user_input = self.ui.handle_event(event)
                if user_input and not self.awaiting_response:
                    asyncio.create_task(self.process_user_input(user_input))

    def show_help(self):
        """Display help information in conversation."""
        help_text = """
Controls:
- Type your message and press Enter to send
- ESC: Return to menu
- TAB: Switch aircraft types
- F1: Show this help

Ask about aircraft specifications, operations, or history!
        """
        self.ui.add_message("system", help_text)

    def switch_subject(self):
        """Switch to next aircraft type."""
        current = game_data.educational_subject
        subjects = list(AircraftType)
        current_idx = subjects.index(current)
        next_idx = (current_idx + 1) % len(subjects)
        game_data.educational_subject = subjects[next_idx]
        game_data.save_settings()

        subject_name = game_data.get_subject_name()
        self.ui.add_message("system", f"Switched to: {subject_name}")
        self.ui.update_subject(subject_name)

        # Restart conversation with new subject
        self.conversation.end_conversation()
        self.conversation = EducationalConversation()
        self._register_signal_handlers()
        self.start_conversation()

    def update(self, dt: float):
        """Update game state."""
        if self.is_conversing:
            self.ui.update(dt)
        elif self.is_flying:
            # Update flight simulation
            status = flight_simulator.update_flight(dt)
            self.flight_ui.update(dt)

            # Check if flight completed automatically
            if not status['is_flying']:
                self._end_flight()

    def draw(self):
        """Draw the game."""
        if self.show_menu:
            self.menu.draw(self.screen)
        elif self.current_submenu:
            self.current_submenu.draw(self.screen)
        elif self.is_flying:
            self.flight_ui.draw()
        else:
            self.ui.draw()

        pygame.display.flip()

    async def run(self):
        """Main game loop."""
        # Check for Ollama on startup
        if not self.ollama_status:
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