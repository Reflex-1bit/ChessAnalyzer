"""
Chess.com API integration service
"""
import httpx
from typing import List, Dict, Optional
from datetime import datetime
from app.config import settings
from tenacity import retry, stop_after_attempt, wait_exponential


class ChessComService:
    """Service for interacting with Chess.com API"""
    
    BASE_URL = settings.chess_com_api_base
    RATE_LIMIT_PER_MINUTE = settings.chess_com_rate_limit_per_minute
    
    def __init__(self):
        self.client = httpx.AsyncClient(
            base_url=self.BASE_URL,
            timeout=30.0,
            follow_redirects=True
        )
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def get_user_games(self, username: str, year: int, month: int) -> List[Dict]:
        """
        Get games for a user for a specific year/month
        Returns list of game objects with url, id, etc.
        """
        url = f"/player/{username}/games/{year}/{month:02d}"
        try:
            response = await self.client.get(url)
            response.raise_for_status()
            data = response.json()
            # Chess.com API returns: {"games": [{"url": "...", ...}, ...]}
            games = data.get("games", [])
            if not isinstance(games, list):
                return []
            return games
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return []  # User has no games for this month
            print(f"Error fetching games: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            print(f"Unexpected error in get_user_games: {e}")
            raise
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def get_game_pgn(self, game_url: str) -> Optional[str]:
        """
        Get PGN for a specific game
        Chess.com returns PGN directly as text
        """
        try:
            response = await self.client.get(game_url, headers={"Accept": "application/x-chess-pgn"})
            response.raise_for_status()
            return response.text
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            raise
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def get_player_profile(self, username: str) -> Optional[Dict]:
        """Get player profile information"""
        try:
            response = await self.client.get(f"/player/{username}")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError:
            return None
    
    async def get_recent_games(self, username: str, limit: int = 10) -> List[Dict]:
        """
        Get recent games for a user
        Fetches from current month and previous month
        """
        now = datetime.now()
        all_games = []
        
        # Current month
        games = await self.get_user_games(username, now.year, now.month)
        all_games.extend(games)
        
        # Previous month
        prev_month = now.month - 1
        prev_year = now.year
        if prev_month == 0:
            prev_month = 12
            prev_year -= 1
        games = await self.get_user_games(username, prev_year, prev_month)
        all_games.extend(games)
        
        # Sort by date (newest first) and limit
        all_games.sort(key=lambda x: x.get("end_time", 0), reverse=True)
        return all_games[:limit]


# Singleton instance
_chess_com_service: Optional[ChessComService] = None


async def get_chess_com_service() -> ChessComService:
    """Get or create Chess.com service instance"""
    global _chess_com_service
    if _chess_com_service is None:
        _chess_com_service = ChessComService()
    return _chess_com_service
