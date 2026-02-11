from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Database
    database_url: str = "sqlite+aiosqlite:///./chess_coach.db"
    
    # Stockfish (required for accurate analysis)
    stockfish_path: Optional[str] = None
    stockfish_depth: int = 18  # 18 recommended for accurate WintrCat classification
    stockfish_pool_size: int = 4  # Number of parallel engines (4 = ~4x faster)
    
    # Chess.com API
    chess_com_api_base: str = "https://api.chess.com/pub"
    
    # Lichess API
    lichess_api_base: str = "https://lichess.org/api"
    lichess_api_token: Optional[str] = None
    
    # Security
    secret_key: str = "change-this-secret-key-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Redis (optional)
    redis_url: Optional[str] = None
    
    # ML Configuration (not used in no-ML version, but kept for compatibility)
    ml_model_path: str = "./models/chess_coach_model"
    batch_size: int = 32
    learning_rate: float = 0.001
    
    # Rate Limiting
    rate_limit_per_minute: int = 60
    chess_com_rate_limit_per_minute: int = 10
    lichess_rate_limit_per_minute: int = 30
    
    # Logging
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields in .env that aren't in this class


settings = Settings()
