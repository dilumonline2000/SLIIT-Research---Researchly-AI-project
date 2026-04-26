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
        console.log('[AIProvider] Toggle clicked. Current:', { provider, isLocalAvailable });
        if (provider === 'gemini' && !isLocalAvailable) {
          console.warn('[AIProvider] Cannot switch to local - models not ready');
          return;
        }
        const newProvider = provider === 'gemini' ? 'local' : 'gemini';
        console.log('[AIProvider] Switching to:', newProvider);
        set({ provider: newProvider });
      },

      checkLocalAvailability: async () => {
        set({ isChecking: true });
        try {
          const gatewayUrl = process.env.NEXT_PUBLIC_API_GATEWAY_URL || 'http://localhost:3001';
          console.log('[AIProvider] Checking local availability at:', `${gatewayUrl}/api/v1/ai/local/health`);
          const res = await fetch(`${gatewayUrl}/api/v1/ai/local/health`, {
            signal: AbortSignal.timeout(5000),
          });
          if (!res.ok) throw new Error(`Health check failed with status ${res.status}`);
          const data = await res.json();
          console.log('[AIProvider] Health check response:', data);
          set({
            isLocalAvailable: data.available ?? false,
            modelStatuses: data.models ?? {},
            isChecking: false,
          });
        } catch (err) {
          console.error('[AIProvider] Local availability check failed:', err);
          set({ isLocalAvailable: false, isChecking: false });
        }
      },
    }),
    {
      name: 'r26-ai-provider',
      partialize: (s) => ({ provider: s.provider }),
    }
  )
);
