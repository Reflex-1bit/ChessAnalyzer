export type PieceType = 'K' | 'Q' | 'R' | 'B' | 'N' | 'P' | 'k' | 'q' | 'r' | 'b' | 'n' | 'p' | null;

// WintrCat classification types
export type MoveQuality = 'brilliant' | 'great' | 'best' | 'excellent' | 'good' | 'book' | 'forced' | 'inaccuracy' | 'mistake' | 'blunder' | 'neutral';

export interface ChessMove {
  from: string;
  to: string;
  piece: PieceType;
  san: string;
  quality?: MoveQuality;
  evaluation?: number;
  bestMove?: string;
  explanation?: string;
}

export interface GameSummary {
  id: string;
  white: string;
  black: string;
  result: '1-0' | '0-1' | '1/2-1/2';
  date: string;
  timeControl: string;
  opening: string;
  accuracy: {
    white: number;
    black: number;
  };
  moves: ChessMove[];
  criticalMoments: CriticalMoment[];
}

export interface CriticalMoment {
  moveNumber: number;
  type: 'blunder' | 'missed_win' | 'turning_point' | 'brilliant';
  position: string;
  explanation: string;
  bestMove: string;
  playedMove: string;
  evalBefore: number;
  evalAfter: number;
}

export interface PlayerProfile {
  username: string;
  rating: number;
  ratingHistory: { date: string; rating: number }[];
  gamesPlayed: number;
  winRate: number;
  strengths: string[];
  weaknesses: string[];
  favoriteOpenings: { name: string; winRate: number; games: number }[];
}

export interface Puzzle {
  id: string;
  fen: string;
  moves: string[];
  rating: number;
  themes: string[];
  reason: string;
}

export interface PlayablePuzzle {
  puzzle_id: string;
  fen: string;
  solution: string[];
  rating: number;
  themes: string[];
  theme?: string;
  url?: string;
  pgn?: string;
  initialPly?: number;
  isTrainingLink?: boolean;
}

export interface SkillArea {
  name: string;
  score: number;
  improvement: number;
  description: string;
}
