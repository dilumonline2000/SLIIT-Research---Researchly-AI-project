"use client";

import { create } from "zustand";
import { persist } from "zustand/middleware";

interface CollaborationState {
  otpEnabled: boolean;
  setOtpEnabled: (enabled: boolean) => void;
}

export const useCollaborationStore = create<CollaborationState>()(
  persist(
    (set) => ({
      otpEnabled: true,
      setOtpEnabled: (otpEnabled) => set({ otpEnabled }),
    }),
    {
      name: "r26-collaboration",
      partialize: (s) => ({ otpEnabled: s.otpEnabled }),
    },
  ),
);
