"""
Skill analysis service - calculates player skill profile from game analysis.
Based on WintrCat classification data to generate skill scores.
"""
from typing import Dict, List, Optional
from app.services.classification import CLASSIFICATION_VALUES


def calculate_phase_accuracy(moves: List[Dict], start_move: int, end_move: int) -> float:
    """
    Calculate accuracy for a specific game phase.
    
    Args:
        moves: List of analyzed moves with 'quality' and 'move_number' keys
        start_move: Starting move number (inclusive)
        end_move: Ending move number (inclusive)
    
    Returns:
        Accuracy percentage (0-100)
    """
    phase_moves = [
        m for m in moves 
        if start_move <= m.get("move_number", 0) <= end_move
    ]
    
    if not phase_moves:
        return 75.0  # Default if no moves in phase
    
    total_value = sum(
        CLASSIFICATION_VALUES.get(m.get("quality", "book").lower(), 0.5)
        for m in phase_moves
    )
    
    return (total_value / len(phase_moves)) * 100


def calculate_tactics_score(moves: List[Dict]) -> float:
    """
    Calculate tactics score based on brilliant/great moves and avoiding blunders.
    
    High score = finding brilliant moves + avoiding tactical mistakes
    """
    if not moves:
        return 70.0
    
    brilliant_count = sum(1 for m in moves if m.get("quality") == "brilliant")
    great_count = sum(1 for m in moves if m.get("quality") == "great")
    best_count = sum(1 for m in moves if m.get("quality") == "best")
    blunder_count = sum(1 for m in moves if m.get("quality") == "blunder")
    mistake_count = sum(1 for m in moves if m.get("quality") == "mistake")
    
    total_moves = len(moves)
    
    # Base score from accuracy
    base_accuracy = sum(
        CLASSIFICATION_VALUES.get(m.get("quality", "book").lower(), 0.5)
        for m in moves
    ) / total_moves * 100
    
    # Bonus for brilliant/great moves (tactics finder)
    bonus = (brilliant_count * 5 + great_count * 3 + best_count * 1) / total_moves * 100
    
    # Penalty for tactical blunders
    penalty = (blunder_count * 3 + mistake_count * 1) / total_moves * 50
    
    score = base_accuracy + bonus - penalty
    return max(0, min(100, score))


def calculate_time_management_score(moves: List[Dict], time_control: Optional[str] = None) -> float:
    """
    Calculate time management score.
    
    Without actual clock data, we estimate based on:
    - Consistency of move quality throughout the game
    - Avoiding late-game blunders (time trouble indicator)
    """
    if not moves:
        return 60.0
    
    total_moves = len(moves)
    if total_moves < 20:
        return 70.0  # Short game, hard to assess
    
    # Check late-game performance (last 25% of moves)
    late_game_start = int(total_moves * 0.75)
    late_moves = moves[late_game_start:]
    early_moves = moves[:late_game_start]
    
    if not late_moves or not early_moves:
        return 65.0
    
    # Calculate accuracy for early vs late game
    early_accuracy = sum(
        CLASSIFICATION_VALUES.get(m.get("quality", "book").lower(), 0.5)
        for m in early_moves
    ) / len(early_moves)
    
    late_accuracy = sum(
        CLASSIFICATION_VALUES.get(m.get("quality", "book").lower(), 0.5)
        for m in late_moves
    ) / len(late_moves)
    
    # If late game accuracy drops significantly, time trouble
    accuracy_drop = early_accuracy - late_accuracy
    
    # Base score
    base_score = 70
    
    # Penalty for accuracy drop in late game (time trouble)
    if accuracy_drop > 0.2:
        base_score -= 25
    elif accuracy_drop > 0.1:
        base_score -= 15
    elif accuracy_drop > 0.05:
        base_score -= 5
    elif accuracy_drop < -0.05:
        # Improvement in late game (good time management)
        base_score += 10
    
    # Bonus for consistent performance
    late_blunders = sum(1 for m in late_moves if m.get("quality") == "blunder")
    if late_blunders == 0:
        base_score += 10
    elif late_blunders >= 2:
        base_score -= 15
    
    return max(0, min(100, base_score))


def get_skill_description(skill_name: str, score: float) -> str:
    """Get contextual description based on skill score."""
    
    descriptions = {
        "Opening": {
            "high": "Excellent theoretical knowledge, strong repertoire",
            "medium": "Good theoretical knowledge, could explore more variations",
            "low": "Consider studying opening principles and main lines"
        },
        "Middlegame": {
            "high": "Strong positional understanding and piece coordination",
            "medium": "Piece coordination needs work, especially in complex positions",
            "low": "Focus on piece activity and central control"
        },
        "Endgame": {
            "high": "Excellent technique, converts advantages well",
            "medium": "Improving! Focus on king activity and passed pawns",
            "low": "Study basic endgame principles and king activity"
        },
        "Tactics": {
            "high": "Sharp tactical vision, finds combinations",
            "medium": "Solid tactical vision, practice deeper calculations",
            "low": "Practice tactical puzzles daily to improve pattern recognition"
        },
        "Time Management": {
            "high": "Efficient use of clock, consistent performance",
            "medium": "Generally good, avoid rushing in critical positions",
            "low": "Spending too much time in familiar positions"
        }
    }
    
    skill_descs = descriptions.get(skill_name, {
        "high": "Excellent performance",
        "medium": "Good performance, room for improvement",
        "low": "Focus area for improvement"
    })
    
    if score >= 75:
        return skill_descs["high"]
    elif score >= 55:
        return skill_descs["medium"]
    else:
        return skill_descs["low"]


def analyze_skills_from_game(
    moves: List[Dict],
    player_color: str = "w",
    previous_skills: Optional[Dict] = None
) -> List[Dict]:
    """
    Analyze player skills from a single game's moves.
    
    Args:
        moves: List of analyzed moves with quality classifications
        player_color: 'w' or 'b' for which player to analyze
        previous_skills: Previous skill scores for calculating improvement
    
    Returns:
        List of skill area dictionaries
    """
    # Filter to player's moves only
    player_moves = [m for m in moves if m.get("color") == player_color]
    
    if not player_moves:
        return get_default_skills()
    
    total_moves = len(player_moves)
    
    # Determine game phases based on move count
    # Opening: first 15 moves (30 half-moves)
    # Middlegame: moves 15-40
    # Endgame: after move 40
    opening_end = min(15, total_moves)
    middlegame_end = min(40, total_moves)
    
    # Calculate phase accuracies
    opening_score = calculate_phase_accuracy(player_moves, 1, opening_end)
    middlegame_score = calculate_phase_accuracy(player_moves, opening_end + 1, middlegame_end)
    endgame_score = calculate_phase_accuracy(player_moves, middlegame_end + 1, total_moves * 2)
    
    # Calculate other skills
    tactics_score = calculate_tactics_score(player_moves)
    time_score = calculate_time_management_score(player_moves)
    
    # Calculate improvements if previous data exists
    def get_improvement(skill_name: str, current: float) -> int:
        if not previous_skills:
            return 0
        prev = previous_skills.get(skill_name, {}).get("score", current)
        diff = current - prev
        if abs(diff) < 2:
            return 0
        return int(round(diff / 10))  # Convert to percentage change
    
    skills = [
        {
            "name": "Opening",
            "score": int(round(opening_score)),
            "improvement": get_improvement("Opening", opening_score),
            "description": get_skill_description("Opening", opening_score)
        },
        {
            "name": "Middlegame",
            "score": int(round(middlegame_score)),
            "improvement": get_improvement("Middlegame", middlegame_score),
            "description": get_skill_description("Middlegame", middlegame_score)
        },
        {
            "name": "Endgame",
            "score": int(round(endgame_score)),
            "improvement": get_improvement("Endgame", endgame_score),
            "description": get_skill_description("Endgame", endgame_score)
        },
        {
            "name": "Tactics",
            "score": int(round(tactics_score)),
            "improvement": get_improvement("Tactics", tactics_score),
            "description": get_skill_description("Tactics", tactics_score)
        },
        {
            "name": "Time Management",
            "score": int(round(time_score)),
            "improvement": get_improvement("Time Management", time_score),
            "description": get_skill_description("Time Management", time_score)
        }
    ]
    
    return skills


def analyze_skills_from_multiple_games(
    games_analysis: List[List[Dict]],
    player_color: str = "w"
) -> List[Dict]:
    """
    Analyze skills from multiple games for a more accurate profile.
    
    Args:
        games_analysis: List of games, each containing list of analyzed moves
        player_color: 'w' or 'b'
    
    Returns:
        Aggregated skill profile
    """
    if not games_analysis:
        return get_default_skills()
    
    # Calculate skills for each game
    all_skills = []
    for game_moves in games_analysis:
        skills = analyze_skills_from_game(game_moves, player_color)
        all_skills.append({s["name"]: s["score"] for s in skills})
    
    # Average the scores
    skill_names = ["Opening", "Middlegame", "Endgame", "Tactics", "Time Management"]
    averaged_skills = []
    
    for name in skill_names:
        scores = [g.get(name, 70) for g in all_skills]
        avg_score = sum(scores) / len(scores)
        
        # Calculate trend (improvement from first to last games)
        if len(scores) >= 3:
            early_avg = sum(scores[:len(scores)//2]) / (len(scores)//2)
            late_avg = sum(scores[len(scores)//2:]) / (len(scores) - len(scores)//2)
            improvement = int(round((late_avg - early_avg) / 10))
        else:
            improvement = 0
        
        averaged_skills.append({
            "name": name,
            "score": int(round(avg_score)),
            "improvement": improvement,
            "description": get_skill_description(name, avg_score)
        })
    
    return averaged_skills


def get_default_skills() -> List[Dict]:
    """Return default skill profile when no data available."""
    return [
        {"name": "Opening", "score": 70, "improvement": 0, "description": "Import games to analyze your opening play"},
        {"name": "Middlegame", "score": 65, "improvement": 0, "description": "Import games to analyze your middlegame"},
        {"name": "Endgame", "score": 60, "improvement": 0, "description": "Import games to analyze your endgame technique"},
        {"name": "Tactics", "score": 68, "improvement": 0, "description": "Import games to analyze your tactical vision"},
        {"name": "Time Management", "score": 55, "improvement": 0, "description": "Import games to analyze time usage"},
    ]
