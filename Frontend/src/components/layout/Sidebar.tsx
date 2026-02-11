import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Badge } from '@/components/ui/badge';
import { 
  Home, 
  Search, 
  Trophy, 
  Puzzle, 
  BookOpen, 
  BarChart3, 
  Clock, 
  Star,
  ChevronRight,
  X
} from 'lucide-react';
import { cn } from '@/lib/utils';

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
  recentGames?: { id: string | number; opponent: string; result: string; date: string }[];
  onGameSelect?: (gameId: number) => void;
}

const navItems = [
  { icon: Home, label: 'Dashboard', href: '/', active: false },
  { icon: Search, label: 'Analyze Game', href: '/analyze', active: true },
  { icon: Trophy, label: 'My Games', href: '/games', active: false, badge: '147' },
  { icon: Puzzle, label: 'Puzzles', href: '/puzzles', active: false },
  { icon: BookOpen, label: 'Openings', href: '/openings', active: false },
  { icon: BarChart3, label: 'Statistics', href: '/stats', active: false },
];

export function Sidebar({ isOpen, onClose, recentGames = [], onGameSelect }: SidebarProps) {
  return (
    <>
      {/* Mobile overlay */}
      {isOpen && (
        <div 
          className="fixed inset-0 bg-background/80 backdrop-blur-sm z-40 md:hidden"
          onClick={onClose}
        />
      )}
      
      {/* Sidebar */}
      <aside className={cn(
        'fixed top-16 left-0 z-40 h-[calc(100vh-4rem)] w-64 bg-sidebar border-r border-sidebar-border transition-transform duration-300 ease-in-out',
        'md:translate-x-0',
        isOpen ? 'translate-x-0' : '-translate-x-full'
      )}>
        <div className="flex flex-col h-full">
          {/* Mobile close button */}
          <div className="flex items-center justify-between p-4 md:hidden">
            <span className="font-semibold">Menu</span>
            <Button variant="ghost" size="icon-sm" onClick={onClose}>
              <X className="w-4 h-4" />
            </Button>
          </div>
          
          {/* Navigation */}
          <nav className="p-3 space-y-1">
            {navItems.map((item) => (
              <Button
                key={item.label}
                variant={item.active ? 'secondary' : 'ghost'}
                className={cn(
                  'w-full justify-start gap-3',
                  item.active && 'bg-sidebar-accent text-sidebar-accent-foreground'
                )}
              >
                <item.icon className="w-4 h-4" />
                <span className="flex-1 text-left">{item.label}</span>
                {item.badge && (
                  <Badge variant="secondary" className="text-[10px] px-1.5 py-0">
                    {item.badge}
                  </Badge>
                )}
              </Button>
            ))}
          </nav>
          
          <div className="border-t border-sidebar-border mx-4 my-2" />
          
          {/* Recent Games */}
          <div className="flex-1 overflow-hidden">
            <div className="px-4 py-2 flex items-center justify-between">
              <span className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                Recent Games
              </span>
              <Clock className="w-3 h-3 text-muted-foreground" />
            </div>
            
            <ScrollArea className="h-full px-3">
              <div className="space-y-1 pb-20">
                {recentGames.length > 0 ? recentGames.map((game) => (
                  <Button
                    key={game.id}
                    variant="ghost"
                    className="w-full justify-start h-auto py-2 px-3 text-left hover:bg-accent cursor-pointer"
                    onClick={(e) => {
                      e.preventDefault();
                      e.stopPropagation();
                      
                      if (!onGameSelect) {
                        console.warn("onGameSelect not available");
                        return;
                      }
                      
                      if (!game || !game.id) {
                        console.warn("Invalid game data:", game);
                        return;
                      }
                      
                      try {
                        const gameId = typeof game.id === 'number' 
                          ? game.id 
                          : (typeof game.id === 'string' ? parseInt(game.id, 10) : null);
                          
                        if (gameId !== null && !isNaN(gameId) && gameId > 0) {
                          console.log("Selecting game:", gameId);
                          onGameSelect(gameId);
                          // Don't close immediately - let the async operation start
                          setTimeout(() => onClose(), 100);
                        } else {
                          console.error("Invalid gameId:", gameId, "from game.id:", game.id);
                        }
                      } catch (err) {
                        console.error("Error selecting game:", err);
                        alert("Error loading game. Check console for details.");
                      }
                    }}
                  >
                    <div className="flex items-center gap-3 w-full">
                      <div className={cn(
                        'w-2 h-2 rounded-full',
                        game.result === 'W' || game.result === 'win' ? 'bg-move-great' : 
                        game.result === 'L' || game.result === 'loss' ? 'bg-move-blunder' : 'bg-muted-foreground'
                      )} />
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium truncate">vs {game.opponent}</p>
                        <p className="text-xs text-muted-foreground">
                          {new Date(game.date).toLocaleDateString()}
                        </p>
                      </div>
                      <ChevronRight className="w-4 h-4 text-muted-foreground" />
                    </div>
                  </Button>
                )) : (
                  <div className="text-center py-8 text-muted-foreground">
                    <Star className="w-8 h-8 mx-auto mb-2 opacity-50" />
                    <p className="text-xs">No recent games</p>
                  </div>
                )}
              </div>
            </ScrollArea>
          </div>
        </div>
      </aside>
    </>
  );
}
