/**
 * API client for Chess Coach AI backend
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export class ApiError extends Error {
  constructor(
    message: string,
    public status?: number,
    public response?: any
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

async function request<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  
  const config: RequestInit = {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  };

  try {
    const response = await fetch(url, config);
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new ApiError(
        errorData.detail || `HTTP error! status: ${response.status}`,
        response.status,
        errorData
      );
    }

    // Handle empty responses
    const contentType = response.headers.get('content-type');
    if (contentType && contentType.includes('application/json')) {
      return await response.json();
    }
    
    return {} as T;
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }
    throw new ApiError(
      `Network error: ${error instanceof Error ? error.message : 'Unknown error'}`,
      0,
      error
    );
  }
}

// Health check
export async function checkHealth() {
  return request<{ status: string; db: string; mode: string }>('/health');
}

export async function getInfo() {
  return request<{ service: string; database: string; stockfish_required: boolean; ml: string }>('/info');
}

// Game endpoints
export interface Game {
  id: number;
  chess_com_url: string | null;
  white_player: string;
  black_player: string;
  result: string | null;
  time_control: string | null;
  game_type: string | null;
  analyzed: boolean;
  played_at: string | null;
}

export async function listGames(params?: { user_id?: number; analyzed?: boolean; limit?: number }): Promise<Game[]> {
  const queryParams = new URLSearchParams();
  if (params?.user_id) queryParams.append('user_id', params.user_id.toString());
  if (params?.analyzed !== undefined) queryParams.append('analyzed', params.analyzed.toString());
  if (params?.limit) queryParams.append('limit', params.limit.toString());
  
  const query = queryParams.toString();
  return request<Game[]>(`/api/games${query ? `?${query}` : ''}`);
}

export async function getGame(gameId: number): Promise<Game> {
  return request<Game>(`/api/games/${gameId}`);
}

export async function importGames(username: string, limit: number = 10): Promise<{ imported: number; games: Game[] }> {
  return request<{ imported: number; games: Game[] }>('/api/games/import', {
    method: 'POST',
    body: JSON.stringify({
      chess_com_username: username,
      limit,
    }),
  });
}

export interface AnalyzedMove {
  move_number: number;
  color: string;
  san: string;
  uci?: string;
  fen_before?: string;
  fen_after?: string;
  evaluation_before: number;
  evaluation_after: number;
  evaluation_loss: number;
  best_move?: string;
  best_move_eval?: number;
  is_blunder: boolean;
  is_mistake: boolean;
  is_inaccuracy: boolean;
  quality?: 'blunder' | 'mistake' | 'inaccuracy' | 'good' | 'great' | 'book' | 'neutral';
  source?: string;
}

export interface AnalysisResult {
  game_id: number;
  total_moves: number;
  blunders: number;
  mistakes: number;
  inaccuracies: number;
  accuracy?: number;
  moves: AnalyzedMove[];
  analysis_source?: 'lichess_cloud' | 'stockfish' | 'heuristic' | 'unknown';
  stockfish_available?: boolean;
}

export interface AnalysisSummary {
  total_moves: number;
  blunders: number;
  mistakes: number;
  inaccuracies: number;
  accuracy: number;
  analysis_source: string;
}

export async function analyzeGame(gameId: number, force: boolean = false): Promise<{ game_id: number; analysis: AnalysisResult; summary: AnalysisSummary }> {
  const queryParams = force ? '?force=true' : '';
  return request<{ game_id: number; analysis: AnalysisResult; summary: AnalysisSummary }>(`/api/games/${gameId}/analyze${queryParams}`, {
    method: 'POST',
  });
}

export async function getGameMistakes(gameId: number): Promise<{ game_id: number; mistakes: any[]; count: number }> {
  return request<{ game_id: number; mistakes: any[]; count: number }>(`/api/games/${gameId}/mistakes`);
}

// Puzzle recommendations
export interface PuzzleData {
  puzzle_id: string;
  theme?: string;
  themes?: string[];
  rating?: number;
  url?: string;
  fen?: string;
  solution?: string[];
  pgn?: string;
  initialPly?: number;
  isTrainingLink?: boolean;
}

export interface Puzzle {
  puzzle_id: string;
  theme?: string;
  rating?: number;
  url?: string;
}

export async function getPuzzleRecommendations(themes?: string, limit: number = 5): Promise<{ puzzles: PuzzleData[]; count: number }> {
  const queryParams = new URLSearchParams();
  if (themes) queryParams.append('themes', themes);
  queryParams.append('limit', limit.toString());
  
  return request<{ puzzles: PuzzleData[]; count: number }>(`/api/recommendations/puzzles?${queryParams.toString()}`);
}

export async function getPuzzleRecommendationsForGame(gameId: number, limit: number = 5): Promise<{ game_id: number; puzzles: PuzzleData[]; count: number; themes: string[]; weaknesses: any }> {
  return request<{ game_id: number; puzzles: PuzzleData[]; count: number; themes: string[]; weaknesses: any }>(`/api/recommendations/puzzles/weaknesses/${gameId}?limit=${limit}`);
}

export async function getDailyPuzzle(): Promise<PuzzleData> {
  return request<PuzzleData>('/api/recommendations/puzzles/daily');
}

export async function getPuzzleById(puzzleId: string): Promise<PuzzleData> {
  return request<PuzzleData>(`/api/recommendations/puzzles/${puzzleId}`);
}

// User analytics endpoints
export interface UserAnalytics {
  user_id: number;
  total_games: number;
  total_moves_analyzed: number;
  overall_statistics: {
    blunders: number;
    mistakes: number;
    inaccuracies: number;
    blunder_rate_percent: number;
    mistake_rate_percent: number;
    inaccuracy_rate_percent: number;
    blunders_per_game: number;
  };
  weakness_patterns: {
    weakest_game_phase: string;
    game_phase_breakdown: {
      opening: { blunders: number; percentage: number };
      middlegame: { blunders: number; percentage: number };
      endgame: { blunders: number; percentage: number };
    };
    most_blunder_prone_move: number | null;
    blunders_at_move: number;
  };
  opening_performance: Record<string, any>;
  time_control_performance: Record<string, any>;
  color_performance: {
    white: { wins: number; losses: number; draws: number };
    black: { wins: number; losses: number; draws: number };
  };
  recommendations: {
    focus_area: string;
    targeted_themes: string[];
    improvement_priority: string;
  };
}

export async function getUserAnalytics(username: string): Promise<UserAnalytics> {
  return request<UserAnalytics>(`/api/analytics/user/${username}`);
}

export async function getUserWeaknesses(username: string): Promise<any> {
  return request<any>(`/api/analytics/user/${username}/weaknesses`);
}

export async function getUserPerformance(username: string): Promise<any> {
  return request<any>(`/api/analytics/user/${username}/performance`);
}

export interface SkillData {
  name: string;
  score: number;
  improvement: number;
  description: string;
}

export interface SkillsResponse {
  username: string;
  skills: SkillData[];
  games_analyzed: number;
}

export async function getUserSkills(username: string): Promise<SkillsResponse> {
  return request<SkillsResponse>(`/api/analytics/user/${username}/skills`);
}
