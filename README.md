# ML Education Game with Local LLM

An interactive educational game that teaches machine learning fundamentals using a local LLM (Gemma 3n) via Ollama. This is a Pygame recreation of the original Godot game, focused on ML education instead of agriculture.

## Features

- **6 ML Learning Topics:**
  - Supervised Learning
  - Neural Networks
  - Training and Validation
  - Loss Functions and Optimization
  - Overfitting and Regularization
  - Model Evaluation Metrics

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

- **SPACE**: Start learning conversation
- **TAB**: Switch between ML topics
- **Enter**: Send message
- **ESC**: Exit conversation / Quit game
- **F1**: Show help
- **Arrow Keys**: Scroll conversation
- **Page Up/Down**: Fast scroll

## Configuration

Settings are saved in `~/.ml_education_game/settings.json` and include:
- Ollama host URL (default: http://localhost:11434)
- Current educational subject
- Model selection (gemma3n:e4b or gemma3n:e2b)
- Player name and pronouns

## Project Structure

```
pygame/
├── main.py                 # Main game entry point
├── core/
│   ├── game_data.py       # Settings and configuration
│   ├── ollama_service.py  # Ollama API integration
│   ├── conversation.py    # Core conversation logic
│   └── educational_conversation.py  # ML education specifics
├── ui/
│   └── conversation_ui.py # Pygame UI components
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

The game uses Dr. Maya Chen, a virtual ML educator, who:
- Adapts teaching to your understanding level
- Uses real-world examples and analogies
- Provides hands-on coding exercises
- Tracks your progress across sessions
- Celebrates achievements and breakthroughs

## License

This educational game is provided as-is for learning purposes.