'use client';

import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export type AIProvider = 'gemini' | 'local';

export interface ModelStatus {
  loaded: boolean;
  version: string;
  description: string;
}

interface AIProviderState {
  provider: AIProvider;
  isLocalAvailable: boolean;
  isChecking: boolean;
  modelStatuses: Record<string, ModelStatus>;
  lastCheckedAt: number;
  setProvider: (p: AIProvider) => void;
  toggleProvider: () => void;
  checkLocalAvailability: (force?: boolean) => Promise<void>;
}

// Throttle: don't recheck within this many ms unless forced
const CHECK_THROTTLE_MS = 30_000; // 30 seconds

export const useAIProviderStore = create<AIProviderState>()(
  persist(
    (set, get) => ({
      provider: 'gemini',
      isLocalAvailable: false,
      isChecking: false,
      modelStatuses: {},
      lastCheckedAt: 0,

      setProvider: (provider) => set({ provider }),

      toggleProvider: () => {
        const { provider, isLocalAvailable } = get();
        if (provider === 'gemini' && !isLocalAvailable) {
          console.warn('[AIProvider] Cannot switch to local - models not ready');
          return;
        }
        const newProvider = provider === 'gemini' ? 'local' : 'gemini';
        set({ provider: newProvider });
      },

      checkLocalAvailability: async (force = false) => {
        const { lastCheckedAt, isChecking } = get();
        const now = Date.now();

        // Skip if already checking or if we checked recently (unless forced)
        if (isChecking) return;
        if (!force && now - lastCheckedAt < CHECK_THROTTLE_MS) return;

        set({ isChecking: true });
        try {
          const gatewayUrl = process.env.NEXT_PUBLIC_API_GATEWAY_URL || 'http://localhost:3001';
          const res = await fetch(`${gatewayUrl}/api/v1/ai/local/health`, {
            signal: AbortSignal.timeout(5000),
          });
          if (!res.ok) throw new Error(`Health check failed: ${res.status}`);
          const data = await res.json();
          set({
            isLocalAvailable: data.available ?? false,
            modelStatuses: data.models ?? {},
            isChecking: false,
            lastCheckedAt: Date.now(),
          });
        } catch (err) {
          console.warn('[AIProvider] Health check failed:', err);
          set({ isLocalAvailable: false, isChecking: false, lastCheckedAt: Date.now() });
        }
      },
    }),
    {
      name: 'r26-ai-provider',
      partialize: (s) => ({ provider: s.provider }),
    }
  )
);
