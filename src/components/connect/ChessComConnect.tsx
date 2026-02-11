import { useState } from 'react';
import type React from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Loader2, Link2, CheckCircle, ExternalLink } from 'lucide-react';

interface ChessComConnectProps {
  onConnect: (username: string) => Promise<void>;
  isConnected?: boolean;
  connectedUsername?: string;
  isLoading?: boolean;
}

export function ChessComConnect({ onConnect, isConnected, connectedUsername, isLoading: externalLoading }: ChessComConnectProps) {
  const [username, setUsername] = useState('');
  const [internalLoading, setInternalLoading] = useState(false);
  const [error, setError] = useState('');
  
  const isLoading = externalLoading || internalLoading;
  
  const handleConnect = async (e?: React.MouseEvent) => {
    e?.preventDefault();
    e?.stopPropagation();
    
    console.log("Button clicked, username:", username);
    
    if (!username.trim()) {
      setError('Please enter your Chess.com username');
      return;
    }
    
    setInternalLoading(true);
    setError('');
    
    try {
      console.log("Calling onConnect with:", username.trim());
      await onConnect(username.trim());
      console.log("onConnect completed");
    } catch (err: any) {
      console.error("onConnect error:", err);
      setError(err.message || 'Failed to connect. Please check your username.');
    } finally {
      setInternalLoading(false);
    }
  };

  if (isConnected && connectedUsername) {
    return (
      <Card className="glass-card border-move-great/30">
        <CardContent className="flex items-center justify-between p-4">
          <div className="flex items-center gap-3">
            <CheckCircle className="w-5 h-5 text-move-great" />
            <div>
              <p className="font-medium text-sm">Connected to Chess.com</p>
              <p className="text-xs text-muted-foreground">{connectedUsername}</p>
            </div>
          </div>
          <Badge variant="secondary" className="bg-move-great/10 text-move-great border-move-great/20">
            Synced
          </Badge>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="glass-card">
      <CardHeader className="pb-3">
        <CardTitle className="text-lg flex items-center gap-2">
          <Link2 className="w-5 h-5 text-primary" />
          Connect Chess.com
        </CardTitle>
        <CardDescription>
          Import your games for AI-powered analysis
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="username" className="text-sm">Chess.com Username</Label>
          <div className="flex gap-2">
            <Input
              id="username"
              placeholder="e.g., magnuscarlsen"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  e.preventDefault();
                  handleConnect();
                }
              }}
              className="bg-secondary/50"
            />
            <Button 
              onClick={handleConnect} 
              disabled={isLoading || !username.trim()}
              type="button"
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin mr-2" />
                  Loading...
                </>
              ) : (
                'Connect'
              )}
            </Button>
          </div>
          {error && <p className="text-xs text-destructive">{error}</p>}
        </div>
        
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          <ExternalLink className="w-3 h-3" />
          <span>We only access public game data</span>
        </div>
      </CardContent>
    </Card>
  );
}
