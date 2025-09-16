from typing import Dict, List, Optional
from enum import Enum
from core.conversation import Conversation, Message
from core.game_data import MLSubject, game_data


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
        """Get the initial system prompt for the current ML subject."""
        prompts = {
            MLSubject.SUPERVISED_LEARNING: """You are an expert ML educator teaching supervised learning.
Focus on:
- Classification vs regression
- Training data and labels
- Common algorithms (decision trees, linear regression, SVM)
- Real-world applications
- Evaluation metrics (accuracy, precision, recall)
Start with simple examples using everyday scenarios.""",

            MLSubject.NEURAL_NETWORKS: """You are an expert ML educator teaching neural networks.
Focus on:
- Neurons and activation functions
- Layers and architectures
- Forward propagation
- Backpropagation basics
- Simple perceptrons to deep networks
Use visual analogies and simple math when needed.""",

            MLSubject.TRAINING_VALIDATION: """You are an expert ML educator teaching training and validation.
Focus on:
- Training, validation, and test sets
- Cross-validation techniques
- Data splitting strategies
- Monitoring training progress
- Early stopping
- Batch vs epoch concepts
Emphasize practical examples and common pitfalls.""",

            MLSubject.LOSS_OPTIMIZATION: """You are an expert ML educator teaching loss functions and optimization.
Focus on:
- Common loss functions (MSE, cross-entropy)
- Gradient descent and its variants
- Learning rates and their impact
- Optimization challenges
- Convergence concepts
Use intuitive explanations before mathematical details.""",

            MLSubject.OVERFITTING_REGULARIZATION: """You are an expert ML educator teaching overfitting and regularization.
Focus on:
- What is overfitting and underfitting
- Bias-variance tradeoff
- Regularization techniques (L1, L2, dropout)
- Data augmentation
- Model complexity
- Validation curves
Provide practical examples and visual descriptions.""",

            MLSubject.MODEL_EVALUATION: """You are an expert ML educator teaching model evaluation.
Focus on:
- Confusion matrices
- ROC curves and AUC
- Precision, recall, F1-score
- Cross-validation scores
- A/B testing for ML
- Performance monitoring
Connect metrics to real-world impact and decision-making."""
        }

        base_prompt = prompts.get(self.current_subject, prompts[MLSubject.SUPERVISED_LEARNING])

        return f"""{base_prompt}

You are teaching {game_data.player_name} ({game_data.player_pronouns}).
Adapt your teaching to their responses - if they show understanding, gradually increase complexity.
Use the Socratic method, asking questions to guide learning.
Provide hands-on exercises and coding examples when appropriate.
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
        greetings = {
            MLSubject.SUPERVISED_LEARNING:
                f"Hello {game_data.player_name}! Welcome to our machine learning journey. "
                "Today we'll explore supervised learning - the foundation of many ML applications. "
                "Think of it like learning with a teacher who shows you examples and correct answers. "
                "What's your experience with machine learning so far?",

            MLSubject.NEURAL_NETWORKS:
                f"Hi {game_data.player_name}! Ready to dive into the fascinating world of neural networks? "
                "These are computing systems inspired by the human brain. "
                "We'll start simple and build up your understanding step by step. "
                "Have you heard about neural networks before, or is this your first encounter?",

            MLSubject.TRAINING_VALIDATION:
                f"Welcome {game_data.player_name}! Today we're focusing on a crucial aspect of ML: "
                "training and validation. It's like preparing for an exam - you study (train) "
                "and take practice tests (validate) before the real test. "
                "What do you think is the biggest challenge when training ML models?",

            MLSubject.LOSS_OPTIMIZATION:
                f"Hello {game_data.player_name}! Let's explore loss functions and optimization - "
                "the engine that makes machine learning work. Think of it as teaching a model "
                "to get better by showing it how wrong it is and how to improve. "
                "Have you worked with any optimization problems before?",

            MLSubject.OVERFITTING_REGULARIZATION:
                f"Hi {game_data.player_name}! Today's topic is overfitting and regularization. "
                "Imagine memorizing answers vs understanding concepts - that's the challenge we'll tackle. "
                "Have you ever trained a model that performed great on training data but poorly on new data?",

            MLSubject.MODEL_EVALUATION:
                f"Welcome {game_data.player_name}! Let's learn about model evaluation - "
                "how we measure if our ML models are actually good. It's not just about accuracy! "
                "What metrics do you think are important when evaluating a machine learning model?"
        }

        return greetings.get(self.current_subject, greetings[MLSubject.SUPERVISED_LEARNING])

    def analyze_response_complexity(self, response: str) -> Dict:
        """Analyze user response to adjust difficulty."""
        words = response.split()
        word_count = len(words)

        # Check for ML terminology
        ml_terms = {
            'beginner': ['model', 'data', 'train', 'test', 'predict', 'accuracy'],
            'intermediate': ['validation', 'overfitting', 'gradient', 'epoch', 'batch',
                           'regularization', 'hyperparameter', 'cross-validation'],
            'advanced': ['backpropagation', 'convolution', 'embedding', 'attention',
                        'transformer', 'gan', 'reinforcement', 'bayesian', 'ensemble']
        }

        complexity_score = 0
        detected_terms = []

        for level, terms in ml_terms.items():
            for term in terms:
                if term.lower() in response.lower():
                    detected_terms.append(term)
                    if level == 'beginner':
                        complexity_score += 1
                    elif level == 'intermediate':
                        complexity_score += 2
                    else:  # advanced
                        complexity_score += 3

        return {
            'word_count': word_count,
            'complexity_score': complexity_score,
            'detected_terms': detected_terms,
            'shows_understanding': word_count > 15 and complexity_score > 3
        }

    def update_difficulty(self, analysis: Dict):
        """Update difficulty based on response analysis."""
        if self.state.session_count < 3:
            return  # Don't adjust too early

        shows_understanding = analysis['shows_understanding']
        complexity = analysis['complexity_score']

        if self.difficulty_level == DifficultyLevel.BEGINNER:
            if self.state.session_count >= 5 and shows_understanding and complexity >= 5:
                self.difficulty_level = DifficultyLevel.INTERMEDIATE
                self.add_system_message("Adjusting to intermediate level based on your understanding.")

        elif self.difficulty_level == DifficultyLevel.INTERMEDIATE:
            if self.state.session_count >= 10 and shows_understanding and complexity >= 10:
                self.difficulty_level = DifficultyLevel.ADVANCED
                self.add_system_message("Advancing to expert level based on your progress.")

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
            MLSubject.SUPERVISED_LEARNING: [
                "Linear regression basics",
                "Classification algorithms",
                "Feature engineering",
                "Train-test splitting",
                "Model selection"
            ],
            MLSubject.NEURAL_NETWORKS: [
                "Perceptron model",
                "Activation functions",
                "Multi-layer networks",
                "Convolutional layers",
                "Recurrent networks"
            ],
            MLSubject.TRAINING_VALIDATION: [
                "K-fold cross-validation",
                "Stratified sampling",
                "Validation curves",
                "Learning curves",
                "Hyperparameter tuning"
            ],
            MLSubject.LOSS_OPTIMIZATION: [
                "Mean squared error",
                "Cross-entropy loss",
                "Gradient descent",
                "Adam optimizer",
                "Learning rate scheduling"
            ],
            MLSubject.OVERFITTING_REGULARIZATION: [
                "L1 and L2 regularization",
                "Dropout technique",
                "Early stopping",
                "Data augmentation",
                "Ensemble methods"
            ],
            MLSubject.MODEL_EVALUATION: [
                "Confusion matrix",
                "ROC and AUC",
                "Precision vs recall",
                "F1 score",
                "Cross-validation metrics"
            ]
        }

        suggestions = topic_suggestions.get(self.current_subject, [])

        # Filter out already completed topics
        return [topic for topic in suggestions
                if topic not in self.state.completed_topics]

    def create_practice_exercise(self) -> str:
        """Create a practice exercise based on current topic and difficulty."""
        exercises = {
            DifficultyLevel.BEGINNER: {
                MLSubject.SUPERVISED_LEARNING:
                    "Let's practice: Given a dataset of house prices with features like size and location, "
                    "which type of supervised learning would you use - classification or regression? Why?",
                MLSubject.NEURAL_NETWORKS:
                    "Exercise: Draw or describe a simple neural network with 2 input neurons, "
                    "3 hidden neurons, and 1 output neuron. What could this network be used for?"
            },
            DifficultyLevel.INTERMEDIATE: {
                MLSubject.SUPERVISED_LEARNING:
                    "Challenge: You have a dataset with 1000 samples. How would you split it for "
                    "training and testing? What problems might arise with a 50-50 split?",
                MLSubject.NEURAL_NETWORKS:
                    "Exercise: If you have a network that always predicts the same output regardless "
                    "of input, what might be wrong? Consider activation functions and weight initialization."
            },
            DifficultyLevel.ADVANCED: {
                MLSubject.SUPERVISED_LEARNING:
                    "Advanced exercise: Design a multi-class classification pipeline including "
                    "feature preprocessing, model selection, and evaluation strategy for imbalanced classes.",
                MLSubject.NEURAL_NETWORKS:
                    "Challenge: Explain how you would implement a custom loss function for a neural network "
                    "that penalizes false negatives more than false positives."
            }
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
        for term in analysis['detected_terms']:
            self.track_topic_mention(term)

        # Generate response using parent class method
        response = await self.generate_response(user_input)

        return response