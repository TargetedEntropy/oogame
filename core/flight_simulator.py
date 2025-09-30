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
                "drift_sensitivity": 2.0
            },
            "MULTI_ENGINE_PROPS": {
                "cruise_speed": 180,
                "cruise_altitude": 12000,
                "fuel_consumption": 2.5,
                "drift_sensitivity": 1.5
            },
            "JETS_COMMERCIAL": {
                "cruise_speed": 450,
                "cruise_altitude": 35000,
                "fuel_consumption": 8.0,
                "drift_sensitivity": 0.8
            },
            "JETS_MILITARY": {
                "cruise_speed": 500,
                "cruise_altitude": 40000,
                "fuel_consumption": 12.0,
                "drift_sensitivity": 0.5
            },
            "SEAPLANES_AMPHIBIANS": {
                "cruise_speed": 140,
                "cruise_altitude": 8000,
                "fuel_consumption": 1.8,
                "drift_sensitivity": 2.5
            },
            "HELICOPTERS_ROTORCRAFT": {
                "cruise_speed": 100,
                "cruise_altitude": 1500,
                "fuel_consumption": 2.0,
                "drift_sensitivity": 3.0
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

        # Initialize drift mechanics
        aircraft_specs = self._get_aircraft_specs(flight_plan.aircraft_type)
        self.drift_rate = random.uniform(0.5, 2.0) * aircraft_specs['drift_sensitivity']
        self.current_weather = self._generate_weather()

        # Reset tracking
        self.system_alerts.clear()
        self.emergency_state = False
        self.course_deviations = 0
        self.system_alerts_count = 0

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

        # Update fuel consumption
        if self.flight_phase not in [FlightPhase.TAXI, FlightPhase.COMPLETED]:
            fuel_rate = 0.1 * dt  # Percentage per second
            self.fuel_remaining = max(0, self.fuel_remaining - fuel_rate)

    def _apply_drift_mechanics(self, dt: float):
        """Apply Desert Bus style drift mechanics."""
        # Constant drift due to wind/aircraft characteristics
        drift_amount = self.drift_rate * dt

        # Add wind effect
        wind_effect = self.current_weather.crosswind_component * 0.1 * dt

        # Apply drift to heading
        self.heading += drift_amount + wind_effect
        self.heading = self.heading % 360

        # Calculate how far off course we are
        heading_error = abs(self.heading - self.target_heading)
        if heading_error > 180:
            heading_error = 360 - heading_error

        if heading_error > 10:  # More than 10 degrees off course
            self.off_course_distance += 0.1 * dt
            if heading_error > 20:
                self.course_deviations += 1
                self.system_alerts.append("Course deviation warning")

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
        # Engine temperature check
        if self.flight_phase in [FlightPhase.TAKEOFF, FlightPhase.CLIMB]:
            self.engine_temp += random.uniform(-2, 8)
        else:
            self.engine_temp += random.uniform(-3, 3)

        if self.engine_temp > 220:
            self.system_alerts.append("Engine temperature high")
            self.system_alerts_count += 1

        # Fuel check
        if self.fuel_remaining < 20:
            self.system_alerts.append("Low fuel warning")

        if self.fuel_remaining < 5:
            self.emergency_state = True
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
        if enabled:
            # Autopilot gradually corrects course
            heading_error = self.target_heading - self.heading
            if heading_error > 180:
                heading_error -= 360
            elif heading_error < -180:
                heading_error += 360
            self.heading += heading_error * 0.1  # Gradual correction

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