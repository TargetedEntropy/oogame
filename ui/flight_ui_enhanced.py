import pygame
import pygame_gui
import math
import random
import time
from typing import Dict, Optional, List, Tuple
from core.flight_simulator import flight_simulator, FlightPhase, WeatherCondition


class FlightUIEnhanced:
    """
    Enhanced Flight UI with amazing visuals, animations, and comprehensive displays.
    This is the ultimate Desert Bus flight experience with professional aviation instruments.
    """

    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.width = screen.get_width()
        self.height = screen.get_height()

        # UI Manager for advanced elements
        self.ui_manager = pygame_gui.UIManager((self.width, self.height))

        # === COLOR PALETTE - Aviation Themed ===
        self.colors = {
            # Background and panels
            "sky_gradient_top": (5, 15, 30),
            "sky_gradient_bottom": (20, 35, 60),
            "panel_bg": (15, 20, 28),
            "panel_border": (60, 80, 100),
            "panel_highlight": (80, 100, 140),
            "glass_overlay": (40, 50, 70, 180),
            # Text and UI
            "text_primary": (240, 245, 250),
            "text_secondary": (180, 190, 200),
            "text_dim": (120, 130, 140),
            "text_highlight": (255, 255, 255),
            # Status colors
            "normal": (50, 255, 100),
            "caution": (255, 200, 50),
            "warning": (255, 100, 50),
            "danger": (255, 50, 50),
            "info": (100, 150, 255),
            # Instrument colors
            "gauge_bg": (10, 15, 20),
            "gauge_tick": (100, 120, 140),
            "gauge_needle": (255, 100, 100),
            "gauge_green": (50, 255, 50),
            "gauge_yellow": (255, 255, 50),
            "gauge_red": (255, 50, 50),
            # Map colors
            "map_bg": (10, 20, 30),
            "map_route": (100, 200, 255),
            "map_aircraft": (255, 255, 100),
            "map_waypoint": (255, 100, 255),
            "map_grid": (30, 40, 50),
            # Effects
            "glow": (100, 200, 255),
            "shadow": (0, 0, 0, 128),
        }

        # === FONTS - Multiple sizes for hierarchy ===
        pygame.font.init()
        self.fonts = {
            "huge": pygame.font.Font(None, 48),
            "large": pygame.font.Font(None, 36),
            "medium": pygame.font.Font(None, 28),
            "normal": pygame.font.Font(None, 22),
            "small": pygame.font.Font(None, 18),
            "tiny": pygame.font.Font(None, 14),
            "digital": self._load_digital_font(32),  # Digital display font
            "heading": self._load_bold_font(24),
        }

        # === PANEL LAYOUT - Fixed overlapping issues ===
        # Calculate proper layout based on screen size
        bottom_panel_height = 120  # Reduced from 140
        info_panel_top = 460
        info_panel_height = self.height - info_panel_top - bottom_panel_height - 20

        self.panels = {
            # Primary flight display (left side)
            "pfd": pygame.Rect(20, 60, 350, 360),  # Slightly smaller
            # Navigation display (center)
            "nav": pygame.Rect(390, 60, 350, 360),  # Adjusted position
            # Engine and systems (right side)
            "engine": pygame.Rect(760, 60, 180, 360),
            # Top status bar
            "status_bar": pygame.Rect(0, 0, self.width, 50),
            # Bottom control panel - REDUCED HEIGHT
            "controls": pygame.Rect(
                0, self.height - bottom_panel_height, self.width, bottom_panel_height
            ),
            # Secondary panels - PROPER SPACING
            # Radio/comms panel (left)
            "radio": pygame.Rect(20, info_panel_top, 230, info_panel_height),
            # Flight info panel (center-left)
            "info": pygame.Rect(270, info_panel_top, 230, info_panel_height),
            # Weather panel (center-right)
            "weather": pygame.Rect(520, info_panel_top, 230, info_panel_height),
            # Alerts panel (right)
            "alerts": pygame.Rect(
                770, info_panel_top, self.width - 790, info_panel_height
            ),
        }

        # === ANIMATION STATES ===
        self.animations = {
            "compass_rotation": 0,
            "altitude_scroll": 0,
            "speed_scroll": 0,
            "horizon_pitch": 0.0,  # Start level
            "horizon_roll": 0.0,  # Start level
            "warning_flash": 0,
            "radar_sweep": 0,
            "beacon_flash": 0,
            "engine_vibration": 0,
        }

        # === UI ELEMENTS ===
        self.controls = {}
        self.buttons = {}
        self.legend_visible = False
        self.help_overlay_visible = False

        # === DATA TRACKING ===
        self.flight_data_history = []
        self.altitude_tape = []
        self.speed_tape = []
        self.heading_tape = []
        self.message_log = []

        # === VISUAL EFFECTS ===
        self.particles = []
        self.screen_shake = 0
        self.warning_alpha = 0

        # === TIMING ===
        self.last_update = time.time()
        self.frame_count = 0

        # Create all UI elements
        self._create_all_ui_elements()

        # Initialize surfaces for performance
        self._create_cached_surfaces()

    def _load_digital_font(self, size):
        """Load a digital/LCD style font for displays."""
        try:
            # Try to use a monospace font for digital displays
            return pygame.font.SysFont("consolas,courier,monospace", size)
        except:
            return pygame.font.Font(None, size)

    def _load_bold_font(self, size):
        """Load a bold font for headings."""
        try:
            font = pygame.font.SysFont("arial,helvetica", size)
            font.set_bold(True)
            return font
        except:
            return pygame.font.Font(None, size)

    def _create_all_ui_elements(self):
        """Create all UI control elements."""
        # Create course correction controls
        button_y = self.panels["controls"].y + 50
        button_spacing = 90

        # Left corrections
        self.buttons["left_10"] = self._create_button(
            "←← 10°", 50, button_y, 80, 35, self._correct_left_10
        )
        self.buttons["left_5"] = self._create_button(
            "← 5°", 140, button_y, 70, 35, self._correct_left_5
        )
        self.buttons["left_1"] = self._create_button(
            "← 1°", 220, button_y, 60, 35, self._correct_left_1
        )

        # Center controls
        self.buttons["autopilot"] = self._create_button(
            "AUTO", 320, button_y, 80, 35, self._toggle_autopilot
        )
        self.buttons["center"] = self._create_button(
            "CENTER", 410, button_y, 80, 35, self._center_heading
        )

        # Right corrections
        self.buttons["right_1"] = self._create_button(
            "1° →", 520, button_y, 60, 35, self._correct_right_1
        )
        self.buttons["right_5"] = self._create_button(
            "5° →", 590, button_y, 70, 35, self._correct_right_5
        )
        self.buttons["right_10"] = self._create_button(
            "10° →→", 670, button_y, 80, 35, self._correct_right_10
        )

        # System controls
        self.buttons["legend"] = self._create_button(
            "LEGEND", 800, button_y, 80, 35, self._toggle_legend
        )
        self.buttons["help"] = self._create_button(
            "HELP", 890, button_y, 60, 35, self._toggle_help
        )
        self.buttons["end_flight"] = self._create_button(
            "END FLIGHT", self.width - 130, button_y, 110, 35, None
        )

        # Speed controls
        speed_y = button_y + 45
        self.buttons["speed_down"] = self._create_button(
            "SPEED -", 320, speed_y, 80, 30, None
        )
        self.buttons["speed_up"] = self._create_button(
            "SPEED +", 410, speed_y, 80, 30, None
        )

    def _create_button(self, text, x, y, width, height, callback):
        """Create a styled button."""
        button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(x, y, width, height),
            text=text,
            manager=self.ui_manager,
        )
        return button

    def _create_cached_surfaces(self):
        """Pre-create surfaces for better performance."""
        # Create gradient backgrounds
        self.sky_gradient = self._create_gradient_surface(
            self.width,
            self.height,
            self.colors["sky_gradient_top"],
            self.colors["sky_gradient_bottom"],
        )

        # Create glass effect overlays
        self.glass_overlay = pygame.Surface((100, 100), pygame.SRCALPHA)
        self.glass_overlay.fill((255, 255, 255, 20))

    def _create_gradient_surface(self, width, height, top_color, bottom_color):
        """Create a gradient surface."""
        surface = pygame.Surface((width, height))
        for y in range(height):
            ratio = y / height
            r = int(top_color[0] + (bottom_color[0] - top_color[0]) * ratio)
            g = int(top_color[1] + (bottom_color[1] - top_color[1]) * ratio)
            b = int(top_color[2] + (bottom_color[2] - top_color[2]) * ratio)
            pygame.draw.line(surface, (r, g, b), (0, y), (width, y))
        return surface

    def handle_event(self, event) -> Optional[str]:
        """Handle UI events with enhanced feedback."""
        self.ui_manager.process_events(event)

        if event.type == pygame.USEREVENT:
            if event.user_type == pygame_gui.UI_BUTTON_PRESSED:
                # Handle button presses with visual feedback
                if event.ui_element == self.buttons["left_10"]:
                    self._correct_left_10()
                    return "course_correction"
                elif event.ui_element == self.buttons["left_5"]:
                    self._correct_left_5()
                    return "course_correction"
                elif event.ui_element == self.buttons["left_1"]:
                    self._correct_left_1()
                    return "course_correction"
                elif event.ui_element == self.buttons["right_1"]:
                    self._correct_right_1()
                    return "course_correction"
                elif event.ui_element == self.buttons["right_5"]:
                    self._correct_right_5()
                    return "course_correction"
                elif event.ui_element == self.buttons["right_10"]:
                    self._correct_right_10()
                    return "course_correction"
                elif event.ui_element == self.buttons["autopilot"]:
                    self._toggle_autopilot()
                    return "autopilot_toggle"
                elif event.ui_element == self.buttons["center"]:
                    self._center_heading()
                    return "center_heading"
                elif event.ui_element == self.buttons["legend"]:
                    self._toggle_legend()
                    return "toggle_legend"
                elif event.ui_element == self.buttons["help"]:
                    self._toggle_help()
                    return "toggle_help"
                elif event.ui_element == self.buttons["end_flight"]:
                    return "end_flight"

        # Enhanced keyboard controls
        if event.type == pygame.KEYDOWN:
            # Course corrections
            if event.key == pygame.K_LEFT:
                if pygame.key.get_mods() & pygame.KMOD_SHIFT:
                    self._correct_left_5()
                else:
                    self._correct_left_1()
                return "course_correction"
            elif event.key == pygame.K_RIGHT:
                if pygame.key.get_mods() & pygame.KMOD_SHIFT:
                    self._correct_right_5()
                else:
                    self._correct_right_1()
                return "course_correction"

            # System controls
            elif event.key == pygame.K_a:
                self._toggle_autopilot()
                return "autopilot_toggle"
            elif event.key == pygame.K_c:
                self._center_heading()
                return "center_heading"
            elif event.key == pygame.K_l:
                self._toggle_legend()
                return "toggle_legend"
            elif event.key == pygame.K_h or event.key == pygame.K_F1:
                self._toggle_help()
                return "toggle_help"
            elif event.key == pygame.K_ESCAPE:
                return "end_flight"

        return None

    def update(self, dt: float):
        """Update all animations and dynamic elements."""
        self.ui_manager.update(dt)
        self.frame_count += 1

        # Update all animations
        self._update_animations(dt)

        # Update visual effects
        self._update_particles(dt)

        # Update data history
        self._update_flight_data_history()

        # Update screen shake for turbulence
        status = flight_simulator._get_status()
        if status["weather"]["condition"] == "turbulence":
            self.screen_shake = random.uniform(-2, 2)
        else:
            self.screen_shake *= 0.9  # Decay shake

    def _update_animations(self, dt):
        """Update all animation states."""
        # Rotating elements
        self.animations["compass_rotation"] += dt * 10
        self.animations["radar_sweep"] += dt * 45  # Radar sweep speed

        # Flashing elements
        self.animations["warning_flash"] = (
            self.animations["warning_flash"] + dt * 5
        ) % 2
        self.animations["beacon_flash"] = (self.animations["beacon_flash"] + dt * 3) % 2

        # Scrolling tapes
        status = flight_simulator._get_status()
        if status["is_flying"]:
            self.animations["altitude_scroll"] = status["altitude"] % 100
            self.animations["speed_scroll"] = status["airspeed"] % 10

            # Horizon animations based on flight
            phase = status["flight_phase"]
            if phase == "climb":
                self.animations["horizon_pitch"] = min(
                    15, self.animations["horizon_pitch"] + dt * 5
                )
            elif phase == "descent":
                self.animations["horizon_pitch"] = max(
                    -15, self.animations["horizon_pitch"] - dt * 5
                )
            else:
                self.animations["horizon_pitch"] *= 0.95  # Return to level

            # Simulate roll during turns - MUCH more stable
            heading_diff = status["heading"] - status["target_heading"]
            if heading_diff > 180:
                heading_diff -= 360
            elif heading_diff < -180:
                heading_diff += 360

            # Limit roll effect and only during actual flight phases (not taxi)
            if status["flight_phase"] in ["climb", "cruise", "descent", "approach"]:
                target_roll = max(
                    -15, min(15, heading_diff * 0.2)
                )  # Much smaller effect
                # Gradually move toward target roll
                self.animations["horizon_roll"] += (
                    (target_roll - self.animations["horizon_roll"]) * dt * 2
                )
            else:
                # Return to level during taxi, takeoff, landing
                self.animations["horizon_roll"] *= 0.9

    def _update_particles(self, dt):
        """Update particle effects."""
        # Update existing particles
        for particle in self.particles[:]:
            particle["life"] -= dt
            particle["y"] += particle["vy"] * dt
            particle["x"] += particle["vx"] * dt
            particle["vy"] += particle["gravity"] * dt

            if particle["life"] <= 0:
                self.particles.remove(particle)

        # Add new particles for effects
        status = flight_simulator._get_status()
        if status["is_flying"] and status["flight_phase"] in ["takeoff", "climb"]:
            # Engine exhaust particles
            if random.random() < 0.3:
                self.particles.append(
                    {
                        "x": self.width // 2 + random.uniform(-50, 50),
                        "y": self.height - 100,
                        "vx": random.uniform(-20, 20),
                        "vy": random.uniform(-100, -50),
                        "gravity": 50,
                        "life": 2.0,
                        "color": (255, 200, 100),
                        "size": random.uniform(2, 5),
                    }
                )

    def _update_flight_data_history(self):
        """Update historical data for graphs."""
        status = flight_simulator._get_status()
        if status["is_flying"]:
            # Keep last 60 data points
            self.flight_data_history.append(
                {
                    "altitude": status["altitude"],
                    "speed": status["airspeed"],
                    "heading": status["heading"],
                    "fuel": status["fuel_remaining"],
                    "time": self.frame_count,
                }
            )

            if len(self.flight_data_history) > 60:
                self.flight_data_history.pop(0)

    def draw(self):
        """Draw the complete enhanced flight UI."""
        # Draw background with gradient
        self.screen.blit(self.sky_gradient, (0, 0))

        # Apply screen shake if any
        if abs(self.screen_shake) > 0.1:
            self.screen.scroll(int(self.screen_shake), 0)

        # Get current flight status
        status = flight_simulator._get_status()

        if not status["is_flying"]:
            self._draw_no_flight_screen()
            return

        # === DRAW ALL PANELS IN ORDER ===

        # Top status bar
        self._draw_status_bar(status)

        # Primary panels
        self._draw_primary_flight_display(status)
        self._draw_navigation_display(status)
        self._draw_engine_display(status)

        # Secondary panels
        self._draw_radio_panel(status)
        self._draw_flight_info_panel(status)
        self._draw_weather_panel(status)
        self._draw_alerts_panel(status)

        # Control panel at bottom
        self._draw_control_panel(status)

        # Overlays
        if self.legend_visible:
            self._draw_legend_overlay()

        if self.help_overlay_visible:
            self._draw_help_overlay()

        # Draw particles on top
        self._draw_particles()

        # Draw warning overlays if needed
        self._draw_warning_overlays(status)

        # Draw UI manager elements
        self.ui_manager.draw_ui(self.screen)

    def _draw_no_flight_screen(self):
        """Draw attractive no-flight message."""
        # Dark overlay
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))

        # Title
        title = self.fonts["huge"].render(
            "FLIGHT SIMULATOR", True, self.colors["text_highlight"]
        )
        title_rect = title.get_rect(center=(self.width // 2, self.height // 2 - 60))
        self.screen.blit(title, title_rect)

        # Subtitle with animation
        alpha = int(128 + 127 * math.sin(self.frame_count * 0.05))
        subtitle = self.fonts["medium"].render(
            "No Active Flight", True, (*self.colors["text_secondary"], alpha)
        )
        subtitle_rect = subtitle.get_rect(center=(self.width // 2, self.height // 2))
        self.screen.blit(subtitle, subtitle_rect)

        # Instruction
        instruction = self.fonts["normal"].render(
            "Select 'Travel to Airport' from the main menu to start a flight",
            True,
            self.colors["text_dim"],
        )
        inst_rect = instruction.get_rect(
            center=(self.width // 2, self.height // 2 + 40)
        )
        self.screen.blit(instruction, inst_rect)

    def _draw_status_bar(self, status):
        """Draw the top status bar with flight phase and critical info."""
        pygame.draw.rect(
            self.screen, self.colors["panel_bg"], self.panels["status_bar"]
        )
        pygame.draw.rect(
            self.screen, self.colors["panel_border"], self.panels["status_bar"], 2
        )

        x_offset = 20
        y = self.panels["status_bar"].centery

        # Flight phase with color coding
        phase = status["flight_phase"].replace("_", " ").upper()
        phase_colors = {
            "PREFLIGHT": self.colors["info"],
            "TAXI": self.colors["caution"],
            "TAKEOFF": self.colors["warning"],
            "CLIMB": self.colors["normal"],
            "CRUISE": self.colors["normal"],
            "DESCENT": self.colors["caution"],
            "APPROACH": self.colors["warning"],
            "LANDING": self.colors["danger"],
        }
        phase_color = phase_colors.get(
            status["flight_phase"].upper(), self.colors["text_primary"]
        )

        phase_text = self.fonts["large"].render(f"PHASE: {phase}", True, phase_color)
        self.screen.blit(phase_text, (x_offset, y - phase_text.get_height() // 2))

        # Flight time
        x_offset += 300
        time_str = self._format_time(status["elapsed_time"])
        time_text = self.fonts["medium"].render(
            f"TIME: {time_str}", True, self.colors["text_primary"]
        )
        self.screen.blit(time_text, (x_offset, y - time_text.get_height() // 2))

        # Progress bar
        x_offset += 200
        self._draw_progress_bar(x_offset, y - 10, 300, 20, status["progress_percent"])

        # Autopilot status with details
        x_offset += 320
        if flight_simulator.autopilot_enabled:
            auto_text = self.fonts["medium"].render(
                "AUTOPILOT ON", True, self.colors["normal"]
            )
            # Add blinking effect
            if self.animations["beacon_flash"] > 1:
                self.screen.blit(auto_text, (x_offset, y - auto_text.get_height() // 2))

            # Show what autopilot is managing
            if (
                self.animations["beacon_flash"] > 1
            ):  # Only show when main text is visible
                detail_text = self.fonts["tiny"].render(
                    "HDG + TEMP MGMT", True, self.colors["text_secondary"]
                )
                self.screen.blit(detail_text, (x_offset, y + 8))
        else:
            auto_text = self.fonts["medium"].render(
                "MANUAL", True, self.colors["text_dim"]
            )
            self.screen.blit(auto_text, (x_offset, y - auto_text.get_height() // 2))
            detail_text = self.fonts["tiny"].render(
                "FULL CONTROL", True, self.colors["text_dim"]
            )
            self.screen.blit(detail_text, (x_offset, y + 8))

    def _draw_primary_flight_display(self, status):
        """Draw the primary flight display with attitude indicator and key instruments."""
        panel = self.panels["pfd"]
        self._draw_panel_background(panel, "PRIMARY FLIGHT DISPLAY")

        # Center point for instruments
        center_x = panel.centerx
        center_y = panel.centery + 20

        # === ATTITUDE INDICATOR (Artificial Horizon) ===
        self._draw_attitude_indicator(center_x, center_y - 60, 120, status)

        # === ALTITUDE TAPE ===
        self._draw_vertical_tape(
            panel.right - 80,
            center_y - 60,
            60,
            200,
            status["altitude"],
            0,
            50000,
            "ALT",
            "ft",
            self.colors["gauge_green"],
        )

        # === SPEED TAPE ===
        self._draw_vertical_tape(
            panel.left + 20,
            center_y - 60,
            60,
            200,
            status["airspeed"],
            0,
            600,
            "IAS",
            "kts",
            self.colors["gauge_green"],
        )

        # === COMPASS ===
        self._draw_compass(
            center_x, panel.bottom - 60, 50, status["heading"], status["target_heading"]
        )

        # === VERTICAL SPEED INDICATOR ===
        self._draw_vsi(panel.right - 40, center_y + 100, 30, status)

    def _draw_attitude_indicator(self, x, y, size, status):
        """Draw an attitude indicator (artificial horizon)."""
        # Background circle
        pygame.draw.circle(self.screen, self.colors["gauge_bg"], (x, y), size, 0)
        pygame.draw.circle(self.screen, self.colors["panel_border"], (x, y), size, 2)

        # Create clipping region
        clip_rect = pygame.Rect(x - size, y - size, size * 2, size * 2)
        self.screen.set_clip(clip_rect)

        # Draw sky and ground with pitch - limit to prevent wild spinning
        pitch_pixels = int(max(-30, min(30, self.animations["horizon_pitch"])) * 2)

        # Sky (blue gradient)
        sky_rect = pygame.Rect(x - size, y - size - pitch_pixels, size * 2, size)
        pygame.draw.rect(self.screen, (30, 100, 200), sky_rect)

        # Ground (brown)
        ground_rect = pygame.Rect(x - size, y - pitch_pixels, size * 2, size)
        pygame.draw.rect(self.screen, (101, 67, 33), ground_rect)

        # Horizon line
        pygame.draw.line(
            self.screen,
            self.colors["text_highlight"],
            (x - size, y - pitch_pixels),
            (x + size, y - pitch_pixels),
            3,
        )

        # Roll indicator (bank angle) - limit to prevent wild spinning
        roll = max(-30, min(30, self.animations["horizon_roll"]))
        if abs(roll) > 0.1:
            # Draw roll arc
            arc_rect = pygame.Rect(
                x - size + 10, y - size + 10, (size - 10) * 2, (size - 10) * 2
            )
            pygame.draw.arc(
                self.screen,
                self.colors["text_primary"],
                arc_rect,
                math.radians(270 - 30),
                math.radians(270 + 30),
                2,
            )

            # Roll indicator mark
            roll_angle = math.radians(270 + roll)
            roll_x = x + (size - 15) * math.cos(roll_angle)
            roll_y = y + (size - 15) * math.sin(roll_angle)
            pygame.draw.circle(
                self.screen, self.colors["warning"], (int(roll_x), int(roll_y)), 5
            )

        # Remove clipping
        self.screen.set_clip(None)

        # Aircraft symbol (fixed)
        pygame.draw.line(
            self.screen, self.colors["text_highlight"], (x - 30, y), (x + 30, y), 3
        )
        pygame.draw.line(
            self.screen, self.colors["text_highlight"], (x, y - 5), (x, y + 5), 3
        )

        # Pitch marks
        for i in range(-2, 3):
            if i != 0:
                mark_y = y + i * 20
                width = 20 if i % 2 == 0 else 10
                pygame.draw.line(
                    self.screen,
                    self.colors["text_primary"],
                    (x - width, mark_y),
                    (x + width, mark_y),
                    1,
                )
                if i % 2 == 0:
                    pitch_text = self.fonts["tiny"].render(
                        str(abs(i * 10)), True, self.colors["text_dim"]
                    )
                    self.screen.blit(pitch_text, (x + width + 5, mark_y - 5))

    def _draw_vertical_tape(
        self, x, y, width, height, value, min_val, max_val, label, unit, color
    ):
        """Draw a vertical scrolling tape indicator."""
        # Background
        tape_rect = pygame.Rect(x, y, width, height)
        pygame.draw.rect(self.screen, self.colors["gauge_bg"], tape_rect)
        pygame.draw.rect(self.screen, self.colors["panel_border"], tape_rect, 1)

        # Current value box
        value_rect = pygame.Rect(x - 5, y + height // 2 - 15, width + 10, 30)
        pygame.draw.rect(self.screen, self.colors["panel_bg"], value_rect)
        pygame.draw.rect(self.screen, color, value_rect, 2)

        # Draw tape markings
        center_value = value
        pixels_per_unit = 2  # Adjust for scale

        for i in range(-10, 11):
            mark_value = center_value + i * 10
            if min_val <= mark_value <= max_val:
                mark_y = y + height // 2 - i * pixels_per_unit * 10

                if mark_y > y and mark_y < y + height:
                    # Major marking every 50 units
                    if mark_value % 50 == 0:
                        pygame.draw.line(
                            self.screen,
                            self.colors["text_primary"],
                            (x + width - 15, mark_y),
                            (x + width, mark_y),
                            2,
                        )
                        if mark_value % 100 == 0:
                            mark_text = self.fonts["tiny"].render(
                                str(int(mark_value)), True, self.colors["text_dim"]
                            )
                            self.screen.blit(mark_text, (x + 5, mark_y - 6))
                    else:
                        pygame.draw.line(
                            self.screen,
                            self.colors["text_dim"],
                            (x + width - 8, mark_y),
                            (x + width, mark_y),
                            1,
                        )

        # Current value text
        value_text = self.fonts["normal"].render(
            f"{int(value)}", True, self.colors["text_highlight"]
        )
        value_text_rect = value_text.get_rect(center=(x + width // 2, y + height // 2))
        self.screen.blit(value_text, value_text_rect)

        # Label
        label_text = self.fonts["small"].render(
            label, True, self.colors["text_primary"]
        )
        self.screen.blit(label_text, (x + 5, y + 5))

        # Unit
        unit_text = self.fonts["tiny"].render(unit, True, self.colors["text_dim"])
        self.screen.blit(unit_text, (x + width // 2 - 10, y + height - 15))

    def _draw_compass(self, x, y, size, heading, target_heading):
        """Draw a compass with heading indicator."""
        # Outer ring
        pygame.draw.circle(self.screen, self.colors["gauge_bg"], (x, y), size, 0)
        pygame.draw.circle(self.screen, self.colors["panel_border"], (x, y), size, 2)

        # Draw compass markings
        for angle in range(0, 360, 10):
            rad = math.radians(angle - heading + 90)

            # Determine mark length
            if angle % 90 == 0:
                inner_radius = size - 15
                mark_width = 2
            elif angle % 30 == 0:
                inner_radius = size - 10
                mark_width = 2
            else:
                inner_radius = size - 5
                mark_width = 1

            x1 = x + inner_radius * math.cos(rad)
            y1 = y - inner_radius * math.sin(rad)
            x2 = x + size * math.cos(rad)
            y2 = y - size * math.sin(rad)

            pygame.draw.line(
                self.screen, self.colors["text_primary"], (x1, y1), (x2, y2), mark_width
            )

            # Draw cardinal directions
            if angle % 90 == 0:
                directions = {0: "N", 90: "E", 180: "S", 270: "W"}
                if angle in directions:
                    text_x = x + (size - 25) * math.cos(rad)
                    text_y = y - (size - 25) * math.sin(rad)
                    dir_text = self.fonts["small"].render(
                        directions[angle], True, self.colors["text_highlight"]
                    )
                    text_rect = dir_text.get_rect(center=(text_x, text_y))
                    self.screen.blit(dir_text, text_rect)

        # Target heading indicator
        target_rad = math.radians(target_heading - heading + 90)
        target_x = x + (size - 5) * math.cos(target_rad)
        target_y = y - (size - 5) * math.sin(target_rad)
        pygame.draw.circle(
            self.screen, self.colors["info"], (int(target_x), int(target_y)), 6
        )

        # Aircraft indicator (center)
        pygame.draw.polygon(
            self.screen,
            self.colors["warning"],
            [(x, y - 10), (x - 5, y + 5), (x + 5, y + 5)],
        )

        # Heading text
        heading_text = self.fonts["normal"].render(
            f"{int(heading)}°", True, self.colors["text_highlight"]
        )
        heading_rect = heading_text.get_rect(center=(x, y + size + 20))
        self.screen.blit(heading_text, heading_rect)

        # Target heading text
        target_text = self.fonts["small"].render(
            f"Target: {int(target_heading)}°", True, self.colors["info"]
        )
        target_rect = target_text.get_rect(center=(x, y + size + 40))
        self.screen.blit(target_text, target_rect)

    def _draw_vsi(self, x, y, size, status):
        """Draw vertical speed indicator."""
        # Simplified VSI - just show if climbing/descending
        vsi_value = 0
        if status["flight_phase"] == "climb":
            vsi_value = 500
        elif status["flight_phase"] == "descent":
            vsi_value = -400

        # Draw gauge
        pygame.draw.circle(self.screen, self.colors["gauge_bg"], (x, y), size)
        pygame.draw.circle(self.screen, self.colors["panel_border"], (x, y), size, 1)

        # Draw needle
        angle = max(-60, min(60, vsi_value / 10))  # Scale to degrees
        rad = math.radians(270 + angle)
        needle_x = x + (size - 5) * math.cos(rad)
        needle_y = y + (size - 5) * math.sin(rad)
        pygame.draw.line(
            self.screen, self.colors["gauge_needle"], (x, y), (needle_x, needle_y), 2
        )

        # Label
        vsi_text = self.fonts["tiny"].render("VSI", True, self.colors["text_dim"])
        vsi_rect = vsi_text.get_rect(center=(x, y + size + 10))
        self.screen.blit(vsi_text, vsi_rect)

    def _draw_navigation_display(self, status):
        """Draw the navigation display with map and route."""
        panel = self.panels["nav"]
        self._draw_panel_background(panel, "NAVIGATION DISPLAY")

        # Map area
        map_rect = pygame.Rect(
            panel.x + 20, panel.y + 40, panel.width - 40, panel.height - 80
        )
        pygame.draw.rect(self.screen, self.colors["map_bg"], map_rect)
        pygame.draw.rect(self.screen, self.colors["panel_border"], map_rect, 1)

        # Draw grid
        for i in range(1, 5):
            x_line = map_rect.x + (map_rect.width // 5) * i
            y_line = map_rect.y + (map_rect.height // 5) * i
            pygame.draw.line(
                self.screen,
                self.colors["map_grid"],
                (x_line, map_rect.y),
                (x_line, map_rect.bottom),
                1,
            )
            pygame.draw.line(
                self.screen,
                self.colors["map_grid"],
                (map_rect.x, y_line),
                (map_rect.right, y_line),
                1,
            )

        # Draw route line
        if (
            hasattr(flight_simulator, "current_flight")
            and flight_simulator.current_flight
        ):
            # Simple route visualization
            start_x = map_rect.x + 50
            start_y = map_rect.centery
            end_x = map_rect.right - 50
            end_y = map_rect.centery

            pygame.draw.line(
                self.screen,
                self.colors["map_route"],
                (start_x, start_y),
                (end_x, end_y),
                3,
            )

            # Departure point
            pygame.draw.circle(
                self.screen, self.colors["normal"], (start_x, start_y), 8
            )
            dep_text = self.fonts["tiny"].render(
                "DEP", True, self.colors["text_primary"]
            )
            self.screen.blit(dep_text, (start_x - 15, start_y + 10))

            # Destination point
            pygame.draw.circle(self.screen, self.colors["warning"], (end_x, end_y), 8)
            dest_text = self.fonts["tiny"].render(
                "DEST", True, self.colors["text_primary"]
            )
            self.screen.blit(dest_text, (end_x - 15, end_y + 10))

            # Current position
            progress = status["progress_percent"] / 100
            current_x = int(start_x + (end_x - start_x) * progress)
            current_y = int(start_y + (end_y - start_y) * progress)

            # Add drift visualization
            drift_offset = status["off_course_distance"] * 5  # Scale for visibility
            current_y += int(drift_offset)

            # Aircraft icon with rotation
            self._draw_aircraft_icon(current_x, current_y, status["heading"])

            # Distance remaining
            if flight_simulator.current_flight:
                distance_remaining = flight_simulator.current_flight.distance_nm * (
                    1 - progress
                )
                dist_text = self.fonts["small"].render(
                    f"{distance_remaining:.1f} nm to go",
                    True,
                    self.colors["text_primary"],
                )
                self.screen.blit(
                    dist_text, (map_rect.centerx - 50, map_rect.bottom - 30)
                )

        # Radar sweep animation
        sweep_angle = math.radians(self.animations["radar_sweep"] % 360)
        sweep_x = panel.centerx + 150 * math.cos(sweep_angle)
        sweep_y = panel.centery + 150 * math.sin(sweep_angle)
        pygame.draw.line(
            self.screen,
            (0, 255, 0, 50),
            (panel.centerx, panel.centery),
            (sweep_x, sweep_y),
            2,
        )

    def _draw_aircraft_icon(self, x, y, heading):
        """Draw an aircraft icon at the specified position."""
        # Create aircraft shape points
        size = 10
        angle = math.radians(heading - 90)

        # Calculate rotated points for aircraft shape
        points = []
        # Nose
        points.append((x + size * math.cos(angle), y + size * math.sin(angle)))
        # Left wing
        points.append(
            (
                x + size * 0.7 * math.cos(angle + 2.5),
                y + size * 0.7 * math.sin(angle + 2.5),
            )
        )
        # Tail
        points.append(
            (x - size * 0.5 * math.cos(angle), y - size * 0.5 * math.sin(angle))
        )
        # Right wing
        points.append(
            (
                x + size * 0.7 * math.cos(angle - 2.5),
                y + size * 0.7 * math.sin(angle - 2.5),
            )
        )

        # Draw aircraft
        pygame.draw.polygon(self.screen, self.colors["map_aircraft"], points)

        # Add blinking beacon
        if self.animations["beacon_flash"] > 1:
            pygame.draw.circle(self.screen, self.colors["danger"], (x, y), 3)

    def _draw_engine_display(self, status):
        """Draw engine and systems display."""
        panel = self.panels["engine"]
        self._draw_panel_background(panel, "ENGINE")

        y_offset = panel.y + 50

        # Engine temperature gauge
        self._draw_gauge_bar(
            panel.x + 20,
            y_offset,
            panel.width - 40,
            30,
            status["engine_temp"],
            0,
            250,
            "TEMP",
            "°F",
            [
                (0, 180, self.colors["normal"]),
                (180, 220, self.colors["caution"]),
                (220, 250, self.colors["danger"]),
            ],
        )

        y_offset += 60

        # Fuel gauge
        self._draw_gauge_bar(
            panel.x + 20,
            y_offset,
            panel.width - 40,
            30,
            status["fuel_remaining"],
            0,
            100,
            "FUEL",
            "%",
            [
                (0, 20, self.colors["danger"]),
                (20, 50, self.colors["caution"]),
                (50, 100, self.colors["normal"]),
            ],
        )

        y_offset += 60

        # Oil pressure (simulated)
        oil_pressure = 50 + random.uniform(-5, 5)
        self._draw_gauge_bar(
            panel.x + 20,
            y_offset,
            panel.width - 40,
            30,
            oil_pressure,
            0,
            100,
            "OIL",
            "PSI",
            [
                (0, 25, self.colors["danger"]),
                (25, 75, self.colors["normal"]),
                (75, 100, self.colors["danger"]),
            ],
        )

        y_offset += 60

        # Electrical (simulated)
        voltage = 28 + random.uniform(-0.5, 0.5)
        self._draw_digital_display(
            panel.x + 20,
            y_offset,
            panel.width - 40,
            40,
            f"{voltage:.1f}V",
            "ELEC",
            self.colors["normal"],
        )

        y_offset += 60

        # Hydraulics (simulated)
        hyd_pressure = 3000 + random.uniform(-100, 100)
        self._draw_digital_display(
            panel.x + 20,
            y_offset,
            panel.width - 40,
            40,
            f"{int(hyd_pressure)}",
            "HYD",
            self.colors["normal"],
        )

    def _draw_gauge_bar(
        self, x, y, width, height, value, min_val, max_val, label, unit, color_zones
    ):
        """Draw a horizontal bar gauge with color zones."""
        # Background
        pygame.draw.rect(self.screen, self.colors["gauge_bg"], (x, y, width, height))
        pygame.draw.rect(
            self.screen, self.colors["panel_border"], (x, y, width, height), 1
        )

        # Draw color zones
        for zone_min, zone_max, color in color_zones:
            if min_val <= zone_max and max_val >= zone_min:
                zone_x = x + (zone_min - min_val) / (max_val - min_val) * width
                zone_width = (
                    (min(zone_max, max_val) - max(zone_min, min_val))
                    / (max_val - min_val)
                    * width
                )
                pygame.draw.rect(
                    self.screen, (*color, 50), (zone_x, y, zone_width, height)
                )

        # Value bar
        bar_width = (value - min_val) / (max_val - min_val) * width
        bar_color = self.colors["normal"]
        for zone_min, zone_max, color in color_zones:
            if zone_min <= value <= zone_max:
                bar_color = color
                break

        pygame.draw.rect(self.screen, bar_color, (x, y, bar_width, height))

        # Label and value
        label_text = self.fonts["tiny"].render(label, True, self.colors["text_dim"])
        self.screen.blit(label_text, (x + 2, y + 2))

        value_text = self.fonts["small"].render(
            f"{value:.1f}{unit}", True, self.colors["text_primary"]
        )
        value_rect = value_text.get_rect(midright=(x + width - 5, y + height // 2))
        self.screen.blit(value_text, value_rect)

    def _draw_digital_display(self, x, y, width, height, value, label, color):
        """Draw a digital display readout."""
        # Background with LCD effect
        pygame.draw.rect(self.screen, (10, 20, 10), (x, y, width, height))
        pygame.draw.rect(
            self.screen, self.colors["panel_border"], (x, y, width, height), 1
        )

        # Label
        label_text = self.fonts["tiny"].render(label, True, self.colors["text_dim"])
        self.screen.blit(label_text, (x + 2, y + 2))

        # Digital value
        value_text = self.fonts["digital"].render(value, True, color)
        value_rect = value_text.get_rect(center=(x + width // 2, y + height // 2 + 5))
        self.screen.blit(value_text, value_rect)

    def _draw_radio_panel(self, status):
        """Draw radio/communications panel."""
        panel = self.panels["radio"]
        self._draw_panel_background(panel, "RADIO / COMM")

        y_offset = panel.y + 40

        # Simulated radio frequencies
        frequencies = [
            ("COM1", "118.300", self.colors["normal"]),
            ("COM2", "121.500", self.colors["text_dim"]),
            ("NAV1", "110.200", self.colors["info"]),
            ("NAV2", "109.400", self.colors["text_dim"]),
        ]

        for name, freq, color in frequencies:
            freq_text = f"{name}: {freq}"
            text_surface = self.fonts["normal"].render(freq_text, True, color)
            self.screen.blit(text_surface, (panel.x + 20, y_offset))
            y_offset += 30

        # Transponder
        pygame.draw.line(
            self.screen,
            self.colors["panel_border"],
            (panel.x + 20, y_offset),
            (panel.right - 20, y_offset),
            1,
        )
        y_offset += 10

        xpdr_text = self.fonts["normal"].render(
            "XPDR: 1200", True, self.colors["normal"]
        )
        self.screen.blit(xpdr_text, (panel.x + 20, y_offset))

        squawk_text = self.fonts["small"].render("VFR", True, self.colors["text_dim"])
        self.screen.blit(squawk_text, (panel.x + 140, y_offset + 3))

    def _draw_flight_info_panel(self, status):
        """Draw flight information panel."""
        panel = self.panels["info"]
        self._draw_panel_background(panel, "FLIGHT INFO")

        y_offset = panel.y + 40
        line_height = 25

        # Flight details
        if (
            hasattr(flight_simulator, "current_flight")
            and flight_simulator.current_flight
        ):
            flight_plan = flight_simulator.current_flight

            info_items = [
                ("FROM", flight_plan.departure.name[:20], self.colors["text_primary"]),
                ("TO", flight_plan.destination.name[:20], self.colors["text_primary"]),
                (
                    "DIST",
                    f"{flight_plan.distance_nm:.0f} nm",
                    self.colors["text_secondary"],
                ),
                ("ETA", self._calculate_eta(status), self.colors["info"]),
                (
                    "FL",
                    f"{flight_plan.cruise_altitude // 100:03d}",
                    self.colors["text_secondary"],
                ),
                (
                    "TAS",
                    f"{flight_plan.cruise_speed} kts",
                    self.colors["text_secondary"],
                ),
            ]

            for label, value, color in info_items:
                label_surface = self.fonts["small"].render(
                    f"{label}:", True, self.colors["text_dim"]
                )
                value_surface = self.fonts["small"].render(value, True, color)

                self.screen.blit(label_surface, (panel.x + 20, y_offset))
                self.screen.blit(value_surface, (panel.x + 80, y_offset))
                y_offset += line_height

    def _draw_weather_panel(self, status):
        """Draw weather information panel."""
        panel = self.panels["weather"]
        self._draw_panel_background(panel, "WEATHER")

        weather = status["weather"]
        y_offset = panel.y + 40

        # Weather condition with icon
        condition_text = weather["condition"].replace("_", " ").upper()
        condition_colors = {
            "CLEAR": self.colors["normal"],
            "LIGHT WIND": self.colors["normal"],
            "MODERATE WIND": self.colors["caution"],
            "TURBULENCE": self.colors["warning"],
            "RAIN": self.colors["info"],
        }
        condition_color = condition_colors.get(
            condition_text, self.colors["text_primary"]
        )

        cond_surface = self.fonts["medium"].render(
            condition_text, True, condition_color
        )
        self.screen.blit(cond_surface, (panel.x + 20, y_offset))
        y_offset += 35

        # Wind information
        wind_text = (
            f"WIND: {weather['wind_direction']:03d}° @ {weather['wind_speed']} kts"
        )
        wind_surface = self.fonts["small"].render(
            wind_text, True, self.colors["text_primary"]
        )
        self.screen.blit(wind_surface, (panel.x + 20, y_offset))
        y_offset += 25

        # Visibility
        vis_text = f"VIS: {weather['visibility']} miles"
        vis_surface = self.fonts["small"].render(
            vis_text, True, self.colors["text_primary"]
        )
        self.screen.blit(vis_surface, (panel.x + 20, y_offset))
        y_offset += 25

        # Temperature (simulated)
        temp = 15 - (status["altitude"] // 1000) * 2  # Temperature drops with altitude
        temp_text = f"TEMP: {temp}°C"
        temp_color = self.colors["normal"] if temp > 0 else self.colors["info"]
        temp_surface = self.fonts["small"].render(temp_text, True, temp_color)
        self.screen.blit(temp_surface, (panel.x + 20, y_offset))
        y_offset += 25

        # Pressure (simulated)
        pressure = 29.92 - (status["altitude"] / 1000) * 0.1
        press_text = f"QNH: {pressure:.2f} in"
        press_surface = self.fonts["small"].render(
            press_text, True, self.colors["text_secondary"]
        )
        self.screen.blit(press_surface, (panel.x + 20, y_offset))

    def _draw_alerts_panel(self, status):
        """Draw system alerts panel."""
        panel = self.panels["alerts"]

        # Flash border if there are warnings
        border_color = self.colors["panel_border"]
        if status["system_alerts"] and self.animations["warning_flash"] > 1:
            border_color = self.colors["danger"]

        self._draw_panel_background(panel, "ALERTS", border_color)

        y_offset = panel.y + 40

        if status["system_alerts"]:
            # Show recent alerts
            for alert in status["system_alerts"][-6:]:  # Last 6 alerts
                # Determine alert color
                alert_color = self.colors["text_primary"]
                if "WARNING" in alert.upper():
                    alert_color = self.colors["warning"]
                elif "EMERGENCY" in alert.upper():
                    alert_color = self.colors["danger"]
                elif "deviation" in alert.lower():
                    alert_color = self.colors["caution"]

                # Truncate if too long
                if len(alert) > 25:
                    alert = alert[:22] + "..."

                alert_surface = self.fonts["small"].render(alert, True, alert_color)
                self.screen.blit(alert_surface, (panel.x + 10, y_offset))
                y_offset += 22
        else:
            # No alerts
            no_alerts = self.fonts["normal"].render(
                "No active alerts", True, self.colors["normal"]
            )
            no_alerts_rect = no_alerts.get_rect(center=(panel.centerx, panel.centery))
            self.screen.blit(no_alerts, no_alerts_rect)

    def _draw_control_panel(self, status):
        """Draw the bottom control panel."""
        panel = self.panels["controls"]

        # Gradient background
        for y in range(panel.height):
            ratio = y / panel.height
            color_value = int(20 + 20 * ratio)
            pygame.draw.line(
                self.screen,
                (color_value, color_value, color_value + 10),
                (panel.x, panel.y + y),
                (panel.right, panel.y + y),
            )

        pygame.draw.rect(self.screen, self.colors["panel_border"], panel, 2)

        # Control labels
        label_y = panel.y + 10

        # Heading control section
        heading_label = self.fonts["normal"].render(
            "HEADING CONTROL", True, self.colors["text_primary"]
        )
        self.screen.blit(heading_label, (50, label_y))

        # Current vs target heading display
        heading_diff = status["heading"] - status["target_heading"]
        if heading_diff > 180:
            heading_diff -= 360
        elif heading_diff < -180:
            heading_diff += 360

        diff_color = (
            self.colors["normal"] if abs(heading_diff) < 5 else self.colors["warning"]
        )
        diff_text = f"HDG: {status['heading']:03d}° | TGT: {status['target_heading']:03d}° | DIFF: {heading_diff:+.1f}°"
        diff_surface = self.fonts["small"].render(diff_text, True, diff_color)
        self.screen.blit(diff_surface, (50, label_y + 25))

        # Autopilot status indicator
        if flight_simulator.autopilot_enabled:
            auto_rect = pygame.Rect(320, label_y, 80, 30)
            pygame.draw.rect(self.screen, self.colors["normal"], auto_rect, 2)
            auto_text = self.fonts["small"].render("AUTO", True, self.colors["normal"])
            auto_text_rect = auto_text.get_rect(center=auto_rect.center)
            self.screen.blit(auto_text, auto_text_rect)

        # Keyboard hints
        hints_text = "Keys: ← → (turn) | Shift + ← → (5°) | A (auto) | L (legend) | H (help) | ESC (end)"
        hints_surface = self.fonts["tiny"].render(
            hints_text, True, self.colors["text_dim"]
        )
        self.screen.blit(hints_surface, (50, panel.bottom - 20))

    def _draw_panel_background(self, rect, title, border_color=None):
        """Draw a standardized panel background with title."""
        # Background with gradient
        for y in range(rect.height):
            ratio = y / rect.height
            color_value = int(15 + 10 * ratio)
            pygame.draw.line(
                self.screen,
                (color_value, color_value + 5, color_value + 10),
                (rect.x, rect.y + y),
                (rect.right, rect.y + y),
            )

        # Border
        if border_color is None:
            border_color = self.colors["panel_border"]
        pygame.draw.rect(self.screen, border_color, rect, 2)

        # Title bar
        title_rect = pygame.Rect(rect.x, rect.y, rect.width, 30)
        pygame.draw.rect(self.screen, self.colors["panel_bg"], title_rect)
        pygame.draw.rect(self.screen, border_color, title_rect, 2)

        # Title text
        title_surface = self.fonts["small"].render(
            title, True, self.colors["text_primary"]
        )
        title_text_rect = title_surface.get_rect(center=(rect.centerx, rect.y + 15))
        self.screen.blit(title_surface, title_text_rect)

    def _draw_progress_bar(self, x, y, width, height, percent):
        """Draw a progress bar."""
        # Background
        pygame.draw.rect(self.screen, self.colors["gauge_bg"], (x, y, width, height))

        # Progress fill
        fill_width = int((percent / 100) * width)

        # Color based on progress
        if percent < 25:
            fill_color = self.colors["danger"]
        elif percent < 50:
            fill_color = self.colors["warning"]
        elif percent < 75:
            fill_color = self.colors["caution"]
        else:
            fill_color = self.colors["normal"]

        pygame.draw.rect(self.screen, fill_color, (x, y, fill_width, height))

        # Border
        pygame.draw.rect(
            self.screen, self.colors["panel_border"], (x, y, width, height), 1
        )

        # Progress text
        progress_text = self.fonts["tiny"].render(
            f"{percent:.1f}%", True, self.colors["text_primary"]
        )
        text_rect = progress_text.get_rect(center=(x + width // 2, y + height // 2))
        self.screen.blit(progress_text, text_rect)

    def _draw_particles(self):
        """Draw particle effects."""
        for particle in self.particles:
            alpha = int(255 * (particle["life"] / 2.0))
            color = (*particle["color"], alpha)
            size = int(particle["size"] * (particle["life"] / 2.0))

            if size > 0:
                particle_surface = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
                pygame.draw.circle(particle_surface, color, (size, size), size)
                self.screen.blit(
                    particle_surface, (particle["x"] - size, particle["y"] - size)
                )

    def _draw_warning_overlays(self, status):
        """Draw warning overlays for critical situations."""
        if status["emergency_state"]:
            # Red flashing overlay
            if self.animations["warning_flash"] > 1:
                warning_surface = pygame.Surface(
                    (self.width, self.height), pygame.SRCALPHA
                )
                warning_surface.fill((255, 0, 0, 30))
                self.screen.blit(warning_surface, (0, 0))

                # Emergency text
                emergency_text = self.fonts["huge"].render(
                    "EMERGENCY", True, self.colors["danger"]
                )
                emergency_rect = emergency_text.get_rect(center=(self.width // 2, 100))
                self.screen.blit(emergency_text, emergency_rect)

        elif status["off_course_distance"] > 5:
            # Course deviation warning
            if self.animations["warning_flash"] > 1:
                warning_text = self.fonts["large"].render(
                    "COURSE DEVIATION", True, self.colors["warning"]
                )
                warning_rect = warning_text.get_rect(center=(self.width // 2, 100))
                self.screen.blit(warning_text, warning_rect)

    def _draw_legend_overlay(self):
        """Draw the legend overlay."""
        # Dark background
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        self.screen.blit(overlay, (0, 0))

        # Legend panel
        legend_rect = pygame.Rect(self.width // 2 - 400, 100, 800, self.height - 200)
        pygame.draw.rect(self.screen, self.colors["panel_bg"], legend_rect)
        pygame.draw.rect(self.screen, self.colors["panel_border"], legend_rect, 2)

        # Title
        title = self.fonts["large"].render(
            "INSTRUMENT LEGEND", True, self.colors["text_highlight"]
        )
        title_rect = title.get_rect(centerx=legend_rect.centerx, y=legend_rect.y + 20)
        self.screen.blit(title, title_rect)

        # Legend items
        y_offset = legend_rect.y + 70
        legend_items = [
            ("PRIMARY FLIGHT DISPLAY", self.colors["text_primary"], True),
            ("  ALT - Altitude in feet", self.colors["text_secondary"], False),
            (
                "  IAS - Indicated Airspeed in knots",
                self.colors["text_secondary"],
                False,
            ),
            ("  HDG - Heading in degrees", self.colors["text_secondary"], False),
            (
                "  Attitude Indicator - Shows aircraft pitch and roll",
                self.colors["text_secondary"],
                False,
            ),
            ("  VSI - Vertical Speed Indicator", self.colors["text_secondary"], False),
            ("", self.colors["text_primary"], False),
            ("ENGINE DISPLAY", self.colors["text_primary"], True),
            (
                "  TEMP - Engine temperature (keep below 220°F)",
                self.colors["text_secondary"],
                False,
            ),
            (
                "  FUEL - Fuel remaining percentage",
                self.colors["text_secondary"],
                False,
            ),
            ("  OIL - Oil pressure in PSI", self.colors["text_secondary"], False),
            (
                "  ELEC - Electrical system voltage",
                self.colors["text_secondary"],
                False,
            ),
            ("  HYD - Hydraulic system pressure", self.colors["text_secondary"], False),
            ("", self.colors["text_primary"], False),
            ("NAVIGATION DISPLAY", self.colors["text_primary"], True),
            ("  Blue line - Planned route", self.colors["info"], False),
            ("  Yellow icon - Your aircraft", self.colors["caution"], False),
            ("  Green circle - Departure airport", self.colors["normal"], False),
            ("  Orange circle - Destination airport", self.colors["warning"], False),
            ("", self.colors["text_primary"], False),
            ("COLOR CODES", self.colors["text_primary"], True),
            ("  Green - Normal/Good", self.colors["normal"], False),
            ("  Yellow - Caution", self.colors["caution"], False),
            ("  Orange - Warning", self.colors["warning"], False),
            ("  Red - Danger/Emergency", self.colors["danger"], False),
        ]

        for text, color, is_header in legend_items:
            if text:
                font = self.fonts["normal"] if is_header else self.fonts["small"]
                text_surface = font.render(text, True, color)
                self.screen.blit(text_surface, (legend_rect.x + 40, y_offset))
            y_offset += 22 if is_header else 20

        # Close instruction
        close_text = self.fonts["normal"].render(
            "Press 'L' or click LEGEND to close", True, self.colors["text_dim"]
        )
        close_rect = close_text.get_rect(
            centerx=legend_rect.centerx, bottom=legend_rect.bottom - 20
        )
        self.screen.blit(close_text, close_rect)

    def _draw_help_overlay(self):
        """Draw the help overlay."""
        # Dark background
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        self.screen.blit(overlay, (0, 0))

        # Help panel
        help_rect = pygame.Rect(self.width // 2 - 350, 80, 700, self.height - 160)
        pygame.draw.rect(self.screen, self.colors["panel_bg"], help_rect)
        pygame.draw.rect(self.screen, self.colors["panel_border"], help_rect, 2)

        # Title
        title = self.fonts["large"].render(
            "FLIGHT CONTROLS HELP", True, self.colors["text_highlight"]
        )
        title_rect = title.get_rect(centerx=help_rect.centerx, y=help_rect.y + 20)
        self.screen.blit(title, title_rect)

        # Help content
        y_offset = help_rect.y + 70
        help_items = [
            ("KEYBOARD CONTROLS", self.colors["info"], True),
            ("← / → : Turn left/right 1 degree", self.colors["text_primary"], False),
            (
                "Shift + ← / → : Turn left/right 5 degrees",
                self.colors["text_primary"],
                False,
            ),
            ("A : Toggle autopilot", self.colors["text_primary"], False),
            ("C : Center heading to target", self.colors["text_primary"], False),
            ("L : Show/hide legend", self.colors["text_primary"], False),
            ("H or F1 : Show/hide this help", self.colors["text_primary"], False),
            ("ESC : End flight", self.colors["text_primary"], False),
            ("", self.colors["text_primary"], False),
            ("FLIGHT TIPS", self.colors["info"], True),
            (
                "• Watch your heading - aircraft constantly drifts",
                self.colors["text_secondary"],
                False,
            ),
            (
                "• Keep heading close to target heading (blue indicator)",
                self.colors["text_secondary"],
                False,
            ),
            (
                "• Monitor engine temperature - don't let it overheat",
                self.colors["text_secondary"],
                False,
            ),
            (
                "• Watch fuel gauge - emergency landing if you run out",
                self.colors["text_secondary"],
                False,
            ),
            (
                "• Autopilot helps but doesn't eliminate all drift",
                self.colors["text_secondary"],
                False,
            ),
            (
                "• Weather affects how much the aircraft drifts",
                self.colors["text_secondary"],
                False,
            ),
            ("", self.colors["text_primary"], False),
            ("DESERT BUS MODE", self.colors["warning"], True),
            (
                "This flight simulation requires constant attention!",
                self.colors["text_secondary"],
                False,
            ),
            (
                "The aircraft will drift off course if you don't correct it.",
                self.colors["text_secondary"],
                False,
            ),
            (
                "Real-time flights can take hours - stay alert!",
                self.colors["text_secondary"],
                False,
            ),
        ]

        for text, color, is_header in help_items:
            if text:
                font = self.fonts["normal"] if is_header else self.fonts["small"]
                text_surface = font.render(text, True, color)
                self.screen.blit(text_surface, (help_rect.x + 40, y_offset))
            y_offset += 25 if is_header else 22

        # Close instruction
        close_text = self.fonts["normal"].render(
            "Press 'H' or click HELP to close", True, self.colors["text_dim"]
        )
        close_rect = close_text.get_rect(
            centerx=help_rect.centerx, bottom=help_rect.bottom - 20
        )
        self.screen.blit(close_text, close_rect)

    # === CONTROL CALLBACKS ===

    def _correct_left_10(self):
        flight_simulator.apply_course_correction(-10)
        self._add_message("Course correction: -10°")

    def _correct_left_5(self):
        flight_simulator.apply_course_correction(-5)
        self._add_message("Course correction: -5°")

    def _correct_left_1(self):
        flight_simulator.apply_course_correction(-1)

    def _correct_right_1(self):
        flight_simulator.apply_course_correction(1)

    def _correct_right_5(self):
        flight_simulator.apply_course_correction(5)
        self._add_message("Course correction: +5°")

    def _correct_right_10(self):
        flight_simulator.apply_course_correction(10)
        self._add_message("Course correction: +10°")

    def _toggle_autopilot(self):
        current = flight_simulator.autopilot_enabled
        flight_simulator.set_autopilot(not current)
        self._add_message(f"Autopilot {'ON' if not current else 'OFF'}")

    def _center_heading(self):
        """Center heading to target heading."""
        status = flight_simulator._get_status()
        correction = status["target_heading"] - status["heading"]
        if correction > 180:
            correction -= 360
        elif correction < -180:
            correction += 360
        flight_simulator.apply_course_correction(correction)
        self._add_message("Centered to target heading")

    def _toggle_legend(self):
        self.legend_visible = not self.legend_visible

    def _toggle_help(self):
        self.help_overlay_visible = not self.help_overlay_visible

    def _add_message(self, message):
        """Add a message to the log."""
        self.message_log.append({"text": message, "time": time.time()})
        if len(self.message_log) > 10:
            self.message_log.pop(0)

    # === UTILITY METHODS ===

    def _format_time(self, seconds):
        """Format time as HH:MM:SS."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"

    def _calculate_eta(self, status):
        """Calculate estimated time of arrival."""
        if (
            not hasattr(flight_simulator, "current_flight")
            or not flight_simulator.current_flight
        ):
            return "N/A"

        total_time = flight_simulator.current_flight.estimated_time_minutes * 60
        elapsed = status["elapsed_time"]
        remaining = total_time - elapsed

        if remaining < 0:
            return "OVERDUE"

        return self._format_time(remaining)

    def show(self):
        """Show the flight UI."""
        self.legend_visible = False
        self.help_overlay_visible = False
        self.message_log.clear()
        self._add_message("Flight UI activated - check help (H) for controls")

    def hide(self):
        """Hide the flight UI."""
        self.legend_visible = False
        self.help_overlay_visible = False
