import pygame
import pygame_gui
import math
from typing import Dict, Optional
from core.flight_simulator import flight_simulator, FlightPhase

class FlightUI:
    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.width = screen.get_width()
        self.height = screen.get_height()

        # UI Manager for flight instruments
        self.ui_manager = pygame_gui.UIManager((self.width, self.height))

        # Colors
        self.bg_color = (20, 30, 40)
        self.instrument_bg = (40, 50, 60)
        self.text_color = (220, 220, 230)
        self.warning_color = (255, 100, 100)
        self.normal_color = (100, 255, 100)
        self.gauge_color = (100, 150, 255)

        # Font
        self.font = pygame.font.Font(None, 24)
        self.small_font = pygame.font.Font(None, 18)
        self.large_font = pygame.font.Font(None, 32)

        # Instrument panel layout
        self.instrument_panel_rect = pygame.Rect(20, 20, self.width - 40, 200)
        self.info_panel_rect = pygame.Rect(20, 240, 300, self.height - 260)
        self.alerts_panel_rect = pygame.Rect(340, 240, 300, 200)
        self.progress_panel_rect = pygame.Rect(660, 240, self.width - 680, 200)
        self.education_panel_rect = pygame.Rect(20, 460, self.width - 40, self.height - 480)

        # Control states
        self.keys_pressed = set()
        self.last_correction_time = 0

        # UI elements
        self.correction_buttons = {}
        self.autopilot_button = None
        self.end_flight_button = None

        self._create_ui_elements()

        # Educational content
        self.education_text = ""
        self.education_timer = 0

    def _create_ui_elements(self):
        """Create UI elements for flight controls."""
        # Course correction buttons
        button_y = self.height - 100

        self.correction_buttons['left_5'] = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(50, button_y, 80, 30),
            text='← 5°',
            manager=self.ui_manager
        )

        self.correction_buttons['left_1'] = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(140, button_y, 60, 30),
            text='← 1°',
            manager=self.ui_manager
        )

        self.correction_buttons['right_1'] = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(210, button_y, 60, 30),
            text='1° →',
            manager=self.ui_manager
        )

        self.correction_buttons['right_5'] = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(280, button_y, 80, 30),
            text='5° →',
            manager=self.ui_manager
        )

        # Autopilot toggle
        self.autopilot_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(400, button_y, 100, 30),
            text='Autopilot',
            manager=self.ui_manager
        )

        # End flight button
        self.end_flight_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(self.width - 150, button_y, 120, 30),
            text='End Flight',
            manager=self.ui_manager
        )

    def handle_event(self, event) -> Optional[str]:
        """Handle UI events and return any user input."""
        self.ui_manager.process_events(event)

        if event.type == pygame.USEREVENT:
            if event.user_type == pygame_gui.UI_BUTTON_PRESSED:
                if event.ui_element == self.correction_buttons['left_5']:
                    flight_simulator.apply_course_correction(-5)
                    return "course_correction"
                elif event.ui_element == self.correction_buttons['left_1']:
                    flight_simulator.apply_course_correction(-1)
                    return "course_correction"
                elif event.ui_element == self.correction_buttons['right_1']:
                    flight_simulator.apply_course_correction(1)
                    return "course_correction"
                elif event.ui_element == self.correction_buttons['right_5']:
                    flight_simulator.apply_course_correction(5)
                    return "course_correction"
                elif event.ui_element == self.autopilot_button:
                    current_state = flight_simulator.autopilot_enabled
                    flight_simulator.set_autopilot(not current_state)
                    return "autopilot_toggle"
                elif event.ui_element == self.end_flight_button:
                    return "end_flight"

        # Keyboard controls
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:
                flight_simulator.apply_course_correction(-1)
                return "course_correction"
            elif event.key == pygame.K_RIGHT:
                flight_simulator.apply_course_correction(1)
                return "course_correction"
            elif event.key == pygame.K_a:
                current_state = flight_simulator.autopilot_enabled
                flight_simulator.set_autopilot(not current_state)
                return "autopilot_toggle"
            elif event.key == pygame.K_ESCAPE:
                return "end_flight"

        return None

    def update(self, dt: float):
        """Update flight UI."""
        self.ui_manager.update(dt)

        # Update autopilot button text
        if flight_simulator.autopilot_enabled:
            self.autopilot_button.set_text("Autopilot ON")
        else:
            self.autopilot_button.set_text("Autopilot OFF")

        # Update education timer
        self.education_timer += dt
        if self.education_timer > 30:  # New educational content every 30 seconds
            self._update_education_content()
            self.education_timer = 0

    def draw(self):
        """Draw the flight UI."""
        self.screen.fill(self.bg_color)

        # Get current flight status
        status = flight_simulator._get_status()

        if not status['is_flying']:
            self._draw_no_flight_message()
            return

        # Draw instrument panels
        self._draw_primary_instruments(status)
        self._draw_flight_info(status)
        self._draw_alerts_panel(status)
        self._draw_progress_panel(status)
        self._draw_education_panel()

        # Draw UI elements
        self.ui_manager.draw_ui(self.screen)

        # Draw flight phase indicator
        self._draw_flight_phase(status)

    def _draw_no_flight_message(self):
        """Draw message when no flight is active."""
        text = self.large_font.render("No active flight", True, self.text_color)
        text_rect = text.get_rect(center=(self.width // 2, self.height // 2))
        self.screen.blit(text, text_rect)

        instruction = self.font.render("Use 'Travel to Airport' to start a flight", True, self.text_color)
        inst_rect = instruction.get_rect(center=(self.width // 2, self.height // 2 + 40))
        self.screen.blit(instruction, inst_rect)

    def _draw_primary_instruments(self, status: Dict):
        """Draw primary flight instruments."""
        # Draw instrument panel background
        pygame.draw.rect(self.screen, self.instrument_bg, self.instrument_panel_rect)
        pygame.draw.rect(self.screen, self.text_color, self.instrument_panel_rect, 2)

        # Instrument positions
        instruments = [
            ('ALTITUDE', status['altitude'], 'ft', (80, 80)),
            ('AIRSPEED', status['airspeed'], 'kts', (220, 80)),
            ('HEADING', status['heading'], '°', (360, 80)),
            ('ENGINE TEMP', status['engine_temp'], '°F', (500, 80)),
            ('FUEL', f"{status['fuel_remaining']:.1f}", '%', (640, 80))
        ]

        for name, value, unit, pos in instruments:
            self._draw_circular_gauge(name, value, unit, pos)

    def _draw_circular_gauge(self, name: str, value, unit: str, center: tuple):
        """Draw a circular gauge instrument."""
        x, y = center[0] + self.instrument_panel_rect.x, center[1] + self.instrument_panel_rect.y
        radius = 35

        # Outer circle
        pygame.draw.circle(self.screen, self.text_color, (x, y), radius, 2)

        # Value text
        value_text = f"{value}"
        text_surface = self.font.render(value_text, True, self.text_color)
        text_rect = text_surface.get_rect(center=(x, y - 5))
        self.screen.blit(text_surface, text_rect)

        # Unit text
        unit_surface = self.small_font.render(unit, True, self.text_color)
        unit_rect = unit_surface.get_rect(center=(x, y + 15))
        self.screen.blit(unit_surface, unit_rect)

        # Label
        label_surface = self.small_font.render(name, True, self.text_color)
        label_rect = label_surface.get_rect(center=(x, y - 55))
        self.screen.blit(label_surface, label_rect)

        # Warning indicators
        if name == "ENGINE TEMP" and value > 220:
            pygame.draw.circle(self.screen, self.warning_color, (x, y), radius, 3)
        elif name == "FUEL" and float(str(value).replace('%', '')) < 20:
            pygame.draw.circle(self.screen, self.warning_color, (x, y), radius, 3)

    def _draw_flight_info(self, status: Dict):
        """Draw flight information panel."""
        pygame.draw.rect(self.screen, self.instrument_bg, self.info_panel_rect)
        pygame.draw.rect(self.screen, self.text_color, self.info_panel_rect, 2)

        # Title
        title = self.font.render("FLIGHT INFO", True, self.text_color)
        self.screen.blit(title, (self.info_panel_rect.x + 10, self.info_panel_rect.y + 10))

        # Flight information
        y_offset = 40
        info_items = [
            f"Phase: {status['flight_phase'].replace('_', ' ').title()}",
            f"Time: {self._format_time(status['elapsed_time'])}",
            f"Progress: {status['progress_percent']:.1f}%",
            f"Off Course: {status['off_course_distance']:.2f} nm",
            f"Target HDG: {status['target_heading']}°"
        ]

        for item in info_items:
            text = self.small_font.render(item, True, self.text_color)
            self.screen.blit(text, (self.info_panel_rect.x + 10, self.info_panel_rect.y + y_offset))
            y_offset += 25

        # Weather info
        weather = status['weather']
        weather_items = [
            f"Weather: {weather['condition'].replace('_', ' ').title()}",
            f"Wind: {weather['wind_direction']}° @ {weather['wind_speed']} kts",
            f"Visibility: {weather['visibility']} miles"
        ]

        y_offset += 10
        for item in weather_items:
            text = self.small_font.render(item, True, self.text_color)
            self.screen.blit(text, (self.info_panel_rect.x + 10, self.info_panel_rect.y + y_offset))
            y_offset += 20

    def _draw_alerts_panel(self, status: Dict):
        """Draw system alerts panel."""
        pygame.draw.rect(self.screen, self.instrument_bg, self.alerts_panel_rect)

        # Use warning color if there are alerts
        border_color = self.warning_color if status['system_alerts'] else self.text_color
        pygame.draw.rect(self.screen, border_color, self.alerts_panel_rect, 2)

        # Title
        title = self.font.render("ALERTS", True, self.text_color)
        self.screen.blit(title, (self.alerts_panel_rect.x + 10, self.alerts_panel_rect.y + 10))

        # Alerts
        y_offset = 40
        for alert in status['system_alerts'][-8:]:  # Show last 8 alerts
            color = self.warning_color if "WARNING" in alert.upper() or "EMERGENCY" in alert.upper() else self.text_color
            text = self.small_font.render(alert, True, color)
            self.screen.blit(text, (self.alerts_panel_rect.x + 10, self.alerts_panel_rect.y + y_offset))
            y_offset += 20

        if not status['system_alerts']:
            text = self.small_font.render("No active alerts", True, self.normal_color)
            self.screen.blit(text, (self.alerts_panel_rect.x + 10, self.alerts_panel_rect.y + y_offset))

    def _draw_progress_panel(self, status: Dict):
        """Draw flight progress panel."""
        pygame.draw.rect(self.screen, self.instrument_bg, self.progress_panel_rect)
        pygame.draw.rect(self.screen, self.text_color, self.progress_panel_rect, 2)

        # Title
        title = self.font.render("PROGRESS", True, self.text_color)
        self.screen.blit(title, (self.progress_panel_rect.x + 10, self.progress_panel_rect.y + 10))

        # Progress bar
        progress_rect = pygame.Rect(
            self.progress_panel_rect.x + 10,
            self.progress_panel_rect.y + 40,
            self.progress_panel_rect.width - 20,
            20
        )

        pygame.draw.rect(self.screen, (60, 60, 70), progress_rect)

        fill_width = int((status['progress_percent'] / 100) * progress_rect.width)
        fill_rect = pygame.Rect(progress_rect.x, progress_rect.y, fill_width, progress_rect.height)
        pygame.draw.rect(self.screen, self.gauge_color, fill_rect)

        pygame.draw.rect(self.screen, self.text_color, progress_rect, 1)

        # Progress text
        progress_text = f"{status['progress_percent']:.1f}% Complete"
        text = self.small_font.render(progress_text, True, self.text_color)
        self.screen.blit(text, (self.progress_panel_rect.x + 10, self.progress_panel_rect.y + 70))

        # Performance metrics
        perf = status['performance']
        y_offset = 95
        perf_items = [
            f"Course Deviations: {perf['course_deviations']}",
            f"System Alerts: {perf['alerts_count']}",
            f"Fuel Efficiency: {perf['fuel_efficiency']:.1f}%"
        ]

        for item in perf_items:
            text = self.small_font.render(item, True, self.text_color)
            self.screen.blit(text, (self.progress_panel_rect.x + 10, self.progress_panel_rect.y + y_offset))
            y_offset += 20

    def _draw_education_panel(self):
        """Draw educational content panel."""
        if not self.education_text:
            return

        pygame.draw.rect(self.screen, self.instrument_bg, self.education_panel_rect)
        pygame.draw.rect(self.screen, self.text_color, self.education_panel_rect, 2)

        # Title
        title = self.font.render("AVIATION EDUCATION", True, self.text_color)
        self.screen.blit(title, (self.education_panel_rect.x + 10, self.education_panel_rect.y + 10))

        # Education text (word wrapped)
        self._draw_wrapped_text(
            self.education_text,
            self.education_panel_rect.x + 10,
            self.education_panel_rect.y + 40,
            self.education_panel_rect.width - 20,
            self.small_font,
            self.text_color
        )

    def _draw_flight_phase(self, status: Dict):
        """Draw current flight phase indicator."""
        phase_text = f"PHASE: {status['flight_phase'].replace('_', ' ').title()}"
        text = self.large_font.render(phase_text, True, self.text_color)
        self.screen.blit(text, (self.width - text.get_width() - 20, 20))

        # Phase-specific indicators
        if status['flight_phase'] == 'takeoff':
            indicator = self.font.render("TAKING OFF", True, self.normal_color)
            self.screen.blit(indicator, (self.width - indicator.get_width() - 20, 60))
        elif status['flight_phase'] == 'landing':
            indicator = self.font.render("LANDING", True, self.warning_color)
            self.screen.blit(indicator, (self.width - indicator.get_width() - 20, 60))

    def _format_time(self, seconds: float) -> str:
        """Format elapsed time as MM:SS."""
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes:02d}:{secs:02d}"

    def _draw_wrapped_text(self, text: str, x: int, y: int, max_width: int, font, color):
        """Draw text with word wrapping."""
        words = text.split(' ')
        lines = []
        current_line = []

        for word in words:
            test_line = ' '.join(current_line + [word])
            test_surface = font.render(test_line, True, color)

            if test_surface.get_width() <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                    current_line = [word]
                else:
                    lines.append(word)

        if current_line:
            lines.append(' '.join(current_line))

        for i, line in enumerate(lines[:5]):  # Max 5 lines
            line_surface = font.render(line, True, color)
            self.screen.blit(line_surface, (x, y + i * 20))

    def _update_education_content(self):
        """Update educational content based on current flight phase."""
        status = flight_simulator._get_status()
        if not status['is_flying']:
            return

        phase = status['flight_phase']

        education_content = {
            'taxi': "During taxi, pilots follow ground control instructions and perform final checks before takeoff. The aircraft moves slowly on the ground using engine power.",
            'takeoff': "Takeoff requires the pilot to apply full power and maintain runway centerline. Rotation speed varies by aircraft weight and conditions.",
            'climb': "During climb, pilots monitor engine parameters and follow ATC altitude assignments. Rate of climb decreases with altitude due to thinner air.",
            'cruise': "Cruise flight is the most efficient phase. Pilots monitor navigation, weather, and fuel consumption while maintaining assigned altitude and heading.",
            'descent': "Descent planning begins well before the destination. Pilots must balance speed, altitude, and distance to arrive at the correct approach point.",
            'approach': "The approach phase requires precise navigation and speed control. Pilots configure the aircraft for landing and follow instrument procedures.",
            'landing': "Landing requires precise control of airspeed, altitude, and runway alignment. The goal is a smooth touchdown in the first third of the runway."
        }

        self.education_text = education_content.get(phase, "Aviation is a field that requires constant learning and attention to safety procedures.")

    def show(self):
        """Show the flight UI."""
        pass

    def hide(self):
        """Hide the flight UI."""
        pass