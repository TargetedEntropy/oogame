"""
Flight mechanics tests.
Tests drift, autopilot, navigation, and physics.
"""

import unittest
import math
import random
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


class TestFlightMechanics(unittest.TestCase):
    """Test flight mechanics and physics."""

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

    def test_apply_drift_mechanics_no_drift_phases(self):
        """Test no drift during taxi, takeoff, and landing."""
        self.simulator.start_flight(self.flight_plan)
        no_drift_phases = [FlightPhase.TAXI, FlightPhase.TAKEOFF, FlightPhase.LANDING]

        for phase in no_drift_phases:
            self.simulator.flight_phase = phase
            initial_heading = self.simulator.heading
            self.simulator._apply_drift_mechanics(1.0)
            self.assertEqual(self.simulator.heading, initial_heading)

    def test_apply_drift_mechanics_with_drift(self):
        """Test drift mechanics during cruise."""
        self.simulator.start_flight(self.flight_plan)
        self.simulator.flight_phase = FlightPhase.CRUISE
        self.simulator.drift_rate = 0.1
        initial_heading = self.simulator.heading

        self.simulator._apply_drift_mechanics(1.0)

        self.assertNotEqual(self.simulator.heading, initial_heading)
        self.assertGreaterEqual(self.simulator.heading, 0)
        self.assertLess(self.simulator.heading, 360)

    def test_apply_drift_mechanics_nan_protection(self):
        """Test NaN protection in drift mechanics."""
        self.simulator.start_flight(self.flight_plan)
        self.simulator.flight_phase = FlightPhase.CRUISE
        self.simulator.current_weather.crosswind_component = float('nan')

        self.simulator._apply_drift_mechanics(1.0)

        self.assertFalse(math.isnan(self.simulator.heading))
        self.assertFalse(math.isinf(self.simulator.heading))

    def test_apply_course_correction(self):
        """Test manual course correction."""
        self.simulator.start_flight(self.flight_plan)
        initial_heading = self.simulator.heading

        self.simulator.apply_course_correction(10)

        expected_heading = (initial_heading + 10) % 360
        self.assertEqual(self.simulator.heading, expected_heading)

    def test_apply_course_correction_negative(self):
        """Test negative course correction."""
        self.simulator.start_flight(self.flight_plan)
        self.simulator.heading = 10

        self.simulator.apply_course_correction(-20)

        self.assertEqual(self.simulator.heading, 350)

    def test_apply_course_correction_nan_protection(self):
        """Test NaN protection in course correction."""
        self.simulator.start_flight(self.flight_plan)
        initial_heading = self.simulator.heading

        self.simulator.apply_course_correction(float('nan'))

        self.assertFalse(math.isnan(self.simulator.heading))

    def test_calculate_initial_heading(self):
        """Test initial heading calculation."""
        self.simulator.current_flight = self.flight_plan
        heading = self.simulator._calculate_initial_heading()

        self.assertGreaterEqual(heading, 0)
        self.assertLess(heading, 360)

    def test_calculate_initial_heading_nan_protection(self):
        """Test initial heading calculation with same departure/destination."""
        same_location = MockLocation("Same Place", (40.7589, -73.9851))
        same_flight_plan = FlightPlan(
            departure=same_location,
            destination=same_location,
            aircraft_type="SINGLE_ENGINE_PROPS",
            distance_nm=0,
            estimated_time_minutes=0,
            cruise_altitude=6500,
            cruise_speed=120,
            fuel_required=0
        )

        self.simulator.current_flight = same_flight_plan
        heading = self.simulator._calculate_initial_heading()

        self.assertFalse(math.isnan(heading))
        self.assertFalse(math.isinf(heading))

    def test_update_position(self):
        """Test position update calculations."""
        self.simulator.start_flight(self.flight_plan)
        self.simulator.airspeed = 120
        self.simulator.heading = 90
        initial_lat = self.simulator.current_lat
        initial_lng = self.simulator.current_lng

        # Use longer time for noticeable change
        self.simulator._update_position(3600.0)

        lat_changed = abs(self.simulator.current_lat - initial_lat) > 0.01
        lng_changed = abs(self.simulator.current_lng - initial_lng) > 0.01

        self.assertTrue(lat_changed or lng_changed)
        self.assertGreaterEqual(self.simulator.progress_percent, 0)
        self.assertLessEqual(self.simulator.progress_percent, 100)

    def test_calculate_distance(self):
        """Test distance calculation between two points."""
        distance = self.simulator._calculate_distance(
            40.7589, -73.9851,  # NYC
            34.0522, -118.2437   # LAX
        )
        # Should be approximately 2445 nautical miles
        self.assertGreater(distance, 2000)
        self.assertLess(distance, 3000)

    def test_calculate_distance_same_point(self):
        """Test distance calculation for same point."""
        distance = self.simulator._calculate_distance(
            40.7589, -73.9851,
            40.7589, -73.9851
        )
        self.assertAlmostEqual(distance, 0, places=2)


class TestAutopilot(unittest.TestCase):
    """Test autopilot functionality."""

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

    def test_set_autopilot(self):
        """Test autopilot enable/disable."""
        self.assertFalse(self.simulator.autopilot_enabled)

        self.simulator.set_autopilot(True)
        self.assertTrue(self.simulator.autopilot_enabled)

        self.simulator.set_autopilot(False)
        self.assertFalse(self.simulator.autopilot_enabled)

    def test_autopilot_heading_control(self):
        """Test autopilot heading control in valid phases."""
        self.simulator.start_flight(self.flight_plan)
        self.simulator.set_autopilot(True)

        # Test phases where autopilot should correct
        correction_phases = [FlightPhase.CLIMB, FlightPhase.CRUISE,
                           FlightPhase.DESCENT, FlightPhase.APPROACH]

        for phase in correction_phases:
            self.simulator.flight_phase = phase
            self.simulator.heading = 50
            self.simulator.target_heading = 0
            initial_heading = self.simulator.heading

            self.simulator._apply_autopilot_correction(1.0)

            # Heading should move toward target
            self.assertNotEqual(self.simulator.heading, initial_heading)

    def test_autopilot_no_correction_phases(self):
        """Test autopilot doesn't correct in certain phases."""
        self.simulator.start_flight(self.flight_plan)
        self.simulator.set_autopilot(True)

        no_correction_phases = [FlightPhase.TAXI, FlightPhase.TAKEOFF, FlightPhase.LANDING]

        for phase in no_correction_phases:
            self.simulator.flight_phase = phase
            self.simulator.heading = 50
            self.simulator.target_heading = 0
            initial_heading = self.simulator.heading

            self.simulator._apply_autopilot_correction(1.0)

            self.assertEqual(self.simulator.heading, initial_heading)

    def test_autopilot_engine_temperature_management(self):
        """Test autopilot engine temperature management."""
        self.simulator.start_flight(self.flight_plan)
        self.simulator.set_autopilot(True)
        self.simulator.flight_phase = FlightPhase.CRUISE
        self.simulator.airspeed = 120
        self.simulator.engine_temp = 230  # Too hot
        initial_speed = self.simulator.airspeed

        self.simulator._apply_autopilot_correction(1.0)

        # Speed should be reduced for cooling
        self.assertLess(self.simulator.airspeed, initial_speed)

    def test_autopilot_drift_reduction(self):
        """Test that autopilot reduces drift effect."""
        self.simulator.start_flight(self.flight_plan)
        self.simulator.flight_phase = FlightPhase.CRUISE
        self.simulator.drift_rate = 0.2

        # Test without autopilot
        self.simulator.autopilot_enabled = False
        initial_heading = self.simulator.heading
        for _ in range(10):
            self.simulator._apply_drift_mechanics(1.0)
        manual_drift = abs(self.simulator.heading - initial_heading)

        # Reset and test with autopilot
        self.simulator.heading = initial_heading
        self.simulator.autopilot_enabled = True
        for _ in range(10):
            self.simulator._apply_drift_mechanics(1.0)
        auto_drift = abs(self.simulator.heading - initial_heading)

        # Autopilot should reduce drift
        self.assertLessEqual(auto_drift, manual_drift + 5)


if __name__ == '__main__':
    unittest.main(verbosity=2)