"""
NPC system tests.
Tests NPC creation, location management, and system functionality.
"""

import unittest
import json
import sys
import os
from unittest.mock import Mock, patch, mock_open

test_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(test_dir)
sys.path.insert(0, parent_dir)

from core.npc_system import (
    LocationType, NPCRole, Location, NPC, NPCManager, npc_manager
)


class TestLocationType(unittest.TestCase):
    """Test LocationType enum."""

    def test_location_type_values(self):
        """Test LocationType enum values."""
        self.assertEqual(LocationType.GENERAL_AVIATION.value, "general_aviation")
        self.assertEqual(LocationType.COMMERCIAL_AIRPORT.value, "commercial_airport")
        self.assertEqual(LocationType.MILITARY_BASE.value, "military_base")


class TestNPCRole(unittest.TestCase):
    """Test NPCRole enum."""

    def test_npc_role_values(self):
        """Test NPCRole enum values."""
        self.assertEqual(NPCRole.PILOT.value, "pilot")
        self.assertEqual(NPCRole.INSTRUCTOR.value, "instructor")
        self.assertEqual(NPCRole.MECHANIC.value, "mechanic")


class TestLocation(unittest.TestCase):
    """Test Location dataclass."""

    def test_location_creation(self):
        """Test Location creation."""
        location = Location(
            id="test_airport",
            name="Test Airport",
            location_type=LocationType.GENERAL_AVIATION,
            country="USA",
            description="A test airport",
            primary_aircraft_types=["SINGLE_ENGINE_PROPS"],
            coordinates=(40.0, -74.0)
        )

        self.assertEqual(location.id, "test_airport")
        self.assertEqual(location.name, "Test Airport")
        self.assertEqual(location.location_type, LocationType.GENERAL_AVIATION)
        self.assertEqual(location.coordinates, (40.0, -74.0))


class TestNPC(unittest.TestCase):
    """Test NPC class."""

    def setUp(self):
        """Set up test fixtures."""
        self.npc_data = {
            "id": "test_pilot",
            "name": "Test Pilot",
            "role": "pilot",
            "location_types": ["general_aviation"],
            "specialties": ["Cessna", "Navigation"],
            "personality_traits": ["Friendly", "Knowledgeable"],
            "background": "Experienced pilot with 1000+ hours",
            "teaching_style": "Hands-on learning"
        }

    def test_npc_creation(self):
        """Test NPC creation from data."""
        npc = NPC(self.npc_data)

        self.assertEqual(npc.id, "test_pilot")
        self.assertEqual(npc.name, "Test Pilot")
        self.assertEqual(npc.role, NPCRole.PILOT)
        self.assertEqual(npc.location_types, [LocationType.GENERAL_AVIATION])
        self.assertEqual(npc.specialties, ["Cessna", "Navigation"])

    def test_get_backstory(self):
        """Test NPC backstory generation."""
        npc = NPC(self.npc_data)
        backstory = npc.get_backstory()

        self.assertIn(npc.name, backstory)
        self.assertIn("pilot", backstory.lower())
        self.assertIn("cessna", backstory.lower())

    def test_can_teach_subject(self):
        """Test subject teaching capability."""
        npc = NPC(self.npc_data)

        self.assertTrue(npc.can_teach_subject("navigation"))
        self.assertTrue(npc.can_teach_subject("cessna"))
        self.assertFalse(npc.can_teach_subject("jet_engines"))

    def test_get_teaching_approach(self):
        """Test teaching approach generation."""
        npc = NPC(self.npc_data)
        approach = npc.get_teaching_approach("navigation")

        self.assertIsInstance(approach, str)
        self.assertGreater(len(approach), 0)


class TestNPCManager(unittest.TestCase):
    """Test NPCManager class."""

    def setUp(self):
        """Set up test fixtures."""
        self.manager = NPCManager()

        # Create test data
        self.test_locations = [
            {
                "id": "test_airport",
                "name": "Test Airport",
                "location_type": "general_aviation",
                "country": "USA",
                "description": "Test description",
                "primary_aircraft_types": ["SINGLE_ENGINE_PROPS"],
                "coordinates": [40.0, -74.0]
            }
        ]

        self.test_npcs = [
            {
                "id": "test_pilot",
                "name": "Test Pilot",
                "role": "pilot",
                "location_types": ["general_aviation"],
                "specialties": ["Navigation"],
                "personality_traits": ["Friendly"],
                "background": "Test background",
                "teaching_style": "Hands-on"
            }
        ]

    @patch('core.npc_system.Path.exists')
    @patch('builtins.open', new_callable=mock_open)
    @patch('core.npc_system.json.load')
    def test_load_data_success(self, mock_json_load, mock_file_open, mock_exists):
        """Test successful data loading."""
        mock_exists.return_value = True
        mock_json_load.side_effect = [self.test_locations, self.test_npcs]

        self.manager._load_data()

        self.assertEqual(len(self.manager.locations), 1)
        self.assertEqual(len(self.manager.npcs), 1)
        self.assertIn("test_airport", self.manager.locations)

    @patch('core.npc_system.Path.exists')
    def test_load_data_files_not_found(self, mock_exists):
        """Test data loading when files don't exist."""
        mock_exists.return_value = False

        self.manager._load_data()

        # Should create default data
        self.assertGreater(len(self.manager.locations), 0)
        self.assertGreater(len(self.manager.npcs), 0)

    def test_get_location_by_id(self):
        """Test location retrieval by ID."""
        # Manually add test location
        location = Location(**{
            **self.test_locations[0],
            "location_type": LocationType.GENERAL_AVIATION,
            "coordinates": tuple(self.test_locations[0]["coordinates"])
        })
        self.manager.locations["test_airport"] = location

        retrieved = self.manager.get_location_by_id("test_airport")
        self.assertEqual(retrieved.id, "test_airport")

        # Test non-existent location
        self.assertIsNone(self.manager.get_location_by_id("nonexistent"))

    def test_get_npc_by_id(self):
        """Test NPC retrieval by ID."""
        # Manually add test NPC
        npc = NPC(self.test_npcs[0])
        self.manager.npcs["test_pilot"] = npc

        retrieved = self.manager.get_npc_by_id("test_pilot")
        self.assertEqual(retrieved.id, "test_pilot")

        # Test non-existent NPC
        self.assertIsNone(self.manager.get_npc_by_id("nonexistent"))

    def test_get_npcs_for_location_type(self):
        """Test NPC filtering by location type."""
        # Add test NPC
        npc = NPC(self.test_npcs[0])
        self.manager.npcs["test_pilot"] = npc

        npcs = self.manager.get_npcs_for_location_type(LocationType.GENERAL_AVIATION)
        self.assertEqual(len(npcs), 1)
        self.assertEqual(npcs[0].id, "test_pilot")

    def test_get_random_location_by_type(self):
        """Test random location selection by type."""
        # Add test location
        location = Location(**{
            **self.test_locations[0],
            "location_type": LocationType.GENERAL_AVIATION,
            "coordinates": tuple(self.test_locations[0]["coordinates"])
        })
        self.manager.locations["test_airport"] = location

        random_loc = self.manager.get_random_location_by_type(LocationType.GENERAL_AVIATION)
        self.assertEqual(random_loc.id, "test_airport")

    def test_global_npc_manager_instance(self):
        """Test the global npc_manager instance."""
        self.assertIsInstance(npc_manager, NPCManager)


if __name__ == '__main__':
    unittest.main(verbosity=2)