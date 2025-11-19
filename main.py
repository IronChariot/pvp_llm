"""Main CLI interface for LLM PvP Gaming Framework."""
import sys
import yaml
from typing import Dict, Tuple, List
from llm.base import LLMBase
from llm.providers import (
    GoogleProvider, OpenAIProvider, AnthropicProvider,
    XAIProvider, OllamaProvider, OpenRouterProvider
)
from game.codenames.dummy_players import DummyCodenamesSpymaster, DummyCodenamesAgent
from game.codenames.game import CodenamesGame
from stats.tracker import GameTracker


def select_game() -> str:
    """Prompt user to select a game."""
    print("\n=== Select Game ===")
    print("1. Codenames")
    
    while True:
        choice = input("\nEnter your choice (1): ").strip()
        if choice == "1" or choice == "":
            return "codenames"
        else:
            print("Invalid choice. Please enter 1.")


def load_model_config() -> Dict:
    """Load model configuration from YAML file."""
    try:
        with open("config/models.yml", "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"Warning: Could not load config/models.yml: {e}")
        return {}


def select_model_from_list(provider_name: str, provider_key: str, model_config: Dict) -> str:
    """
    Show numbered list of models for a provider and let user select.
    
    Args:
        provider_name: Human-readable provider name
        provider_key: Key in the config file (lowercase)
        model_config: Loaded model configuration
        
    Returns:
        Selected model identifier
    """
    models = model_config.get(provider_key, [])
    
    if not models:
        # Fallback if config not loaded
        custom_model = input(f"Enter model name for {provider_name}: ").strip()
        return custom_model if custom_model else None
    
    print(f"\nAvailable {provider_name} models:")
    for i, model_info in enumerate(models, 1):
        print(f"{i}. {model_info['name']}")
    print(f"{len(models) + 1}. Custom (enter model name manually)")
    
    while True:
        choice = input(f"\nSelect model (1-{len(models) + 1}): ").strip()
        try:
            choice_num = int(choice)
            if 1 <= choice_num <= len(models):
                selected = models[choice_num - 1]
                print(f"Selected: {selected['name']} ({selected['model']})")
                return selected['model']
            elif choice_num == len(models) + 1:
                custom_model = input("Enter model name: ").strip()
                if custom_model:
                    return custom_model
                else:
                    print("Model name cannot be empty.")
            else:
                print(f"Please enter a number between 1 and {len(models) + 1}.")
        except ValueError:
            print("Please enter a valid number.")


def select_model(team_name: str, role: str = "", model_config: Dict = None) -> Tuple[str, LLMBase]:
    """Prompt user to select a model for a team."""
    if model_config is None:
        model_config = {}
    
    role_text = f" {role}" if role else ""
    print(f"\n=== Select Model for {team_name}{role_text} ===")
    print("1. Google (Gemini)")
    print("2. OpenAI (GPT)")
    print("3. Anthropic (Claude)")
    print("4. xAI (Grok)")
    print("5. Ollama (Local)")
    print("6. OpenRouter")
    print("7. Dummy (Testing)")
    
    provider_map = {
        "1": ("Google", "google", GoogleProvider),
        "2": ("OpenAI", "openai", OpenAIProvider),
        "3": ("Anthropic", "anthropic", AnthropicProvider),
        "4": ("xAI", "xai", XAIProvider),
        "5": ("Ollama", "ollama", OllamaProvider),
        "6": ("OpenRouter", "openrouter", OpenRouterProvider),
        "7": ("Dummy", "dummy", None)
    }
    
    while True:
        choice = input("\nEnter your choice (1-7): ").strip()
        if choice in provider_map:
            provider_name, provider_key, provider_class = provider_map[choice]
            
            # For dummy, we need to know the role
            if choice == "7":
                return "Dummy", None
            
            try:
                # Select specific model from list
                model_name = select_model_from_list(provider_name, provider_key, model_config)
                
                if not model_name:
                    print("No model selected. Please try again.")
                    continue
                
                # Create provider instance with selected model
                provider = provider_class(model_name)
                
                return provider_name, provider
            
            except Exception as e:
                print(f"\nError initializing {provider_name}: {e}")
                print("Please check your API keys and try again, or select a different provider.")
        else:
            print("Invalid choice. Please enter a number between 1 and 7.")


def get_num_games() -> int:
    """Prompt user for number of games to play."""
    print("\n=== Number of Games ===")
    while True:
        try:
            num = input("How many games would you like to play? (default: 1): ").strip()
            if num == "":
                return 1
            num_games = int(num)
            if num_games > 0:
                return num_games
            else:
                print("Please enter a positive number.")
        except ValueError:
            print("Please enter a valid number.")


def play_codenames(team_a_models: Dict, team_b_models: Dict, tracker: GameTracker):
    """Play a single game of Codenames."""
    
    # Create LLM instances for each role
    team_a_spymaster = team_a_models["spymaster"]
    team_a_agent = team_a_models["agent"]
    team_b_spymaster = team_b_models["spymaster"]
    team_b_agent = team_b_models["agent"]
    
    # Create the game
    game = CodenamesGame(
        team_a_spymaster_llm=team_a_spymaster,
        team_a_agent_llm=team_a_agent,
        team_b_spymaster_llm=team_b_spymaster,
        team_b_agent_llm=team_b_agent
    )
    
    game.setup()
    
    print("\n" + "=" * 80)
    print("GAME START: Codenames")
    print("=" * 80)
    print(f"Team A goes first!" if game.current_team == "Team A" else "Team B goes first!")
    print(f"Board: {', '.join(game.words)}")
    print("=" * 80 + "\n")
    
    # Game loop
    turn_count = 0
    max_turns = 100  # Prevent infinite loops
    
    while not game.is_game_over() and turn_count < max_turns:
        turn_count += 1
        
        # Get current player
        player = game.get_next_player()
        print(f"\n--- Turn {turn_count}: {player.full_name} ---")
        
        # Get game state for this player
        game_state = game.get_game_state(player)
        
        # Get action from player
        try:
            action, full_response = player.get_action(game_state)
            
            # Execute action
            result = game.execute_action(player, action)
            
            # Get public description
            public_desc = game.get_public_action_description(player, action, result)
            print(public_desc)
            
            # Track statistics
            team = player.team
            tokens = player.llm.total_tokens if hasattr(player.llm, 'total_tokens') else 0
            time_spent = player.llm.total_time if hasattr(player.llm, 'total_time') else 0
            
            # Reset per-turn counters
            if hasattr(player.llm, 'total_tokens'):
                prev_tokens = getattr(player.llm, '_prev_tokens', 0)
                turn_tokens = player.llm.total_tokens - prev_tokens
                player.llm._prev_tokens = player.llm.total_tokens
            else:
                turn_tokens = 0
            
            if hasattr(player.llm, 'total_time'):
                prev_time = getattr(player.llm, '_prev_time', 0.0)
                turn_time = player.llm.total_time - prev_time
                player.llm._prev_time = player.llm.total_time
            else:
                turn_time = 0.0
            
            score = game.get_score(team)
            
            tracker.update_stats(team, turn_tokens, turn_time, score)
            tracker.log_turn(player.full_name, team, full_response, action, result, public_desc)
            
            # Show current scores
            if result.get("success"):
                team_a_score = game.get_score("Team A")
                team_b_score = game.get_score("Team B")
                team_a_total = len(game.team_a_words)
                team_b_total = len(game.team_b_words)
                print(f"Score: Team A: {team_a_score}/{team_a_total}, Team B: {team_b_score}/{team_b_total}")
        
        except Exception as e:
            print(f"Error during {player.full_name}'s turn: {e}")
            import traceback
            traceback.print_exc()
            # Try to continue
            continue
    
    # Game over
    winner = game.get_winner()
    print("\n" + "=" * 80)
    print(f"GAME OVER! Winner: {winner}")
    print("=" * 80)
    
    return winner


def main():
    """Main entry point for the CLI."""
    print("=" * 80)
    print("LLM PvP Gaming Framework")
    print("=" * 80)
    
    # Load model configuration
    model_config = load_model_config()
    
    # Select game
    game_type = select_game()
    
    if game_type == "codenames":
        # For Codenames, we need to select models for each role
        print("\n=== Team A Setup ===")
        team_a_name, team_a_base = select_model("Team A", model_config=model_config)
        
        # Check if dummy, need separate instances for spymaster and agent
        if team_a_name == "Dummy":
            team_a_spymaster = DummyCodenamesSpymaster()
            team_a_agent = DummyCodenamesAgent()
        else:
            # For real LLMs, we can reuse the same provider instance (memory is separate per Player)
            team_a_spymaster = team_a_base
            # Create a fresh instance for the agent
            if team_a_name == "Google":
                team_a_agent = GoogleProvider(team_a_base.model_name)
            elif team_a_name == "OpenAI":
                team_a_agent = OpenAIProvider(team_a_base.model_name)
            elif team_a_name == "Anthropic":
                team_a_agent = AnthropicProvider(team_a_base.model_name)
            elif team_a_name == "xAI":
                team_a_agent = XAIProvider(team_a_base.model_name)
            elif team_a_name == "Ollama":
                team_a_agent = OllamaProvider(team_a_base.model_name)
            elif team_a_name == "OpenRouter":
                team_a_agent = OpenRouterProvider(team_a_base.model_name)
        
        print("\n=== Team B Setup ===")
        team_b_name, team_b_base = select_model("Team B", model_config=model_config)
        
        if team_b_name == "Dummy":
            team_b_spymaster = DummyCodenamesSpymaster()
            team_b_agent = DummyCodenamesAgent()
        else:
            team_b_spymaster = team_b_base
            if team_b_name == "Google":
                team_b_agent = GoogleProvider(team_b_base.model_name)
            elif team_b_name == "OpenAI":
                team_b_agent = OpenAIProvider(team_b_base.model_name)
            elif team_b_name == "Anthropic":
                team_b_agent = AnthropicProvider(team_b_base.model_name)
            elif team_b_name == "xAI":
                team_b_agent = XAIProvider(team_b_base.model_name)
            elif team_b_name == "Ollama":
                team_b_agent = OllamaProvider(team_b_base.model_name)
            elif team_b_name == "OpenRouter":
                team_b_agent = OpenRouterProvider(team_b_base.model_name)
        
        team_a_models = {
            "spymaster": team_a_spymaster,
            "agent": team_a_agent
        }
        
        team_b_models = {
            "spymaster": team_b_spymaster,
            "agent": team_b_agent
        }
        
        # Get number of games
        num_games = get_num_games()
        
        # Play games
        results = {"Team A": 0, "Team B": 0}
        
        for game_num in range(1, num_games + 1):
            print(f"\n\n{'=' * 80}")
            print(f"GAME {game_num} of {num_games}")
            print(f"{'=' * 80}")
            
            # Create tracker for this game
            tracker = GameTracker()
            tracker.start_game(
                game_type="Codenames",
                team_a_model=f"{team_a_name} ({team_a_spymaster.model_name})",
                team_b_model=f"{team_b_name} ({team_b_spymaster.model_name})"
            )
            
            try:
                winner = play_codenames(team_a_models, team_b_models, tracker)
                
                if winner:
                    results[winner] = results.get(winner, 0) + 1
                    tracker.end_game(winner)
                    
                    print(f"\nGame log saved. Current standings:")
                    print(f"Team A: {results['Team A']} wins")
                    print(f"Team B: {results['Team B']} wins")
            
            except Exception as e:
                print(f"\nError during game: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        # Final results
        print("\n\n" + "=" * 80)
        print("FINAL RESULTS")
        print("=" * 80)
        print(f"Team A ({team_a_name}): {results['Team A']} wins")
        print(f"Team B ({team_b_name}): {results['Team B']} wins")
        print("=" * 80)
    
    else:
        print(f"Game type '{game_type}' not yet implemented.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user. Exiting...")
        sys.exit(0)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

