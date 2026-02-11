from sqlalchemy import Column, Integer, String, DateTime, Float, Text, ForeignKey, Boolean, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, index=True, nullable=False)
    chess_com_username = Column(String(100), index=True, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    games = relationship("Game", back_populates="user")


class Game(Base):
    __tablename__ = "games"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Chess.com data
    chess_com_url = Column(String(500), nullable=True, index=True)
    chess_com_id = Column(String(100), nullable=True, index=True)
    
    # Game metadata
    white_player = Column(String(200), nullable=False)
    black_player = Column(String(200), nullable=False)
    result = Column(String(10), nullable=True)  # "1-0", "0-1", "1/2-1/2"
    time_control = Column(String(50), nullable=True)  # e.g., "600+0"
    rated = Column(Boolean, default=False)
    game_type = Column(String(50), nullable=True)  # "rapid", "blitz", "bullet", etc.
    
    # PGN data
    pgn = Column(Text, nullable=True)
    fen_start = Column(String(100), nullable=True)
    
    # Analysis status
    analyzed = Column(Boolean, default=False, index=True)
    analyzed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    played_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", back_populates="games")
    moves = relationship("Move", back_populates="game", order_by="Move.move_number")
    positions = relationship("Position", back_populates="game")


class Move(Base):
    __tablename__ = "moves"

    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(Integer, ForeignKey("games.id"), nullable=False, index=True)
    
    move_number = Column(Integer, nullable=False)  # 1, 2, 3...
    color = Column(String(1), nullable=False)  # "w" or "b"
    san = Column(String(20), nullable=False)  # Standard Algebraic Notation
    uci = Column(String(10), nullable=True)  # UCI notation (e.g., "e2e4")
    
    # Position FENs
    fen_before = Column(String(200), nullable=True)
    fen_after = Column(String(200), nullable=True)
    
    # Evaluation (from Lichess/Stockfish)
    evaluation_before = Column(Float, nullable=True)  # Centipawns
    evaluation_after = Column(Float, nullable=True)
    evaluation_loss = Column(Float, nullable=True)  # Centipawns lost
    best_move = Column(String(10), nullable=True)  # UCI
    best_move_eval = Column(Float, nullable=True)
    
    # Classification
    is_blunder = Column(Boolean, default=False, index=True)
    is_mistake = Column(Boolean, default=False, index=True)
    is_inaccuracy = Column(Boolean, default=False, index=True)
    quality = Column(String(20), nullable=True)  # "blunder", "mistake", "inaccuracy", "good", "great", "book", "neutral"
    explanation = Column(Text, nullable=True)  # AI explanation for the move
    
    # Analysis source
    source = Column(String(50), nullable=True)  # "lichess_cloud", "stockfish", "heuristic"
    
    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    game = relationship("Game", back_populates="moves")


class Position(Base):
    __tablename__ = "positions"

    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(Integer, ForeignKey("games.id"), nullable=False, index=True)
    
    move_number = Column(Integer, nullable=False)
    color = Column(String(1), nullable=False)  # "w" or "b"
    fen = Column(String(200), nullable=False, index=True)
    
    # Stockfish analysis
    evaluation = Column(Float, nullable=True)  # Centipawns
    depth_analyzed = Column(Integer, nullable=True)
    best_move = Column(String(10), nullable=True)
    best_line = Column(Text, nullable=True)  # JSON array of moves
    
    # Additional metadata
    material_balance = Column(Integer, nullable=True)  # Material count
    position_type = Column(String(50), nullable=True)  # "opening", "middlegame", "endgame"
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    game = relationship("Game", back_populates="positions")