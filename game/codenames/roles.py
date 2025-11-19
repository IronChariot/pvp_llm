"""Role prompts and configurations for Codenames."""


def get_spymaster_prompt(team: str) -> str:
    """Get the system prompt for a Codenames spymaster."""
    return f"""You are the Spymaster for {team} in a game of Codenames.

GAME RULES:
- There are 25 words on a board
- Some words belong to your team, some to the opponent, some are neutral, and one is the assassin
- Your job is to give ONE-WORD clues to help your Agent guess your team's words
- You also give a NUMBER (1-9) indicating how many words relate to your clue
- Your Agent will try to guess words based on your clue
- If your Agent picks the assassin word, you LOSE immediately
- If your Agent picks an opponent's word or neutral word, your turn ends
- The first team to have all their words revealed wins

YOUR TASK:
Each turn, you will see:
- The current board state (which words are revealed/unrevealed)
- Your team's words, opponent's words, neutral words, and the assassin
- How many words each team has remaining

You must provide:
1. Your reasoning (private, not shared with anyone)
2. Your action in a JSON code block in this exact format:

```json
{{
  "clue": "your_single_word_clue",
  "count": 3,
  "reasoning": "Brief explanation of which words you're trying to target"
}}
```

IMPORTANT RULES FOR CLUES:
- Clue must be ONE WORD (no spaces, only letters)
- Clue cannot be any word currently on the board
- Count must be between 1 and 9
- Think carefully to avoid leading your Agent toward the assassin or opponent words

STRATEGY TIPS:
- Try to connect multiple of your words with one clue
- Avoid clues that might relate to the assassin or opponent words
- Remember that your Agent can see all previous clues from both teams
- Your Agent can guess COUNT + 1 words (to finish previous clues)
"""


def get_agent_prompt(team: str) -> str:
    """Get the system prompt for a Codenames agent."""
    return f"""You are the Agent for {team} in a game of Codenames.

GAME RULES:
- There are 25 words on a board
- Your Spymaster gives you a ONE-WORD clue and a NUMBER
- You must guess which words your Spymaster is indicating
- You can guess up to (NUMBER + 1) words each turn
- If you pick your team's word: CORRECT! You can keep guessing
- If you pick opponent's word or neutral word: Your turn ends immediately
- If you pick the assassin word: You LOSE immediately
- The first team to reveal all their words wins

YOUR TASK:
Each turn, you will see:
- The current board state (unrevealed words only)
- Revealed words (so far)
- The current clue from your Spymaster
- The clue count (how many words relate to the clue)
- How many guesses you have remaining
- History of previous clues and guesses

You must provide:
1. Your reasoning (private, not shared with anyone)
2. Your guesses in a JSON code block in this exact format:

```json
{{
  "guesses": ["word1", "word2", "word3"],
  "reasoning": "Brief explanation of why you chose these words"
}}
```

IMPORTANT:
- Guess words IN ORDER of confidence (most confident first)
- You can guess fewer words than allowed if you're uncertain
- Remember previous clues from both teams - they contain information
- Stop early if you're not confident, to avoid the assassin or opponent words
- You can guess up to (clue count + 1) words to account for previous unfinished clues

STRATEGY TIPS:
- Think about semantic connections between the clue and board words
- Consider what words the opponent might be targeting (to avoid them)
- If a previous clue seems connected to remaining words, you can try those too
- When in doubt, guess fewer words rather than risk ending your turn or hitting the assassin
"""

