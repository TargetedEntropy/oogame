"""
Core flight simulator functionality tests.
Tests basic flight operations, initialization, and flight planning.
"""

import unittest
import math
import sys
import os

# Add the parent directory to sys.path to import the modules
test_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(test_dir)
sys.path.insert(0, parent_dir)

from core.flight_simulator import (
    FlightSimulator, FlightPlan, FlightPhase, WeatherCondition,
    WeatherData, flight_simulator
)

# Mock the Location class if npc_system is not available
try:
    from core.npc_system import Location
except ImportError:
    class Location:
        def __init__(self, name: str, coordinates: tuple):
            self.name = name
            self.coordinates = coordinates


class MockLocation:
    """Mock location for testing."""
    def __init__(self, name: str, coordinates: tuple):
        self.name = name
        self.coordinates = coordinates


class TestFlightSimulatorCore(unittest.TestCase):
    """Test core flight simulator functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.simulator = FlightSimulator()
        self.departure = MockLocation("Test Airport A", (40.7589, -73.9851))  # NYC
        self.destination = MockLocation("Test Airport B", (34.0522, -118.2437))  # LAX
        self.flight_plan = FlightPlan(
            departure=self.departure,
            destination=self.destination,
            aircraft_type="SINGLE_ENGINE_PROPS",
            distance_nm=2445.0,
            estimated_time_minutes=1222,
            cruise_altitude=6500,
            cruise_speed=120,
            fuel_required=2934.0
        )

    def tearDown(self):
        """Clean up after tests."""
        if self.simulator.is_flying:
            self.simulator.end_flight()

    def test_initialization(self):
        """Test FlightSimulator initialization."""
        self.assertIsNotNone(self.simulator)
        self.assertFalse(self.simulator.is_flying)
        self.assertEqual(self.simulator.flight_phase, FlightPhase.PREFLIGHT)
        self.assertIsNone(self.simulator.current_flight)
        self.assertEqual(self.simulator.altitude, 0)
        self.assertEqual(self.simulator.airspeed, 0)
        self.assertEqual(self.simulator.heading, 0)
        self.assertEqual(self.simulator.fuel_remaining, 100.0)
        self.assertFalse(self.simulator.autopilot_enabled)

    def test_calculate_flight_plan(self):
        """Test flight plan calculation."""
        calculated_plan = self.simulator.calculate_flight_plan(
            self.departure, self.destination, "SINGLE_ENGINE_PROPS"
        )
        self.assertIsInstance(calculated_plan, FlightPlan)
        self.assertEqual(calculated_plan.departure, self.departure)
        self.assertEqual(calculated_plan.destination, self.destination)
        self.assertEqual(calculated_plan.aircraft_type, "SINGLE_ENGINE_PROPS")
        self.assertGreater(calculated_plan.distance_nm, 0)
        self.assertGreater(calculated_plan.estimated_time_minutes, 0)

    def test_start_flight_success(self):
        """Test successful flight start."""
        result = self.simulator.start_flight(self.flight_plan)
        self.assertTrue(result)
        self.assertTrue(self.simulator.is_flying)
        self.assertEqual(self.simulator.current_flight, self.flight_plan)
        self.assertEqual(self.simulator.flight_phase, FlightPhase.PREFLIGHT)

    def test_start_flight_already_flying(self):
        """Test starting flight when already flying."""
        self.simulator.start_flight(self.flight_plan)
        result = self.simulator.start_flight(self.flight_plan)
        self.assertFalse(result)

    def test_end_flight_success(self):
        """Test successful flight completion."""
        self.simulator.start_flight(self.flight_plan)
        self.simulator.flight_phase = FlightPhase.COMPLETED
        self.simulator.course_deviations = 5
        self.simulator.system_alerts_count = 3

        performance = self.simulator.end_flight()

        self.assertFalse(self.simulator.is_flying)
        self.assertIsNone(self.simulator.current_flight)
        self.assertIn('completed', performance)
        self.assertEqual(performance['course_deviations'], 5)

    def test_end_flight_not_flying(self):
        """Test ending flight when not flying."""
        performance = self.simulator.end_flight()
        self.assertEqual(performance, {})

    def test_global_flight_simulator_instance(self):
        """Test the global flight simulator instance."""
        self.assertIsInstance(flight_simulator, FlightSimulator)
        self.assertFalse(flight_simulator.is_flying)


class TestWeatherData(unittest.TestCase):
    """Test cases for WeatherData dataclass."""

    def test_weather_data_creation(self):
        """Test WeatherData creation."""
        weather = WeatherData(
            condition=WeatherCondition.CLEAR,
            wind_direction=270,
            wind_speed=15,
            crosswind_component=7.5,
            visibility=10,
            temperature=72
        )
        self.assertEqual(weather.condition, WeatherCondition.CLEAR)
        self.assertEqual(weather.wind_direction, 270)
        self.assertEqual(weather.wind_speed, 15)


class TestFlightPlan(unittest.TestCase):
    """Test cases for FlightPlan dataclass."""

    def test_flight_plan_creation(self):
        """Test FlightPlan creation."""
        departure = MockLocation("Airport A", (40.0, -74.0))
        destination = MockLocation("Airport B", (41.0, -75.0))

        plan = FlightPlan(
            departure=departure,
            destination=destination,
            aircraft_type="JETS_COMMERCIAL",
            distance_nm=100.0,
            estimated_time_minutes=30,
            cruise_altitude=35000,
            cruise_speed=450,
            fuel_required=800.0
        )
        self.assertEqual(plan.departure, departure)
        self.assertEqual(plan.destination, destination)
        self.assertEqual(plan.aircraft_type, "JETS_COMMERCIAL")


if __name__ == '__main__':
    unittest.main(verbosity=2)