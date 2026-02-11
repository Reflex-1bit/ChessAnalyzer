"""
User-specific analytics and insights
"""
from typing import Dict, List, Any
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Game, Move, User


class UserAnalytics:
    """Generate hyper-specific analytics for a user"""
    
    @staticmethod
    async def get_user_insights(user_id: int, session: AsyncSession) -> Dict[str, Any]:
        """
        Get comprehensive user insights
        
        Returns detailed statistics about:
        - Overall performance
        - Weakness patterns
        - Opening performance
        - Time control performance
        - Improvement trends
        """
        # Get all analyzed games for user
        games_result = await session.execute(
            select(Game)
            .where(Game.user_id == user_id)
            .where(Game.analyzed == True)
        )
        games = games_result.scalars().all()
        
        if not games:
            return {
                "error": "No analyzed games found. Analyze some games first.",
                "total_games": 0
            }
        
        total_games = len(games)
        
        # Get all moves from analyzed games
        game_ids = [g.id for g in games]
        
        # Calculate overall statistics
        total_blunders = 0
        total_mistakes = 0
        total_inaccuracies = 0
        total_moves = 0
        
        opening_performance = {}
        time_control_performance = {}
        color_performance = {"white": {"wins": 0, "losses": 0, "draws": 0}, 
                            "black": {"wins": 0, "losses": 0, "draws": 0}}
        
        move_number_blunders = {}  # Track blunders by move number
        game_phase_issues = {"opening": 0, "middlegame": 0, "endgame": 0}
        
        for game in games:
            # Count moves for this game
            moves_result = await session.execute(
                select(Move).where(Move.game_id == game.id)
            )
            moves = moves_result.scalars().all()
            
            for move in moves:
                total_moves += 1
                quality = move.quality or ""
                is_blunder = quality == "blunder"
                is_mistake = quality == "mistake"
                is_inaccuracy = quality == "inaccuracy"
                
                if is_blunder:
                    total_blunders += 1
                    move_num = move.move_number
                    move_number_blunders[move_num] = move_number_blunders.get(move_num, 0) + 1
                    
                    # Classify by game phase
                    if move_num <= 15:
                        game_phase_issues["opening"] += 1
                    elif move_num <= 35:
                        game_phase_issues["middlegame"] += 1
                    else:
                        game_phase_issues["endgame"] += 1
                        
                if is_mistake:
                    total_mistakes += 1
                if is_inaccuracy:
                    total_inaccuracies += 1
            
            # Track opening performance
            opening = game.game_type or "unknown"
            if opening not in opening_performance:
                opening_performance[opening] = {"games": 0, "wins": 0, "losses": 0, "draws": 0, "blunders": 0}
            opening_performance[opening]["games"] += 1
            if game.result == "1-0":
                opening_performance[opening]["wins"] += 1
            elif game.result == "0-1":
                opening_performance[opening]["losses"] += 1
            else:
                opening_performance[opening]["draws"] += 1
            
            # Track time control performance
            time_control = game.time_control or "unknown"
            if time_control not in time_control_performance:
                time_control_performance[time_control] = {"games": 0, "wins": 0, "blunders_per_game": 0}
            time_control_performance[time_control]["games"] += 1
            if game.result == "1-0":
                time_control_performance[time_control]["wins"] += 1
            
            # Track color performance
            result = game.result
            if game.white_player and game.black_player:
                # Determine which color user played
                # This is simplified - in production, match against username
                if result == "1-0":
                    color_performance["white"]["wins"] += 1
                    color_performance["black"]["losses"] += 1
                elif result == "0-1":
                    color_performance["white"]["losses"] += 1
                    color_performance["black"]["wins"] += 1
                elif result == "1/2-1/2":
                    color_performance["white"]["draws"] += 1
                    color_performance["black"]["draws"] += 1
        
        # Calculate percentages
        blunder_rate = (total_blunders / total_moves * 100) if total_moves > 0 else 0
        mistake_rate = (total_mistakes / total_moves * 100) if total_moves > 0 else 0
        inaccuracy_rate = (total_inaccuracies / total_moves * 100) if total_moves > 0 else 0
        
        # Find worst opening
        worst_opening = None
        worst_opening_blunder_rate = 0
        for opening, stats in opening_performance.items():
            blunder_rate = (stats["blunders"] / stats["games"]) if stats["games"] > 0 else 0
            if blunder_rate > worst_opening_blunder_rate:
                worst_opening_blunder_rate = blunder_rate
                worst_opening = opening
        
        # Find worst move number for blunders
        worst_move_number = None
        worst_move_count = 0
        for move_num, count in move_number_blunders.items():
            if count > worst_move_count:
                worst_move_count = count
                worst_move_number = move_num
        
        # Find weakest game phase
        total_phase_issues = sum(game_phase_issues.values())
        weakest_phase = None
        if total_phase_issues > 0:
            phase_percentages = {
                phase: (count / total_phase_issues * 100) 
                for phase, count in game_phase_issues.items()
            }
            weakest_phase = max(phase_percentages, key=phase_percentages.get)
        
        return {
            "user_id": user_id,
            "total_games": total_games,
            "total_moves_analyzed": total_moves,
            "overall_statistics": {
                "blunders": total_blunders,
                "mistakes": total_mistakes,
                "inaccuracies": total_inaccuracies,
                "blunder_rate_percent": round(blunder_rate, 2),
                "mistake_rate_percent": round(mistake_rate, 2),
                "inaccuracy_rate_percent": round(inaccuracy_rate, 2),
                "blunders_per_game": round(total_blunders / total_games, 2) if total_games > 0 else 0,
            },
            "weakness_patterns": {
                "weakest_game_phase": weakest_phase,
                "game_phase_breakdown": {
                    "opening": {
                        "blunders": game_phase_issues["opening"],
                        "percentage": round((game_phase_issues["opening"] / total_blunders * 100) if total_blunders > 0 else 0, 2)
                    },
                    "middlegame": {
                        "blunders": game_phase_issues["middlegame"],
                        "percentage": round((game_phase_issues["middlegame"] / total_blunders * 100) if total_blunders > 0 else 0, 2)
                    },
                    "endgame": {
                        "blunders": game_phase_issues["endgame"],
                        "percentage": round((game_phase_issues["endgame"] / total_blunders * 100) if total_blunders > 0 else 0, 2)
                    }
                },
                "most_blunder_prone_move": worst_move_number,
                "blunders_at_move": worst_move_count if worst_move_number else 0,
            },
            "opening_performance": opening_performance,
            "time_control_performance": time_control_performance,
            "color_performance": color_performance,
            "recommendations": {
                "focus_area": weakest_phase or "middlegame",
                "targeted_themes": UserAnalytics._get_targeted_themes(game_phase_issues, total_blunders),
                "improvement_priority": UserAnalytics._get_improvement_priority(
                    blunder_rate, mistake_rate, weakest_phase, worst_move_number
                )
            }
        }
    
    @staticmethod
    def _get_targeted_themes(phase_issues: Dict, total_blunders: int) -> List[str]:
        """Get puzzle themes based on weaknesses"""
        themes = []
        if phase_issues["opening"] / total_blunders > 0.3 if total_blunders > 0 else False:
            themes.append("opening")
        if phase_issues["middlegame"] / total_blunders > 0.4 if total_blunders > 0 else False:
            themes.append("tactics")
            themes.append("middlegame")
        if phase_issues["endgame"] / total_blunders > 0.3 if total_blunders > 0 else False:
            themes.append("endgame")
        
        if not themes:
            themes = ["tactics", "endgame"]
        
        return themes
    
    @staticmethod
    def _get_improvement_priority(blunder_rate: float, mistake_rate: float, 
                                   weakest_phase: str, worst_move: int) -> str:
        """Get priority improvement area"""
        if blunder_rate > 5:
            return f"Critical: Reduce blunders in {weakest_phase} (currently {blunder_rate:.1f}% blunder rate)"
        elif mistake_rate > 10:
            return f"High: Focus on {weakest_phase} decision-making"
        elif worst_move and worst_move > 30:
            return "Medium: Improve endgame technique"
        else:
            return "Low: Refine positional understanding"
