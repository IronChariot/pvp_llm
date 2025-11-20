"""Statistics tracking and logging for games."""
import json
import os
from datetime import datetime
from typing import Dict, List


class GameTracker:
    """Tracks game statistics and logs detailed game information."""
    
    def __init__(self):
        self.current_game_log = []
        self.game_stats = {}
        
        # Ensure directories exist
        os.makedirs("logs", exist_ok=True)
        os.makedirs("data", exist_ok=True)
    
    def start_game(self, game_type: str, team_a_model: str, team_b_model: str, initial_game_state: Dict = None):
        """Initialize tracking for a new game."""
        self.current_game_log = []
        self.game_stats = {
            "timestamp": datetime.now().isoformat(),
            "game_type": game_type,
            "team_a_model": team_a_model,
            "team_b_model": team_b_model,
            "team_a_tokens": 0,
            "team_b_tokens": 0,
            "team_a_time": 0.0,
            "team_b_time": 0.0,
            "team_a_score": 0,
            "team_b_score": 0,
            "initial_game_state": initial_game_state or {},
            "turns": [],
            "winner": None
        }
    
    def log_turn(self, player_name: str, team: str, full_response: str, 
                 action: Dict, result: Dict, public_description: str, game_state_after: Dict = None):
        """
        Log a single turn with full details.
        
        Args:
            player_name: Full name of the player (e.g., "Team A Spymaster")
            team: Team identifier ("Team A" or "Team B")
            full_response: Full LLM response including reasoning
            action: The action dict extracted from the response
            result: Result of executing the action
            public_description: Human-readable description for terminal
            game_state_after: Complete game state after this turn (for replay)
        """
        turn_log = {
            "player": player_name,
            "team": team,
            "full_response": full_response,
            "action": action,
            "result": result,
            "public_description": public_description,
            "game_state_after": game_state_after or {}
        }
        
        self.current_game_log.append(turn_log)
        self.game_stats["turns"].append({
            "player": player_name,
            "team": team,
            "action": action,
            "result": result,
            "game_state_after": game_state_after or {}
        })
    
    def update_stats(self, team: str, tokens: int, time_spent: float, score: int = 0):
        """
        Update statistics for a team.
        
        Args:
            team: Team identifier ("Team A" or "Team B")
            tokens: Number of tokens used in this turn
            time_spent: Time spent in seconds
            score: Points scored this turn (optional)
        """
        team_key = team.lower().replace(" ", "_")
        self.game_stats[f"{team_key}_tokens"] += tokens
        self.game_stats[f"{team_key}_time"] += time_spent
        self.game_stats[f"{team_key}_score"] += score
    
    def end_game(self, winner: str):
        """
        Mark the game as finished and save all logs and stats.
        
        Args:
            winner: Winning team identifier
        """
        self.game_stats["winner"] = winner
        
        # Save detailed log
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_filename = f"logs/game_{timestamp}.log"
        
        with open(log_filename, "w", encoding="utf-8") as f:
            f.write(f"Game: {self.game_stats['game_type']}\n")
            f.write(f"Started: {self.game_stats['timestamp']}\n")
            f.write(f"Team A: {self.game_stats['team_a_model']}\n")
            f.write(f"Team B: {self.game_stats['team_b_model']}\n")
            f.write(f"Winner: {winner}\n")
            f.write("=" * 80 + "\n\n")
            
            # Write initial game state
            if self.game_stats.get('initial_game_state'):
                f.write("INITIAL GAME STATE\n")
                f.write("-" * 80 + "\n")
                f.write(json.dumps(self.game_stats['initial_game_state'], indent=2) + "\n")
                f.write("=" * 80 + "\n\n")
            
            for i, turn in enumerate(self.current_game_log, 1):
                f.write(f"Turn {i}: {turn['player']}\n")
                f.write("-" * 80 + "\n")
                f.write("Full Response (including reasoning):\n")
                f.write(turn['full_response'] + "\n\n")
                f.write(f"Action: {json.dumps(turn['action'], indent=2)}\n")
                f.write(f"Result: {json.dumps(turn['result'], indent=2)}\n")
                f.write(f"Public: {turn['public_description']}\n")
                if turn.get('game_state_after'):
                    f.write(f"\nGame State After Turn:\n")
                    f.write(json.dumps(turn['game_state_after'], indent=2) + "\n")
                f.write("=" * 80 + "\n\n")
        
        # Append stats to JSONL file
        stats_filename = "data/games.jsonl"
        with open(stats_filename, "a", encoding="utf-8") as f:
            f.write(json.dumps(self.game_stats) + "\n")
        
        return log_filename
    
    def get_current_stats(self) -> Dict:
        """Return current game statistics."""
        return self.game_stats.copy()

