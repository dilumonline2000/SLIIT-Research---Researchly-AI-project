"use client";

import Link from "next/link";
import { useState } from "react";
import { FileText, MessageSquare, CheckCircle2, Loader2, AlertCircle, RefreshCw, ChevronDown, ChevronUp } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import type { UploadedPaper } from "@/stores/paperStore";
import { apiPost } from "@/lib/api";
import { API_ROUTES } from "@/lib/constants";

function StatusBadge({ status }: { status: string }) {
  if (status === "ready")
    return (
      <span className="inline-flex items-center gap-1 rounded-full bg-emerald-500/10 px-2.5 py-0.5 text-xs font-medium text-emerald-600 dark:text-emerald-300">
        <CheckCircle2 className="h-3 w-3" /> Ready
      </span>
    );
  if (status === "failed")
    return (
      <span className="inline-flex items-center gap-1 rounded-full bg-red-500/10 px-2.5 py-0.5 text-xs font-medium text-red-600 dark:text-red-300">
        <AlertCircle className="h-3 w-3" /> Failed
      </span>
    );
  return (
    <span className="inline-flex items-center gap-1 rounded-full bg-amber-500/10 px-2.5 py-0.5 text-xs font-medium capitalize text-amber-600 dark:text-amber-300">
      <Loader2 className="h-3 w-3 animate-spin" /> {status}
    </span>
  );
}

export function PaperCard({ paper }: { paper: UploadedPaper }) {
  const [retrying, setRetrying] = useState(false);
  const [retryMsg, setRetryMsg] = useState("");
  const [showError, setShowError] = useState(false);

  const isFailed = paper.processing_status === "failed";
  const isStuck = ["extracting", "chunking", "embedding", "indexing"].includes(paper.processing_status);

  const handleRetry = async () => {
    setRetrying(true);
    setRetryMsg("");
    try {
      await apiPost(API_ROUTES.papers.reprocess(paper.id), {});
      setRetryMsg("Reprocessing started — refresh in a few seconds.");
    } catch (err) {
      setRetryMsg(err instanceof Error ? err.message : "Retry failed");
    } finally {
      setRetrying(false);
    }
  };

  return (
    <Card className="group relative flex h-full flex-col overflow-hidden transition-all hover:-translate-y-0.5 hover:shadow-lg">
      <div className="absolute inset-x-0 top-0 h-1 bg-gradient-to-r from-indigo-500 via-violet-500 to-fuchsia-500 opacity-70 transition-opacity group-hover:opacity-100" />
      <CardContent className="flex flex-1 flex-col gap-3 p-5">
        <div className="flex items-start justify-between gap-3">
          <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-500 to-violet-500 text-white shadow-sm">
            <FileText className="h-5 w-5" />
          </span>
          <div className="min-w-0 flex-1">
            <Link
              href={`/papers/${paper.id}`}
              className="line-clamp-2 font-semibold leading-snug hover:text-primary"
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
          <p className="line-clamp-3 text-sm leading-relaxed text-muted-foreground">{paper.abstract}</p>
        )}

        <div className="mt-auto flex items-center justify-between gap-2 border-t pt-3">
          <StatusBadge status={paper.processing_status} />
          <div className="flex items-center gap-2">
            {isFailed && paper.processing_error && (
              <button
                className="text-xs text-muted-foreground hover:text-foreground flex items-center gap-0.5"
                onClick={() => setShowError(!showError)}
              >
                {showError ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
                Details
              </button>
            )}
            {(isFailed || isStuck) && (
              <Button
                size="sm"
                variant="outline"
                onClick={handleRetry}
                disabled={retrying}
                className="h-7 text-xs"
                title="Retry processing"
              >
                <RefreshCw className={`h-3 w-3 ${retrying ? "animate-spin" : ""}`} />
                <span className="ml-1">{retrying ? "Retrying..." : "Retry"}</span>
              </Button>
            )}
            <Link
              href={`/papers/${paper.id}/chat`}
              className="inline-flex items-center gap-1 rounded-lg bg-primary/10 px-2.5 py-1 text-xs font-semibold text-primary transition-colors hover:bg-primary/15"
            >
              <MessageSquare className="h-3 w-3" /> Chat
            </Link>
          </div>
        </div>

        {isFailed && showError && paper.processing_error && (
          <div className="rounded-md border border-red-200 bg-red-50 p-2">
            <p className="text-xs text-red-700 font-mono break-all">{paper.processing_error}</p>
          </div>
        )}

        {retryMsg && (
          <p className="text-xs text-muted-foreground">{retryMsg}</p>
        )}
      </CardContent>
    </Card>
  );
}
