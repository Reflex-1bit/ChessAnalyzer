import { Button } from '@/components/ui/button';
import { 
  SkipBack, 
  ChevronLeft, 
  ChevronRight, 
  SkipForward, 
  Play, 
  Pause,
  RotateCcw
} from 'lucide-react';

interface GameControlsProps {
  onFirst: () => void;
  onPrevious: () => void;
  onNext: () => void;
  onLast: () => void;
  onTogglePlay: () => void;
  onFlip: () => void;
  isPlaying: boolean;
  canGoBack: boolean;
  canGoForward: boolean;
}

export function GameControls({
  onFirst,
  onPrevious,
  onNext,
  onLast,
  onTogglePlay,
  onFlip,
  isPlaying,
  canGoBack,
  canGoForward,
}: GameControlsProps) {
  return (
    <div className="flex items-center justify-center gap-1 p-2 bg-card rounded-xl border border-border">
      <Button
        variant="ghost"
        size="icon-sm"
        onClick={onFlip}
        title="Flip board"
      >
        <RotateCcw className="w-4 h-4" />
      </Button>
      
      <div className="w-px h-6 bg-border mx-1" />
      
      <Button
        variant="ghost"
        size="icon-sm"
        onClick={onFirst}
        disabled={!canGoBack}
        title="First move"
      >
        <SkipBack className="w-4 h-4" />
      </Button>
      
      <Button
        variant="ghost"
        size="icon-sm"
        onClick={onPrevious}
        disabled={!canGoBack}
        title="Previous move"
      >
        <ChevronLeft className="w-4 h-4" />
      </Button>
      
      <Button
        variant="move"
        size="icon"
        onClick={onTogglePlay}
        title={isPlaying ? 'Pause' : 'Play'}
      >
        {isPlaying ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4 ml-0.5" />}
      </Button>
      
      <Button
        variant="ghost"
        size="icon-sm"
        onClick={onNext}
        disabled={!canGoForward}
        title="Next move"
      >
        <ChevronRight className="w-4 h-4" />
      </Button>
      
      <Button
        variant="ghost"
        size="icon-sm"
        onClick={onLast}
        disabled={!canGoForward}
        title="Last move"
      >
        <SkipForward className="w-4 h-4" />
      </Button>
    </div>
  );
}
