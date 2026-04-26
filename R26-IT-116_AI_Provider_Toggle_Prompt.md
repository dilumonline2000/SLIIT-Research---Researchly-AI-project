# 🔀 AI PROVIDER TOGGLE — FULL IMPLEMENTATION PROMPT
## R26-IT-116 | Gemini API ⟷ Local Trained Models
### Claude Code / Cursor AI — Complete Build Guide

---

## 📌 CONTEXT — READ FIRST

You are working on the existing **R26-IT-116 monorepo** (Next.js 14 App Router +
TypeScript + Tailwind + shadcn/ui + Express.js API Gateway + Supabase + Python
FastAPI ML services).

**Current state:**
- ✅ Gemini API already connected and working (frontend, `NEXT_PUBLIC_GEMINI_API_KEY`)
- ✅ General chat + 4 module-specific chats already implemented
- ✅ Local ML models being trained (SBERT, SciBERT, BART, Citation NER, etc.)
- ❌ No way to switch between Gemini and local models

**What to build:**
A **global AI Provider Toggle** — one switch that tells the entire platform
whether to use **Google Gemini API** or **your own trained local models** for
every AI response across all 5 chat surfaces.

```
Toggle ON  (Gemini) → All chats use Google Gemini API
Toggle OFF (Local)  → All chats use your trained SBERT/SciBERT/BART/RAG models
```

---

## 🗂️ FILES TO CREATE AND UPDATE

### New files to CREATE:
```
apps/web/src/
├── stores/
│   └── aiProviderStore.ts                   # Global toggle state (Zustand + persist)
├── lib/
│   ├── ai-router.ts                         # Abstraction layer — routes to Gemini or Local
│   └── local-models.ts                      # Local model API call helpers
├── hooks/
│   └── useAIProvider.ts                     # Hook used by every chat component
└── components/
    └── shared/
        ├── AIProviderToggle.tsx             # The toggle UI component (full)
        ├── AIProviderBadge.tsx              # Compact badge showing current mode
        └── ModelStatusGrid.tsx              # Grid showing which local models are ready

services/paper-chat/app/
├── routers/
│   └── local_inference.py                   # NEW FastAPI router for local model inference
└── services/
    └── model_registry.py                    # Tracks which models are loaded and ready
```

### Existing files to UPDATE:
```
apps/web/src/
├── lib/
│   └── gemini.ts                            # Keep as-is, used only when provider='gemini'
├── components/
│   ├── chat/
│   │   └── GeneralChatWindow.tsx            # Replace direct Gemini call → useAIProvider
│   ├── module1/
│   │   └── IntegrityPaperChat.tsx           # Replace direct Gemini call → useAIProvider
│   ├── module2/
│   │   └── SupervisorChat.tsx               # Replace direct Gemini call → useAIProvider
│   ├── module3/
│   │   └── DataInsightChat.tsx              # Replace direct Gemini call → useAIProvider
│   └── module4/
│       └── AnalyticsChat.tsx                # Replace direct Gemini call → useAIProvider
├── app/
│   └── (dashboard)/
│       ├── layout.tsx                       # Add AIProviderToggle to header/navbar
│       └── settings/
│           └── page.tsx                     # Add AI Provider Settings section
└── components/shared/
    └── Navbar.tsx                           # Add AIProviderBadge to navbar

apps/api-gateway/src/
└── routes/
    └── ai-provider.routes.ts                # New Express routes proxying to Python

services/paper-chat/app/
└── main.py                                  # Register local_inference router
```

---

## ⚙️ STEP 1 — GLOBAL STATE: aiProviderStore.ts

```typescript
// apps/web/src/stores/aiProviderStore.ts
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export type AIProvider = 'gemini' | 'local';

interface ModelStatus {
  loaded: boolean;
  version: string;
  description: string;
}

interface AIProviderState {
  provider: AIProvider;
  isLocalAvailable: boolean;
  isChecking: boolean;
  modelStatuses: Record<string, ModelStatus>;

  setProvider: (p: AIProvider) => void;
  toggleProvider: () => void;
  checkLocalAvailability: () => Promise<void>;
}

export const useAIProviderStore = create<AIProviderState>()(
  persist(
    (set, get) => ({
      provider: 'gemini',
      isLocalAvailable: false,
      isChecking: false,
      modelStatuses: {},

      setProvider: (provider) => set({ provider }),

      toggleProvider: () => {
        const { provider, isLocalAvailable } = get();
        if (provider === 'gemini' && !isLocalAvailable) {
          // Block switch — local models not ready
          console.warn('Local models not ready. Train models first.');
          return;
        }
        set({ provider: provider === 'gemini' ? 'local' : 'gemini' });
      },

      checkLocalAvailability: async () => {
        set({ isChecking: true });
        try {
          const res = await fetch('/api/v1/ai/local/health', {
            signal: AbortSignal.timeout(5000),
          });
          if (!res.ok) throw new Error('Health check failed');
          const data = await res.json();
          set({
            isLocalAvailable: data.available,
            modelStatuses: data.models ?? {},
            isChecking: false,
          });
        } catch {
          set({ isLocalAvailable: false, isChecking: false });
        }
      },
    }),
    {
      name: 'r26-ai-provider',           // localStorage key
      partialize: (s) => ({ provider: s.provider }),  // Only persist provider choice
    }
  )
);
```

---

## ⚙️ STEP 2 — ABSTRACTION LAYER: ai-router.ts

```typescript
// apps/web/src/lib/ai-router.ts
//
// This is the SINGLE entry point for ALL AI calls across the platform.
// Components never call Gemini or local model APIs directly.
// They always go through this router.

import {
  startGeneralChatSession,
  startModuleChatSession,
  sendMessageStreaming,
} from './gemini';
import { useAIProviderStore, type AIProvider } from '@/stores/aiProviderStore';

// ─── Types ────────────────────────────────────────────────────────

export type ChatMode =
  | 'general'
  | 'integrity'
  | 'collaboration'
  | 'dataManagement'
  | 'analytics';

export interface AISession {
  sendMessage: (
    message: string,
    onChunk: (chunk: string) => void,
    onDone: (fullText: string) => void,
    onError: (error: string) => void
  ) => Promise<void>;
  provider: AIProvider;
  mode: ChatMode;
}

// ─── Session Factory ──────────────────────────────────────────────

export async function createAISession(
  mode: ChatMode,
  contextData?: string
): Promise<AISession> {
  const { provider } = useAIProviderStore.getState();

  if (provider === 'gemini') {
    return createGeminiSession(mode, contextData);
  } else {
    return createLocalSession(mode, contextData);
  }
}

// ─── Gemini Session ───────────────────────────────────────────────

async function createGeminiSession(
  mode: ChatMode,
  contextData?: string
): Promise<AISession> {
  const chat =
    mode === 'general'
      ? await startGeneralChatSession()
      : await startModuleChatSession(mode as any, contextData);

  return {
    provider: 'gemini',
    mode,
    sendMessage: async (message, onChunk, onDone, onError) => {
      try {
        let fullText = '';
        await sendMessageStreaming(
          chat,
          message,
          (chunk) => {
            fullText += chunk;
            onChunk(chunk);
          },
          () => onDone(fullText)
        );
      } catch (err: any) {
        onError(err?.message ?? 'Gemini API error');
      }
    },
  };
}

// ─── Local Model Session ──────────────────────────────────────────

async function createLocalSession(
  mode: ChatMode,
  contextData?: string
): Promise<AISession> {
  // Local sessions are stateless (no persistent chat history like Gemini)
  // Each message is a fresh request carrying the full context
  const capturedContext = contextData;

  return {
    provider: 'local',
    mode,
    sendMessage: async (message, onChunk, onDone, onError) => {
      try {
        const response = await fetch('/api/v1/ai/local/chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            mode,
            message,
            context: capturedContext ?? null,
          }),
        });

        if (!response.ok) {
          throw new Error(`Local model error: ${response.status}`);
        }

        // Read SSE stream
        const reader = response.body?.getReader();
        const decoder = new TextDecoder();
        if (!reader) throw new Error('No response body');

        let fullText = '';
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          const raw = decoder.decode(value);
          const lines = raw.split('\n');

          for (const line of lines) {
            if (!line.startsWith('data: ')) continue;
            const payload = line.slice(6).trim();
            if (payload === '[DONE]') {
              onDone(fullText);
              return;
            }
            fullText += payload;
            onChunk(payload);
          }
        }
        onDone(fullText);
      } catch (err: any) {
        onError(err?.message ?? 'Local model error');
      }
    },
  };
}
```

---

## ⚙️ STEP 3 — HOOK: useAIProvider.ts

```typescript
// apps/web/src/hooks/useAIProvider.ts
//
// Drop-in replacement for any direct Gemini usage.
// Every chat component uses this hook.

'use client';
import { useState, useRef, useCallback, useEffect } from 'react';
import { createAISession, type AISession, type ChatMode } from '@/lib/ai-router';
import { useAIProviderStore } from '@/stores/aiProviderStore';

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  provider: 'gemini' | 'local';
  timestamp: Date;
  isStreaming?: boolean;
  isError?: boolean;
}

export function useAIProvider(mode: ChatMode) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [streamingContent, setStreamingContent] = useState('');
  const sessionRef = useRef<AISession | null>(null);
  const { provider } = useAIProviderStore();

  // Re-init session whenever provider changes
  useEffect(() => {
    sessionRef.current = null;
  }, [provider]);

  const initSession = useCallback(async (contextData?: string) => {
    sessionRef.current = await createAISession(mode, contextData);
  }, [mode, provider]);

  const sendMessage = useCallback(
    async (userText: string, contextData?: string) => {
      if (!sessionRef.current) {
        await initSession(contextData);
      }

      // Add user message immediately
      const userMsg: Message = {
        id: crypto.randomUUID(),
        role: 'user',
        content: userText,
        provider,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, userMsg]);
      setIsLoading(true);
      setStreamingContent('');

      // Placeholder for streaming assistant message
      const assistantId = crypto.randomUUID();
      setMessages((prev) => [
        ...prev,
        {
          id: assistantId,
          role: 'assistant',
          content: '',
          provider,
          timestamp: new Date(),
          isStreaming: true,
        },
      ]);

      await sessionRef.current!.sendMessage(
        userText,
        // onChunk
        (chunk) => {
          setStreamingContent((prev) => {
            const next = prev + chunk;
            // Keep placeholder message in sync
            setMessages((msgs) =>
              msgs.map((m) =>
                m.id === assistantId ? { ...m, content: next } : m
              )
            );
            return next;
          });
        },
        // onDone
        (fullText) => {
          setMessages((msgs) =>
            msgs.map((m) =>
              m.id === assistantId
                ? { ...m, content: fullText, isStreaming: false }
                : m
            )
          );
          setIsLoading(false);
          setStreamingContent('');
        },
        // onError
        (error) => {
          setMessages((msgs) =>
            msgs.map((m) =>
              m.id === assistantId
                ? {
                    ...m,
                    content: `⚠️ ${error}. ${
                      provider === 'local'
                        ? 'Try switching to Gemini mode.'
                        : 'Please try again.'
                    }`,
                    isStreaming: false,
                    isError: true,
                  }
                : m
            )
          );
          setIsLoading(false);
          setStreamingContent('');
        }
      );
    },
    [mode, provider, initSession]
  );

  const clearMessages = useCallback(() => {
    setMessages([]);
    sessionRef.current = null;
  }, []);

  return {
    messages,
    isLoading,
    streamingContent,
    currentProvider: provider,
    sendMessage,
    initSession,
    clearMessages,
  };
}
```

---

## 🎨 STEP 4 — UI: AIProviderToggle.tsx

```tsx
// apps/web/src/components/shared/AIProviderToggle.tsx
'use client';

import { useEffect } from 'react';
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
import {
  Cpu,
  Sparkles,
  AlertCircle,
  Loader2,
  RefreshCw,
} from 'lucide-react';
import { cn } from '@/lib/utils';

interface AIProviderToggleProps {
  compact?: boolean;   // Compact mode for navbar
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

  // Check local model availability on mount
  useEffect(() => {
    checkLocalAvailability();
  }, []);

  const handleToggle = () => {
    if (isGemini && !isLocalAvailable) return; // Block
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
            <p className="text-xs text-muted-foreground mt-0.5">
              Click to switch AI provider
            </p>
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>
    );
  }

  // Full toggle (for settings page / header)
  return (
    <TooltipProvider>
      <div className="flex items-center gap-4 p-3 rounded-xl border bg-card shadow-sm">

        {/* Local Models Side */}
        <div
          className={cn(
            'flex items-center gap-2 transition-opacity',
            !isGemini ? 'opacity-100' : 'opacity-40'
          )}
        >
          <Cpu className={cn('w-4 h-4', !isGemini ? 'text-green-500' : 'text-muted-foreground')} />
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
                <p className="text-xs mt-1">
                  Train your models first. Check the Model Status section below.
                </p>
              </TooltipContent>
            </Tooltip>
          )}
        </div>

        {/* Toggle Switch */}
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

        {/* Gemini Side */}
        <div
          className={cn(
            'flex items-center gap-2 transition-opacity',
            isGemini ? 'opacity-100' : 'opacity-40'
          )}
        >
          <Sparkles className={cn('w-4 h-4', isGemini ? 'text-blue-500' : 'text-muted-foreground')} />
          <span className="text-sm font-medium">Gemini</span>
          <span className="w-2 h-2 rounded-full bg-blue-500" />
        </div>

        {/* Active Badge */}
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

        {/* Refresh local status button */}
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
```

---

## 🎨 STEP 5 — UI: ModelStatusGrid.tsx

```tsx
// apps/web/src/components/shared/ModelStatusGrid.tsx
'use client';

import { useAIProviderStore } from '@/stores/aiProviderStore';
import { Badge } from '@/components/ui/badge';
import { CheckCircle2, XCircle, AlertCircle } from 'lucide-react';
import { cn } from '@/lib/utils';

const MODEL_LABELS: Record<string, { label: string; module: string }> = {
  sbert:              { label: 'SBERT Embeddings',       module: 'Shared'   },
  scibert_classifier: { label: 'SciBERT Classifier',     module: 'Module 3' },
  rag_engine:         { label: 'RAG Engine',             module: 'Shared'   },
  citation_ner:       { label: 'Citation NER',           module: 'Module 1' },
  summarizer:         { label: 'BART Summarizer',        module: 'Module 3' },
  sentiment_bert:     { label: 'Sentiment BERT',         module: 'Module 2' },
  trend_forecaster:   { label: 'ARIMA + Prophet',        module: 'Module 4' },
  quality_scorer:     { label: 'Quality Scorer',         module: 'Module 4' },
  success_predictor:  { label: 'XGBoost Predictor',      module: 'Module 4' },
  proposal_llm:       { label: 'Proposal Generator LLM', module: 'Module 1' },
};

const MODULE_COLORS: Record<string, string> = {
  'Shared':   'bg-gray-100 text-gray-600',
  'Module 1': 'bg-blue-100 text-blue-700',
  'Module 2': 'bg-green-100 text-green-700',
  'Module 3': 'bg-orange-100 text-orange-700',
  'Module 4': 'bg-purple-100 text-purple-700',
};

export function ModelStatusGrid() {
  const { modelStatuses, isChecking } = useAIProviderStore();

  const totalModels = Object.keys(MODEL_LABELS).length;
  const loadedCount = Object.entries(modelStatuses).filter(
    ([, s]) => s.loaded
  ).length;

  return (
    <div className="space-y-3">
      {/* Summary bar */}
      <div className="flex items-center justify-between text-sm">
        <span className="text-muted-foreground">
          Local models ready: <strong>{loadedCount}/{totalModels}</strong>
        </span>
        <div className="w-32 h-2 bg-muted rounded-full overflow-hidden">
          <div
            className="h-full bg-green-500 rounded-full transition-all"
            style={{ width: `${(loadedCount / totalModels) * 100}%` }}
          />
        </div>
      </div>

      {/* Model grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
        {Object.entries(MODEL_LABELS).map(([key, { label, module }]) => {
          const status = modelStatuses[key];
          const isLoaded = status?.loaded ?? false;

          return (
            <div
              key={key}
              className={cn(
                'flex items-center gap-2.5 p-2.5 rounded-lg border text-sm',
                isLoaded ? 'border-green-200 bg-green-50/50' : 'border-gray-200 bg-gray-50/50'
              )}
            >
              {isLoaded ? (
                <CheckCircle2 className="w-4 h-4 text-green-500 shrink-0" />
              ) : (
                <XCircle className="w-4 h-4 text-gray-300 shrink-0" />
              )}

              <div className="flex-1 min-w-0">
                <p className={cn(
                  'font-medium truncate',
                  isLoaded ? 'text-gray-900' : 'text-gray-400'
                )}>
                  {label}
                </p>
                {status?.version && isLoaded && (
                  <p className="text-xs text-muted-foreground">{status.version}</p>
                )}
                {!isLoaded && (
                  <p className="text-xs text-muted-foreground">Not trained yet</p>
                )}
              </div>

              <Badge
                variant="secondary"
                className={cn('text-xs shrink-0', MODULE_COLORS[module])}
              >
                {module}
              </Badge>
            </div>
          );
        })}
      </div>

      {loadedCount === 0 && !isChecking && (
        <div className="flex items-start gap-2 p-3 rounded-lg bg-yellow-50 border border-yellow-200 text-sm text-yellow-800">
          <AlertCircle className="w-4 h-4 mt-0.5 shrink-0" />
          <div>
            <p className="font-medium">No local models trained yet</p>
            <p className="text-xs mt-0.5">
              Run the training pipeline to enable Local AI mode.
              Until then, Gemini API will be used.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
```

---

## ⚙️ STEP 6 — UPDATE: Dashboard Layout (Add Toggle to Navbar)

```tsx
// apps/web/src/app/(dashboard)/layout.tsx
// ADD the AIProviderToggle to the existing navbar/header

import { AIProviderToggle } from '@/components/shared/AIProviderToggle';

// Inside your existing navbar/header JSX, add:
<div className="flex items-center gap-3">
  {/* ... existing navbar items ... */}
  <AIProviderToggle compact={true} />     {/* Compact version for navbar */}
  {/* ... user menu, notifications, etc ... */}
</div>
```

---

## ⚙️ STEP 7 — UPDATE: Settings Page (Add AI Provider Section)

```tsx
// apps/web/src/app/(dashboard)/settings/page.tsx
// ADD this section to the existing settings page

import { AIProviderToggle } from '@/components/shared/AIProviderToggle';
import { ModelStatusGrid } from '@/components/shared/ModelStatusGrid';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Separator } from '@/components/ui/separator';

// Add this Card inside your settings page:
<Card>
  <CardHeader>
    <CardTitle className="flex items-center gap-2">
      🤖 AI Provider Settings
    </CardTitle>
    <CardDescription>
      Switch between Google Gemini API and your locally trained research models.
      This setting applies to all AI features across the platform.
    </CardDescription>
  </CardHeader>
  <CardContent className="space-y-6">

    {/* Main Toggle */}
    <AIProviderToggle />

    {/* Provider descriptions */}
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
      <div className="p-3 rounded-lg bg-blue-50 border border-blue-200 space-y-1">
        <p className="font-semibold text-blue-800 flex items-center gap-1.5">
          ⚡ Gemini API Mode
        </p>
        <ul className="text-blue-700 space-y-0.5 text-xs">
          <li>• Uses Google Gemini 1.5 Flash / Pro</li>
          <li>• Fast responses, handles any question</li>
          <li>• Requires internet connection</li>
          <li>• Uses your API key quota</li>
          <li>• Best for general questions</li>
        </ul>
      </div>
      <div className="p-3 rounded-lg bg-green-50 border border-green-200 space-y-1">
        <p className="font-semibold text-green-800 flex items-center gap-1.5">
          🧠 Local AI Mode
        </p>
        <ul className="text-green-700 space-y-0.5 text-xs">
          <li>• Uses your trained SBERT / SciBERT / BART models</li>
          <li>• Answers based on your research data</li>
          <li>• Works offline, no API cost</li>
          <li>• Improves as you upload more papers</li>
          <li>• Best for domain-specific research questions</li>
        </ul>
      </div>
    </div>

    <Separator />

    {/* Model Status */}
    <div className="space-y-3">
      <h3 className="text-sm font-semibold">Local Model Status</h3>
      <ModelStatusGrid />
    </div>

  </CardContent>
</Card>
```

---

## ⚙️ STEP 8 — UPDATE: All Chat Components

**Apply this pattern to every single chat component.**
Replace all direct Gemini calls with `useAIProvider`.

### Before (OLD pattern in every chat):
```tsx
// OLD — direct Gemini call
import { startModuleChatSession, sendMessageStreaming } from '@/lib/gemini';

const chat = await startModuleChatSession('integrity', paperText);
await sendMessageStreaming(chat, userMessage, onChunk, onDone);
```

### After (NEW pattern using the hook):
```tsx
// NEW — goes through ai-router automatically
import { useAIProvider } from '@/hooks/useAIProvider';
import { AIProviderToggle } from '@/components/shared/AIProviderToggle';

// Inside component:
const { messages, isLoading, sendMessage, initSession, currentProvider, clearMessages }
  = useAIProvider('integrity');   // ← mode matches the module

// On paper upload / context ready:
await initSession(paperText);

// On user sends message:
await sendMessage(userInput);

// In JSX — show provider badge so user knows which AI is answering:
<div className="flex items-center justify-between">
  <h3>Research Integrity Assistant</h3>
  <AIProviderToggle compact />
</div>
```

### Apply to these 5 files:
| File | Mode |
|------|------|
| `GeneralChatWindow.tsx` | `'general'` |
| `IntegrityPaperChat.tsx` | `'integrity'` |
| `SupervisorChat.tsx` | `'collaboration'` |
| `DataInsightChat.tsx` | `'dataManagement'` |
| `AnalyticsChat.tsx` | `'analytics'` |

---

## 🐍 STEP 9 — Python: model_registry.py

```python
# services/paper-chat/app/services/model_registry.py
"""
Central registry for all locally trained models.
Models register here after loading. Frontend queries this
to know if Local AI mode is available.
"""
from typing import Any, Dict

_registry: Dict[str, Any] = {}
_versions: Dict[str, str] = {}

MODEL_DESCRIPTIONS: Dict[str, str] = {
    "sbert":              "Sentence-BERT embeddings for semantic search",
    "scibert_classifier": "SciBERT multi-label topic classifier",
    "rag_engine":         "Retrieval-Augmented Generation over paper corpus",
    "citation_ner":       "spaCy NER for citation entity extraction",
    "summarizer":         "BART/T5 abstractive summarizer",
    "sentiment_bert":     "BERT aspect-based sentiment for feedback",
    "trend_forecaster":   "ARIMA + Prophet ensemble for trend prediction",
    "quality_scorer":     "Multi-dimensional research quality scorer",
    "success_predictor":  "XGBoost/RF project success predictor",
    "proposal_llm":       "LoRA fine-tuned LLM for proposal generation",
}

# Core models required for Local AI mode to be 'available'
CORE_MODELS = {"sbert", "rag_engine"}


def register(name: str, model: Any, version: str = "v1.0") -> None:
    """Call this after a model finishes loading."""
    _registry[name] = model
    _versions[name] = version
    print(f"[ModelRegistry] ✅ {name} registered (version: {version})")


def get(name: str) -> Any | None:
    """Retrieve a loaded model."""
    return _registry.get(name)


def is_loaded(name: str) -> bool:
    return name in _registry


def get_status() -> Dict[str, dict]:
    """Return status of all known models."""
    return {
        name: {
            "loaded": name in _registry,
            "version": _versions.get(name, "not trained"),
            "description": desc,
        }
        for name, desc in MODEL_DESCRIPTIONS.items()
    }


def is_local_available() -> bool:
    """True only if all core models are loaded."""
    return all(is_loaded(m) for m in CORE_MODELS)
```

---

## 🐍 STEP 10 — Python: local_inference.py

```python
# services/paper-chat/app/routers/local_inference.py
import asyncio
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from app.services.model_registry import get_status, is_local_available, get

router = APIRouter(prefix="/local", tags=["local-inference"])


class ChatRequest(BaseModel):
    mode: str           # general | integrity | collaboration | dataManagement | analytics
    message: str
    context: str | None = None


# ─── Health Check ─────────────────────────────────────────────────

@router.get("/health")
async def health_check():
    """
    Frontend calls this on load to decide if Local AI toggle is available.
    Returns: { available: bool, models: { model_name: { loaded, version, description } } }
    """
    return {
        "available": is_local_available(),
        "models": get_status(),
    }


# ─── Chat Endpoint ────────────────────────────────────────────────

@router.post("/chat")
async def local_chat(request: ChatRequest):
    """
    Routes user message to the appropriate local model(s).
    Returns a Server-Sent Events (SSE) stream.
    """
    async def generate():
        try:
            response_text = await _route_to_model(
                mode=request.mode,
                message=request.message,
                context=request.context,
            )

            # Stream word-by-word for natural feel
            words = response_text.split(" ")
            for i, word in enumerate(words):
                chunk = word + (" " if i < len(words) - 1 else "")
                yield f"data: {chunk}\n\n"
                await asyncio.sleep(0.025)

            yield "data: [DONE]\n\n"

        except Exception as e:
            yield f"data: ⚠️ Local model error: {str(e)}\n\n"
            yield "data: [DONE]\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# ─── Mode Router ──────────────────────────────────────────────────

async def _route_to_model(mode: str, message: str, context: str | None) -> str:
    """
    Dispatches to the right local model based on chat mode and question content.
    Falls back to RAG engine for unhandled cases.
    """
    msg = message.lower()

    # ── GENERAL ───────────────────────────────────────────────────
    if mode == "general":
        return await _rag_query(message, context)

    # ── INTEGRITY (Module 1) ──────────────────────────────────────
    elif mode == "integrity":
        if any(w in msg for w in ["citation", "reference", "apa", "ieee", "format"]):
            return await _citation_answer(message, context)
        elif any(w in msg for w in ["gap", "missing", "novel", "contribution", "unexplored"]):
            return await _gap_analysis(message, context)
        elif any(w in msg for w in ["summarize", "summary", "what is this paper about"]):
            return await _summarize(context or message)
        elif any(w in msg for w in ["plagiarism", "similarity", "overlap"]):
            return await _plagiarism_check(message, context)
        else:
            return await _rag_query(message, context)

    # ── COLLABORATION (Module 2) ──────────────────────────────────
    elif mode == "collaboration":
        return await _supervisor_guidance(message, context)

    # ── DATA MANAGEMENT (Module 3) ────────────────────────────────
    elif mode == "dataManagement":
        if any(w in msg for w in ["summarize", "summary", "what is"]):
            return await _summarize(context or message)
        elif any(w in msg for w in ["topic", "category", "classify"]):
            return await _topic_classification(message, context)
        else:
            return await _rag_query(message, context)

    # ── ANALYTICS (Module 4) ──────────────────────────────────────
    elif mode == "analytics":
        if any(w in msg for w in ["trend", "forecast", "future", "predict topic"]):
            return await _trend_interpretation(message, context)
        elif any(w in msg for w in ["quality", "score", "improve", "rating"]):
            return await _quality_explanation(message, context)
        elif any(w in msg for w in ["risk", "success", "fail", "complete"]):
            return await _prediction_explanation(message, context)
        else:
            return await _rag_query(message, context)

    return (
        "I couldn't find a local model suitable for this question. "
        "Try switching to Gemini mode for general questions."
    )


# ─── Model Callers ────────────────────────────────────────────────
# Each function calls the appropriate loaded model from registry.
# If model not loaded, returns a helpful message.

async def _rag_query(question: str, context: str | None) -> str:
    rag = get("rag_engine")
    if not rag:
        return "RAG engine not ready. Please ensure papers are uploaded and indexed."
    return await rag.query(question, extra_context=context)

async def _citation_answer(question: str, context: str | None) -> str:
    ner = get("citation_ner")
    if not ner:
        return "Citation NER model not trained yet."
    return await ner.answer_question(question, context)

async def _gap_analysis(question: str, context: str | None) -> str:
    rag = get("rag_engine")
    if not rag:
        return "Gap analysis requires the RAG engine. Not ready yet."
    return await rag.analyze_gaps(question, context)

async def _summarize(text: str) -> str:
    summarizer = get("summarizer")
    if not summarizer:
        return "Summarization model not trained yet."
    return await summarizer.summarize(text[:4000])   # Truncate for safety

async def _plagiarism_check(question: str, context: str | None) -> str:
    rag = get("rag_engine")
    if not rag:
        return "Plagiarism analysis requires the RAG engine. Not ready yet."
    return await rag.check_similarity(question, context)

async def _supervisor_guidance(question: str, context: str | None) -> str:
    rag = get("rag_engine")
    if not rag:
        return "Supervisor guidance requires the RAG engine. Not ready yet."
    return await rag.supervisor_style_query(question, context)

async def _topic_classification(question: str, context: str | None) -> str:
    classifier = get("scibert_classifier")
    if not classifier:
        return "Topic classifier (SciBERT) not trained yet."
    topics = await classifier.classify(context or question)
    return f"Based on the content, the identified topics are: {', '.join(topics)}."

async def _trend_interpretation(question: str, context: str | None) -> str:
    forecaster = get("trend_forecaster")
    if not forecaster:
        return "Trend forecaster (ARIMA + Prophet) not trained yet."
    return await forecaster.interpret(question, context)

async def _quality_explanation(question: str, context: str | None) -> str:
    scorer = get("quality_scorer")
    if not scorer:
        return "Quality scorer not trained yet."
    return await scorer.explain(question, context)

async def _prediction_explanation(question: str, context: str | None) -> str:
    predictor = get("success_predictor")
    if not predictor:
        return "Success predictor (XGBoost) not trained yet."
    return await predictor.explain(question, context)
```

---

## ⚙️ STEP 11 — Express Gateway: New Routes

```typescript
// apps/api-gateway/src/routes/ai-provider.routes.ts
import { Router } from 'express';
import { authMiddleware } from '../middleware/auth';
import axios from 'axios';

const router = Router();
const LOCAL_SERVICE = process.env.PAPER_CHAT_SERVICE_URL ?? 'http://localhost:8005';

// Health check — no auth needed (called on app load)
router.get('/local/health', async (req, res) => {
  try {
    const { data } = await axios.get(`${LOCAL_SERVICE}/local/health`, {
      timeout: 4000,
    });
    res.json(data);
  } catch {
    res.json({ available: false, models: {}, error: 'Local service unreachable' });
  }
});

// Chat — requires auth, proxies SSE stream
router.post('/local/chat', authMiddleware, async (req, res) => {
  try {
    const response = await axios.post(
      `${LOCAL_SERVICE}/local/chat`,
      req.body,
      {
        responseType: 'stream',
        headers: { 'Content-Type': 'application/json' },
        timeout: 60000,
      }
    );

    res.setHeader('Content-Type', 'text/event-stream');
    res.setHeader('Cache-Control', 'no-cache');
    res.setHeader('X-Accel-Buffering', 'no');
    response.data.pipe(res);

  } catch (err: any) {
    res.status(500).json({ error: 'Local model inference failed' });
  }
});

export default router;
```

```typescript
// apps/api-gateway/src/routes/index.ts — ADD this line:
import aiProviderRoutes from './ai-provider.routes';
app.use('/api/v1/ai', aiProviderRoutes);
```

---

## ⚙️ STEP 12 — Register Router in Python main.py

```python
# services/paper-chat/app/main.py
# ADD these lines to the existing main.py:

from app.routers.local_inference import router as local_router

app.include_router(local_router, prefix="/local", tags=["local"])
```

---

## ⚙️ STEP 13 — Initialize App: Check Local Status on Load

```tsx
// apps/web/src/app/(dashboard)/layout.tsx
// Add this to check local model availability when dashboard loads:

'use client';
import { useEffect } from 'react';
import { useAIProviderStore } from '@/stores/aiProviderStore';

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const checkLocalAvailability = useAIProviderStore((s) => s.checkLocalAvailability);

  useEffect(() => {
    // Check if local models are ready when app loads
    checkLocalAvailability();
  }, []);

  return (
    // ... existing layout JSX
  );
}
```

---

## 📋 IMPLEMENTATION ORDER (Follow Exactly)

```
STEP 1   Create stores/aiProviderStore.ts
STEP 2   Create lib/ai-router.ts
STEP 3   Create hooks/useAIProvider.ts
STEP 4   Create components/shared/AIProviderToggle.tsx
STEP 5   Create components/shared/ModelStatusGrid.tsx
STEP 6   Update app/(dashboard)/layout.tsx — add toggle + check on load
STEP 7   Update app/(dashboard)/settings/page.tsx — add AI Provider section
STEP 8   Update GeneralChatWindow.tsx — use useAIProvider('general')
STEP 9   Update IntegrityPaperChat.tsx — use useAIProvider('integrity')
STEP 10  Update SupervisorChat.tsx — use useAIProvider('collaboration')
STEP 11  Update DataInsightChat.tsx — use useAIProvider('dataManagement')
STEP 12  Update AnalyticsChat.tsx — use useAIProvider('analytics')
STEP 13  Create services/paper-chat/app/services/model_registry.py
STEP 14  Create services/paper-chat/app/routers/local_inference.py
STEP 15  Update services/paper-chat/app/main.py — register router
STEP 16  Create apps/api-gateway/src/routes/ai-provider.routes.ts
STEP 17  Update apps/api-gateway/src/routes/index.ts — mount new routes
STEP 18  Test: Gemini ON → Gemini responds, badge shows "⚡ Gemini"
STEP 19  Test: Toggle to Local → badge shows "🧠 Local AI"
STEP 20  Test: If local models not trained → toggle blocked with tooltip warning
```

---

## ⚠️ CRITICAL RULES — DO NOT SKIP

```
1.  ONE toggle, GLOBAL effect — changing provider affects ALL 5 chat surfaces
2.  Provider persists in localStorage — user's choice saved across sessions
3.  Local mode BLOCKED until CORE_MODELS (sbert + rag_engine) are loaded
4.  Provider badge visible in EVERY chat — user always knows which AI is active
5.  Session resets on provider switch — call clearMessages() when toggle changes
6.  Health check on app load — always know current local model status
7.  Local inference endpoint returns SSE — same streaming UX as Gemini
8.  If local model fails → show error in chat, do NOT silently fall back to Gemini
9.  No Gemini API key needed in local mode — guard against accidental API calls
10. Each local model caller checks registry first — graceful "not trained yet" message
11. model_registry.py is the single source of truth for which models are ready
12. Express gateway proxies SSE correctly — do not buffer the stream response
```

---

## 🧪 TEST CHECKLIST

```
□ Toggle ON  (Gemini): All 5 chats use Gemini, badge shows "⚡ Gemini"
□ Toggle OFF (Local):  All 5 chats use local models, badge shows "🧠 Local AI"
□ Local mode blocked when no models trained (tooltip shown)
□ Health check returns correct model statuses
□ ModelStatusGrid shows ✅ / ✗ for each model correctly
□ Settings page shows full toggle + descriptions + model grid
□ Navbar shows compact toggle badge
□ Provider choice persists after page refresh (localStorage)
□ Switching provider resets chat messages (fresh session)
□ SSE streaming works in local mode (words appear gradually)
□ Error state shown in chat if local model fails (not silent)
□ Both modes work for all 5 chat surfaces
```
