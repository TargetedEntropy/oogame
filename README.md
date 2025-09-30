# Aircraft Education Game with Local LLM

An interactive educational game that teaches about different aircraft types using a local LLM (Gemma 3n) via Ollama. Explore aviation at airports worldwide! Now featuring modern UI with pygame_gui and pygame-menu!

## Features

- **6 Aircraft Learning Topics:**
  - Single-Engine Propeller Aircraft
  - Multi-Engine Propeller Aircraft
  - Commercial Jet Aircraft
  - Military Jet Aircraft
  - Seaplanes & Amphibious Aircraft
  - Helicopters & Rotorcraft

- **Modern UI with pygame_gui and pygame-menu:**
  - Professional menu system with settings
  - Clean conversation interface with HTML-formatted text
  - Auto-scrolling message display
  - Interactive progress tracking

- **Adaptive Learning System:**
  - Difficulty adjusts based on learner responses
  - Progress tracking (sessions, topics, assessments, checkpoints)
  - Personalized teaching with Socratic method

- **Local LLM Integration:**
  - Uses Ollama with Gemma 3n models
  - Completely offline once models are downloaded
  - Structured responses with educational signals

## Prerequisites

1. **Python 3.8+** installed
2. **Ollama** installed and running
3. **Gemma 3n model** pulled in Ollama

## Installation

1. **Install Python dependencies:**
```bash
cd pygame
pip install -r requirements.txt
```

2. **Install and configure Ollama:**
```bash
# Install Ollama (see https://ollama.com for your OS)
# Pull the Gemma 3n model
ollama pull gemma3n:e4b  # Larger, more capable model
# OR
ollama pull gemma3n:e2b  # Smaller, faster model
```

3. **Ensure Ollama is running:**
```bash
ollama serve  # Usually runs automatically after installation
```

## Running the Game

```bash
cd pygame
python3 main.py
```

## Controls

### Menu:
- **Arrow Keys**: Navigate menu
- **Enter**: Select option
- **ESC**: Go back/Exit

### In Conversation:
- **Type & Enter**: Send message
- **ESC**: Return to menu
- **TAB**: Switch aircraft types
- **F1**: Show help

## New GUI Features

### pygame_gui Integration:
- HTML-formatted conversation display
- Auto-scrolling text box
- Modern UI elements with theming
- Improved text input handling

### pygame-menu Integration:
- Professional menu system
- Settings configuration screen
- Interactive topic selection
- Player profile customization
- Connection testing for Ollama

## Configuration

Settings are saved in `~/.ml_education_game/settings.json` and include:
- Ollama host URL (default: http://localhost:11434)
- Current educational subject
- Model selection (gemma3n:e4b or gemma3n:e2b)
- Player name and pronouns

## Project Structure

```
pygame/
├── main.py                 # Main entry point with pygame_gui/menu
├── core/
│   ├── game_data.py       # Settings and configuration
│   ├── ollama_service.py  # Ollama API integration
│   ├── conversation.py    # Core conversation logic
│   └── educational_conversation.py  # ML education specifics
├── ui/
│   └── conversation_ui.py  # UI implementation with pygame_gui
├── data/
│   ├── npc_backstory.txt  # ML tutor personality
│   └── response_schema.json  # Structured response format
└── requirements.txt        # Python dependencies
```

## Troubleshooting

### Ollama not connecting:
- Ensure Ollama is running: `ollama list` should show available models
- Check the URL in settings matches your Ollama instance
- For network access, configure Ollama with `OLLAMA_HOST=0.0.0.0`

### Slow responses:
- Try the smaller model: gemma3n:e2b
- Ensure adequate system resources (8GB+ RAM recommended)
- Close other applications to free up memory

### Installation issues:
- Use a virtual environment: `python3 -m venv venv && source venv/bin/activate`
- Upgrade pip: `pip install --upgrade pip`
- Install requirements one by one if batch install fails

## Educational Approach

The game uses Captain Sarah "Sky" Mitchell, a veteran pilot and aviation educator, who:
- Adapts teaching to your aviation knowledge level
- Uses real-world flying experiences and examples
- Provides hands-on aircraft walkarounds and explanations
- Tracks your progress across different aircraft types
- Celebrates aviation milestones and achievements

## License

This educational game is provided as-is for learning purposes.
