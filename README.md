# LLM PvP Gaming Framework

A Python framework for allowing various Large Language Models (LLMs) to compete against each other in text-based games.

## Features

- **Multiple LLM Support**: Google (Gemini), OpenAI (GPT), Anthropic (Claude), xAI (Grok), Ollama (local), and OpenRouter
- **Dummy Players**: Test games without spending API tokens
- **Detailed Logging**: Full game logs with LLM reasoning and actions
- **Statistics Tracking**: Token usage, time, scores, and outcomes
- **Extensible Architecture**: Easy to add new games

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up API keys as environment variables:
```bash
# Google AI Studio
set GOOGLE_API_KEY=your_key_here

# OpenAI
set OPENAI_API_KEY=your_key_here

# Anthropic
set ANTHROPIC_API_KEY=your_key_here

# xAI
set XAI_API_KEY=your_key_here

# OpenRouter
set OPENROUTER_API_KEY=your_key_here

# Ollama (optional, defaults to http://localhost:11434)
set OLLAMA_BASE_URL=http://localhost:11434
```

## Usage

Run the interactive CLI:
```bash
python main.py
```

You will be prompted to:
1. Select a game (currently: Codenames)
2. Select Team A's model
3. Select Team B's model
4. Enter the number of games to play

### Example Session

```
=== Select Game ===
1. Codenames
Enter your choice (1): 1

=== Select Model for Team A ===
1. Google (Gemini)
2. OpenAI (GPT)
3. Anthropic (Claude)
4. xAI (Grok)
5. Ollama (Local)
6. OpenRouter
7. Dummy (Testing)
Enter your choice (1-7): 1

=== Select Model for Team B ===
Enter your choice (1-7): 3

=== Number of Games ===
How many games would you like to play? (default: 1): 3
```

## Games

### Codenames

A team-based word association game where:
- Each team has a **Spymaster** and an **Agent**
- 25 words are displayed on a board
- Spymasters know which words belong to their team
- Spymasters give one-word clues and a count
- Agents guess words based on the clues
- First team to reveal all their words wins
- Revealing the assassin word = instant loss

**Game Rules**:
- Spymasters see: all word assignments, scores
- Agents see: board state, previous clues, current clue
- Memory is separate per role (agents can't see spymaster's private reasoning)
- All clues are public (both teams hear them)

## Output

### Terminal Display

During gameplay, you'll see abbreviated action descriptions:
```
Team A Spymaster: animal, 3
Team A Agent chooses elephant, Correct! One of your words.
Team A Agent chooses penguin, Correct! One of your words.
Team A Agent chooses python, Neutral word. Turn ends.
Score: Team A: 2/9, Team B: 0/8
```

### Game Logs

Detailed logs are saved to `logs/game_TIMESTAMP.log` containing:
- Full LLM responses with reasoning
- Extracted actions (JSON)
- Results and outcomes
- Public descriptions

### Statistics

Game statistics are appended to `data/games.jsonl` (one JSON object per line):
```json
{
  "timestamp": "2025-11-19T21:20:04.814026",
  "game_type": "Codenames",
  "team_a_model": "Google (gemini-2.0-flash-exp)",
  "team_b_model": "Anthropic (claude-3-5-sonnet-20241022)",
  "team_a_tokens": 1543,
  "team_b_tokens": 1821,
  "team_a_time": 12.34,
  "team_b_time": 15.67,
  "team_a_score": 9,
  "team_b_score": 6,
  "turns": [...],
  "winner": "Team A"
}
```

## Project Structure

```
pvp_llm/
├── main.py                          # CLI entry point
├── requirements.txt                 # Dependencies
├── config/
│   └── words.txt                    # Word list for Codenames
├── llm/
│   ├── __init__.py
│   ├── base.py                      # Abstract LLM interface
│   ├── providers.py                 # API implementations
│   └── dummy.py                     # Mock LLM for testing
├── game/
│   ├── __init__.py
│   ├── base.py                      # Abstract Game base class
│   ├── player.py                    # Player/Role abstraction
│   └── codenames/
│       ├── __init__.py
│       ├── game.py                  # Codenames game logic
│       ├── roles.py                 # Spymaster and Agent roles
│       └── dummy_players.py         # Dummy Codenames players
├── stats/
│   ├── __init__.py
│   └── tracker.py                   # Statistics tracking and storage
├── logs/                            # Game logs (created at runtime)
└── data/                            # Statistics storage (created at runtime)
```

## Adding New Games

To add a new game:

1. Create a new directory under `game/` (e.g., `game/poker/`)

2. Implement the game logic by extending `game.base.Game`:
```python
from game.base import Game

class PokerGame(Game):
    def setup(self):
        # Initialize game state
        pass
    
    def get_next_player(self):
        # Return next player
        pass
    
    # ... implement other abstract methods
```

3. Define role prompts explaining the rules and expected JSON format

4. Create dummy players for testing:
```python
from llm.dummy import DummyProvider

class DummyPokerPlayer(DummyProvider):
    def send_message(self, messages, system_prompt):
        # Implement simple rule-based or random behavior
        pass
```

5. Add the game to `main.py` in the game selection menu

## Configuration

### Model Selection

Models are configured in `config/models.yml`. After selecting a provider, you'll see a numbered list of available models:

```
Available Google models:
1. Gemini 2.0 Flash (Experimental)
2. Gemini 1.5 Pro
3. Gemini 1.5 Flash
4. Gemini 1.0 Pro
5. Custom (enter model name manually)

Select model (1-5): 1
```

To add new models, simply edit `config/models.yml` - no code changes needed! See `MODELS.md` for details.

### Word List

Edit `config/words.txt` to customize the Codenames word list. Each line should contain one word. The game randomly selects 25 words per game.

## Testing

Test the framework with dummy players to avoid API costs:
```python
from game.codenames.dummy_players import DummyCodenamesSpymaster, DummyCodenamesAgent
from game.codenames.game import CodenamesGame
from stats.tracker import GameTracker

# Create dummy LLMs
team_a_spymaster = DummyCodenamesSpymaster()
team_a_agent = DummyCodenamesAgent()
team_b_spymaster = DummyCodenamesSpymaster()
team_b_agent = DummyCodenamesAgent()

# Create and play game
game = CodenamesGame(
    team_a_spymaster_llm=team_a_spymaster,
    team_a_agent_llm=team_a_agent,
    team_b_spymaster_llm=team_b_spymaster,
    team_b_agent_llm=team_b_agent
)

game.setup()
# ... run game loop
```

## License

This project is provided as-is for educational and research purposes.

## Future Enhancements

- More games (Poker, Chess variants, Diplomacy, etc.)
- Web interface for viewing games
- Analytics dashboard for statistics
- Tournament mode
- ELO ratings for models
- Multi-game championships

