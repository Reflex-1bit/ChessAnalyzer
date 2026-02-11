import { cn } from '@/lib/utils';
import type { MoveQuality } from '@/types/chess';
import { Sparkles, Zap, Star, BookOpen, AlertTriangle, AlertCircle, CheckCircle2, Trophy, Lock } from 'lucide-react';

interface MoveQualityBadgeProps {
  quality: MoveQuality;
  size?: 'sm' | 'md' | 'lg';
  showLabel?: boolean;
}

// WintrCat classification config
const qualityConfig: Record<MoveQuality, { 
  label: string; 
  icon: React.ElementType; 
  className: string;
  description: string;
}> = {
  brilliant: {
    label: 'Brilliant',
    icon: Sparkles,
    className: 'move-brilliant',
    description: 'A creative sacrifice that wins material or leads to checkmate'
  },
  great: {
    label: 'Great',
    icon: Trophy,
    className: 'move-great',
    description: 'The only move that punishes opponent\'s mistake'
  },
  best: {
    label: 'Best',
    icon: CheckCircle2,
    className: 'move-best',
    description: 'The best move in the position'
  },
  excellent: {
    label: 'Excellent',
    icon: Zap,
    className: 'move-excellent',
    description: 'An excellent move, nearly as good as the best'
  },
  good: {
    label: 'Good',
    icon: Star,
    className: 'move-good',
    description: 'A solid move that maintains advantage'
  },
  book: {
    label: 'Book',
    icon: BookOpen,
    className: 'move-book',
    description: 'A known theoretical opening move'
  },
  forced: {
    label: 'Forced',
    icon: Lock,
    className: 'move-forced',
    description: 'The only legal move in this position'
  },
  inaccuracy: {
    label: 'Inaccuracy',
    icon: AlertTriangle,
    className: 'move-inaccuracy',
    description: 'A small mistake that gives away some advantage'
  },
  mistake: {
    label: 'Mistake',
    icon: AlertCircle,
    className: 'move-mistake',
    description: 'A significant error that changes the evaluation'
  },
  blunder: {
    label: 'Blunder',
    icon: AlertCircle,
    className: 'move-blunder',
    description: 'A serious mistake that loses material or the game'
  },
  neutral: {
    label: '',
    icon: () => null,
    className: '',
    description: ''
  }
};

export function MoveQualityBadge({ quality, size = 'md', showLabel = true }: MoveQualityBadgeProps) {
  if (quality === 'neutral') return null;
  
  const config = qualityConfig[quality];
  const Icon = config.icon;
  
  const sizeClasses = {
    sm: 'text-xs px-1.5 py-0.5',
    md: 'text-sm px-2 py-1',
    lg: 'text-base px-3 py-1.5',
  };

  const iconSizes = {
    sm: 'w-3 h-3',
    md: 'w-4 h-4',
    lg: 'w-5 h-5',
  };

  return (
    <span 
      className={cn(
        'inline-flex items-center gap-1 rounded-full font-medium',
        config.className,
        sizeClasses[size]
      )}
      title={config.description}
    >
      <Icon className={iconSizes[size]} />
      {showLabel && <span>{config.label}</span>}
    </span>
  );
}
