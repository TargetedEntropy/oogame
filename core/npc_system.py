from dataclasses import dataclass
from typing import List, Dict, Optional
from enum import Enum
import json
import random
from pathlib import Path

class LocationType(Enum):
    GENERAL_AVIATION = "general_aviation"
    COMMERCIAL_AIRPORT = "commercial_airport"
    MILITARY_BASE = "military_base"
    SEAPLANE_BASE = "seaplane_base"
    HELICOPTER_PORT = "helicopter_port"
    FLIGHT_TRAINING = "flight_training"
    CARGO_HUB = "cargo_hub"
    VINTAGE_AIRFIELD = "vintage_airfield"

class NPCRole(Enum):
    PILOT = "pilot"
    INSTRUCTOR = "instructor"
    MECHANIC = "mechanic"
    AIR_TRAFFIC_CONTROLLER = "air_traffic_controller"
    AIRPORT_MANAGER = "airport_manager"
    AIRLINE_CAPTAIN = "airline_captain"
    MILITARY_PILOT = "military_pilot"
    BUSH_PILOT = "bush_pilot"
    TEST_PILOT = "test_pilot"
    VINTAGE_ENTHUSIAST = "vintage_enthusiast"

@dataclass
class Location:
    id: str
    name: str
    location_type: LocationType
    country: str
    description: str
    primary_aircraft_types: List[str]
    coordinates: tuple  # (lat, lng)

class NPC:
    def __init__(self, npc_data: Dict):
        self.id = npc_data["id"]
        self.name = npc_data["name"]
        self.role = NPCRole(npc_data["role"])
        self.location_types = [LocationType(lt) for lt in npc_data["location_types"]]
        self.specialties = npc_data["specialties"]
        self.personality_traits = npc_data["personality_traits"]
        self.backstory = npc_data["backstory"]
        self.teaching_style = npc_data.get("teaching_style", "")
        self.signature_phrases = npc_data.get("signature_phrases", [])
        self.experience_years = npc_data.get("experience_years", 10)
        self.preferred_aircraft = npc_data.get("preferred_aircraft", [])

    def get_full_backstory(self, location: Location) -> str:
        """Generate contextualized backstory for specific location."""
        context = f"You are currently at {location.name} in {location.country}. "
        context += f"This is a {location.location_type.value.replace('_', ' ')} where {location.description}"

        return f"{context}\n\n{self.backstory}\n\n{self.teaching_style}"

    def is_suitable_for_location(self, location_type: LocationType) -> bool:
        """Check if NPC is suitable for this location type."""
        return location_type in self.location_types

class NPCManager:
    def __init__(self):
        self.npcs: List[NPC] = []
        self.locations: List[Location] = []
        self.current_location: Optional[Location] = None
        self.current_npc: Optional[NPC] = None
        self.visited_npcs: set = set()

        self._load_npcs()
        self._load_locations()

    def _load_npcs(self):
        """Load NPCs from JSON files."""
        npc_dir = Path("data/npcs")
        if npc_dir.exists():
            for npc_file in npc_dir.glob("*.json"):
                try:
                    with open(npc_file, 'r') as f:
                        npc_data = json.load(f)
                        self.npcs.append(NPC(npc_data))
                except Exception as e:
                    print(f"Error loading NPC from {npc_file}: {e}")

    def _load_locations(self):
        """Load locations from JSON file."""
        locations_file = Path("data/locations.json")
        if locations_file.exists():
            try:
                with open(locations_file, 'r') as f:
                    locations_data = json.load(f)
                    for loc_data in locations_data["locations"]:
                        location = Location(
                            id=loc_data["id"],
                            name=loc_data["name"],
                            location_type=LocationType(loc_data["location_type"]),
                            country=loc_data["country"],
                            description=loc_data["description"],
                            primary_aircraft_types=loc_data["primary_aircraft_types"],
                            coordinates=tuple(loc_data["coordinates"])
                        )
                        self.locations.append(location)
            except Exception as e:
                print(f"Error loading locations: {e}")

    def get_suitable_npcs(self, location: Location) -> List[NPC]:
        """Get NPCs suitable for a specific location."""
        return [npc for npc in self.npcs
                if npc.is_suitable_for_location(location.location_type)]

    def select_npc_for_location(self, location: Location, prefer_new: bool = True) -> Optional[NPC]:
        """Select an appropriate NPC for the location."""
        suitable_npcs = self.get_suitable_npcs(location)

        if not suitable_npcs:
            return None

        if prefer_new:
            # Try to find unvisited NPCs first
            unvisited = [npc for npc in suitable_npcs if npc.id not in self.visited_npcs]
            if unvisited:
                suitable_npcs = unvisited

        # Select random NPC from suitable candidates
        selected_npc = random.choice(suitable_npcs)
        self.visited_npcs.add(selected_npc.id)

        return selected_npc

    def travel_to_location(self, location_id: str) -> tuple[Optional[Location], Optional[NPC]]:
        """Travel to a location and select an NPC."""
        location = next((loc for loc in self.locations if loc.id == location_id), None)
        if not location:
            return None, None

        npc = self.select_npc_for_location(location)

        self.current_location = location
        self.current_npc = npc

        return location, npc

    def get_random_location(self, location_type: Optional[LocationType] = None) -> Optional[Location]:
        """Get a random location, optionally filtered by type."""
        candidates = self.locations
        if location_type:
            candidates = [loc for loc in self.locations if loc.location_type == location_type]

        return random.choice(candidates) if candidates else None

    def get_locations_by_type(self, location_type: LocationType) -> List[Location]:
        """Get all locations of a specific type."""
        return [loc for loc in self.locations if loc.location_type == location_type]

    def get_npc_conversation_context(self) -> str:
        """Get the current NPC's contextualized backstory."""
        if not self.current_npc or not self.current_location:
            return "You are an aviation educator helping students learn about aircraft."

        return self.current_npc.get_full_backstory(self.current_location)

    def get_travel_options(self, count: int = 5) -> List[Location]:
        """Get random travel options for the player."""
        available_locations = [loc for loc in self.locations if loc != self.current_location]
        return random.sample(available_locations, min(count, len(available_locations)))

# Global instance
npc_manager = NPCManager()