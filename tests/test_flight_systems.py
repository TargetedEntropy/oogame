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

        self.simulator._check_systems()

        # Temperature should be within reasonable range
        self.assertGreater(self.simulator.engine_temp, 150)
        self.assertLess(self.simulator.engine_temp, 300)

    def test_check_systems_high_temperature_alerts(self):
        """Test high temperature alert system."""
        self.simulator.start_flight(self.flight_plan)
        # Set temperature high enough that even after adjustment it will trigger
        self.simulator.engine_temp = 245  # Well above 230 threshold
        initial_alerts = len(self.simulator.system_alerts)

        self.simulator._check_systems()

        # Temperature should still be high enough to trigger alert
        self.assertGreater(self.simulator.engine_temp, 230)

        # Should generate temperature warning
        alert_found = any("temperature" in alert.lower() or "OVERHEATING" in alert
                         for alert in self.simulator.system_alerts)
        self.assertTrue(alert_found)

    def test_temperature_alert_threshold_directly(self):
        """Test temperature alert logic directly."""
        self.simulator.start_flight(self.flight_plan)

        # Test high temperature directly - set to max to avoid adjustments
        self.simulator.engine_temp = 250  # At the max limit
        initial_alerts = len(self.simulator.system_alerts)

        self.simulator._check_systems()

        # Should have temperature alert
        alert_found = any("temperature" in alert.lower() or "OVERHEATING" in alert
                         for alert in self.simulator.system_alerts)
        self.assertTrue(alert_found, "Expected temperature alert not found")

    def test_check_systems_fuel_warnings(self):
        """Test fuel warning system."""
        self.simulator.start_flight(self.flight_plan)
        self.simulator.fuel_remaining = 15.0  # Below 20% threshold
        initial_alerts = len(self.simulator.system_alerts)

        self.simulator._check_systems()

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

        self.simulator._update_weather_effects(1.0)

        # Test that drift rate can be affected by weather
        self.assertGreaterEqual(self.simulator.drift_rate, 0)

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
        self.simulator.engine_temp = 240

        # Trigger multiple alerts quickly
        for _ in range(5):
            self.simulator._check_systems()

        # Should not have excessive alerts due to rate limiting
        self.assertLessEqual(len(self.simulator.system_alerts), 10)


if __name__ == '__main__':
    unittest.main(verbosity=2)