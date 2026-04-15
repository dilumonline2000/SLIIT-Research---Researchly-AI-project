import { create } from "zustand";

export type ProcessingStatus =
  | "uploading"
  | "extracting"
  | "chunking"
  | "embedding"
  | "indexing"
  | "ready"
  | "failed";

export interface UploadedPaper {
  id: string;
  title: string | null;
  authors: string[] | null;
  abstract: string | null;
  page_count: number | null;
  processing_status: ProcessingStatus;
  created_at?: string;
  publication_year?: number | null;
  keywords?: string[] | null;
}

interface PaperState {
  papers: UploadedPaper[];
  loading: boolean;
  setPapers: (papers: UploadedPaper[]) => void;
  upsertPaper: (paper: UploadedPaper) => void;
  removePaper: (id: string) => void;
  setLoading: (v: boolean) => void;
}

export const usePaperStore = create<PaperState>((set) => ({
  papers: [],
  loading: false,
  setPapers: (papers) => set({ papers }),
  upsertPaper: (paper) =>
    set((state) => {
      const idx = state.papers.findIndex((p) => p.id === paper.id);
      if (idx === -1) return { papers: [paper, ...state.papers] };
      const next = [...state.papers];
      next[idx] = { ...next[idx], ...paper };
      return { papers: next };
    }),
  removePaper: (id) =>
    set((state) => ({ papers: state.papers.filter((p) => p.id !== id) })),
  setLoading: (loading) => set({ loading }),
}));
