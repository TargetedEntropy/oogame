import time
import math
import random
from typing import Dict, Tuple, Optional, List
from dataclasses import dataclass
from enum import Enum
from core.npc_system import Location, npc_manager

class FlightPhase(Enum):
    PREFLIGHT = "preflight"
    TAXI = "taxi"
    TAKEOFF = "takeoff"
    CLIMB = "climb"
    CRUISE = "cruise"
    DESCENT = "descent"
    APPROACH = "approach"
    LANDING = "landing"
    TAXI_TO_GATE = "taxi_to_gate"
    COMPLETED = "completed"

class WeatherCondition(Enum):
    CLEAR = "clear"
    LIGHT_WIND = "light_wind"
    MODERATE_WIND = "moderate_wind"
    TURBULENCE = "turbulence"
    RAIN = "rain"

@dataclass
class FlightPlan:
    departure: Location
    destination: Location
    aircraft_type: str
    distance_nm: float  # Nautical miles
    estimated_time_minutes: int
    cruise_altitude: int
    cruise_speed: int  # Knots
    fuel_required: float  # Gallons

@dataclass
class WeatherData:
    condition: WeatherCondition
    wind_direction: int  # Degrees
    wind_speed: int  # Knots
    crosswind_component: float
    visibility: int  # Miles
    temperature: int  # Fahrenheit

class FlightSimulator:
    def __init__(self):
        self.current_flight: Optional[FlightPlan] = None
        self.flight_phase = FlightPhase.PREFLIGHT
        self.is_flying = False
        self.flight_start_time = 0.0
        self.elapsed_time = 0.0

        # Aircraft state
        self.altitude = 0  # Feet
        self.airspeed = 0  # Knots
        self.heading = 0  # Degrees (0-359)
        self.target_heading = 0
        self.engine_temp = 180  # Fahrenheit
        self.fuel_remaining = 100.0  # Percentage
        self.autopilot_enabled = False

        # Position tracking
        self.current_lat = 0.0
        self.current_lng = 0.0
        self.progress_percent = 0.0

        # Desert Bus style mechanics
        self.drift_rate = 0.0  # Degrees per second drift
        self.wind_effect = 0.0
        self.last_correction_time = 0.0
        self.off_course_distance = 0.0  # Nautical miles off course

        # Weather
        self.current_weather = self._generate_weather()

        # System failures and alerts
        self.system_alerts: List[str] = []
        self.emergency_state = False

        # Performance tracking
        self.course_deviations = 0
        self.system_alerts_count = 0
        self.fuel_efficiency = 100.0

    def _generate_weather(self) -> WeatherData:
        """Generate random weather conditions for the flight."""
        conditions = list(WeatherCondition)
        condition = random.choice(conditions)

        wind_dir = random.randint(0, 359)
        wind_speed = random.randint(5, 25)

        # Calculate crosswind component (simplified)
        crosswind = wind_speed * math.sin(math.radians(abs(wind_dir - self.heading)))

        return WeatherData(
            condition=condition,
            wind_direction=wind_dir,
            wind_speed=wind_speed,
            crosswind_component=crosswind,
            visibility=random.randint(3, 10),
            temperature=random.randint(32, 85)
        )

    def calculate_flight_plan(self, departure: Location, destination: Location, aircraft_type: str) -> FlightPlan:
        """Calculate flight plan between two airports."""
        # Calculate great circle distance
        lat1, lng1 = math.radians(departure.coordinates[0]), math.radians(departure.coordinates[1])
        lat2, lng2 = math.radians(destination.coordinates[0]), math.radians(destination.coordinates[1])

        dlat = lat2 - lat1
        dlng = lng2 - lng1

        a = (math.sin(dlat/2)**2 +
             math.cos(lat1) * math.cos(lat2) * math.sin(dlng/2)**2)
        c = 2 * math.asin(math.sqrt(a))

        # Distance in nautical miles (Earth radius ≈ 3440 nm)
        distance_nm = 3440 * c

        # Aircraft performance characteristics
        aircraft_specs = self._get_aircraft_specs(aircraft_type)

        # Calculate flight time
        estimated_minutes = int((distance_nm / aircraft_specs['cruise_speed']) * 60)

        # Add time for taxi, takeoff, climb, descent, landing
        estimated_minutes += 20  # 20 minutes for airport operations

        return FlightPlan(
            departure=departure,
            destination=destination,
            aircraft_type=aircraft_type,
            distance_nm=distance_nm,
            estimated_time_minutes=estimated_minutes,
            cruise_altitude=aircraft_specs['cruise_altitude'],
            cruise_speed=aircraft_specs['cruise_speed'],
            fuel_required=distance_nm * aircraft_specs['fuel_consumption']
        )

    def _get_aircraft_specs(self, aircraft_type: str) -> Dict:
        """Get performance specifications for different aircraft types."""
        specs = {
            "SINGLE_ENGINE_PROPS": {
                "cruise_speed": 120,  # knots
                "cruise_altitude": 6500,  # feet
                "fuel_consumption": 1.2,  # gallons per nm
                "drift_sensitivity": 1.0  # Reduced from 2.0
            },
            "MULTI_ENGINE_PROPS": {
                "cruise_speed": 180,
                "cruise_altitude": 12000,
                "fuel_consumption": 2.5,
                "drift_sensitivity": 0.8  # Reduced from 1.5
            },
            "JETS_COMMERCIAL": {
                "cruise_speed": 450,
                "cruise_altitude": 35000,
                "fuel_consumption": 8.0,
                "drift_sensitivity": 0.5  # Reduced from 0.8
            },
            "JETS_MILITARY": {
                "cruise_speed": 500,
                "cruise_altitude": 40000,
                "fuel_consumption": 12.0,
                "drift_sensitivity": 0.3  # Reduced from 0.5
            },
            "SEAPLANES_AMPHIBIANS": {
                "cruise_speed": 140,
                "cruise_altitude": 8000,
                "fuel_consumption": 1.8,
                "drift_sensitivity": 1.2  # Reduced from 2.5
            },
            "HELICOPTERS_ROTORCRAFT": {
                "cruise_speed": 100,
                "cruise_altitude": 1500,
                "fuel_consumption": 2.0,
                "drift_sensitivity": 1.5  # Reduced from 3.0
            }
        }
        return specs.get(aircraft_type, specs["SINGLE_ENGINE_PROPS"])

    def start_flight(self, flight_plan: FlightPlan) -> bool:
        """Start a new flight with the given flight plan."""
        if self.is_flying:
            return False

        self.current_flight = flight_plan
        self.flight_phase = FlightPhase.PREFLIGHT
        self.is_flying = True
        self.flight_start_time = time.time()
        self.elapsed_time = 0.0

        # Initialize aircraft state
        self.altitude = flight_plan.departure.coordinates[0] * 100  # Rough field elevation
        self.airspeed = 0
        self.heading = self._calculate_initial_heading()
        self.target_heading = self.heading
        self.engine_temp = 180
        self.fuel_remaining = 100.0

        # Initialize position
        self.current_lat = flight_plan.departure.coordinates[0]
        self.current_lng = flight_plan.departure.coordinates[1]
        self.progress_percent = 0.0

        # Initialize drift mechanics - MUCH MORE REASONABLE!
        aircraft_specs = self._get_aircraft_specs(flight_plan.aircraft_type)
        self.drift_rate = random.uniform(0.1, 0.3) * aircraft_specs['drift_sensitivity']  # Reduced from 0.5-2.0
        self.current_weather = self._generate_weather()

        # Reset tracking
        self.system_alerts.clear()
        self.emergency_state = False
        self.course_deviations = 0
        self.system_alerts_count = 0
        self.last_alert_time = 0  # Reset alert timing

        return True

    def _calculate_initial_heading(self) -> float:
        """Calculate initial heading from departure to destination."""
        if not self.current_flight:
            return 0.0

        lat1 = math.radians(self.current_flight.departure.coordinates[0])
        lng1 = math.radians(self.current_flight.departure.coordinates[1])
        lat2 = math.radians(self.current_flight.destination.coordinates[0])
        lng2 = math.radians(self.current_flight.destination.coordinates[1])

        dlng = lng2 - lng1

        y = math.sin(dlng) * math.cos(lat2)
        x = (math.cos(lat1) * math.sin(lat2) -
             math.sin(lat1) * math.cos(lat2) * math.cos(dlng))

        heading = math.atan2(y, x)
        heading = math.degrees(heading)
        return (heading + 360) % 360

    def update_flight(self, dt: float) -> Dict:
        """Update flight simulation. Returns current flight status."""
        if not self.is_flying or not self.current_flight:
            return self._get_status()

        self.elapsed_time += dt
        current_time = time.time()

        # Update flight phase
        self._update_flight_phase()

        # Update aircraft state based on phase
        self._update_aircraft_state(dt)

        # Apply Desert Bus style drift mechanics
        self._apply_drift_mechanics(dt)

        # Apply autopilot correction if enabled
        self._apply_autopilot_correction(dt)

        # Update position
        self._update_position(dt)

        # Check for system issues
        self._check_systems()

        # Update weather effects
        self._update_weather_effects(dt)

        return self._get_status()

    def _update_flight_phase(self):
        """Update current flight phase based on elapsed time and conditions."""
        if not self.current_flight:
            return

        total_time = self.current_flight.estimated_time_minutes * 60

        if self.elapsed_time < 180:  # First 3 minutes
            self.flight_phase = FlightPhase.TAXI
        elif self.elapsed_time < 300:  # Next 2 minutes
            self.flight_phase = FlightPhase.TAKEOFF
        elif self.elapsed_time < 900:  # Next 10 minutes
            self.flight_phase = FlightPhase.CLIMB
        elif self.elapsed_time < total_time - 900:  # Most of flight
            self.flight_phase = FlightPhase.CRUISE
        elif self.elapsed_time < total_time - 300:  # 10 minutes before end
            self.flight_phase = FlightPhase.DESCENT
        elif self.elapsed_time < total_time - 120:  # 5 minutes before end
            self.flight_phase = FlightPhase.APPROACH
        elif self.elapsed_time < total_time:  # Last 2 minutes
            self.flight_phase = FlightPhase.LANDING
        else:
            self.flight_phase = FlightPhase.COMPLETED
            self.is_flying = False

    def _update_aircraft_state(self, dt: float):
        """Update aircraft systems based on current flight phase."""
        if self.flight_phase == FlightPhase.TAXI:
            self.airspeed = 15
            self.altitude += 0  # Ground level
        elif self.flight_phase == FlightPhase.TAKEOFF:
            self.airspeed = 65
            self.altitude += 500 * dt  # Climb rate
        elif self.flight_phase == FlightPhase.CLIMB:
            self.airspeed = 90
            target_alt = self.current_flight.cruise_altitude
            if self.altitude < target_alt:
                self.altitude += 300 * dt  # Climb rate
        elif self.flight_phase == FlightPhase.CRUISE:
            self.airspeed = self.current_flight.cruise_speed
            # Maintain cruise altitude
        elif self.flight_phase == FlightPhase.DESCENT:
            self.airspeed = 120
            self.altitude -= 400 * dt  # Descent rate
        elif self.flight_phase == FlightPhase.APPROACH:
            self.airspeed = 80
            self.altitude -= 200 * dt
        elif self.flight_phase == FlightPhase.LANDING:
            self.airspeed = 60
            dest_alt = self.current_flight.destination.coordinates[0] * 100
            if self.altitude > dest_alt:
                self.altitude -= 100 * dt

        # Update fuel consumption - MUCH MORE REASONABLE
        if self.flight_phase not in [FlightPhase.TAXI, FlightPhase.COMPLETED]:
            fuel_rate = 0.02 * dt  # Reduced from 0.1 - percentage per second
            self.fuel_remaining = max(0, self.fuel_remaining - fuel_rate)

    def _apply_drift_mechanics(self, dt: float):
        """Apply Desert Bus style drift mechanics - BALANCED VERSION."""
        # NO DRIFT during taxi, takeoff, or landing phases
        if self.flight_phase in [FlightPhase.TAXI, FlightPhase.TAKEOFF, FlightPhase.LANDING]:
            return

        # Base drift rate - reduced when autopilot is active
        drift_multiplier = 0.3 if self.autopilot_enabled else 0.5  # Autopilot reduces drift effect
        base_drift = self.drift_rate * dt * drift_multiplier

        # Wind effect - also reduced with autopilot
        wind_multiplier = 0.01 if self.autopilot_enabled else 0.02
        wind_effect = self.current_weather.crosswind_component * wind_multiplier * dt

        # Apply drift to heading (much more reasonable)
        total_drift = base_drift + wind_effect
        self.heading += total_drift
        self.heading = self.heading % 360

        # Calculate how far off course we are
        heading_error = abs(self.heading - self.target_heading)
        if heading_error > 180:
            heading_error = 360 - heading_error

        # More forgiving thresholds, especially with autopilot
        warning_threshold = 30 if self.autopilot_enabled else 20
        critical_threshold = 60 if self.autopilot_enabled else 45

        if heading_error > warning_threshold:
            self.off_course_distance += 0.03 * dt  # Further reduced penalty
            if heading_error > critical_threshold:
                self.course_deviations += 1
                # Only add alerts if we haven't warned recently
                current_time = time.time()
                if not hasattr(self, 'last_alert_time'):
                    self.last_alert_time = 0

                if current_time - self.last_alert_time > 10:  # Only warn every 10 seconds
                    if not self.autopilot_enabled:
                        self.system_alerts.append("Course deviation warning")
                    else:
                        # Only warn if autopilot is struggling significantly
                        if heading_error > 90:
                            self.system_alerts.append("Autopilot course correction")
                    self.last_alert_time = current_time

                    # Limit alert list size to prevent spam
                    if len(self.system_alerts) > 10:
                        self.system_alerts = self.system_alerts[-5:]  # Keep only last 5

    def _update_position(self, dt: float):
        """Update aircraft position based on speed and heading."""
        if not self.current_flight:
            return

        # Convert speed to distance per second
        speed_nm_per_sec = self.airspeed / 3600  # knots to nm per second

        # Calculate new position
        distance = speed_nm_per_sec * dt

        # Convert heading to radians
        heading_rad = math.radians(self.heading)

        # Simple position update (not accounting for earth curvature)
        lat_change = distance * math.cos(heading_rad) / 60  # 60 nm per degree
        lng_change = distance * math.sin(heading_rad) / (60 * math.cos(math.radians(self.current_lat)))

        self.current_lat += lat_change
        self.current_lng += lng_change

        # Calculate progress percentage
        total_distance = self.current_flight.distance_nm
        dep_lat, dep_lng = self.current_flight.departure.coordinates
        dest_lat, dest_lng = self.current_flight.destination.coordinates

        # Distance from departure
        dist_from_dep = self._calculate_distance(dep_lat, dep_lng, self.current_lat, self.current_lng)
        self.progress_percent = min(100, (dist_from_dep / total_distance) * 100)

    def _calculate_distance(self, lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        """Calculate distance in nautical miles between two points."""
        lat1, lng1, lat2, lng2 = map(math.radians, [lat1, lng1, lat2, lng2])
        dlat = lat2 - lat1
        dlng = lng2 - lng1
        a = (math.sin(dlat/2)**2 +
             math.cos(lat1) * math.cos(lat2) * math.sin(dlng/2)**2)
        c = 2 * math.asin(math.sqrt(a))
        return 3440 * c  # Earth radius in nautical miles

    def _check_systems(self):
        """Check aircraft systems for issues."""
        # Engine temperature based on speed and phase
        target_temp_base = 180  # Base operating temperature

        # Calculate target temperature based on current conditions
        if self.flight_phase in [FlightPhase.TAKEOFF, FlightPhase.CLIMB]:
            target_temp_base = 200  # Higher temp during climb

        # Speed affects temperature - higher speed = higher temp
        if self.current_flight:
            cruise_speed = self.current_flight.cruise_speed
            speed_factor = self.airspeed / cruise_speed
            target_temp = target_temp_base + (speed_factor - 1) * 40  # Speed impact
        else:
            target_temp = target_temp_base

        # Temperature gradually moves toward target
        temp_diff = target_temp - self.engine_temp
        temp_change_rate = 2.0  # degrees per second

        # Add some random variation
        temp_change = temp_diff * 0.1 + random.uniform(-0.5, 0.5)

        self.engine_temp += temp_change

        # Keep temperature in reasonable range
        self.engine_temp = max(160, min(250, self.engine_temp))

        # Temperature warnings
        if self.engine_temp > 230:  # High temp warning
            if "Engine temperature high" not in str(self.system_alerts[-3:]):
                self.system_alerts.append("Engine temperature high")
                self.system_alerts_count += 1
        elif self.engine_temp > 240:  # Critical temp
            if "ENGINE OVERHEATING" not in str(self.system_alerts[-3:]):
                self.system_alerts.append("ENGINE OVERHEATING")
                self.system_alerts_count += 1

        # Fuel check
        if self.fuel_remaining < 20:
            if "Low fuel warning" not in str(self.system_alerts[-3:]):
                self.system_alerts.append("Low fuel warning")

        if self.fuel_remaining < 5:
            self.emergency_state = True
            if "FUEL EMERGENCY" not in str(self.system_alerts[-3:]):
                self.system_alerts.append("FUEL EMERGENCY")

    def _update_weather_effects(self, dt: float):
        """Update weather effects on flight."""
        # Occasionally change weather
        if random.random() < 0.001:  # Small chance each update
            self.current_weather = self._generate_weather()

        # Weather affects drift
        if self.current_weather.condition == WeatherCondition.TURBULENCE:
            self.drift_rate *= 1.5
        elif self.current_weather.condition == WeatherCondition.MODERATE_WIND:
            self.drift_rate *= 1.2

    def apply_course_correction(self, correction_degrees: float):
        """Apply course correction (player input)."""
        self.heading += correction_degrees
        self.heading = self.heading % 360
        self.last_correction_time = time.time()

    def set_autopilot(self, enabled: bool):
        """Enable/disable autopilot."""
        self.autopilot_enabled = enabled

    def _apply_autopilot_correction(self, dt: float):
        """Apply autopilot corrections for both heading and engine management."""
        if not self.autopilot_enabled:
            return

        # NO AUTOPILOT HEADING CORRECTIONS during taxi, takeoff, or landing
        # Only apply heading control during climb, cruise, descent, and approach
        if self.flight_phase in [FlightPhase.CLIMB, FlightPhase.CRUISE, FlightPhase.DESCENT, FlightPhase.APPROACH]:
            # === HEADING CONTROL ===
            heading_error = self.target_heading - self.heading
            if heading_error > 180:
                heading_error -= 360
            elif heading_error < -180:
                heading_error += 360

            # More effective and stable autopilot correction
            correction_rate = 1.5  # Slightly reduced for smoother control
            max_correction = correction_rate * dt

            if abs(heading_error) > 0.2:  # Even smaller threshold for smoother control
                if heading_error > 0:
                    correction = min(heading_error, max_correction)
                else:
                    correction = max(heading_error, -max_correction)

                self.heading += correction
                self.heading = self.heading % 360

        # === ENGINE TEMPERATURE MANAGEMENT VIA SPEED CONTROL ===
        target_temp = 200  # Target operating temperature
        temp_error = self.engine_temp - target_temp

        # Calculate target speed based on current phase and temperature
        if self.flight_phase == FlightPhase.CRUISE and self.current_flight:
            base_speed = self.current_flight.cruise_speed
        elif self.flight_phase == FlightPhase.CLIMB:
            base_speed = 90
        elif self.flight_phase == FlightPhase.DESCENT:
            base_speed = 120
        elif self.flight_phase == FlightPhase.APPROACH:
            base_speed = 80
        else:
            base_speed = self.airspeed  # Keep current speed for other phases

        # Adjust speed based on engine temperature
        if temp_error > 20:  # Engine too hot
            target_speed = base_speed * 0.85  # Reduce speed significantly
            if len(self.system_alerts) == 0 or "Autopilot reducing speed" not in str(self.system_alerts[-5:]):
                self.system_alerts.append("Autopilot reducing speed for cooling")
        elif temp_error > 10:  # Engine warm
            target_speed = base_speed * 0.92  # Reduce speed moderately
        elif temp_error < -15:  # Engine too cool (rare)
            target_speed = base_speed * 1.05  # Increase speed slightly
        else:
            target_speed = base_speed  # Normal speed

        # Gradually adjust airspeed toward target
        speed_error = target_speed - self.airspeed
        speed_adjustment_rate = 10.0  # knots per second
        max_speed_change = speed_adjustment_rate * dt

        if abs(speed_error) > 1:  # Only adjust if significant error
            if speed_error > 0:
                speed_change = min(speed_error, max_speed_change)
            else:
                speed_change = max(speed_error, -max_speed_change)

            # Apply speed change (but respect phase minimums)
            new_speed = self.airspeed + speed_change

            # Set reasonable speed limits based on phase
            if self.flight_phase == FlightPhase.CRUISE:
                new_speed = max(80, min(new_speed, self.current_flight.cruise_speed * 1.1))
            elif self.flight_phase == FlightPhase.CLIMB:
                new_speed = max(70, min(new_speed, 120))
            elif self.flight_phase == FlightPhase.DESCENT:
                new_speed = max(90, min(new_speed, 150))
            elif self.flight_phase == FlightPhase.APPROACH:
                new_speed = max(65, min(new_speed, 100))

            self.airspeed = new_speed

    def _get_status(self) -> Dict:
        """Get current flight status."""
        return {
            'is_flying': self.is_flying,
            'flight_phase': self.flight_phase.value if self.flight_phase else None,
            'elapsed_time': self.elapsed_time,
            'progress_percent': self.progress_percent,
            'altitude': int(self.altitude),
            'airspeed': int(self.airspeed),
            'heading': int(self.heading),
            'target_heading': int(self.target_heading),
            'engine_temp': int(self.engine_temp),
            'fuel_remaining': self.fuel_remaining,
            'off_course_distance': self.off_course_distance,
            'system_alerts': self.system_alerts.copy(),
            'emergency_state': self.emergency_state,
            'weather': {
                'condition': self.current_weather.condition.value,
                'wind_direction': self.current_weather.wind_direction,
                'wind_speed': self.current_weather.wind_speed,
                'visibility': self.current_weather.visibility
            },
            'performance': {
                'course_deviations': self.course_deviations,
                'alerts_count': self.system_alerts_count,
                'fuel_efficiency': self.fuel_efficiency
            }
        }

    def end_flight(self) -> Dict:
        """End current flight and return performance summary."""
        if not self.is_flying:
            return {}

        performance = {
            'completed': self.flight_phase == FlightPhase.COMPLETED,
            'flight_time': self.elapsed_time,
            'course_deviations': self.course_deviations,
            'system_alerts': self.system_alerts_count,
            'fuel_efficiency': self.fuel_efficiency,
            'emergency_landing': self.emergency_state,
            'final_progress': self.progress_percent
        }

        self.is_flying = False
        self.current_flight = None

        return performance

# Global flight simulator instance
flight_simulator = FlightSimulator()