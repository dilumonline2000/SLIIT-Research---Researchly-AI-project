"use client";

import { useCallback, useRef, useState } from "react";
import { Upload, FileText, X, Loader2, CheckCircle2, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { usePaperUpload } from "@/hooks/usePaperUpload";
import { cn } from "@/lib/utils";

export function PaperUploader({ onUploaded }: { onUploaded?: () => void }) {
  const [dragActive, setDragActive] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const { uploads, uploadFiles } = usePaperUpload();

  const handleFiles = useCallback(
    async (files: File[]) => {
      const pdfs = files.filter((f) => f.type === "application/pdf" || f.name.toLowerCase().endsWith(".pdf"));
      if (!pdfs.length) return;
      await uploadFiles(pdfs);
      onUploaded?.();
    },
    [uploadFiles, onUploaded],
  );

  const onDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setDragActive(false);
    handleFiles(Array.from(e.dataTransfer.files));
  };

  return (
    <Card>
      <CardContent className="p-6">
        <div
          onDragOver={(e) => {
            e.preventDefault();
            setDragActive(true);
          }}
          onDragLeave={() => setDragActive(false)}
          onDrop={onDrop}
          className={cn(
            "flex flex-col items-center justify-center gap-3 rounded-lg border-2 border-dashed p-10 text-center transition-colors",
            dragActive ? "border-primary bg-primary/5" : "border-muted",
          )}
        >
          <Upload className="h-10 w-10 text-muted-foreground" />
          <p className="text-base font-medium">Drag &amp; drop research PDFs</p>
          <p className="text-sm text-muted-foreground">or click to browse — multi-file supported</p>
          <input
            ref={inputRef}
            type="file"
            multiple
            accept="application/pdf,.pdf"
            className="hidden"
            onChange={(e) => handleFiles(Array.from(e.target.files || []))}
          />
          <Button onClick={() => inputRef.current?.click()}>Choose files</Button>
        </div>

        {uploads.length > 0 && (
          <div className="mt-6 space-y-2">
            {uploads.map((u) => (
              <div
                key={u.fileName}
                className="flex items-center justify-between rounded-md border bg-muted/30 px-3 py-2"
              >
                <div className="flex items-center gap-2 truncate">
                  <FileText className="h-4 w-4 text-muted-foreground" />
                  <span className="truncate text-sm">{u.fileName}</span>
                </div>
                <div className="flex items-center gap-2 text-xs">
                  {u.status === "uploading" && (
                    <>
                      <Loader2 className="h-3 w-3 animate-spin" />
                      <span>Uploading…</span>
                    </>
                  )}
                  {u.status === "processing" && (
                    <>
                      <Loader2 className="h-3 w-3 animate-spin" />
                      <span>Processing…</span>
                    </>
                  )}
                  {u.status === "ready" && (
                    <>
                      <CheckCircle2 className="h-3 w-3 text-green-500" />
                      <span>Ready</span>
                    </>
                  )}
                  {u.status === "failed" && (
                    <>
                      <AlertCircle className="h-3 w-3 text-red-500" />
                      <span>{u.error || "Failed"}</span>
                    </>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
