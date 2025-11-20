"""Codenames game implementation."""
import random
from typing import Dict, List, Optional
from game.base import Game
from game.player import Player


class CodenamesGame(Game):
    """Implementation of the Codenames game."""
    
    def __init__(self, team_a_spymaster_llm, team_a_agent_llm, 
                 team_b_spymaster_llm, team_b_agent_llm, word_file: str = "config/words.txt"):
        super().__init__()
        self.team_a_spymaster_llm = team_a_spymaster_llm
        self.team_a_agent_llm = team_a_agent_llm
        self.team_b_spymaster_llm = team_b_spymaster_llm
        self.team_b_agent_llm = team_b_agent_llm
        self.word_file = word_file
        
        # Game state
        self.words: List[str] = []
        self.team_a_words: set = set()
        self.team_b_words: set = set()
        self.neutral_words: set = set()
        self.assassin_word: str = ""
        self.revealed_words: set = set()
        self.current_team = "Team A"
        self.current_phase = "spymaster"  # "spymaster" or "agent"
        self.current_clue = None
        self.current_clue_count = 0
        self.guesses_remaining = 0
        self.game_history: List[str] = []
        
        # Track clues and correct guesses per team for extra guess optimization
        self.team_a_total_clue_counts = 0
        self.team_a_correct_guesses = 0
        self.team_b_total_clue_counts = 0
        self.team_b_correct_guesses = 0
    
    def setup(self):
        """Initialize the Codenames game."""
        # Load words
        with open(self.word_file, "r", encoding="utf-8") as f:
            all_words = [line.strip() for line in f if line.strip()]
        
        # Select 25 random words
        self.words = random.sample(all_words, min(25, len(all_words)))
        
        # Randomly assign words
        word_indices = list(range(25))
        random.shuffle(word_indices)
        
        # One team gets 9, the other gets 8
        first_team_count = 9
        second_team_count = 8
        
        # Randomly decide which team goes first (gets 9 words)
        if random.random() < 0.5:
            self.current_team = "Team A"
            team_a_indices = word_indices[:first_team_count]
            team_b_indices = word_indices[first_team_count:first_team_count + second_team_count]
        else:
            self.current_team = "Team B"
            team_b_indices = word_indices[:first_team_count]
            team_a_indices = word_indices[first_team_count:first_team_count + second_team_count]
        
        assassin_index = word_indices[first_team_count + second_team_count]
        neutral_indices = word_indices[first_team_count + second_team_count + 1:]
        
        self.team_a_words = {self.words[i] for i in team_a_indices}
        self.team_b_words = {self.words[i] for i in team_b_indices}
        self.assassin_word = self.words[assassin_index]
        self.neutral_words = {self.words[i] for i in neutral_indices}
        
        # Create players with prompts
        from game.codenames.roles import get_spymaster_prompt, get_agent_prompt
        
        self.players = [
            Player("Spymaster", "Team A", self.team_a_spymaster_llm, 
                   get_spymaster_prompt("Team A")),
            Player("Agent", "Team A", self.team_a_agent_llm,
                   get_agent_prompt("Team A")),
            Player("Spymaster", "Team B", self.team_b_spymaster_llm,
                   get_spymaster_prompt("Team B")),
            Player("Agent", "Team B", self.team_b_agent_llm,
                   get_agent_prompt("Team B"))
        ]
        
        self.current_phase = "spymaster"
    
    def get_next_player(self) -> Player:
        """Return the next player whose turn it is."""
        # Find the appropriate player based on current team and phase
        for player in self.players:
            if player.team == self.current_team:
                if self.current_phase == "spymaster" and player.role == "Spymaster":
                    return player
                elif self.current_phase == "agent" and player.role == "Agent":
                    return player
        
        return self.players[0]  # Fallback
    
    def is_game_over(self) -> bool:
        """Check if the game has ended."""
        # Game ends if all of one team's words are revealed
        team_a_remaining = self.team_a_words - self.revealed_words
        team_b_remaining = self.team_b_words - self.revealed_words
        
        if len(team_a_remaining) == 0:
            self.winner = "Team A"
            return True
        
        if len(team_b_remaining) == 0:
            self.winner = "Team B"
            return True
        
        # Game ends if assassin is revealed
        if self.assassin_word in self.revealed_words:
            # The team that revealed it loses
            return True
        
        return False
    
    def get_game_state(self, for_player: Player) -> Dict:
        """Get game state from a specific player's perspective."""
        state = {
            "words_on_board": [w for w in self.words if w not in self.revealed_words],
            "revealed_words": list(self.revealed_words),
            "turn_number": self.turn_number,
            "current_team": self.current_team,
            "recent_history": self.game_history[-10:] if self.game_history else []
        }
        
        # Spymasters see the word assignments
        if for_player.role == "Spymaster":
            state["your_words"] = list(self.team_a_words if for_player.team == "Team A" else self.team_b_words)
            state["opponent_words"] = list(self.team_b_words if for_player.team == "Team A" else self.team_a_words)
            state["neutral_words"] = list(self.neutral_words)
            state["assassin_word"] = self.assassin_word
            
            # Calculate remaining words
            your_remaining = len([w for w in state["your_words"] if w not in self.revealed_words])
            opponent_remaining = len([w for w in state["opponent_words"] if w not in self.revealed_words])
            state["your_remaining_count"] = your_remaining
            state["opponent_remaining_count"] = opponent_remaining
        
        # Agents see clues and guessing state
        if for_player.role == "Agent":
            if self.current_phase == "agent" and for_player.team == self.current_team:
                state["current_clue"] = self.current_clue
                state["clue_count"] = self.current_clue_count
                state["guesses_remaining"] = self.guesses_remaining
        
        return state
    
    def execute_action(self, player: Player, action: Dict) -> Dict:
        """Process a player's action."""
        if player.role == "Spymaster":
            return self._execute_spymaster_action(player, action)
        elif player.role == "Agent":
            return self._execute_agent_action(player, action)
        
        return {"success": False, "message": "Unknown role"}
    
    def _execute_spymaster_action(self, player: Player, action: Dict) -> Dict:
        """Process a spymaster's clue."""
        clue = action.get("clue", "").strip().lower()
        count = action.get("count", 1)
        
        # Validate clue
        if not clue:
            return {"success": False, "message": "No clue provided"}
        
        # Check that clue is a single word
        if " " in clue or not clue.isalpha():
            return {"success": False, "message": "Clue must be a single word with only letters"}
        
        # Check that clue is not on the board
        if clue.capitalize() in self.words or clue.upper() in self.words or clue in self.words:
            return {"success": False, "message": "Clue cannot be a word on the board"}
        
        # Validate count
        if not isinstance(count, int) or count < 1 or count > 9:
            return {"success": False, "message": "Count must be an integer between 1 and 9"}
        
        # Store the clue
        self.current_clue = clue
        self.current_clue_count = count
        self.guesses_remaining = count + 1  # Can guess one more than the count
        
        # Track total clue counts for this team
        if player.team == "Team A":
            self.team_a_total_clue_counts += count
        else:
            self.team_b_total_clue_counts += count
        
        # Add to history
        history_msg = f"{player.team} Spymaster: {clue}, {count}"
        self.game_history.append(history_msg)
        
        # Broadcast clue to all players
        for p in self.players:
            if p != player:  # Don't send to the spymaster who just gave the clue
                p.add_public_message(history_msg)
        
        # Switch to agent phase
        self.current_phase = "agent"
        
        return {
            "success": True,
            "message": f"Clue given: {clue}, {count}",
            "clue": clue,
            "count": count
        }
    
    def _execute_agent_action(self, player: Player, action: Dict) -> Dict:
        """Process an agent's guesses."""
        guesses = action.get("guesses", [])
        
        if not guesses:
            # If no guesses, end turn and switch teams
            self.current_team = "Team B" if self.current_team == "Team A" else "Team A"
            self.current_phase = "spymaster"
            self.current_clue = None
            self.current_clue_count = 0
            self.guesses_remaining = 0
            return {"success": False, "message": "No guesses provided, turn ends"}
        
        results = []
        stop_guessing = False
        
        for guess in guesses:
            # Check if we've run out of guesses
            if self.guesses_remaining <= 0:
                break
            
            guess = guess.strip()
            
            # Validate guess
            if guess not in self.words:
                results.append({
                    "word": guess,
                    "result": "invalid",
                    "message": "Not on the board"
                })
                continue
            
            if guess in self.revealed_words:
                results.append({
                    "word": guess,
                    "result": "already_revealed",
                    "message": "Already revealed"
                })
                continue
            
            # Reveal the word
            self.revealed_words.add(guess)
            self.guesses_remaining -= 1
            
            # Check what type of word it is
            if guess == self.assassin_word:
                results.append({
                    "word": guess,
                    "result": "assassin",
                    "message": "ASSASSIN! Game over!"
                })
                # The team that picked the assassin loses
                self.winner = "Team B" if player.team == "Team A" else "Team A"
                self.game_over = True
                stop_guessing = True
                break
            elif guess in (self.team_a_words if player.team == "Team A" else self.team_b_words):
                results.append({
                    "word": guess,
                    "result": "correct",
                    "message": "Correct! One of your words."
                })
                # Track correct guesses for this team
                if player.team == "Team A":
                    self.team_a_correct_guesses += 1
                else:
                    self.team_b_correct_guesses += 1
                # Continue guessing
            elif guess in (self.team_b_words if player.team == "Team A" else self.team_a_words):
                results.append({
                    "word": guess,
                    "result": "opponent",
                    "message": "Opponent's word. Turn ends."
                })
                stop_guessing = True
                break
            elif guess in self.neutral_words:
                results.append({
                    "word": guess,
                    "result": "neutral",
                    "message": "Neutral word. Turn ends."
                })
                stop_guessing = True
                break
        
        # Add results to history
        for result in results:
            history_msg = f"{player.team} Agent chose {result['word']}: {result['message']}"
            self.game_history.append(history_msg)
            
            # Broadcast to all players
            for p in self.players:
                if p != player:
                    p.add_public_message(history_msg)
        
        # Check if turn should end
        should_end_turn = False
        
        if stop_guessing:
            # Made a wrong guess, turn ends immediately
            should_end_turn = True
        elif self.guesses_remaining <= 0:
            # Used all guesses
            should_end_turn = True
        elif self.guesses_remaining == 1:
            # Only the +1 extra guess remains
            # Check if there are leftover clues from previous turns
            if player.team == "Team A":
                total_clues = self.team_a_total_clue_counts
                correct_guesses = self.team_a_correct_guesses
            else:
                total_clues = self.team_b_total_clue_counts
                correct_guesses = self.team_b_correct_guesses
            
            # If all clues have been used perfectly (no leftovers), skip the extra guess
            if total_clues <= correct_guesses:
                should_end_turn = True
                # Note: We don't decrement guesses_remaining here since we're skipping it
        
        if should_end_turn:
            # Switch to other team's spymaster
            self.current_team = "Team B" if self.current_team == "Team A" else "Team A"
            self.current_phase = "spymaster"
            self.current_clue = None
            self.current_clue_count = 0
            self.guesses_remaining = 0
        
        return {
            "success": True,
            "results": results,
            "guesses_remaining": self.guesses_remaining
        }
    
    def get_winner(self) -> Optional[str]:
        """Return the winner of the game."""
        if self.winner:
            return self.winner
        
        # Check if game is over
        if self.is_game_over():
            return self.winner
        
        return None
    
    def get_public_action_description(self, player: Player, action: Dict, result: Dict) -> str:
        """Get human-readable description of an action."""
        if player.role == "Spymaster":
            if result.get("success"):
                return f"{player.full_name}: {result['clue']}, {result['count']}"
            else:
                return f"{player.full_name}: [Invalid clue attempt]"
        
        elif player.role == "Agent":
            if not result.get("success"):
                return f"{player.full_name}: [Invalid guess attempt]"
            
            descriptions = []
            for guess_result in result.get("results", []):
                word = guess_result["word"]
                message = guess_result["message"]
                descriptions.append(f"{player.full_name} chooses {word}, {message}")
            
            return "\n".join(descriptions) if descriptions else f"{player.full_name}: [No valid guesses]"
        
        return f"{player.full_name}: [Unknown action]"
    
    def get_score(self, team: str) -> int:
        """Get the current score for a team (words correctly revealed)."""
        team_words = self.team_a_words if team == "Team A" else self.team_b_words
        return len(team_words & self.revealed_words)

