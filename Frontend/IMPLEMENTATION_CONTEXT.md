# Chess Coach AI - Implementation Context

## Overview

This document provides context for the Chess Coach AI implementation, including the WintrCat classification algorithm, skill analysis, and UI components.

---

## 0. Quick Start - Stockfish Setup (REQUIRED)

**Accurate move classification requires local Stockfish.** Without it, analysis will be inaccurate.

### Installation

1. **Download Stockfish** from https://stockfishchess.org/download/
2. **Extract** to a location like `C:\stockfish\`
3. **Update `.env`** file in the `backend/` folder:

```env
STOCKFISH_PATH=C:\stockfish\stockfish-windows-x86-64-avx2.exe
STOCKFISH_DEPTH=18
```

### Why Stockfish is Required

- **Multi-PV Analysis**: Stockfish provides the top 2+ moves, which is essential for:
  - **Brilliant detection**: Requires knowing if second-best move eval < 700cp
  - **Great detection**: Requires 150+ cp gap between best and second-best move
- **Consistent Depth**: Cloud APIs have variable depth and may not have your positions cached
- **Accuracy**: Local analysis at depth 18 gives reliable classifications

---

## 1. Move Classification System (WintrCat Algorithm)

Based on [WintrCat's freechess](https://github.com/WintrCat/freechess) - an open-source chess analysis tool.

### Classification Types

```python
class Classification(Enum):
    BRILLIANT = "brilliant"   # Creative sacrifice that wins
    GREAT = "great"           # Punishes opponent's blunder
    BEST = "best"             # The engine's top choice
    EXCELLENT = "excellent"   # Nearly as good as best
    GOOD = "good"             # Solid move
    INACCURACY = "inaccuracy" # Small mistake (75-150cp loss)
    MISTAKE = "mistake"       # Significant error (150-300cp loss)
    BLUNDER = "blunder"       # Serious mistake (300+ cp loss)
    BOOK = "book"             # Opening theory move
    FORCED = "forced"         # Only legal move
```

### WTF Algorithm (Dynamic Thresholds)

The key innovation is **dynamic evaluation loss thresholds** based on position complexity:

```python
def get_evaluation_loss_threshold(classification, prev_eval):
    prev_eval = abs(prev_eval)
    
    if classification == Classification.BEST:
        threshold = 0.0001 * (prev_eval ** 2) + (0.0236 * prev_eval) - 3.7143
    elif classification == Classification.EXCELLENT:
        threshold = 0.0002 * (prev_eval ** 2) + (0.1231 * prev_eval) + 27.5455
    elif classification == Classification.GOOD:
        threshold = 0.0002 * (prev_eval ** 2) + (0.2643 * prev_eval) + 60.5455
    elif classification == Classification.INACCURACY:
        threshold = 0.0002 * (prev_eval ** 2) + (0.3624 * prev_eval) + 108.0909
    elif classification == Classification.MISTAKE:
        threshold = 0.0003 * (prev_eval ** 2) + (0.4027 * prev_eval) + 225.8182
    
    return max(threshold, 0)
```

**Why dynamic?** In positions with large evaluations (e.g., +500cp), a 100cp loss is less significant than in equal positions.

### Accuracy Calculation

Uses weighted classification values (0-1 scale):

```python
CLASSIFICATION_VALUES = {
    "blunder": 0,
    "mistake": 0.2,
    "inaccuracy": 0.4,
    "good": 0.65,
    "excellent": 0.9,
    "best": 1,
    "great": 1,
    "brilliant": 1,
    "book": 1,
    "forced": 1,
}

accuracy = (sum(classification_values) / num_moves) * 100
```

### Brilliant Move Detection

A move is **brilliant** if:
1. It's the best move
2. Player is not already winning easily (second-best eval < 700cp)
3. A piece is left hanging (sacrifice)
4. The sacrifice leads to a winning position

```python
# Check for hanging pieces after the move
for square in chess.SQUARES:
    piece = board_after.piece_at(square)
    if piece and piece.color == mover_color:
        if is_piece_hanging(fen_before, fen_after, square):
            classification = Classification.BRILLIANT
```

### Great Move Detection

A move is **great** if:
1. It's the best move
2. There's a significant gap (150+ cp) between best and second-best move
3. The moved piece is not hanging

---

## 2. Skill Analysis System

### Game Phases

```python
# Opening: moves 1-15
# Middlegame: moves 15-40  
# Endgame: after move 40
```

### Skill Categories

| Skill | How It's Calculated |
|-------|---------------------|
| **Opening** | Accuracy of moves 1-15 |
| **Middlegame** | Accuracy of moves 15-40 |
| **Endgame** | Accuracy after move 40 |
| **Tactics** | Brilliant/great moves bonus, blunder penalty |
| **Time Management** | Compares early vs late game accuracy |

### Tactics Score Formula

```python
base_accuracy = sum(classification_values) / total_moves * 100
bonus = (brilliant * 5 + great * 3 + best * 1) / total_moves * 100
penalty = (blunder * 3 + mistake * 1) / total_moves * 50
tactics_score = base_accuracy + bonus - penalty
```

### Time Management Detection

Detects time trouble by comparing accuracy drop in late game:

```python
late_game_start = int(total_moves * 0.75)
early_accuracy = avg(early_moves)
late_accuracy = avg(late_moves)
accuracy_drop = early_accuracy - late_accuracy

if accuracy_drop > 0.2:
    base_score -= 25  # Severe time trouble
elif accuracy_drop > 0.1:
    base_score -= 15  # Moderate time trouble
```

---

## 3. Backend API Endpoints

### Analysis Endpoints

```
POST /api/games/{game_id}/analyze
  - Analyzes game with WintrCat classification
  - Returns move-by-move analysis with quality ratings
  - Caches results for fast subsequent access

GET /api/analytics/user/{username}/skills
  - Returns skill profile based on analyzed games
  - Calculates scores for Opening, Middlegame, Endgame, Tactics, Time Management
```

### Response Format

```json
{
  "analysis": {
    "total_moves": 45,
    "blunders": 2,
    "mistakes": 3,
    "inaccuracies": 5,
    "accuracy": 78.5,
    "accuracy_white": 82.1,
    "accuracy_black": 74.9,
    "moves": [
      {
        "move_number": 1,
        "color": "w",
        "san": "e4",
        "quality": "book",
        "evaluation_before": 0,
        "evaluation_after": 30,
        "is_blunder": false,
        "is_mistake": false
      }
    ]
  }
}
```

---

## 4. Frontend Components

### MoveQualityBadge

Displays classification badges with icons:

| Classification | Icon | Color |
|----------------|------|-------|
| Brilliant | Sparkles | Cyan (#00d4ff) |
| Great | Trophy | Teal |
| Best | CheckCircle2 | Green |
| Excellent | Zap | Light Green |
| Good | Star | Dark Green |
| Book | BookOpen | Blue |
| Forced | Lock | Purple |
| Inaccuracy | AlertTriangle | Yellow |
| Mistake | AlertCircle | Orange |
| Blunder | AlertCircle | Red |

### SkillRadar Component

Displays skill profile with:
- Score (0-100)
- Improvement trend (+X% or -X%)
- Progress bar (color-coded by score)
- Contextual description

```tsx
<SkillRadar 
  skills={[
    { name: "Opening", score: 78, improvement: 5, description: "..." },
    { name: "Middlegame", score: 65, improvement: -2, description: "..." },
    // ...
  ]} 
  gamesAnalyzed={10}
/>
```

---

## 5. File Structure

```
backend/
├── app/
│   ├── services/
│   │   ├── classification.py    # WintrCat algorithm
│   │   ├── skill_analysis.py    # Skill profile calculation
│   │   ├── game_analyzer.py     # Game analysis orchestration
│   │   └── lichess.py           # Lichess cloud eval integration
│   └── routers/
│       ├── games.py             # /api/games endpoints
│       └── analytics.py         # /api/analytics endpoints

src/
├── components/
│   ├── chess/
│   │   ├── MoveQualityBadge.tsx # Classification badge
│   │   ├── MoveList.tsx         # Move list with quality indicators
│   │   └── Chessboard.tsx       # Board with highlighting
│   └── analysis/
│       ├── SkillRadar.tsx       # Skill profile display
│       └── GameSummaryCard.tsx  # Game summary with move counts
├── types/
│   └── chess.ts                 # MoveQuality type definitions
└── lib/
    └── api.ts                   # API client functions
```

---

## 6. Comparison with WintrCat Website

| Feature | WintrCat Website | This Implementation |
|---------|------------------|---------------------|
| Engine | Local Stockfish (depth 16-20) | Local Stockfish (depth 18) ✅ |
| Multi-PV | Yes (top 2+ lines) | Yes (2 PVs for brilliant/great) ✅ |
| Opening Book | openings.json database | Move number heuristic (≤5 moves) |
| Evaluation | Consistent depth | Consistent depth 18 ✅ |
| Fallback | None | Lichess Cloud → Heuristic |

**This implementation now matches WintrCat's core algorithm:**
- ✅ Local Stockfish with multi-PV enabled
- ✅ Consistent analysis depth (18)
- ✅ Second-best move evaluation for brilliant/great detection
- ✅ Dynamic WTF thresholds based on position evaluation

---

## 7. CSS Variables

```css
/* Move quality colors */
--move-brilliant: 190 85% 50%;   /* Cyan */
--move-great: 175 70% 42%;       /* Teal */
--move-best: 145 70% 45%;        /* Green */
--move-excellent: 145 60% 50%;   /* Light Green */
--move-good: 145 50% 40%;        /* Dark Green */
--move-forced: 260 50% 55%;      /* Purple */
--move-inaccuracy: 45 90% 50%;   /* Yellow */
--move-mistake: 25 90% 55%;      /* Orange */
--move-blunder: 0 75% 55%;       /* Red */
--move-book: 200 60% 55%;        /* Blue */
```

---

## 8. Usage

### Analyze a Game

```typescript
import { analyzeGame, getUserSkills } from '@/lib/api';

// Analyze game
const result = await analyzeGame(gameId);
console.log(result.analysis.accuracy); // 78.5

// Get skill profile
const skills = await getUserSkills(username);
console.log(skills.skills); // [{ name: "Opening", score: 78, ... }]
```

### Classify a Move (Backend)

```python
from app.services.classification import classify_move, Classification

classification = classify_move(
    move_san="Nxe5",
    move_uci="d4e5",
    fen_before="...",
    fen_after="...",
    eval_before=50,
    eval_after=-200,
    best_move_uci="d4e5",
    move_number=15
)

print(classification)  # Classification.BEST
```

---

## References

- [WintrCat's freechess](https://github.com/WintrCat/freechess) - Original classification algorithm
- [Lichess Cloud Eval API](https://lichess.org/api#tag/Analysis) - Position evaluation source
- [python-chess](https://python-chess.readthedocs.io/) - Chess library for Python
