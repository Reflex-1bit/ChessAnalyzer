import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Crown, Settings, User, Bell, Menu } from 'lucide-react';
import { useState } from 'react';

interface HeaderProps {
  username?: string;
  onMenuClick?: () => void;
}

export function Header({ username = 'Guest', onMenuClick }: HeaderProps) {
  return (
    <header className="sticky top-0 z-50 w-full border-b border-border/50 bg-background/80 backdrop-blur-xl">
      <div className="container flex h-16 items-center justify-between px-4">
        {/* Left: Logo & Nav */}
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" className="md:hidden" onClick={onMenuClick}>
            <Menu className="w-5 h-5" />
          </Button>
          
          <a href="/" className="flex items-center gap-2">
            <div className="relative">
              <Crown className="w-8 h-8 text-primary" />
              <div className="absolute inset-0 bg-primary/20 blur-lg rounded-full" />
            </div>
            <span className="font-bold text-xl hidden sm:block">
              Chess<span className="text-primary">Mind</span>
            </span>
          </a>
          
          <nav className="hidden md:flex items-center gap-1 ml-6">
            <Button variant="ghost" size="sm" className="text-muted-foreground hover:text-foreground">
              Dashboard
            </Button>
            <Button variant="ghost" size="sm" className="text-foreground">
              Analysis
            </Button>
            <Button variant="ghost" size="sm" className="text-muted-foreground hover:text-foreground">
              Puzzles
            </Button>
            <Button variant="ghost" size="sm" className="text-muted-foreground hover:text-foreground">
              Openings
            </Button>
          </nav>
        </div>

        {/* Right: User & Actions */}
        <div className="flex items-center gap-2">
          <Button variant="ghost" size="icon-sm" className="hidden sm:flex">
            <Bell className="w-4 h-4" />
          </Button>
          
          <Button variant="ghost" size="icon-sm">
            <Settings className="w-4 h-4" />
          </Button>
          
          <div className="w-px h-6 bg-border mx-1 hidden sm:block" />
          
          <Button variant="glass" size="sm" className="gap-2">
            <User className="w-4 h-4" />
            <span className="hidden sm:inline">{username}</span>
            <Badge variant="secondary" className="text-[10px] px-1.5 py-0 hidden sm:flex">
              1523
            </Badge>
          </Button>
        </div>
      </div>
    </header>
  );
}
