from typing import Dict, List, Optional
from enum import Enum
from core.conversation import Conversation, Message
from core.game_data import AircraftType, game_data
from core.npc_system import npc_manager


class DifficultyLevel(Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class EducationalConversation(Conversation):
    def __init__(self):
        super().__init__()
        self.difficulty_level = DifficultyLevel.BEGINNER
        self.topic_mentions: Dict[str, int] = {}
        self.learning_objectives: List[str] = []
        self.current_subject = game_data.educational_subject

    def get_subject_prompt(self) -> str:
        """Get the initial system prompt for the current aircraft type."""
        # Use NPC context if available
        npc_context = npc_manager.get_npc_conversation_context()
        if (
            npc_context
            and npc_context
            != "You are an aviation educator helping students learn about aircraft."
        ):
            return npc_context

        # Fall back to default prompts
        prompts = {
            AircraftType.SINGLE_ENGINE_PROPS: """You are an expert aviation educator teaching about single-engine propeller aircraft.
Focus on:
- Common models (Cessna 172, Piper Cherokee, Beechcraft Bonanza)
- Engine types and configurations
- Flight characteristics and performance
- Training and recreational uses
- Maintenance and operational costs
Start with popular training aircraft and their role in pilot education.""",
            AircraftType.MULTI_ENGINE_PROPS: """You are an expert aviation educator teaching about multi-engine propeller aircraft.
Focus on:
- Twin-engine configurations and safety
- Engine-out procedures and training
- Popular models (Beechcraft Baron, Piper Seneca)
- Commercial and charter operations
- Complex systems and instrument flying
Use examples from real-world commercial operations.""",
            AircraftType.JETS_COMMERCIAL: """You are an expert aviation educator teaching about commercial jet aircraft.
Focus on:
- Airliner families (Boeing 737, Airbus A320)
- Turbofan engines and efficiency
- Airline operations and scheduling
- Passenger capacity and range
- Modern avionics and automation
Connect to passenger travel experiences.""",
            AircraftType.JETS_MILITARY: """You are an expert aviation educator teaching about military jet aircraft.
Focus on:
- Fighter aircraft roles and missions
- Military transport and cargo planes
- Engine technology and performance
- Stealth and advanced systems
- Historical development and famous aircraft
Use declassified information and airshow examples.""",
            AircraftType.SEAPLANES_AMPHIBIANS: """You are an expert aviation educator teaching about seaplanes and amphibious aircraft.
Focus on:
- Float plane configurations
- Water operations and safety
- Amphibious capabilities
- Bush flying and remote access
- Popular models (Cessna 208 Caravan, DHC Beaver)
Emphasize unique operational environments.""",
            AircraftType.HELICOPTERS_ROTORCRAFT: """You are an expert aviation educator teaching about helicopters and rotorcraft.
Focus on:
- Rotor systems and flight principles
- Helicopter vs airplane differences
- Emergency medical and rescue operations
- Military and civilian roles
- Autorotation and unique capabilities
Use rescue and utility operation examples.""",
        }

        base_prompt = prompts.get(
            self.current_subject, prompts[AircraftType.SINGLE_ENGINE_PROPS]
        )

        return f"""{base_prompt}

You are teaching {game_data.player_name} ({game_data.player_pronouns}).
Adapt your teaching to their responses - if they show understanding, gradually increase complexity.
Use the Socratic method, asking questions to guide aviation learning.
Provide hands-on aircraft walkarounds and operational examples when appropriate.
Always be encouraging and patient.

Current difficulty level: {self.difficulty_level.value}"""

    def start_educational_session(self):
        """Start a new educational conversation session."""
        system_prompt = self.get_subject_prompt()
        self.start_conversation(system_prompt)

        # Add initial greeting
        greeting = self.get_initial_greeting()
        self.add_assistant_message(greeting)

    def get_initial_greeting(self) -> str:
        """Get subject-specific initial greeting."""
        # Use NPC-specific greeting if available
        if npc_manager.current_npc and npc_manager.current_location:
            npc = npc_manager.current_npc
            location = npc_manager.current_location
            return (
                f"Hello {game_data.player_name}! I'm {npc.name}, and welcome to {location.name}. "
                f"{location.description} I specialize in {', '.join(npc.specialties[:2])} "
                f"and I'm excited to share my knowledge of aviation with you. "
                f"What would you like to learn about today?"
            )

        # Fall back to default greetings
        greetings = {
            AircraftType.SINGLE_ENGINE_PROPS: f"Welcome to the flight line, {game_data.player_name}! "
            "We're at a busy general aviation airport where single-engine aircraft are the backbone of flight training. "
            "These trusty machines have taught countless pilots to fly. "
            "What draws you to single-engine propeller aircraft?",
            AircraftType.MULTI_ENGINE_PROPS: f"Greetings {game_data.player_name}! Welcome to the twin-engine hangar. "
            "Multi-engine propeller aircraft represent a step up in complexity and capability. "
            "They're the workhorses of charter operations and advanced pilot training. "
            "Have you had any experience with twin-engine aircraft before?",
            AircraftType.JETS_COMMERCIAL: f"Hello {game_data.player_name}! Welcome aboard our tour of commercial aviation. "
            "We're at a major airport where these magnificent jets connect the world. "
            "From regional jets to wide-body airliners, each has a story to tell. "
            "What's your experience with commercial aviation as a passenger or enthusiast?",
            AircraftType.JETS_MILITARY: f"Welcome {game_data.player_name}! Today we're exploring military aviation at this air base. "
            "From supersonic fighters to massive cargo haulers, military aircraft push the boundaries of technology. "
            "These machines defend nations and project power across the globe. "
            "What aspects of military aviation interest you most?",
            AircraftType.SEAPLANES_AMPHIBIANS: f"Hello {game_data.player_name}! Welcome to this unique seaplane base. "
            "Here, aircraft operate from both water and land, opening up remote destinations. "
            "Seaplanes and amphibians are aviation's adventurers, reaching places others cannot. "
            "Have you ever experienced flight operations from water?",
            AircraftType.HELICOPTERS_ROTORCRAFT: f"Welcome {game_data.player_name}! You're at a helicopter base where rotorcraft demonstrate unique capabilities. "
            "Unlike fixed-wing aircraft, helicopters can hover, land anywhere, and perform vertical operations. "
            "From life-saving rescues to precision construction work, they're aviation's workhorses. "
            "What fascinates you about helicopter flight?",
        }

        return greetings.get(
            self.current_subject, greetings[AircraftType.SINGLE_ENGINE_PROPS]
        )

    def analyze_response_complexity(self, response: str) -> Dict:
        """Analyze user response to adjust difficulty."""
        words = response.split()
        word_count = len(words)

        # Check for aviation terminology
        aviation_terms = {
            "beginner": [
                "aircraft",
                "propeller",
                "engine",
                "wing",
                "cockpit",
                "runway",
            ],
            "intermediate": [
                "avionics",
                "turbine",
                "navigation",
                "instruments",
                "performance",
                "certification",
                "maintenance",
                "weather",
            ],
            "advanced": [
                "aerodynamics",
                "turbofan",
                "autopilot",
                "pressurization",
                "approach",
                "systems",
                "regulations",
                "operations",
            ],
        }

        complexity_score = 0
        detected_terms = []

        for level, terms in aviation_terms.items():
            for term in terms:
                if term.lower() in response.lower():
                    detected_terms.append(term)
                    if level == "beginner":
                        complexity_score += 1
                    elif level == "intermediate":
                        complexity_score += 2
                    else:  # advanced
                        complexity_score += 3

        return {
            "word_count": word_count,
            "complexity_score": complexity_score,
            "detected_terms": detected_terms,
            "shows_understanding": word_count > 15 and complexity_score > 3,
        }

    def update_difficulty(self, analysis: Dict):
        """Update difficulty based on response analysis."""
        if self.state.session_count < 3:
            return  # Don't adjust too early

        shows_understanding = analysis["shows_understanding"]
        complexity = analysis["complexity_score"]

        if self.difficulty_level == DifficultyLevel.BEGINNER:
            if (
                self.state.session_count >= 5
                and shows_understanding
                and complexity >= 5
            ):
                self.difficulty_level = DifficultyLevel.INTERMEDIATE
                self.add_system_message(
                    "Adjusting to intermediate level based on your understanding."
                )

        elif self.difficulty_level == DifficultyLevel.INTERMEDIATE:
            if (
                self.state.session_count >= 10
                and shows_understanding
                and complexity >= 10
            ):
                self.difficulty_level = DifficultyLevel.ADVANCED
                self.add_system_message(
                    "Advancing to expert level based on your progress."
                )

    def add_system_message(self, content: str):
        """Add a system message to guide the AI's behavior."""
        self.state.messages.append(Message("system", content))

    def track_topic_mention(self, topic: str):
        """Track how often topics are mentioned."""
        if topic not in self.topic_mentions:
            self.topic_mentions[topic] = 0
        self.topic_mentions[topic] += 1

    def get_suggested_topics(self) -> List[str]:
        """Get suggested topics based on current subject and progress."""
        topic_suggestions = {
            AircraftType.SINGLE_ENGINE_PROPS: [
                "Cessna 172 characteristics",
                "Engine operation basics",
                "Pre-flight inspection",
                "Traffic pattern procedures",
                "Landing techniques",
            ],
            AircraftType.MULTI_ENGINE_PROPS: [
                "Twin-engine safety",
                "Engine-out procedures",
                "Beechcraft Baron systems",
                "Complex aircraft operations",
                "Multi-engine training",
            ],
            AircraftType.JETS_COMMERCIAL: [
                "Boeing 737 family",
                "Airbus A320 systems",
                "Turbofan engine operation",
                "Airline operations",
                "Modern avionics",
            ],
            AircraftType.JETS_MILITARY: [
                "Fighter aircraft roles",
                "Military transport planes",
                "Stealth technology",
                "Air combat systems",
                "Historic military aircraft",
            ],
            AircraftType.SEAPLANES_AMPHIBIANS: [
                "Float plane operations",
                "Water landing techniques",
                "DHC Beaver capabilities",
                "Bush flying operations",
                "Amphibious conversions",
            ],
            AircraftType.HELICOPTERS_ROTORCRAFT: [
                "Rotor system design",
                "Autorotation procedures",
                "Medical helicopter operations",
                "Helicopter vs airplane flight",
                "Unique helicopter capabilities",
            ],
        }

        suggestions = topic_suggestions.get(self.current_subject, [])

        # Filter out already completed topics
        return [
            topic for topic in suggestions if topic not in self.state.completed_topics
        ]

    def create_practice_exercise(self) -> str:
        """Create a practice exercise based on current topic and difficulty."""
        exercises = {
            DifficultyLevel.BEGINNER: {
                AircraftType.SINGLE_ENGINE_PROPS: "Let's practice: You're looking at a Cessna 172 and a Piper Cherokee. "
                "What are the key differences you would look for during a pre-flight inspection?",
                AircraftType.JETS_COMMERCIAL: "Exercise: Explain why commercial jets have turbofan engines instead of propellers. "
                "What advantages do turbofans provide for airline operations?",
            },
            DifficultyLevel.INTERMEDIATE: {
                AircraftType.MULTI_ENGINE_PROPS: "Challenge: You're flying a twin-engine aircraft and one engine fails. "
                "What immediate actions would the pilot take? Why is engine-out training so important?",
                AircraftType.HELICOPTERS_ROTORCRAFT: "Exercise: Describe the principle of autorotation in helicopters. "
                "How does this safety feature allow helicopters to land without engine power?",
            },
            DifficultyLevel.ADVANCED: {
                AircraftType.JETS_MILITARY: "Advanced exercise: Compare the design philosophy of a fighter jet like the F-22 "
                "versus a cargo aircraft like the C-130. How do their missions drive different designs?",
                AircraftType.SEAPLANES_AMPHIBIANS: "Challenge: Design considerations for seaplane operations - what unique challenges "
                "do water operations present compared to traditional runway operations?",
            },
        }

        if self.difficulty_level in exercises:
            level_exercises = exercises[self.difficulty_level]
            if self.current_subject in level_exercises:
                return level_exercises[self.current_subject]

        return "Let's try an exercise: Can you explain the concept we just discussed in your own words?"

    async def process_educational_response(self, user_input: str) -> str:
        """Process user input in educational context."""
        # Analyze response complexity
        analysis = self.analyze_response_complexity(user_input)
        self.update_difficulty(analysis)

        # Track mentioned topics
        for term in analysis["detected_terms"]:
            self.track_topic_mention(term)

        # Generate response using parent class method
        response = await self.generate_response(user_input)

        return response
