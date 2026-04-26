'use client';

import { useEffect } from 'react';
import { toast } from 'sonner';
import { useAIProviderStore } from '@/stores/aiProviderStore';
import { Switch } from '@/components/ui/switch';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import { Cpu, Sparkles, AlertCircle, Loader2, RefreshCw } from 'lucide-react';
import { cn } from '@/lib/utils';

interface AIProviderToggleProps {
  compact?: boolean;
}

export function AIProviderToggle({ compact = false }: AIProviderToggleProps) {
  const {
    provider,
    isLocalAvailable,
    isChecking,
    modelStatuses,
    toggleProvider,
    checkLocalAvailability,
  } = useAIProviderStore();

  const isGemini = provider === 'gemini';

  useEffect(() => {
    console.log('[AIProviderToggle] Mounted, compact:', compact);
    checkLocalAvailability();
  }, [checkLocalAvailability]);

  const handleToggle = () => {
    console.log('[handleToggle] Clicked! isGemini:', isGemini, 'isLocalAvailable:', isLocalAvailable);

    // Warn if switching to local without trained models
    if (isGemini && !isLocalAvailable) {
      toast.warning('Local models not trained yet', {
        description: 'Train your ML models first to use Local AI mode. For now, Gemini API is available.',
      });
      return;
    }

    toggleProvider();
  };

  if (compact) {
    return (
      <TooltipProvider>
        <Tooltip>
          <TooltipTrigger asChild>
            <button
              onClick={handleToggle}
              className={cn(
                'flex items-center gap-1.5 px-2 py-1 rounded-md text-xs font-medium transition-colors',
                isGemini
                  ? 'bg-blue-50 text-blue-700 hover:bg-blue-100 border border-blue-200'
                  : 'bg-green-50 text-green-700 hover:bg-green-100 border border-green-200'
              )}
            >
              {isGemini ? (
                <Sparkles className="w-3 h-3" />
              ) : (
                <Cpu className="w-3 h-3" />
              )}
              {isGemini ? 'Gemini' : 'Local AI'}
            </button>
          </TooltipTrigger>
          <TooltipContent side="bottom">
            <p className="font-medium">
              {isGemini ? '⚡ Using Google Gemini API' : '🧠 Using Local Trained Models'}
            </p>
            <p className="text-xs text-muted-foreground mt-0.5">Click to switch AI provider</p>
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>
    );
  }

  return (
    <TooltipProvider>
      <div className="flex items-center gap-4 p-3 rounded-xl border bg-card shadow-sm">
        <div
          className={cn(
            'flex items-center gap-2 transition-opacity',
            !isGemini ? 'opacity-100' : 'opacity-40'
          )}
        >
          <Cpu
            className={cn('w-4 h-4', !isGemini ? 'text-green-500' : 'text-muted-foreground')}
          />
          <span className="text-sm font-medium">Local AI</span>
          {isChecking ? (
            <Loader2 className="w-3 h-3 animate-spin text-muted-foreground" />
          ) : isLocalAvailable ? (
            <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
          ) : (
            <Tooltip>
              <TooltipTrigger>
                <AlertCircle className="w-3.5 h-3.5 text-yellow-500" />
              </TooltipTrigger>
              <TooltipContent className="max-w-[200px]">
                <p className="font-medium">Local models not ready</p>
                <p className="text-xs mt-1">Train your models first. Check the Model Status section below.</p>
              </TooltipContent>
            </Tooltip>
          )}
        </div>

        <Tooltip>
          <TooltipTrigger asChild>
            <div className="relative">
              <Switch
                checked={isGemini}
                onCheckedChange={handleToggle}
                disabled={isChecking}
                className={cn(
                  'data-[state=checked]:bg-blue-500',
                  'data-[state=unchecked]:bg-green-500',
                  isGemini && !isLocalAvailable ? 'cursor-not-allowed' : 'cursor-pointer'
                )}
              />
            </div>
          </TooltipTrigger>
          <TooltipContent>
            {isGemini
              ? isLocalAvailable
                ? 'Switch to Local AI'
                : 'Train models first to use Local AI'
              : 'Switch to Gemini API'}
          </TooltipContent>
        </Tooltip>

        <div
          className={cn(
            'flex items-center gap-2 transition-opacity',
            isGemini ? 'opacity-100' : 'opacity-40'
          )}
        >
          <Sparkles
            className={cn('w-4 h-4', isGemini ? 'text-blue-500' : 'text-muted-foreground')}
          />
          <span className="text-sm font-medium">Gemini</span>
          <span className="w-2 h-2 rounded-full bg-blue-500" />
        </div>

        <Badge
          className={cn(
            'ml-2 text-xs font-semibold',
            isGemini
              ? 'bg-blue-100 text-blue-700 border-blue-200'
              : 'bg-green-100 text-green-700 border-green-200'
          )}
          variant="outline"
        >
          {isGemini ? '⚡ Active: Gemini' : '🧠 Active: Local AI'}
        </Badge>

        <Tooltip>
          <TooltipTrigger asChild>
            <Button
              variant="ghost"
              size="icon"
              className="w-6 h-6 ml-1"
              onClick={checkLocalAvailability}
              disabled={isChecking}
            >
              <RefreshCw className={cn('w-3 h-3', isChecking && 'animate-spin')} />
            </Button>
          </TooltipTrigger>
          <TooltipContent>Refresh local model status</TooltipContent>
        </Tooltip>
      </div>
    </TooltipProvider>
  );
}
