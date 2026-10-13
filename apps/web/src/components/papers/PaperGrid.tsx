"use client";

import Link from "next/link";
import { FileUp } from "lucide-react";
import { PaperCard } from "./PaperCard";
import type { UploadedPaper } from "@/stores/paperStore";

export function PaperGrid({ papers }: { papers: UploadedPaper[] }) {
  if (!papers.length) {
    return (
      <div className="flex flex-col items-center gap-3 rounded-2xl border border-dashed bg-card/50 p-10 text-center">
        <span className="flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-indigo-500 to-violet-500 text-white shadow-md">
          <FileUp className="h-7 w-7" />
        </span>
        <div>
          <p className="font-semibold">Your library is empty</p>
          <p className="mt-1 text-sm text-muted-foreground">
            Upload your first research PDF to chat with it and power model training.
          </p>
        </div>
        <Link
          href="/papers/upload"
          className="inline-flex h-10 items-center rounded-lg bg-gradient-to-r from-indigo-600 to-violet-600 px-4 text-sm font-semibold text-white"
        >
          Upload a paper
        </Link>
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
