import pygame
import textwrap
from typing import List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class UIColors:
    BACKGROUND = (30, 30, 40)
    PANEL_BG = (45, 45, 60)
    TEXT_PRIMARY = (220, 220, 230)
    TEXT_SECONDARY = (160, 160, 180)
    USER_MESSAGE = (100, 150, 250)
    ASSISTANT_MESSAGE = (150, 250, 150)
    SYSTEM_MESSAGE = (250, 200, 100)
    INPUT_BG = (60, 60, 80)
    INPUT_BORDER = (100, 100, 120)
    BUTTON_BG = (80, 80, 100)
    BUTTON_HOVER = (100, 100, 120)
    BUTTON_ACTIVE = (120, 120, 140)
    SCROLL_BAR = (70, 70, 90)
    SCROLL_THUMB = (100, 100, 120)


class ConversationUI:
    def __init__(self, screen: pygame.Surface, font_size: int = 16):
        self.screen = screen
        self.width, self.height = screen.get_size()
        self.colors = UIColors()

        # Fonts
        pygame.font.init()
        self.font = pygame.font.Font(None, font_size)
        self.font_bold = pygame.font.Font(None, font_size + 2)
        self.font_small = pygame.font.Font(None, font_size - 2)

        # Layout dimensions
        self.margin = 20
        self.padding = 10
        self.line_height = font_size + 8
        self.max_line_width = 60  # Characters per line

        # Conversation display area
        self.conv_x = self.margin
        self.conv_y = self.margin
        self.conv_width = self.width - (2 * self.margin)
        self.conv_height = self.height - 200  # Leave room for input

        # Input area
        self.input_y = self.conv_y + self.conv_height + self.margin
        self.input_height = 40
        self.input_text = ""
        self.cursor_visible = True
        self.cursor_timer = 0

        # Scroll state
        self.scroll_offset = 0
        self.max_scroll = 0
        self.scroll_speed = 20

        # Message history for display
        self.display_messages: List[Tuple[str, str, Tuple[int, int, int]]] = []

        # Buttons
        self.submit_button = pygame.Rect(
            self.width - 100 - self.margin,
            self.input_y,
            100,
            self.input_height
        )

        # Progress display
        self.progress_y = self.input_y + self.input_height + self.margin
        self.progress_data = {
            "sessions": 0,
            "topics": 0,
            "assessments": 0,
            "checkpoints": 0
        }

    def add_message(self, role: str, content: str):
        """Add a message to the display."""
        color = self.colors.TEXT_PRIMARY
        prefix = ""

        if role == "user":
            color = self.colors.USER_MESSAGE
            prefix = "[You] "
        elif role == "assistant":
            color = self.colors.ASSISTANT_MESSAGE
            prefix = "[ML Tutor] "
        elif role == "system":
            color = self.colors.SYSTEM_MESSAGE
            prefix = "[System] "

        # Wrap long messages
        wrapped_lines = self._wrap_text(content, self.max_line_width)
        for i, line in enumerate(wrapped_lines):
            if i == 0:
                self.display_messages.append((prefix + line, role, color))
            else:
                self.display_messages.append((line, role, color))

        # Auto-scroll to bottom
        self._update_scroll_bounds()
        self.scroll_offset = max(0, self.max_scroll)

    def _wrap_text(self, text: str, max_width: int) -> List[str]:
        """Wrap text to fit within max width."""
        words = text.split()
        lines = []
        current_line = []
        current_length = 0

        for word in words:
            word_length = len(word)
            if current_length + word_length + 1 <= max_width:
                current_line.append(word)
                current_length += word_length + 1
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
                current_length = word_length

        if current_line:
            lines.append(' '.join(current_line))

        return lines if lines else ['']

    def _update_scroll_bounds(self):
        """Update maximum scroll offset."""
        total_height = len(self.display_messages) * self.line_height
        visible_height = self.conv_height - (2 * self.padding)
        self.max_scroll = max(0, total_height - visible_height)

    def handle_event(self, event: pygame.event.Event) -> Optional[str]:
        """Handle pygame events. Returns user input if submitted."""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                if self.input_text.strip():
                    text = self.input_text
                    self.input_text = ""
                    return text
            elif event.key == pygame.K_BACKSPACE:
                self.input_text = self.input_text[:-1]
            elif event.key == pygame.K_UP:
                self.scroll_offset = max(0, self.scroll_offset - self.scroll_speed)
            elif event.key == pygame.K_DOWN:
                self.scroll_offset = min(self.max_scroll, self.scroll_offset + self.scroll_speed)
            elif event.key == pygame.K_PAGEUP:
                self.scroll_offset = max(0, self.scroll_offset - self.conv_height)
            elif event.key == pygame.K_PAGEDOWN:
                self.scroll_offset = min(self.max_scroll, self.scroll_offset + self.conv_height)
            else:
                # Add character to input
                if len(self.input_text) < 200:  # Limit input length
                    self.input_text += event.unicode

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click
                if self.submit_button.collidepoint(event.pos):
                    if self.input_text.strip():
                        text = self.input_text
                        self.input_text = ""
                        return text
            elif event.button == 4:  # Scroll up
                self.scroll_offset = max(0, self.scroll_offset - self.scroll_speed)
            elif event.button == 5:  # Scroll down
                self.scroll_offset = min(self.max_scroll, self.scroll_offset + self.scroll_speed)

        return None

    def update(self, dt: float):
        """Update UI state (e.g., cursor blinking)."""
        self.cursor_timer += dt
        if self.cursor_timer >= 0.5:
            self.cursor_visible = not self.cursor_visible
            self.cursor_timer = 0

    def draw(self):
        """Draw the conversation UI."""
        # Clear screen
        self.screen.fill(self.colors.BACKGROUND)

        # Draw conversation panel
        conv_rect = pygame.Rect(self.conv_x, self.conv_y, self.conv_width, self.conv_height)
        pygame.draw.rect(self.screen, self.colors.PANEL_BG, conv_rect)
        pygame.draw.rect(self.screen, self.colors.INPUT_BORDER, conv_rect, 2)

        # Create clipping region for conversation
        clip_rect = pygame.Rect(
            self.conv_x + self.padding,
            self.conv_y + self.padding,
            self.conv_width - (2 * self.padding) - 20,  # Leave room for scrollbar
            self.conv_height - (2 * self.padding)
        )
        self.screen.set_clip(clip_rect)

        # Draw messages
        y = self.conv_y + self.padding - self.scroll_offset
        for message, role, color in self.display_messages:
            if y > self.conv_y - self.line_height and y < self.conv_y + self.conv_height:
                text_surface = self.font.render(message, True, color)
                self.screen.blit(text_surface, (self.conv_x + self.padding, y))
            y += self.line_height

        # Reset clipping
        self.screen.set_clip(None)

        # Draw scrollbar if needed
        if self.max_scroll > 0:
            self._draw_scrollbar()

        # Draw input field
        self._draw_input_field()

        # Draw submit button
        self._draw_submit_button()

        # Draw progress info
        self._draw_progress()

    def _draw_scrollbar(self):
        """Draw vertical scrollbar."""
        scrollbar_x = self.conv_x + self.conv_width - 15
        scrollbar_rect = pygame.Rect(scrollbar_x, self.conv_y, 15, self.conv_height)
        pygame.draw.rect(self.screen, self.colors.SCROLL_BAR, scrollbar_rect)

        # Calculate thumb position and size
        visible_ratio = self.conv_height / (self.max_scroll + self.conv_height)
        thumb_height = max(20, int(self.conv_height * visible_ratio))

        scroll_ratio = self.scroll_offset / max(1, self.max_scroll)
        thumb_y = self.conv_y + int((self.conv_height - thumb_height) * scroll_ratio)

        thumb_rect = pygame.Rect(scrollbar_x, thumb_y, 15, thumb_height)
        pygame.draw.rect(self.screen, self.colors.SCROLL_THUMB, thumb_rect)

    def _draw_input_field(self):
        """Draw the input text field."""
        input_rect = pygame.Rect(
            self.margin,
            self.input_y,
            self.width - 140 - (2 * self.margin),
            self.input_height
        )
        pygame.draw.rect(self.screen, self.colors.INPUT_BG, input_rect)
        pygame.draw.rect(self.screen, self.colors.INPUT_BORDER, input_rect, 2)

        # Draw input text
        text_surface = self.font.render(self.input_text, True, self.colors.TEXT_PRIMARY)
        text_x = input_rect.x + 5
        text_y = input_rect.y + (self.input_height - text_surface.get_height()) // 2
        self.screen.blit(text_surface, (text_x, text_y))

        # Draw cursor
        if self.cursor_visible:
            cursor_x = text_x + text_surface.get_width() + 2
            cursor_y1 = input_rect.y + 5
            cursor_y2 = input_rect.y + self.input_height - 5
            pygame.draw.line(self.screen, self.colors.TEXT_PRIMARY,
                           (cursor_x, cursor_y1), (cursor_x, cursor_y2), 2)

    def _draw_submit_button(self):
        """Draw the submit button."""
        mouse_pos = pygame.mouse.get_pos()
        is_hover = self.submit_button.collidepoint(mouse_pos)

        button_color = self.colors.BUTTON_HOVER if is_hover else self.colors.BUTTON_BG
        pygame.draw.rect(self.screen, button_color, self.submit_button)
        pygame.draw.rect(self.screen, self.colors.INPUT_BORDER, self.submit_button, 2)

        # Draw button text
        button_text = self.font.render("Send", True, self.colors.TEXT_PRIMARY)
        text_x = self.submit_button.x + (self.submit_button.width - button_text.get_width()) // 2
        text_y = self.submit_button.y + (self.submit_button.height - button_text.get_height()) // 2
        self.screen.blit(button_text, (text_x, text_y))

    def _draw_progress(self):
        """Draw progress information."""
        progress_text = (f"Sessions: {self.progress_data['sessions']} | "
                        f"Topics: {self.progress_data['topics']} | "
                        f"Assessments: {self.progress_data['assessments']} | "
                        f"Checkpoints: {self.progress_data['checkpoints']}")

        text_surface = self.font_small.render(progress_text, True, self.colors.TEXT_SECONDARY)
        self.screen.blit(text_surface, (self.margin, self.progress_y))

    def update_progress(self, progress_data: dict):
        """Update progress display data."""
        self.progress_data.update(progress_data)

    def clear_messages(self):
        """Clear all display messages."""
        self.display_messages.clear()
        self.scroll_offset = 0
        self.max_scroll = 0