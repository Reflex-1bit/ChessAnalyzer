import { useState, useEffect } from 'react';
import { Header } from '@/components/layout/Header';
import { Sidebar } from '@/components/layout/Sidebar';
import { Chessboard } from '@/components/chess/Chessboard';
import { EvaluationBar } from '@/components/chess/EvaluationBar';
import { MoveList } from '@/components/chess/MoveList';
import { GameControls } from '@/components/chess/GameControls';
import { PuzzlePlayer } from '@/components/chess/PuzzlePlayer';
import { GameSummaryCard } from '@/components/analysis/GameSummaryCard';
import { AIExplanation } from '@/components/analysis/AIExplanation';
import { CriticalMoments } from '@/components/analysis/CriticalMoments';
import { SkillRadar } from '@/components/analysis/SkillRadar';
import { PuzzleRecommendations } from '@/components/analysis/PuzzleRecommendations';
import { EvaluationChart } from '@/components/analysis/EvaluationChart';
import { ChessComConnect } from '@/components/connect/ChessComConnect';
import { UserAnalytics } from '@/components/analysis/UserAnalytics';
import { Brain, X, Puzzle } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { 
  mockGame, 
  mockSkills, 
  mockPuzzles, 
  mockRecentGames, 
  mockEvaluationData,
  mockPositions 
} from '@/data/mockData';
import { importGames, analyzeGame, listGames, getGame, getGameMistakes, getPuzzleRecommendationsForGame, getUserAnalytics, getUserSkills, getDailyPuzzle, type PuzzleData, type SkillData } from '@/lib/api';
import { useToast } from '@/hooks/use-toast';
import type { PlayablePuzzle } from '@/types/chess';

const Index = () => {
  let toastFn: any = null;
  try {
    const toastHook = useToast();
    toastFn = toastHook?.toast;
  } catch (e) {
    console.warn("Toast hook error:", e);
  }
  
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const [connectedUsername, setConnectedUsername] = useState('');
  const [isLoadingGames, setIsLoadingGames] = useState(false);
  const [importedGames, setImportedGames] = useState<any[]>([]);
  const [selectedGame, setSelectedGame] = useState<any>(null);
  const [gameAnalysis, setGameAnalysis] = useState<any>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [puzzleRecommendations, setPuzzleRecommendations] = useState<any[]>([]);
  const [userAnalytics, setUserAnalytics] = useState<any>(null);
  const [userSkills, setUserSkills] = useState<SkillData[]>([]);
  const [gamesAnalyzedForSkills, setGamesAnalyzedForSkills] = useState(0);
  const [activePuzzle, setActivePuzzle] = useState<PlayablePuzzle | null>(null);
  const [showPuzzlePlayer, setShowPuzzlePlayer] = useState(false);
  const [currentPuzzleIndex, setCurrentPuzzleIndex] = useState(0);
  
  // Game analysis state
  const [currentMoveIndex, setCurrentMoveIndex] = useState(-1);
  const [isPlaying, setIsPlaying] = useState(false);
  const [flipped, setFlipped] = useState(false);

  // Use real game data if available, otherwise fall back to mock
  let currentGameMoves: any[] = [];
  try {
    if (gameAnalysis?.moves && Array.isArray(gameAnalysis.moves) && gameAnalysis.moves.length > 0) {
      currentGameMoves = gameAnalysis.moves;
    } else if (mockGame?.moves && Array.isArray(mockGame.moves)) {
      currentGameMoves = mockGame.moves;
    }
  } catch (e) {
    console.warn("Error getting moves:", e);
    currentGameMoves = mockGame?.moves || [];
  }
  
  // Get the starting position from actual game data or use standard starting position
  const getStartingPosition = () => {
    // If we have real game moves with FEN data, use the fen_before of the first move
    if (currentGameMoves.length > 0 && currentGameMoves[0]?.fen_before) {
      return currentGameMoves[0].fen_before;
    }
    // Fallback to standard starting position
    return 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1';
  };
  
  // Check if we have real game data with FEN positions
  const hasRealGameData = currentGameMoves.length > 0 && currentGameMoves[0]?.fen_after;
  
  let currentPosition = getStartingPosition();
  let currentMove = null;
  let currentEval = 0;
  
  try {
    if (currentMoveIndex >= 0 && Array.isArray(currentGameMoves) && currentGameMoves[currentMoveIndex]) {
      const move = currentGameMoves[currentMoveIndex];
      currentMove = move;
      
      if (hasRealGameData) {
        // Use fen_after from real game data
        currentPosition = move.fen_after || getStartingPosition();
        currentEval = move.evaluation_after ?? move.evaluation ?? 0;
      } else {
        // For mock data, use mockPositions array
        // mockPositions[0] is starting, mockPositions[1] is after move 0, etc.
        if (mockPositions && mockPositions[currentMoveIndex + 1]) {
          currentPosition = mockPositions[currentMoveIndex + 1];
        }
        currentEval = move.evaluation ?? 0;
      }
    }
  } catch (e) {
    console.warn("Error getting position:", e);
  }
  
  // Get last move for highlighting
  const lastMove = (currentMoveIndex >= 0 && currentMove && currentMove.uci && currentMove.uci.length >= 4) ? {
    from: currentMove.uci.substring(0, 2),
    to: currentMove.uci.substring(2, 4),
  } : undefined;

  // Auto-play functionality
  useEffect(() => {
    if (!isPlaying) return;
    
    const interval = setInterval(() => {
      setCurrentMoveIndex(prev => {
        const maxIndex = Array.isArray(currentGameMoves) ? currentGameMoves.length - 1 : (mockGame?.moves?.length || 0) - 1;
        if (prev >= maxIndex) {
          setIsPlaying(false);
          return prev;
        }
        return prev + 1;
      });
    }, 1000);
    
    return () => clearInterval(interval);
  }, [isPlaying, currentGameMoves]);

  const handleConnect = async (username: string) => {
    setIsLoadingGames(true);
    try {
      // Import games from Chess.com
      const result = await importGames(username, 10);
      
      setIsConnected(true);
      setConnectedUsername(username);
      
      // Fetch all games to display
      const allGames = await listGames({ limit: 50 });
      setImportedGames(allGames);
      
      // Fetch user analytics for hyper-specific data
      try {
        const analytics = await getUserAnalytics(username);
        setUserAnalytics(analytics);
      } catch (analyticsError) {
        console.warn("Could not fetch analytics:", analyticsError);
      }
      
      // Fetch user skills profile
      try {
        const skillsResponse = await getUserSkills(username);
        setUserSkills(skillsResponse.skills);
        setGamesAnalyzedForSkills(skillsResponse.games_analyzed);
      } catch (skillsError) {
        console.warn("Could not fetch skills:", skillsError);
      }
      
      if (toastFn) {
        toastFn({
          title: "Success!",
          description: `Imported ${result.imported} games`,
        });
      }
    } catch (error: any) {
      if (toastFn) {
        toastFn({
          title: "Error",
          description: error.message || "Failed to import games",
          variant: "destructive",
        });
      }
    } finally {
      setIsLoadingGames(false);
    }
  };

  const handleMoveClick = (index: number) => {
    setCurrentMoveIndex(index);
    setIsPlaying(false);
  };

  const handleMomentClick = (moveNumber: number) => {
    // Find the move index for this move number
    const index = (moveNumber - 1);
    const moves = (gameAnalysis?.moves && Array.isArray(gameAnalysis.moves)) 
      ? gameAnalysis.moves 
      : (mockGame.moves || []);
      
    if (Array.isArray(moves) && index >= 0 && index < moves.length) {
      setCurrentMoveIndex(index);
      setIsPlaying(false);
    }
  };

  const handleGameSelect = async (gameId: number | string) => {
    console.log("handleGameSelect called with:", gameId, typeof gameId);
    
    // Normalize gameId
    const normalizedId = typeof gameId === 'string' ? parseInt(gameId, 10) : gameId;
    
    if (!normalizedId || isNaN(normalizedId) || normalizedId <= 0) {
      console.error("Invalid gameId:", normalizedId);
      if (toastFn) {
        toastFn({
          title: "Error",
          description: "Invalid game ID",
          variant: "destructive",
        });
      }
      return;
    }
    
    try {
      setIsAnalyzing(true);
      setSelectedGame(null);
      setCurrentMoveIndex(-1);
      setGameAnalysis(null);
      
      console.log("Fetching game:", normalizedId);
      
      // Get full game details
      const game = await getGame(normalizedId);
      console.log("Game fetched:", game);
      
      if (!game || !game.id) {
        throw new Error("Game not found or invalid");
      }
      
      setSelectedGame(game);
      
      // Auto-flip board based on which color the user played
      const userPlayedAsBlack = game.black_player?.toLowerCase() === connectedUsername?.toLowerCase();
      setFlipped(userPlayedAsBlack);
      
      if (toastFn) {
        toastFn({
          title: "Analyzing game...",
          description: "This may take a moment",
        });
      }
      
      // Always analyze to get full move data (force=true to use fresh Stockfish analysis)
      try {
        console.log("Starting analysis for game:", normalizedId);
        const analysisResult = await analyzeGame(normalizedId, true);
        console.log("Analysis result:", analysisResult);
        
        if (analysisResult && analysisResult.analysis) {
          setGameAnalysis(analysisResult.analysis);
          
          // Get puzzle recommendations based on weaknesses
          try {
            const puzzleResult = await getPuzzleRecommendationsForGame(normalizedId, 5);
            setPuzzleRecommendations(puzzleResult.puzzles || []);
          } catch (puzzleError) {
            console.warn("Could not fetch puzzles:", puzzleError);
            setPuzzleRecommendations([]);
          }
          
          // Refresh skills profile after analysis
          if (connectedUsername) {
            try {
              const skillsResponse = await getUserSkills(connectedUsername);
              setUserSkills(skillsResponse.skills);
              setGamesAnalyzedForSkills(skillsResponse.games_analyzed);
            } catch (skillsError) {
              console.warn("Could not refresh skills:", skillsError);
            }
          }
          
          if (toastFn && analysisResult.summary) {
            toastFn({
              title: "Analysis complete!",
              description: `Found ${analysisResult.summary.blunders || 0} blunders, ${analysisResult.summary.mistakes || 0} mistakes`,
            });
          }
        }
      } catch (analysisError: any) {
        console.error("Analysis error:", analysisError);
        // Don't fail the whole thing if analysis fails
        if (toastFn) {
          toastFn({
            title: "Game loaded",
            description: "Analysis may not be available yet",
            variant: "default",
          });
        }
      }
    } catch (error: any) {
      console.error("Error loading game:", error);
      console.error("Error stack:", error.stack);
      
      const errorMessage = error?.message || error?.toString() || "Failed to load game";
      
      if (toastFn) {
        toastFn({
          title: "Error",
          description: errorMessage,
          variant: "destructive",
        });
      } else {
        alert(`Error: ${errorMessage}`);
      }
    } finally {
      setIsAnalyzing(false);
    }
  };

  return (
    <div className="min-h-screen bg-background">
      <Header 
        username={connectedUsername || 'Guest'} 
        onMenuClick={() => setSidebarOpen(true)} 
      />
      
      <Sidebar 
        isOpen={sidebarOpen} 
        onClose={() => setSidebarOpen(false)}
        recentGames={importedGames.length > 0 ? importedGames
          // Filter to only show games where the connected user played
          .filter(g => {
            const userIsWhite = g.white_player?.toLowerCase() === connectedUsername?.toLowerCase();
            const userIsBlack = g.black_player?.toLowerCase() === connectedUsername?.toLowerCase();
            return userIsWhite || userIsBlack;
          })
          .map(g => {
            // Case-insensitive username comparison
            const userIsWhite = g.white_player?.toLowerCase() === connectedUsername?.toLowerCase();
            const userIsBlack = g.black_player?.toLowerCase() === connectedUsername?.toLowerCase();
            
            // Determine opponent
            let opponent = 'Unknown';
            if (userIsWhite) {
              opponent = g.black_player || 'Unknown';
            } else if (userIsBlack) {
              opponent = g.white_player || 'Unknown';
            }
            
            // Determine result from user's perspective
            let result = 'D'; // Default to draw
            if (g.result === '1-0') {
              result = userIsWhite ? 'W' : 'L';
            } else if (g.result === '0-1') {
              result = userIsBlack ? 'W' : 'L';
            } else if (g.result === '1/2-1/2') {
              result = 'D';
            }
            
            return {
              id: g.id,
              opponent,
              result,
              date: g.played_at || new Date().toISOString(),
            };
          }) : mockRecentGames}
        onGameSelect={handleGameSelect}
      />
      
      <main className="md:ml-64 min-h-[calc(100vh-4rem)]">
        <div className="container py-6 px-4 max-w-7xl">
          {/* Connection status */}
          <div className="mb-6 flex flex-col sm:flex-row gap-4">
            <div className="flex-1">
              <ChessComConnect 
                onConnect={handleConnect}
                isConnected={isConnected}
                connectedUsername={connectedUsername}
                isLoading={isLoadingGames}
              />
            </div>
            
            {/* Daily Puzzle Quick Access */}
            <Card className="glass-card sm:w-64">
              <CardContent className="p-4">
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-lg bg-primary/10">
                    <Puzzle className="w-5 h-5 text-primary" />
                  </div>
                  <div className="flex-1">
                    <p className="text-sm font-medium">Daily Puzzle</p>
                    <p className="text-xs text-muted-foreground">Train with today's puzzle</p>
                  </div>
                </div>
                <Button 
                  className="w-full mt-3" 
                  size="sm"
                  onClick={async () => {
                    try {
                      if (toastFn) {
                        toastFn({
                          title: "Loading daily puzzle...",
                          description: "Fetching from Lichess",
                        });
                      }
                      
                      const dailyPuzzle = await getDailyPuzzle();
                      
                      if (dailyPuzzle && dailyPuzzle.fen && dailyPuzzle.solution && dailyPuzzle.solution.length > 0) {
                        const playablePuzzle: PlayablePuzzle = {
                          puzzle_id: dailyPuzzle.puzzle_id,
                          fen: dailyPuzzle.fen,
                          solution: dailyPuzzle.solution,
                          rating: dailyPuzzle.rating || 1500,
                          themes: dailyPuzzle.themes || ['daily'],
                          theme: 'daily',
                          url: dailyPuzzle.url,
                          isTrainingLink: false,
                        };
                        setActivePuzzle(playablePuzzle);
                        setShowPuzzlePlayer(true);
                      } else {
                        // Fallback to Lichess website
                        window.open('https://lichess.org/training/daily', '_blank', 'noopener,noreferrer');
                      }
                    } catch (error) {
                      console.error("Error fetching daily puzzle:", error);
                      // Fallback to Lichess website
                      window.open('https://lichess.org/training/daily', '_blank', 'noopener,noreferrer');
                    }
                  }}
                >
                  Play Now
                </Button>
              </CardContent>
            </Card>
          </div>

          {/* Analysis status */}
          {isAnalyzing && (
            <div className="mb-6 p-4 bg-primary/10 border border-primary/20 rounded-lg">
              <p className="text-sm text-primary">Analyzing game... This may take a moment.</p>
            </div>
          )}

          {/* Selected game info */}
          {selectedGame && !isAnalyzing && (
            <div className="mb-6 p-4 bg-card border rounded-lg">
              <p className="text-sm font-medium">
                {selectedGame.white_player} vs {selectedGame.black_player}
                {gameAnalysis && (
                  <span className="ml-2 text-muted-foreground">
                    - {gameAnalysis.blunders} blunders, {gameAnalysis.mistakes} mistakes
                  </span>
                )}
              </p>
            </div>
          )}

          {/* Main Analysis Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            {/* Left Column - Board & Controls */}
            <div className="lg:col-span-5 space-y-4">
              {/* Board with Eval Bar */}
              <div className="flex gap-3 justify-center lg:justify-start">
                <EvaluationBar 
                  evaluation={currentEval} 
                  className="h-80 md:h-96 hidden sm:block" 
                />
                <div className="space-y-3">
                  <Chessboard 
                    position={currentPosition}
                    lastMove={lastMove}
                    flipped={flipped}
                    size="md"
                  />
                  <GameControls 
                    onFirst={() => setCurrentMoveIndex(-1)}
                    onPrevious={() => setCurrentMoveIndex(prev => Math.max(-1, prev - 1))}
                    onNext={() => setCurrentMoveIndex(prev => Math.min((Array.isArray(currentGameMoves) ? currentGameMoves.length : 0) - 1, prev + 1))}
                    onLast={() => setCurrentMoveIndex((Array.isArray(currentGameMoves) ? currentGameMoves.length : 0) - 1)}
                    onTogglePlay={() => setIsPlaying(!isPlaying)}
                    onFlip={() => setFlipped(!flipped)}
                    isPlaying={isPlaying}
                    canGoBack={currentMoveIndex > -1}
                    canGoForward={currentMoveIndex < (Array.isArray(currentGameMoves) ? currentGameMoves.length : 0) - 1}
                  />
                </div>
              </div>

              {/* Mobile Eval Bar */}
              <div className="sm:hidden">
                <EvaluationBar 
                  evaluation={currentEval} 
                  orientation="horizontal"
                  className="h-6 w-full" 
                />
              </div>

              {/* Move List */}
              {Array.isArray(currentGameMoves) && currentGameMoves.length > 0 && (
                <MoveList 
                  moves={currentGameMoves}
                  currentMoveIndex={currentMoveIndex}
                  onMoveClick={handleMoveClick}
                />
              )}

              {/* Evaluation Chart */}
              <EvaluationChart 
                data={mockEvaluationData}
                currentMove={currentMoveIndex + 1}
                onMoveClick={(move) => setCurrentMoveIndex(move - 1)}
              />
            </div>

            {/* Right Column - Analysis */}
            <div className="lg:col-span-7 space-y-4">
              {/* Game Summary */}
              {selectedGame && Array.isArray(currentGameMoves) ? (
                <GameSummaryCard 
                  game={{
                    id: String(selectedGame.id ?? 'local'),
                    white: selectedGame.white_player || 'White',
                    black: selectedGame.black_player || 'Black',
                    result: selectedGame.result || '*',
                    date: selectedGame.played_at || new Date().toISOString(),
                    timeControl: selectedGame.time_control || 'N/A',
                    opening: gameAnalysis?.analysis_source ? `Analyzed by ${gameAnalysis.analysis_source}` : 'Unknown',
                    accuracy: {
                      white: gameAnalysis?.accuracy || 80,
                      black: gameAnalysis?.accuracy || 80,
                    },
                    moves: currentGameMoves.map((m: any, idx: number) => ({
                      ...m,
                      quality: m.quality || (m.is_blunder ? 'blunder' : 
                              m.is_mistake ? 'mistake' : 
                              m.is_inaccuracy ? 'inaccuracy' : 
                              m.evaluation_loss <= -50 ? 'great' :
                              m.evaluation_loss <= -20 ? 'good' : 'neutral'),
                    })),
                    criticalMoments: [],
                  }} 
                  playerColor={selectedGame.white_player?.toLowerCase() === connectedUsername?.toLowerCase() ? "white" : "black"} 
                />
              ) : (
                <GameSummaryCard game={mockGame} playerColor="white" />
              )}
              
              {/* AI Explanation */}
              {currentMove && (
                <AIExplanation 
                  move={{
                    ...currentMove,
                    quality: currentMove.is_blunder ? 'blunder' : 
                            currentMove.is_mistake ? 'mistake' : 
                            currentMove.is_inaccuracy ? 'inaccuracy' : 'good',
                    san: currentMove.san || '',
                    bestMove: currentMove.best_move || '',
                    evaluation: currentMove.evaluation_after || currentMove.evaluation || 0,
                  }}
                  moveNumber={currentMoveIndex + 1}
                  isPlayerMove={currentMoveIndex % 2 === 0}
                />
              )}
              {!currentMove && selectedGame && (
                <Card className="glass-card">
                  <CardContent className="flex flex-col items-center justify-center py-12 text-center">
                    <Brain className="w-12 h-12 text-muted-foreground/50 mb-3" />
                    <p className="text-muted-foreground">Navigate moves to see AI analysis</p>
                  </CardContent>
                </Card>
              )}
              
              {/* Critical Moments - show mistakes from analysis */}
              {gameAnalysis && gameAnalysis.moves && Array.isArray(gameAnalysis.moves) && (
                <CriticalMoments 
                  moments={gameAnalysis.moves
                    .filter((m: any) => m && (m.is_blunder || m.is_mistake))
                    .map((m: any) => ({
                      moveNumber: m.move_number || 0,
                      type: m.is_blunder ? 'blunder' : 'mistake',
                      evaluation: m.evaluation_loss || 0,
                    }))}
                  onMomentClick={handleMomentClick}
                />
              )}
              
              {/* Two column grid for skills and puzzles */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <SkillRadar 
                  skills={userSkills.length > 0 ? userSkills : mockSkills} 
                  gamesAnalyzed={gamesAnalyzedForSkills}
                />
                <PuzzleRecommendations 
                  puzzles={puzzleRecommendations.length > 0 ? puzzleRecommendations.map((p, idx) => ({
                    id: String(p.puzzle_id || p.id || `puzzle-${idx}`),
                    fen: p.fen || 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1',
                    moves: Array.isArray(p.solution) ? p.solution : (Array.isArray(p.moves) ? p.moves : []),
                    rating: p.rating || 1500,
                    themes: Array.isArray(p.themes) ? p.themes : [p.theme || 'tactics'],
                    reason: p.isTrainingLink 
                      ? `Practice ${p.theme || 'tactics'} puzzles on Lichess`
                      : `Play this puzzle to improve your ${p.theme || (Array.isArray(p.themes) ? p.themes[0] : 'tactics')}`,
                  })) : []}
                  onPuzzleSelect={(puzzle) => {
                    console.log("Puzzle selected:", puzzle);
                    // Find the full puzzle data from recommendations
                    const fullPuzzle = puzzleRecommendations.find(
                      p => String(p.puzzle_id || p.id) === puzzle.id
                    );
                    
                    if (fullPuzzle && fullPuzzle.solution && fullPuzzle.solution.length > 0 && !fullPuzzle.isTrainingLink) {
                      // Open interactive puzzle player
                      const playablePuzzle: PlayablePuzzle = {
                        puzzle_id: String(fullPuzzle.puzzle_id || fullPuzzle.id),
                        fen: fullPuzzle.fen,
                        solution: fullPuzzle.solution,
                        rating: fullPuzzle.rating || 1500,
                        themes: Array.isArray(fullPuzzle.themes) ? fullPuzzle.themes : [fullPuzzle.theme || 'tactics'],
                        theme: fullPuzzle.theme,
                        url: fullPuzzle.url,
                        isTrainingLink: false,
                      };
                      setActivePuzzle(playablePuzzle);
                      setCurrentPuzzleIndex(puzzleRecommendations.indexOf(fullPuzzle));
                      setShowPuzzlePlayer(true);
                    } else {
                      // Open Lichess for training links
                      const url = fullPuzzle?.url || (puzzle.themes && puzzle.themes.length > 0 
                        ? `https://lichess.org/training/${puzzle.themes[0]}` 
                        : 'https://lichess.org/training/tactics');
                      window.open(url, '_blank', 'noopener,noreferrer');
                    }
                  }}
                />
              </div>
              
              {/* User Analytics - Hyper-specific data */}
              {userAnalytics && (
                <div className="mt-6">
                  <UserAnalytics analytics={userAnalytics} />
                </div>
              )}
            </div>
          </div>
        </div>
      </main>
      
      {/* Puzzle Player Modal */}
      {showPuzzlePlayer && activePuzzle && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
          <div className="relative max-w-lg w-full max-h-[90vh] overflow-y-auto">
            <Button
              variant="ghost"
              size="icon"
              className="absolute -top-2 -right-2 z-10 bg-background rounded-full shadow-lg"
              onClick={() => {
                setShowPuzzlePlayer(false);
                setActivePuzzle(null);
              }}
            >
              <X className="w-4 h-4" />
            </Button>
            
            <PuzzlePlayer
              puzzle={activePuzzle}
              onComplete={(success, attempts) => {
                console.log(`Puzzle completed: success=${success}, attempts=${attempts}`);
                if (toastFn) {
                  toastFn({
                    title: success ? "Puzzle Solved! 🎉" : "Better luck next time",
                    description: success 
                      ? `Completed in ${attempts === 0 ? 'first try!' : `${attempts + 1} attempts`}`
                      : "Keep practicing to improve!",
                  });
                }
              }}
              onClose={() => {
                // Try to load next puzzle
                const nextIndex = currentPuzzleIndex + 1;
                if (nextIndex < puzzleRecommendations.length) {
                  const nextPuzzle = puzzleRecommendations[nextIndex];
                  if (nextPuzzle && nextPuzzle.solution && nextPuzzle.solution.length > 0 && !nextPuzzle.isTrainingLink) {
                    const playablePuzzle: PlayablePuzzle = {
                      puzzle_id: String(nextPuzzle.puzzle_id || nextPuzzle.id),
                      fen: nextPuzzle.fen,
                      solution: nextPuzzle.solution,
                      rating: nextPuzzle.rating || 1500,
                      themes: Array.isArray(nextPuzzle.themes) ? nextPuzzle.themes : [nextPuzzle.theme || 'tactics'],
                      theme: nextPuzzle.theme,
                      url: nextPuzzle.url,
                      isTrainingLink: false,
                    };
                    setActivePuzzle(playablePuzzle);
                    setCurrentPuzzleIndex(nextIndex);
                  } else {
                    setShowPuzzlePlayer(false);
                    setActivePuzzle(null);
                  }
                } else {
                  setShowPuzzlePlayer(false);
                  setActivePuzzle(null);
                }
              }}
            />
          </div>
        </div>
      )}
    </div>
  );
};

export default Index;
