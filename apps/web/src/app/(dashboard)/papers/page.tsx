"use client";

import { useCallback, useEffect } from "react";
import Link from "next/link";
import { Plus } from "lucide-react";
import { Button } from "@/components/ui/button";
import { PaperGrid } from "@/components/papers/PaperGrid";
import { apiGet } from "@/lib/api";
import { API_ROUTES } from "@/lib/constants";
import { usePaperStore, type UploadedPaper } from "@/stores/paperStore";

export default function PapersLibraryPage() {
  const { papers, setPapers, loading, setLoading } = usePaperStore();

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const r = await apiGet<{ papers: UploadedPaper[] }>(API_ROUTES.papers.list);
      setPapers(r.papers || []);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }, [setPapers, setLoading]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">My Papers</h1>
          <p className="text-sm text-muted-foreground">
            Upload research papers, chat with them, and feed them into model training.
          </p>
        </div>
        <Link href="/papers/upload">
          <Button>
            <Plus className="mr-2 h-4 w-4" />
            Upload PDFs
          </Button>
        </Link>
      </div>

      {loading ? (
        <p className="text-sm text-muted-foreground">Loading papers…</p>
      ) : (
        <PaperGrid papers={papers} />
      )}
    </div>
  );
}
