import type { GameSummary, CriticalMoment, SkillArea, Puzzle, ChessMove } from '@/types/chess';

export const mockMoves: ChessMove[] = [
  { from: 'e2', to: 'e4', piece: 'P', san: 'e4', quality: 'book', evaluation: 0.3 },
  { from: 'e7', to: 'e5', piece: 'p', san: 'e5', quality: 'book', evaluation: 0.2 },
  { from: 'g1', to: 'f3', piece: 'N', san: 'Nf3', quality: 'book', evaluation: 0.3 },
  { from: 'b8', to: 'c6', piece: 'n', san: 'Nc6', quality: 'book', evaluation: 0.2 },
  { from: 'f1', to: 'b5', piece: 'B', san: 'Bb5', quality: 'good', evaluation: 0.4 },
  { from: 'a7', to: 'a6', piece: 'p', san: 'a6', quality: 'good', evaluation: 0.3 },
  { from: 'b5', to: 'a4', piece: 'B', san: 'Ba4', quality: 'good', evaluation: 0.4 },
  { from: 'g8', to: 'f6', piece: 'n', san: 'Nf6', quality: 'great', evaluation: 0.2 },
  { from: 'e1', to: 'g1', piece: 'K', san: 'O-O', quality: 'good', evaluation: 0.4 },
  { from: 'f8', to: 'e7', piece: 'b', san: 'Be7', quality: 'good', evaluation: 0.3 },
  { from: 'd2', to: 'd4', piece: 'P', san: 'd4', quality: 'great', evaluation: 0.6 },
  { from: 'e5', to: 'd4', piece: 'p', san: 'exd4', quality: 'inaccuracy', evaluation: 0.9, bestMove: 'd6', explanation: 'Taking the pawn opens up lines for White' },
  { from: 'f3', to: 'd4', piece: 'N', san: 'Nxd4', quality: 'good', evaluation: 0.8 },
  { from: 'e8', to: 'g8', piece: 'k', san: 'O-O', quality: 'good', evaluation: 0.7 },
  { from: 'b1', to: 'c3', piece: 'N', san: 'Nc3', quality: 'good', evaluation: 0.8 },
  { from: 'd7', to: 'd6', piece: 'p', san: 'd6', quality: 'good', evaluation: 0.6 },
  { from: 'c1', to: 'e3', piece: 'B', san: 'Be3', quality: 'great', evaluation: 0.9 },
  { from: 'c8', to: 'g4', piece: 'b', san: 'Bg4', quality: 'mistake', evaluation: 1.5, bestMove: 'Bd7', explanation: 'The bishop is exposed on g4' },
  { from: 'f2', to: 'f3', piece: 'P', san: 'f3', quality: 'brilliant', evaluation: 2.1 },
  { from: 'g4', to: 'e6', piece: 'b', san: 'Be6', quality: 'good', evaluation: 1.8 },
  { from: 'd4', to: 'e6', piece: 'N', san: 'Nxe6', quality: 'great', evaluation: 2.5 },
  { from: 'f7', to: 'e6', piece: 'p', san: 'fxe6', quality: 'neutral', evaluation: 2.3 },
  { from: 'd1', to: 'd3', piece: 'Q', san: 'Qd3', quality: 'good', evaluation: 2.5 },
  { from: 'd8', to: 'd7', piece: 'q', san: 'Qd7', quality: 'blunder', evaluation: 4.2, bestMove: 'Qe8', explanation: 'This allows a devastating attack' },
];

export const mockGame: GameSummary = {
  id: 'game-001',
  white: 'You',
  black: 'Magnus_Fan_2024',
  result: '1-0',
  date: 'Jan 21, 2025',
  timeControl: '10+0',
  opening: 'Ruy Lopez, Morphy Defense',
  accuracy: {
    white: 87.4,
    black: 72.1,
  },
  moves: mockMoves,
  criticalMoments: [
    {
      moveNumber: 12,
      type: 'missed_win',
      position: 'r1bq1rk1/1pp1bppp/2np1n2/4p3/B2PP3/5N2/PPP2PPP/RNBQ1RK1 w - - 0 8',
      explanation: 'Black should have played d6 to solidify the center. Taking the pawn opens lines for White.',
      bestMove: 'd6',
      playedMove: 'exd4',
      evalBefore: 0.4,
      evalAfter: 0.9,
    },
    {
      moveNumber: 18,
      type: 'blunder',
      position: 'r2q1rk1/1pp1bppp/2npbn2/8/B3P3/2N1BP2/PPP3PP/R2Q1RK1 b - - 0 12',
      explanation: 'Bg4 puts the bishop on a square where it can be attacked and driven away.',
      bestMove: 'Bd7',
      playedMove: 'Bg4',
      evalBefore: 0.8,
      evalAfter: 1.5,
    },
    {
      moveNumber: 19,
      type: 'brilliant',
      position: 'r2q1rk1/1pp1bppp/2npbn2/8/B3P3/2N1BP2/PPP3PP/R2Q1RK1 w - - 0 13',
      explanation: 'f3 brilliantly traps the bishop while opening the f-file for future attacks.',
      bestMove: 'f3',
      playedMove: 'f3',
      evalBefore: 1.5,
      evalAfter: 2.1,
    },
    {
      moveNumber: 24,
      type: 'blunder',
      position: 'r4rk1/1ppqbppp/2np4/4p3/B3P3/2NQ1P2/PPP3PP/R4RK1 b - - 0 16',
      explanation: 'Qd7 walks into a devastating attack. Qe8 was necessary to defend.',
      bestMove: 'Qe8',
      playedMove: 'Qd7',
      evalBefore: 2.5,
      evalAfter: 4.2,
    },
  ],
};

export const mockSkills: SkillArea[] = [
  { name: 'Opening', score: 78, improvement: 5, description: 'Good theoretical knowledge, could explore more variations' },
  { name: 'Middlegame', score: 65, improvement: -2, description: 'Piece coordination needs work, especially in complex positions' },
  { name: 'Endgame', score: 58, improvement: 8, description: 'Improving! Focus on king activity and passed pawns' },
  { name: 'Tactics', score: 72, improvement: 3, description: 'Solid tactical vision, practice deeper calculations' },
  { name: 'Time Management', score: 45, improvement: -5, description: 'Spending too much time in familiar positions' },
];

export const mockPuzzles: Puzzle[] = [
  {
    id: '8742',
    fen: 'r1bqkb1r/pppp1ppp/2n2n2/4p2Q/2B1P3/8/PPPP1PPP/RNB1K1NR w KQkq - 4 4',
    moves: ['Qxf7#'],
    rating: 1200,
    themes: ['Tactics', 'Checkmate'],
    reason: 'Practice spotting quick checkmate patterns like in move 19',
  },
  {
    id: '12453',
    fen: 'r1b1k2r/ppppqppp/2n2n2/4p3/1bB1P3/2N2N2/PPPP1PPP/R1BQK2R w KQkq - 4 5',
    moves: ['d3', 'Bxc3+', 'bxc3'],
    rating: 1350,
    themes: ['Defense', 'Pins'],
    reason: 'Learn to handle bishop pins like Black attempted in this game',
  },
  {
    id: '9821',
    fen: 'r2qkb1r/ppp2ppp/2n1bn2/3pp3/4P3/2N2N2/PPPP1PPP/R1BQKB1R w KQkq d6 0 5',
    moves: ['exd5', 'Nxd5', 'Nxd5', 'Bxd5'],
    rating: 1450,
    themes: ['Opening', 'Center Control'],
    reason: 'Master pawn breaks in the center during the opening phase',
  },
];

export const mockRecentGames = [
  { id: '1', opponent: 'ChessKnight42', result: 'win', date: '2 hours ago' },
  { id: '2', opponent: 'QueenGambit99', result: 'loss', date: '5 hours ago' },
  { id: '3', opponent: 'RookRuler', result: 'win', date: 'Yesterday' },
  { id: '4', opponent: 'BishopMaster', result: 'draw', date: 'Yesterday' },
  { id: '5', opponent: 'PawnStorm', result: 'win', date: '2 days ago' },
];

export const mockEvaluationData = mockMoves.map((move, index) => ({
  move: index + 1,
  evaluation: move.evaluation || 0,
  quality: move.quality,
}));

// Position FENs for each move
export const mockPositions = [
  'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR', // starting
  'rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR', // 1. e4
  'rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR', // 1...e5
  'rnbqkbnr/pppp1ppp/8/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R', // 2. Nf3
  'r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R', // 2...Nc6
  'r1bqkbnr/pppp1ppp/2n5/1B2p3/4P3/5N2/PPPP1PPP/RNBQK2R', // 3. Bb5
  'r1bqkbnr/1ppp1ppp/p1n5/1B2p3/4P3/5N2/PPPP1PPP/RNBQK2R', // 3...a6
  'r1bqkbnr/1ppp1ppp/p1n5/4p3/B3P3/5N2/PPPP1PPP/RNBQK2R', // 4. Ba4
  'r1bqkb1r/1ppp1ppp/p1n2n2/4p3/B3P3/5N2/PPPP1PPP/RNBQK2R', // 4...Nf6
  'r1bqkb1r/1ppp1ppp/p1n2n2/4p3/B3P3/5N2/PPPP1PPP/RNBQ1RK1', // 5. O-O
  'r1bqk2r/1pppbppp/p1n2n2/4p3/B3P3/5N2/PPPP1PPP/RNBQ1RK1', // 5...Be7
  'r1bqk2r/1pppbppp/p1n2n2/4p3/B2PP3/5N2/PPP2PPP/RNBQ1RK1', // 6. d4
  'r1bqk2r/1pppbppp/p1n2n2/8/B2pP3/5N2/PPP2PPP/RNBQ1RK1', // 6...exd4
  'r1bqk2r/1pppbppp/p1n2n2/8/B2NP3/8/PPP2PPP/RNBQ1RK1', // 7. Nxd4
  'r1bq1rk1/1pppbppp/p1n2n2/8/B2NP3/8/PPP2PPP/RNBQ1RK1', // 7...O-O
  'r1bq1rk1/1pppbppp/p1n2n2/8/B2NP3/2N5/PPP2PPP/R1BQ1RK1', // 8. Nc3
  'r1bq1rk1/1pp1bppp/p1np1n2/8/B2NP3/2N5/PPP2PPP/R1BQ1RK1', // 8...d6
  'r1bq1rk1/1pp1bppp/p1np1n2/8/B2NP3/2N1B3/PPP2PPP/R2Q1RK1', // 9. Be3
  'r2q1rk1/1pp1bppp/p1np1n2/8/B2NP1b1/2N1B3/PPP2PPP/R2Q1RK1', // 9...Bg4
  'r2q1rk1/1pp1bppp/p1np1n2/8/B2NP1b1/2N1BP2/PPP3PP/R2Q1RK1', // 10. f3
  'r2q1rk1/1pp1bppp/p1npbn2/8/B2NP3/2N1BP2/PPP3PP/R2Q1RK1', // 10...Be6
  'r2q1rk1/1pp1bppp/p1npNn2/8/B3P3/2N1BP2/PPP3PP/R2Q1RK1', // 11. Nxe6
  'r2q1rk1/1pp1bppp/p1np1n2/8/B3P3/2N1BP2/PPP3PP/R2Q1RK1', // 11...fxe6
  'r2q1rk1/1pp1bppp/p1nppn2/8/B3P3/2NQBP2/PPP3PP/R4RK1', // 12. Qd3
  'r4rk1/1ppqbppp/p1nppn2/8/B3P3/2NQBP2/PPP3PP/R4RK1', // 12...Qd7
];
