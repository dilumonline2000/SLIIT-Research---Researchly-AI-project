"use client";

import { PaperCard } from "./PaperCard";
import type { UploadedPaper } from "@/stores/paperStore";

export function PaperGrid({ papers }: { papers: UploadedPaper[] }) {
  if (!papers.length) {
    return (
      <div className="rounded-lg border border-dashed p-10 text-center text-sm text-muted-foreground">
        No papers uploaded yet. Drop a PDF in the uploader above to get started.
      </div>
    );
  }
  return (
    <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
      {papers.map((p) => (
        <PaperCard key={p.id} paper={p} />
      ))}
    </div>
  );
}
