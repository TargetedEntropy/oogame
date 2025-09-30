"""
Flight systems and monitoring tests.
Tests engine temperature, fuel consumption, alerts, and weather effects.
"""

import unittest
import math
import sys
import os

test_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(test_dir)
sys.path.insert(0, parent_dir)

from core.flight_simulator import (
    FlightSimulator, FlightPlan, FlightPhase, WeatherCondition
)

try:
    from core.npc_system import Location
except ImportError:
    class Location:
        def __init__(self, name: str, coordinates: tuple):
            self.name = name
            self.coordinates = coordinates


class MockLocation:
    def __init__(self, name: str, coordinates: tuple):
        self.name = name
        self.coordinates = coordinates


class TestFlightSystems(unittest.TestCase):
    """Test flight systems and monitoring."""

    def setUp(self):
        self.simulator = FlightSimulator()
        self.departure = MockLocation("Test Airport A", (40.7589, -73.9851))
        self.destination = MockLocation("Test Airport B", (34.0522, -118.2437))
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
        if self.simulator.is_flying:
            self.simulator.end_flight()

    def test_fuel_consumption(self):
        """Test fuel consumption calculations."""
        self.simulator.start_flight(self.flight_plan)
        self.simulator.flight_phase = FlightPhase.CRUISE
        self.simulator.airspeed = 120
        initial_fuel = self.simulator.fuel_remaining

        self.simulator._update_aircraft_state(3600.0)

        self.assertLess(self.simulator.fuel_remaining, initial_fuel)
        self.assertGreaterEqual(self.simulator.fuel_remaining, 0)

    def test_fuel_consumption_taxi_phase(self):
        """Test fuel consumption during taxi phase."""
        self.simulator.start_flight(self.flight_plan)
        self.simulator.flight_phase = FlightPhase.TAXI
        initial_fuel = self.simulator.fuel_remaining

        self.simulator._update_aircraft_state(3600.0)

        # Should consume very little fuel during taxi
        fuel_consumed = initial_fuel - self.simulator.fuel_remaining
        self.assertLess(fuel_consumed, 5.0)

    def test_check_systems_engine_temperature(self):
        """Test engine temperature monitoring."""
        self.simulator.start_flight(self.flight_plan)
        self.simulator.flight_phase = FlightPhase.CRUISE
        self.simulator.airspeed = 150
        initial_temp = self.simulator.engine_temp

        self.simulator._check_systems(60.0)

        # Temperature should change based on airspeed
        self.assertNotEqual(self.simulator.engine_temp, initial_temp)
        self.assertGreater(self.simulator.engine_temp, 150)
        self.assertLess(self.simulator.engine_temp, 300)

    def test_check_systems_high_temperature_alerts(self):
        """Test high temperature alert system."""
        self.simulator.start_flight(self.flight_plan)
        self.simulator.engine_temp = 250
        initial_alerts = len(self.simulator.system_alerts)

        self.simulator._check_systems(1.0)

        # Should generate temperature warning
        self.assertGreater(len(self.simulator.system_alerts), initial_alerts)
        alert_found = any("temperature" in alert.lower()
                         for alert in self.simulator.system_alerts)
        self.assertTrue(alert_found)

    def test_temperature_alert_threshold_directly(self):
        """Test temperature alert is triggered at correct threshold."""
        self.simulator.start_flight(self.flight_plan)

        # Set temperature just below threshold
        self.simulator.engine_temp = 249
        self.simulator._check_systems(1.0)
        no_alert_count = len(self.simulator.system_alerts)

        # Set temperature above threshold
        self.simulator.engine_temp = 251
        self.simulator._check_systems(1.0)
        alert_count = len(self.simulator.system_alerts)

        self.assertGreater(alert_count, no_alert_count)

    def test_check_systems_fuel_warnings(self):
        """Test fuel warning system."""
        self.simulator.start_flight(self.flight_plan)
        self.simulator.fuel_remaining = 15.0  # Below 20% threshold
        initial_alerts = len(self.simulator.system_alerts)

        self.simulator._check_systems(1.0)

        # Should generate fuel warning
        alert_found = any("fuel" in alert.lower()
                         for alert in self.simulator.system_alerts)
        self.assertTrue(alert_found)

    def test_update_weather_effects(self):
        """Test weather effects on flight."""
        self.simulator.start_flight(self.flight_plan)
        self.simulator.current_weather.wind_speed = 30
        self.simulator.current_weather.crosswind_component = 15
        initial_drift = self.simulator.drift_rate

        self.simulator._update_weather_effects()

        self.assertNotEqual(self.simulator.drift_rate, initial_drift)

    def test_course_deviation_alerts(self):
        """Test course deviation alert system."""
        self.simulator.start_flight(self.flight_plan)
        self.simulator.flight_phase = FlightPhase.CRUISE
        self.simulator.heading = 90
        self.simulator.target_heading = 270  # 180 degree difference
        initial_alerts = len(self.simulator.system_alerts)

        self.simulator._apply_drift_mechanics(1.0)

        alert_found = any("course" in alert.lower()
                         for alert in self.simulator.system_alerts)
        self.assertTrue(alert_found)

    def test_alert_rate_limiting(self):
        """Test alert rate limiting prevents spam."""
        self.simulator.start_flight(self.flight_plan)
        self.simulator.engine_temp = 260

        # Trigger multiple alerts quickly
        for _ in range(5):
            self.simulator._check_systems(0.1)

        # Should not have excessive alerts due to rate limiting
        self.assertLessEqual(len(self.simulator.system_alerts), 10)


if __name__ == '__main__':
    unittest.main(verbosity=2)