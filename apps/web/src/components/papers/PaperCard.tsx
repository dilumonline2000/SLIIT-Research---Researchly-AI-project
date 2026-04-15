"use client";

import Link from "next/link";
import { FileText, MessageSquare, CheckCircle2, Loader2, AlertCircle } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import type { UploadedPaper } from "@/stores/paperStore";

function StatusBadge({ status }: { status: string }) {
  if (status === "ready")
    return (
      <span className="inline-flex items-center gap-1 rounded-full bg-green-500/10 px-2 py-0.5 text-xs text-green-600">
        <CheckCircle2 className="h-3 w-3" /> Ready
      </span>
    );
  if (status === "failed")
    return (
      <span className="inline-flex items-center gap-1 rounded-full bg-red-500/10 px-2 py-0.5 text-xs text-red-600">
        <AlertCircle className="h-3 w-3" /> Failed
      </span>
    );
  return (
    <span className="inline-flex items-center gap-1 rounded-full bg-amber-500/10 px-2 py-0.5 text-xs text-amber-600">
      <Loader2 className="h-3 w-3 animate-spin" /> {status}
    </span>
  );
}

export function PaperCard({ paper }: { paper: UploadedPaper }) {
  return (
    <Card className="transition-shadow hover:shadow-md">
      <CardContent className="space-y-3 p-4">
        <div className="flex items-start justify-between gap-2">
          <FileText className="mt-1 h-5 w-5 shrink-0 text-muted-foreground" />
          <div className="min-w-0 flex-1">
            <Link
              href={`/papers/${paper.id}`}
              className="line-clamp-2 font-medium hover:underline"
            >
              {paper.title || "Untitled paper"}
            </Link>
            <p className="mt-0.5 line-clamp-1 text-xs text-muted-foreground">
              {(paper.authors || []).slice(0, 3).join(", ") || "Unknown authors"}
              {paper.publication_year ? ` · ${paper.publication_year}` : ""}
            </p>
          </div>
        </div>

        {paper.abstract && (
          <p className="line-clamp-3 text-xs text-muted-foreground">{paper.abstract}</p>
        )}

        <div className="flex items-center justify-between">
          <StatusBadge status={paper.processing_status} />
          <Link
            href={`/papers/${paper.id}/chat`}
            className="inline-flex items-center gap-1 text-xs font-medium text-primary hover:underline"
          >
            <MessageSquare className="h-3 w-3" /> Chat
          </Link>
        </div>
      </CardContent>
    </Card>
  );
}
