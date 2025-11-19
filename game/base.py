"""Abstract base class for games."""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from game.player import Player


class Game(ABC):
    """Abstract base class for all games."""
    
    def __init__(self):
        self.players: List[Player] = []
        self.current_player_index = 0
        self.game_state = {}
        self.turn_number = 0
        self.game_over = False
        self.winner = None
    
    @abstractmethod
    def setup(self):
        """Initialize the game state, board, and players."""
        pass
    
    @abstractmethod
    def get_next_player(self) -> Player:
        """Return the next player whose turn it is."""
        pass
    
    @abstractmethod
    def is_game_over(self) -> bool:
        """Check if the game has ended."""
        pass
    
    @abstractmethod
    def get_game_state(self, for_player: Player) -> Dict:
        """
        Get the current game state from a specific player's perspective.
        This allows for hidden information (different players see different things).
        
        Args:
            for_player: The player whose perspective to show
            
        Returns:
            Dict containing the game state visible to that player
        """
        pass
    
    @abstractmethod
    def execute_action(self, player: Player, action: Dict) -> Dict:
        """
        Process a player's action and update game state.
        
        Args:
            player: The player taking the action
            action: Dict containing the action details
            
        Returns:
            Dict with result information (success, message, etc.)
        """
        pass
    
    @abstractmethod
    def get_winner(self) -> Optional[str]:
        """
        Return the winner of the game.
        
        Returns:
            String identifying the winner (e.g., "Team A", "Team B") or None
        """
        pass
    
    @abstractmethod
    def get_public_action_description(self, player: Player, action: Dict, result: Dict) -> str:
        """
        Get a human-readable description of an action for terminal display.
        This is what other players and viewers see.
        
        Args:
            player: The player who took the action
            action: The action that was taken
            result: The result of the action
            
        Returns:
            String describing the action for public display
        """
        pass

