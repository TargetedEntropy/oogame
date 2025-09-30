"""
Flight phases and edge case tests.
Tests flight phase transitions, edge cases, and complete flight simulations.
"""

import unittest
import math
import time
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


class TestFlightPhases(unittest.TestCase):
    """Test flight phases and transitions."""

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

    def test_update_flight_phases(self):
        """Test flight phase transitions."""
        self.simulator.start_flight(self.flight_plan)

        # Test TAXI phase (3 minutes)
        self.simulator.update_flight(60.0)
        self.assertEqual(self.simulator.flight_phase, FlightPhase.TAXI)

        # Skip to after taxi time
        self.simulator.elapsed_time = 200.0
        self.simulator.update_flight(1.0)
        self.assertEqual(self.simulator.flight_phase, FlightPhase.TAKEOFF)

        # Skip to climb phase
        self.simulator.elapsed_time = 330.0
        self.simulator.update_flight(1.0)
        self.assertEqual(self.simulator.flight_phase, FlightPhase.CLIMB)

        # Skip to cruise phase
        self.simulator.altitude = self.flight_plan.cruise_altitude
        self.simulator.update_flight(1.0)
        self.assertEqual(self.simulator.flight_phase, FlightPhase.CRUISE)

    def test_update_aircraft_state_all_phases(self):
        """Test aircraft state updates in all phases."""
        phases_to_test = [
            FlightPhase.TAXI, FlightPhase.TAKEOFF, FlightPhase.CLIMB,
            FlightPhase.CRUISE, FlightPhase.DESCENT, FlightPhase.APPROACH,
            FlightPhase.LANDING
        ]

        self.simulator.start_flight(self.flight_plan)

        for phase in phases_to_test:
            self.simulator.flight_phase = phase
            initial_fuel = self.simulator.fuel_remaining
            initial_temp = self.simulator.engine_temp

            self.simulator._update_aircraft_state(60.0)

            # Verify fuel consumption
            if phase != FlightPhase.LANDING:
                self.assertLessEqual(self.simulator.fuel_remaining, initial_fuel)

            # Verify temperature changes
            self.assertGreaterEqual(self.simulator.engine_temp, 150)

    def test_full_flight_simulation(self):
        """Test complete flight from start to finish."""
        start_time = time.time()
        self.simulator.start_flight(self.flight_plan)

        # Simulate partial flight
        time_steps = [60.0, 120.0, 180.0, 240.0, 300.0]
        for dt in time_steps:
            if self.simulator.is_flying:
                self.simulator.update_flight(dt)

        # Should still be flying after short simulation
        self.assertTrue(self.simulator.is_flying)

        # Verify systems are functioning
        self.assertGreater(self.simulator.engine_temp, 150)
        self.assertLess(self.simulator.fuel_remaining, 100.0)
        self.assertGreater(self.simulator.elapsed_time, 0)

        end_time = time.time()
        self.assertLess(end_time - start_time, 5.0)  # Should complete quickly

    def test_edge_case_zero_distance_flight(self):
        """Test edge case with zero distance flight."""
        same_location = MockLocation("Same Place", (40.7589, -73.9851))
        zero_flight_plan = FlightPlan(
            departure=same_location,
            destination=same_location,
            aircraft_type="SINGLE_ENGINE_PROPS",
            distance_nm=0,
            estimated_time_minutes=0,
            cruise_altitude=6500,
            cruise_speed=120,
            fuel_required=0
        )

        result = self.simulator.start_flight(zero_flight_plan)
        self.assertTrue(result)

        # Should handle zero distance gracefully
        self.simulator.update_flight(60.0)
        self.assertFalse(math.isnan(self.simulator.progress_percent))
        self.assertFalse(math.isinf(self.simulator.progress_percent))

    def test_extreme_weather_conditions(self):
        """Test extreme weather conditions."""
        self.simulator.start_flight(self.flight_plan)
        self.simulator.flight_phase = FlightPhase.CRUISE

        # Test extreme crosswind - use valid weather condition
        self.simulator.current_weather.condition = WeatherCondition.TURBULENCE
        self.simulator.current_weather.wind_speed = 50
        self.simulator.current_weather.crosswind_component = 40

        initial_heading = self.simulator.heading
        self.simulator._apply_drift_mechanics(1.0)

        # Should handle extreme conditions without crashing
        self.assertFalse(math.isnan(self.simulator.heading))
        self.assertFalse(math.isinf(self.simulator.heading))
        self.assertGreaterEqual(self.simulator.heading, 0)
        self.assertLess(self.simulator.heading, 360)


if __name__ == '__main__':
    unittest.main(verbosity=2)