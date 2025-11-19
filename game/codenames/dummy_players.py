"""Dummy/mock players for Codenames testing."""
import random
import json
from typing import Dict, List
from llm.dummy import DummyProvider


class DummyCodenamesSpymaster(DummyProvider):
    """Dummy Spymaster that gives random clues."""
    
    def __init__(self, model_name: str = "dummy-spymaster"):
        super().__init__(model_name)
        self.word_pool = [
            "animal", "object", "place", "color", "food", "vehicle",
            "sport", "music", "science", "nature", "building", "weather"
        ]
    
    def send_message(self, messages: List[Dict[str, str]], system_prompt: str = "") -> Dict:
        """Generate a random clue not on the board."""
        import time
        start_time = time.time()
        
        # Simulate thinking time
        time.sleep(0.1)
        
        # Extract board words from the last message to avoid using them
        board_words = set()
        if messages:
            last_message = messages[-1]["content"]
            # Simple extraction - look for words in the message
            for word in self.word_pool:
                if word.lower() not in last_message.lower():
                    board_words.add(word)
        
        # Pick a random word that's likely not on the board
        clue_word = random.choice(list(board_words) if board_words else self.word_pool)
        clue_count = random.randint(1, 4)
        
        # Format response with reasoning and JSON action
        response = f"""Let me think about this... I'll give a random clue to see what happens.

I'm going to try the word '{clue_word}' and say it relates to {clue_count} words.

```json
{{
  "clue": "{clue_word}",
  "count": {clue_count},
  "reasoning": "Random selection for testing purposes"
}}
```
"""
        
        elapsed_time = time.time() - start_time
        self.total_time += elapsed_time
        
        tokens = random.randint(20, 50)
        self.total_tokens += tokens
        
        return {
            "response": response,
            "tokens": tokens
        }


class DummyCodenamesAgent(DummyProvider):
    """Dummy Agent that guesses random words."""
    
    def __init__(self, model_name: str = "dummy-agent"):
        super().__init__(model_name)
    
    def send_message(self, messages: List[Dict[str, str]], system_prompt: str = "") -> Dict:
        """Guess random unrevealed words."""
        import time
        start_time = time.time()
        
        # Simulate thinking time
        time.sleep(0.1)
        
        # Extract unrevealed words and clue count from the last message
        unrevealed_words = []
        clue_count = 1
        
        if messages:
            last_message = messages[-1]["content"]
            
            # Look for "words_on_board:" section (parsing list items)
            lines = last_message.split("\n")
            for i, line in enumerate(lines):
                if "words_on_board:" in line.lower():
                    # Next lines starting with "  - " are the words
                    j = i + 1
                    while j < len(lines):
                        if lines[j].strip().startswith("- "):
                            word = lines[j].strip()[2:].strip()
                            if word:
                                unrevealed_words.append(word)
                            j += 1
                        else:
                            break
            
            # Look for clue_count and guesses_remaining
            for line in lines:
                if "clue_count:" in line.lower():
                    try:
                        clue_count = int(line.split(":")[-1].strip())
                    except:
                        clue_count = 1
                elif "guesses_remaining:" in line.lower():
                    try:
                        # Use guesses_remaining if available
                        remaining = int(line.split(":")[-1].strip())
                        if remaining > 0:
                            clue_count = remaining
                    except:
                        pass
        
        # Pick random words (up to clue_count)
        num_guesses = min(clue_count, len(unrevealed_words))
        if num_guesses > 0:
            guesses = random.sample(unrevealed_words, num_guesses)
        else:
            guesses = []
        
        # Format response
        response = f"""Looking at the clue and the board... I'll just pick some random words for testing.

I'll guess these words in order: {', '.join(guesses) if guesses else 'none'}

```json
{{
  "guesses": {json.dumps(guesses)},
  "reasoning": "Random selection for testing purposes"
}}
```
"""
        
        elapsed_time = time.time() - start_time
        self.total_time += elapsed_time
        
        tokens = random.randint(20, 50)
        self.total_tokens += tokens
        
        return {
            "response": response,
            "tokens": tokens
        }

