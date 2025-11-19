"""Player/Role abstraction for games."""
import json
import re
from typing import Dict, List
from llm.base import LLMBase


class Player:
    """Represents a player/role in a game with an LLM backend."""
    
    def __init__(self, role: str, team: str, llm: LLMBase, system_prompt: str):
        """
        Initialize a player.
        
        Args:
            role: Role name (e.g., "Spymaster", "Agent")
            team: Team identifier (e.g., "Team A", "Team B")
            llm: LLM instance to use for this player
            system_prompt: System prompt explaining the role and rules
        """
        self.role = role
        self.team = team
        self.llm = llm
        self.system_prompt = system_prompt
        self.memory: List[Dict[str, str]] = []  # Separate memory stream per role
        self.full_name = f"{team} {role}"
    
    def get_action(self, game_state: Dict) -> tuple[Dict, str]:
        """
        Request an action from the LLM based on current game state.
        
        Args:
            game_state: Current game state visible to this player
            
        Returns:
            Tuple of (action dict, full response with reasoning)
        """
        # Build the message with game state
        message_content = self._format_game_state_message(game_state)
        
        # Add to memory
        self.memory.append({
            "role": "user",
            "content": message_content
        })
        
        # Get response from LLM
        response_data = self.llm.send_message(self.memory, self.system_prompt)
        full_response = response_data["response"]
        
        # Add response to memory
        self.memory.append({
            "role": "assistant",
            "content": full_response
        })
        
        # Extract action from JSON code block
        action = self._extract_action_from_response(full_response)
        
        return action, full_response
    
    def _format_game_state_message(self, game_state: Dict) -> str:
        """Format the game state into a message for the LLM."""
        message_parts = ["Current game state:"]
        
        for key, value in game_state.items():
            if isinstance(value, list):
                message_parts.append(f"\n{key}:")
                for item in value:
                    message_parts.append(f"\n  - {item}")
            elif isinstance(value, dict):
                message_parts.append(f"\n{key}:")
                for k, v in value.items():
                    message_parts.append(f"\n  {k}: {v}")
            else:
                message_parts.append(f"\n{key}: {value}")
        
        message_parts.append("\n\nProvide your reasoning and then your action in a JSON code block.")
        
        return "".join(message_parts)
    
    def _extract_action_from_response(self, response: str) -> Dict:
        """
        Extract the action JSON from the LLM response.
        Looks for JSON in code blocks (```json ... ``` or ```{ ... }```).
        """
        # Try to find JSON in code blocks
        json_pattern = r'```(?:json)?\s*(\{.*?\})\s*```'
        matches = re.findall(json_pattern, response, re.DOTALL)
        
        if matches:
            try:
                return json.loads(matches[0])
            except json.JSONDecodeError:
                pass
        
        # Try to find raw JSON object
        json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
        matches = re.findall(json_pattern, response, re.DOTALL)
        
        for match in matches:
            try:
                return json.loads(match)
            except json.JSONDecodeError:
                continue
        
        # If no valid JSON found, return empty dict
        return {}
    
    def add_public_message(self, message: str):
        """
        Add a public message to the player's memory (e.g., opponent's clue).
        This is information that all players can see.
        
        Args:
            message: The public message to add
        """
        self.memory.append({
            "role": "user",
            "content": message
        })

