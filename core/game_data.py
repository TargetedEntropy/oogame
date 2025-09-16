import json
import os
from pathlib import Path
from enum import IntEnum
from typing import Optional


class MLSubject(IntEnum):
    SUPERVISED_LEARNING = 0
    NEURAL_NETWORKS = 1
    TRAINING_VALIDATION = 2
    LOSS_OPTIMIZATION = 3
    OVERFITTING_REGULARIZATION = 4
    MODEL_EVALUATION = 5


class GameData:
    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self.config_dir = Path.home() / ".ml_education_game"
            self.config_file = self.config_dir / "settings.json"

            self.ollama_host_url = "http://localhost:11434"
            self.educational_subject = MLSubject.SUPERVISED_LEARNING
            self.use_gemma3n_latest = True
            self.player_name = "Learner"
            self.player_pronouns = "they/them"

            self._initialized = True
            self.load_settings()

    def get_model_name(self) -> str:
        """Get the Ollama model name based on settings."""
        if self.use_gemma3n_latest:
            return "gemma3n:e4b"
        return "gemma3n:e2b"

    def get_subject_name(self) -> str:
        """Get the current educational subject name."""
        subject_names = {
            MLSubject.SUPERVISED_LEARNING: "Supervised Learning",
            MLSubject.NEURAL_NETWORKS: "Neural Networks",
            MLSubject.TRAINING_VALIDATION: "Training and Validation",
            MLSubject.LOSS_OPTIMIZATION: "Loss Functions and Optimization",
            MLSubject.OVERFITTING_REGULARIZATION: "Overfitting and Regularization",
            MLSubject.MODEL_EVALUATION: "Model Evaluation Metrics"
        }
        return subject_names.get(self.educational_subject, "Machine Learning")

    def save_settings(self):
        """Save settings to JSON file."""
        self.config_dir.mkdir(parents=True, exist_ok=True)

        settings = {
            "ollama_host_url": self.ollama_host_url,
            "educational_subject": int(self.educational_subject),
            "use_gemma3n_latest": self.use_gemma3n_latest,
            "player_name": self.player_name,
            "player_pronouns": self.player_pronouns
        }

        with open(self.config_file, 'w') as f:
            json.dump(settings, f, indent=2)

    def load_settings(self):
        """Load settings from JSON file."""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    settings = json.load(f)

                self.ollama_host_url = settings.get("ollama_host_url", self.ollama_host_url)
                self.educational_subject = MLSubject(settings.get("educational_subject", 0))
                self.use_gemma3n_latest = settings.get("use_gemma3n_latest", True)
                self.player_name = settings.get("player_name", "Learner")
                self.player_pronouns = settings.get("player_pronouns", "they/them")
            except (json.JSONDecodeError, ValueError) as e:
                print(f"Error loading settings: {e}")
                self.save_settings()

    def reset_to_defaults(self):
        """Reset all settings to default values."""
        self.ollama_host_url = "http://localhost:11434"
        self.educational_subject = MLSubject.SUPERVISED_LEARNING
        self.use_gemma3n_latest = True
        self.player_name = "Learner"
        self.player_pronouns = "they/them"
        self.save_settings()


game_data = GameData()