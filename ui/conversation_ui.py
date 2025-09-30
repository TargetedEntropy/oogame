import pygame
import pygame_gui
from typing import Optional, Dict


class ConversationUI:
    """Conversation UI using pygame_gui."""

    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.width, self.height = screen.get_size()

        # Create UI manager with theme
        self.manager = pygame_gui.UIManager(
            (self.width, self.height),
            theme_path=None  # Can add custom theme JSON later
        )

        # Set up custom theme colors
        self.manager.get_theme().load_theme({
            "colours": {
                "dark_bg": "#1E1E28",
                "normal_bg": "#2D2D3C",
                "hovered_bg": "#3D3D4C",
                "disabled_bg": "#202028",
                "selected_bg": "#4A4A5A",
                "active_bg": "#5A5A6A",
                "normal_text": "#DCDCE6",
                "hovered_text": "#FFFFFF",
                "disabled_text": "#808080",
                "selected_text": "#FFFFFF",
                "active_text": "#FFFFFF",
                "normal_border": "#646478",
                "hovered_border": "#8888A0",
                "disabled_border": "#404040",
                "selected_border": "#9696FA",
                "active_border": "#AAAAFF"
            }
        })

        # Create conversation display (scrollable text box)
        self.conversation_box = pygame_gui.elements.UITextBox(
            html_text="<b>Aircraft Education Session</b><br><br>Press SPACE in the menu to start learning!",
            relative_rect=pygame.Rect(20, 20, self.width - 40, self.height - 200),
            manager=self.manager,
            wrap_to_height=False
        )

        # Create input field
        self.input_field = pygame_gui.elements.UITextEntryLine(
            relative_rect=pygame.Rect(20, self.height - 160, self.width - 160, 40),
            manager=self.manager,
            placeholder_text="Type your message here..."
        )

        # Create send button
        self.send_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(self.width - 120, self.height - 160, 100, 40),
            text="Send",
            manager=self.manager
        )

        # Create progress panel
        self.progress_panel = pygame_gui.elements.UIPanel(
            relative_rect=pygame.Rect(20, self.height - 100, self.width - 40, 80),
            starting_height=1,
            manager=self.manager
        )

        # Progress labels
        self.progress_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(10, 10, self.width - 60, 30),
            text="Progress: Sessions: 0 | Topics: 0 | Assessments: 0 | Checkpoints: 0",
            manager=self.manager,
            container=self.progress_panel
        )

        self.subject_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(10, 40, self.width - 60, 30),
            text="Subject: Single-Engine Propeller Aircraft",
            manager=self.manager,
            container=self.progress_panel
        )

        # Store conversation HTML
        self.conversation_html = []
        self.max_messages = 100  # Limit stored messages for performance

        # Progress data
        self.progress_data = {
            "sessions": 0,
            "topics": 0,
            "assessments": 0,
            "checkpoints": 0
        }

    def add_message(self, role: str, content: str):
        """Add a message to the conversation display."""
        # Format message based on role
        if role == "user":
            formatted = f'<font color="#6496FA"><b>[You]</b></font> {self._escape_html(content)}'
        elif role == "assistant":
            formatted = f'<font color="#96FA96"><b>[Aviation Instructor]</b></font> {self._escape_html(content)}'
        elif role == "system":
            formatted = f'<font color="#FAC864"><b>[System]</b></font> {self._escape_html(content)}'
        else:
            formatted = self._escape_html(content)

        # Add to conversation history
        self.conversation_html.append(formatted)

        # Limit message history
        if len(self.conversation_html) > self.max_messages:
            self.conversation_html = self.conversation_html[-self.max_messages:]

        # Update text box
        html_content = "<br><br>".join(self.conversation_html)
        self.conversation_box.set_text(html_content)

        # Auto-scroll to bottom
        self.conversation_box.scroll_y_percentage = 1.0

    def _escape_html(self, text: str) -> str:
        """Escape HTML special characters."""
        return (text.replace("&", "&amp;")
                   .replace("<", "&lt;")
                   .replace(">", "&gt;")
                   .replace('"', "&quot;")
                   .replace("'", "&#x27;"))

    def handle_event(self, event: pygame.event.Event) -> Optional[str]:
        """Handle pygame events and return user input if submitted."""
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == self.send_button:
                text = self.input_field.get_text().strip()
                if text:
                    self.input_field.set_text("")
                    return text

        elif event.type == pygame_gui.UI_TEXT_ENTRY_FINISHED:
            if event.ui_element == self.input_field:
                text = self.input_field.get_text().strip()
                if text:
                    self.input_field.set_text("")
                    return text

        # Let the UI manager handle the event
        self.manager.process_events(event)
        return None

    def update(self, dt: float):
        """Update UI elements."""
        self.manager.update(dt)

    def draw(self):
        """Draw the UI."""
        self.screen.fill((30, 30, 40))  # Background color
        self.manager.draw_ui(self.screen)

    def update_progress(self, progress_data: dict):
        """Update progress display."""
        self.progress_data.update(progress_data)
        progress_text = (f"Progress: Sessions: {self.progress_data['sessions']} | "
                        f"Topics: {self.progress_data['topics']} | "
                        f"Assessments: {self.progress_data['assessments']} | "
                        f"Checkpoints: {self.progress_data['checkpoints']}")
        self.progress_label.set_text(progress_text)

    def update_subject(self, subject_name: str):
        """Update the subject display."""
        self.subject_label.set_text(f"Subject: {subject_name}")

    def clear_messages(self):
        """Clear all messages from the conversation."""
        self.conversation_html.clear()
        self.conversation_box.set_text("<b>New Conversation Started</b>")

    def show(self):
        """Show the conversation UI."""
        self.conversation_box.show()
        self.input_field.show()
        self.send_button.show()
        self.progress_panel.show()

    def hide(self):
        """Hide the conversation UI."""
        self.conversation_box.hide()
        self.input_field.hide()
        self.send_button.hide()
        self.progress_panel.hide()