// Global State
let games = [];
let currentGame = null;
let gameSteps = [];
let currentStepIndex = -1;

// DOM Elements
const gameSelector = document.getElementById('game-selector');
const gameGrid = document.getElementById('game-grid');
const teamAModel = document.getElementById('team-a-model');
const teamBModel = document.getElementById('team-b-model');
const teamAScore = document.getElementById('team-a-score');
const teamBScore = document.getElementById('team-b-score');
const teamALog = document.getElementById('team-a-log');
const teamBLog = document.getElementById('team-b-log');
const clueDisplay = document.getElementById('clue-display');
const clueText = document.getElementById('clue-text');
const clueCount = document.getElementById('clue-count');
const turnIndicator = document.getElementById('turn-indicator');
const statusMessage = document.getElementById('status-message');
const prevBtn = document.getElementById('prev-btn');
const nextBtn = document.getElementById('next-btn');
const resetBtn = document.getElementById('reset-btn');

// Initialization
document.addEventListener('DOMContentLoaded', () => {
    fetchGames();
    
    gameSelector.addEventListener('change', (e) => {
        const index = e.target.value;
        loadGame(games[index]);
    });

    nextBtn.addEventListener('click', nextStep);
    prevBtn.addEventListener('click', prevStep);
    resetBtn.addEventListener('click', resetGame);
    
    document.addEventListener('keydown', (e) => {
        if (e.code === 'Space') {
            e.preventDefault(); // Prevent scrolling
            if (!nextBtn.disabled) nextStep();
        } else if (e.code === 'ArrowLeft') {
            if (!prevBtn.disabled) prevStep();
        } else if (e.code === 'ArrowRight') {
            if (!nextBtn.disabled) nextStep();
        }
    });
});

async function fetchGames() {
    try {
        const response = await fetch('/data/games.jsonl');
        const text = await response.text();
        const lines = text.trim().split('\n');
        
        games = lines
            .map(line => {
                try { return JSON.parse(line); } catch (e) { return null; }
            })
            .filter(g => g !== null);

        populateGameSelector();
    } catch (error) {
        console.error('Error fetching games:', error);
        statusMessage.textContent = "Error loading games data. Make sure run_viewer.py is running.";
    }
}

function populateGameSelector() {
    gameSelector.innerHTML = '<option value="" disabled selected>Select a Game</option>';
    games.forEach((game, index) => {
        const date = new Date(game.timestamp).toLocaleString();
        const option = document.createElement('option');
        option.value = index;
        option.textContent = `${date} - ${game.team_a_model} vs ${game.team_b_model}`;
        gameSelector.appendChild(option);
    });
}

function loadGame(game) {
    currentGame = game;
    
    // Reset UI
    gameGrid.innerHTML = '';
    teamALog.innerHTML = '';
    teamBLog.innerHTML = '';
    clueDisplay.classList.add('hidden');
    teamAScore.textContent = '0';
    teamBScore.textContent = '0';
    statusMessage.textContent = '';
    
    // Set Team Info
    teamAModel.textContent = game.team_a_model;
    teamBModel.textContent = game.team_b_model;

    // Build Grid
    const words = game.initial_game_state.words;
    const teamAWords = new Set(game.initial_game_state.team_a_words);
    const teamBWords = new Set(game.initial_game_state.team_b_words);
    const assassinWord = game.initial_game_state.assassin_word;
    
    // Create cards
    words.forEach(word => {
        const card = document.createElement('div');
        card.classList.add('card');
        card.textContent = word;
        card.dataset.word = word;
        
        // Determine type for border
        if (teamAWords.has(word)) {
            card.classList.add('team-a');
            card.dataset.type = 'team-a';
        } else if (teamBWords.has(word)) {
            card.classList.add('team-b');
            card.dataset.type = 'team-b';
        } else if (word === assassinWord) {
            card.classList.add('assassin');
            card.dataset.type = 'assassin';
        } else {
            card.classList.add('neutral');
            card.dataset.type = 'neutral';
        }
        
        gameGrid.appendChild(card);
    });

    // Pre-process steps
    buildGameSteps(game);
    currentStepIndex = -1;
    updateControls();
    
    // Initial State
    turnIndicator.textContent = `Start of Game`;
    turnIndicator.className = 'turn-indicator';
}

function buildGameSteps(game) {
    gameSteps = [];
    
    // Initial Step (Game Start)
    gameSteps.push({
        type: 'init',
        teamAScore: 0,
        teamBScore: 0,
        message: "Game Started"
    });

    let currentTeamAScore = 0;
    let currentTeamBScore = 0;

    game.turns.forEach(turn => {
        const isTeamA = turn.team === "Team A";
        
        // 1. Spymaster Phase (if available - some turns might be just guesses if structured differently, but standard is Spymaster -> Agent)
        // The logs have "Team X Spymaster" player entries.
        
        if (turn.player.includes("Spymaster")) {
            // Spymaster Reasoning
            if (turn.action.reasoning) {
                gameSteps.push({
                    type: 'reasoning',
                    team: turn.team,
                    text: turn.action.reasoning,
                    role: 'Spymaster'
                });
            }
            
            // Spymaster Clue
            if (turn.action.clue) {
                gameSteps.push({
                    type: 'clue',
                    team: turn.team,
                    clue: turn.action.clue,
                    count: turn.action.count
                });
            }
        } 
        else if (turn.player.includes("Agent")) {
             // Agent Reasoning
             if (turn.action.reasoning) {
                gameSteps.push({
                    type: 'reasoning',
                    team: turn.team,
                    text: turn.action.reasoning,
                    role: 'Agent'
                });
            }

            // Guesses
            if (turn.result && turn.result.results) {
                turn.result.results.forEach(guessResult => {
                    
                    // Update local score tracking for the step state
                    // Note: This is a simplified scoring logic. 
                    // Codenames rules: +1 for own team. Opponent gets point if you guess theirs? 
                    // Usually in logs we just see score increments.
                    // We will rely on the game state in the log if possible, but the 'turn' object usually has 'game_state_after'
                    // We can use 'game_state_after' to sync scores at the end of the turn, 
                    // but for intermediate guess steps we might need to estimate or just wait for end of turn.
                    // Actually, let's just look at the result type.
                    
                    if (guessResult.result === 'correct') {
                        if (isTeamA) currentTeamAScore++; else currentTeamBScore++;
                    } else if (guessResult.result === 'opponent') {
                        if (isTeamA) currentTeamBScore++; else currentTeamAScore++;
                    }
                    // Neutral/Assassin don't change score directly (except assassin ends game)

                    gameSteps.push({
                        type: 'guess',
                        team: turn.team,
                        word: guessResult.word,
                        result: guessResult.result,
                        message: guessResult.message,
                        teamAScore: currentTeamAScore,
                        teamBScore: currentTeamBScore
                    });
                });
            }
        }
        
        // Sync scores from game_state_after if available to be precise
        if (turn.game_state_after) {
            currentTeamAScore = turn.game_state_after.team_a_score;
            currentTeamBScore = turn.game_state_after.team_b_score;
            
            // Check if this was an agent turn, to decide if we should hide the clue
            const isAgent = turn.player.toLowerCase().includes('agent');

            // Determine if we need a sync step.
            // We need it if:
            // 1. We need to hide the clue (Agent finished turn)
            // 2. The scores significantly mismatch what we tracked (Safety net)
            // For Spymaster turns, usually neither happens, so we skip to avoid an empty step.
            const scoresMismatch = (currentTeamAScore !== turn.game_state_after.team_a_score) || 
                                   (currentTeamBScore !== turn.game_state_after.team_b_score);

            // Always update internal tracking to match authoritative state
            currentTeamAScore = turn.game_state_after.team_a_score;
            currentTeamBScore = turn.game_state_after.team_b_score;

            if (isAgent || scoresMismatch) {
                 gameSteps.push({
                    type: 'sync',
                    teamAScore: currentTeamAScore,
                    teamBScore: currentTeamBScore,
                    hideClue: isAgent
                });
            }
        }
    });

    // Game Over Step
    if (game.winner) {
        gameSteps.push({
            type: 'finish',
            message: `Game Over! Winner: ${game.winner}`
        });
    }
}

function nextStep() {
    if (currentStepIndex < gameSteps.length - 1) {
        currentStepIndex++;
        executeStep(gameSteps[currentStepIndex], 'forward');
        updateControls();
        scrollToBottom();
    }
}

function prevStep() {
    if (currentStepIndex >= 0) {
        executeStep(gameSteps[currentStepIndex], 'backward');
        currentStepIndex--;
        updateControls();
    }
}

function resetGame() {
    loadGame(currentGame);
}

function updateControls() {
    prevBtn.disabled = currentStepIndex < 0;
    nextBtn.disabled = currentStepIndex >= gameSteps.length - 1;
    resetBtn.disabled = currentStepIndex < 0;
}

function executeStep(step, direction) {
    const isForward = direction === 'forward';

    // Common: Update Turn Indicator
    if (step.team) {
        turnIndicator.textContent = `${step.team} Turn`;
        turnIndicator.className = `turn-indicator ${step.team.replace(' ', '-').toLowerCase()}`;
    }

    switch (step.type) {
        case 'init':
            if (isForward) {
                statusMessage.textContent = step.message;
            } else {
                statusMessage.textContent = "";
            }
            break;

        case 'reasoning':
            const logContainer = step.team === 'Team A' ? teamALog : teamBLog;
            if (isForward) {
                const entry = document.createElement('div');
                entry.classList.add('log-entry', 'reasoning');
                entry.innerHTML = `<strong>${step.role}:</strong> ${step.text}`;
                entry.id = `log-${currentStepIndex}`; // Tag for removal
                
                // Prepend because we use column-reverse for scrolling behavior
                // Actually, with flex-direction: column-reverse, the bottom element is first in DOM? 
                // No, usually bottom is last. Let's check CSS. 
                // CSS: flex-direction: column-reverse. This means first child is at bottom.
                // So to add new item at bottom (visually), we should prepend it to the container?
                // Wait, standard log: new items at bottom.
                // column-reverse: 1, 2, 3 -> 3 is at top, 1 at bottom? No.
                // Let's use standard column and scrollTop for simplicity if we want scrolling.
                // My CSS had `flex-direction: column-reverse`. This means:
                // Container Top
                // [Child 3]
                // [Child 2]
                // [Child 1]
                // Container Bottom
                // So if I appendChild(4), it goes to the visual TOP.
                // I want new items at visual BOTTOM.
                // So with column-reverse, I should PREPEND (insertBefore(firstChild)) to make it appear at visual BOTTOM (which is start of flex axis reversed? No, wait.)
                // Flex-start is bottom in column-reverse. 
                // Let's stick to standard flex-direction: column and just scroll to bottom.
                // I will modify the CSS logic slightly via JS or just use standard append.
                // Checking CSS again: `flex-direction: column-reverse;`
                // If I want new logs at the bottom, I should add them as the *first* child if using column-reverse?
                // Let's try standard append (last child) and see where it goes.
                // If column-reverse:
                // Child 1 (Bottom)
                // Child 2 (Top)
                // This is usually used for chat apps where you want to stick to bottom.
                // Actually, let's just use standard 'column' and JS scroll. It's more predictable for 'backward' step.
                
                // Re-reading CSS: `display: flex; flex-direction: column-reverse;`
                // This usually puts the last DOM element at the visual TOP.
                // If I want new elements at the bottom, I need to make them the FIRST DOM element.
                logContainer.insertBefore(entry, logContainer.firstChild);
            } else {
                const entry = document.getElementById(`log-${currentStepIndex}`);
                if (entry) entry.remove();
            }
            break;

        case 'clue':
            const logContainerClue = step.team === 'Team A' ? teamALog : teamBLog;
            if (isForward) {
                // Add log
                const entry = document.createElement('div');
                entry.classList.add('log-entry', 'clue');
                entry.innerHTML = `<strong>Clue:</strong> ${step.clue} (${step.count})`;
                entry.id = `log-${currentStepIndex}`;
                logContainerClue.insertBefore(entry, logContainerClue.firstChild);

                // Show Display
                clueText.textContent = step.clue;
                clueCount.textContent = step.count;
                clueDisplay.classList.remove('hidden');
            } else {
                // Remove log
                const entry = document.getElementById(`log-${currentStepIndex}`);
                if (entry) entry.remove();

                // Hide display (or revert to previous if we tracked history, but simpler to just hide if reversing a clue step)
                // Realistically, we should look at the previous step to see if it was a clue, but hiding is safe for now as we usually reverse to undo.
                clueDisplay.classList.add('hidden');
            }
            break;

        case 'guess':
            const card = Array.from(document.querySelectorAll('.card')).find(c => c.dataset.word === step.word);
            const logContainerGuess = step.team === 'Team A' ? teamALog : teamBLog;
            
            if (isForward) {
                // Reveal Card
                if (card) {
                    card.classList.add('revealed');
                    // Add specific reveal class based on type is handled by CSS (.card.revealed.team-a etc)
                    // But wait, the card type is already set in data-type and class. 
                    // So adding 'revealed' is enough?
                    // CSS: .card.revealed.team-a { ... } - Yes.
                }

                // Log
                const entry = document.createElement('div');
                entry.classList.add('log-entry', 'action');
                entry.innerHTML = `<strong>Guess:</strong> ${step.word} - ${step.result}`;
                entry.id = `log-${currentStepIndex}`;
                logContainerGuess.insertBefore(entry, logContainerGuess.firstChild);

                // Update Scores
                if (step.teamAScore !== undefined) teamAScore.textContent = step.teamAScore;
                if (step.teamBScore !== undefined) teamBScore.textContent = step.teamBScore;

                // Status
                statusMessage.textContent = `guessed ${step.word} (${step.result})`;
                
                // If turn ended (opponent/neutral/assassin), maybe hide clue display?
                // Usually clue stays until end of turn.
                // The next step might be 'reasoning' of other team, which implies turn change.
            } else {
                // Undo Reveal
                if (card) {
                    card.classList.remove('revealed');
                }

                // Remove log
                const entry = document.getElementById(`log-${currentStepIndex}`);
                if (entry) entry.remove();

                // Revert Scores (Need previous scores)
                // This is tricky without tracking previous state explicitly.
                // Hack: Look at previous steps to find last score?
                // Or just rely on the fact that `sync` steps handle strict scores, 
                // and guess steps update them incrementally.
                // If we go back, we need to set score to what it was BEFORE this step.
                // Easier: step object should have `prevTeamAScore`.
                // For now, let's just recalculate or ignore score revert for simple implementation, 
                // OR simply rely on 'sync' steps to fix it? 
                // Better: Find the last 'sync' or 'guess' step before this index and use its score.
                const prevScoreStep = findPrevScoreStep(currentStepIndex);
                teamAScore.textContent = prevScoreStep ? prevScoreStep.teamAScore : 0;
                teamBScore.textContent = prevScoreStep ? prevScoreStep.teamBScore : 0;
                
                statusMessage.textContent = "";
            }
            break;
            
        case 'sync':
             if (isForward) {
                 teamAScore.textContent = step.teamAScore;
                 teamBScore.textContent = step.teamBScore;
                 // End of turn, hide clue only if it was an agent turn (end of full team turn)
                 if (step.hideClue) {
                    clueDisplay.classList.add('hidden');
                 }
             } else {
                 // Revert means we are going BACK into the turn.
                 // Minimal: Just restore scores.
                 const prevScoreStep = findPrevScoreStep(currentStepIndex);
                 teamAScore.textContent = prevScoreStep ? prevScoreStep.teamAScore : 0;
                 teamBScore.textContent = prevScoreStep ? prevScoreStep.teamBScore : 0;
                 
                 // If we go back across a sync that hid the clue, restore it
                 if (step.hideClue) {
                     clueDisplay.classList.remove('hidden');
                 }
             }
             break;

        case 'finish':
            if (isForward) {
                statusMessage.textContent = step.message;
                statusMessage.style.fontWeight = 'bold';
            } else {
                statusMessage.textContent = '';
                statusMessage.style.fontWeight = 'normal';
            }
            break;
    }
}

function findPrevScoreStep(index) {
    for (let i = index - 1; i >= 0; i--) {
        if (gameSteps[i].teamAScore !== undefined) {
            return gameSteps[i];
        }
    }
    return { teamAScore: 0, teamBScore: 0 };
}

function scrollToBottom() {
    // Because of flex-direction: column-reverse, scrollTop 0 is the bottom?
    // No, usually it flips the axis.
    // Let's just try to ensure the newest element is visible.
    // Since we are insertingBefore firstChild, the new element is at the "visual bottom" (if column-reverse starts from bottom).
    // Actually, let's correct the CSS assumption in style.css if needed.
    // If style.css has .log-container { flex-direction: column-reverse; }
    // Then DOM: [Newest, ..., Oldest]
    // Visual: 
    // Oldest
    // ...
    // Newest (at bottom)
    // So inserting at firstChild (Newest) puts it at the bottom.
    // And it should naturally stay at the bottom unless overflow?
    // If overflow, column-reverse anchors to bottom.
    // So we might not need manual scrolling!
}

