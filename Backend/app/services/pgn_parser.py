"""
PGN parsing and game data extraction
"""
import chess
import chess.pgn
from typing import Dict, List, Optional, Tuple
from io import StringIO
from datetime import datetime


class PGNParser:
    """Parser for PGN chess games"""
    
    @staticmethod
    def parse_pgn(pgn_text: str) -> Optional[Dict]:
        """
        Parse PGN text and extract game information
        
        Returns:
            Dict with keys: headers, moves (list of dicts), final_fen
        """
        if not pgn_text or not pgn_text.strip():
            return None
        
        try:
            pgn = StringIO(pgn_text)
            game = chess.pgn.read_game(pgn)
            
            if game is None:
                return None
            
            # Extract headers
            headers = dict(game.headers)
            
            # Extract moves
            moves = []
            board = game.board()
            move_number = 1
            
            for node in game.mainline():
                move = node.move
                
                move_data = {
                    "move_number": move_number,
                    "color": "w" if board.turn == chess.WHITE else "b",
                    "san": board.san(move),
                    "uci": move.uci(),
                    "fen_before": board.fen(),
                }
                
                board.push(move)
                move_data["fen_after"] = board.fen()
                
                moves.append(move_data)
                
                # Increment move number for white moves
                if board.turn == chess.BLACK:
                    move_number += 1
            
            # Parse game result
            result = headers.get("Result", "")
            
            # Parse time control
            time_control = headers.get("TimeControl", "")
            
            # Determine game type from time control
            game_type = PGNParser._determine_game_type(time_control)
            
            # Parse date
            date_str = headers.get("Date", "")
            played_at = PGNParser._parse_date(date_str)
            
            return {
                "headers": headers,
                "moves": moves,
                "final_fen": board.fen(),
                "result": result,
                "time_control": time_control,
                "game_type": game_type,
                "played_at": played_at,
                "white_player": headers.get("White", ""),
                "black_player": headers.get("Black", ""),
                "rated": headers.get("WhiteTitle") or headers.get("BlackTitle") or False,
            }
        except Exception as e:
            print(f"Error parsing PGN: {e}")
            return None
    
    @staticmethod
    def _determine_game_type(time_control: str) -> str:
        """Determine game type from time control"""
        if not time_control or time_control == "-":
            return "correspondence"
        
        # Parse time control (e.g., "600+0" or "180+0")
        parts = time_control.split("+")
        if len(parts) == 2:
            try:
                initial_seconds = int(parts[0])
                # Convert to minutes
                initial_minutes = initial_seconds / 60
                
                if initial_minutes < 3:
                    return "bullet"
                elif initial_minutes < 10:
                    return "blitz"
                elif initial_minutes < 30:
                    return "rapid"
                else:
                    return "classical"
            except ValueError:
                pass
        
        return "unknown"
    
    @staticmethod
    def _parse_date(date_str: str) -> Optional[datetime]:
        """Parse date string (YYYY.MM.DD format)"""
        if not date_str or date_str == "??.??.??":
            return None
        
        try:
            # Chess.com format: YYYY.MM.DD
            parts = date_str.split(".")
            if len(parts) == 3:
                year, month, day = map(int, parts)
                return datetime(year, month, day)
        except (ValueError, AttributeError):
            pass
        
        return None
    
    @staticmethod
    def extract_opening_name(headers: Dict) -> Optional[str]:
        """Extract opening name from headers"""
        return headers.get("ECO", "") or headers.get("Opening", "")


# Convenience function
def parse_pgn(pgn_text: str) -> Optional[Dict]:
    """Parse PGN text"""
    return PGNParser.parse_pgn(pgn_text)
