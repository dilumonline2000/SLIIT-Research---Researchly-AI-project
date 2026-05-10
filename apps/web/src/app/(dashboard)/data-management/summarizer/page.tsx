"use client";

import { useRef, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import {
  Database, Sparkles, FileText, Copy, Check, Upload, FileUp, X,
  BookOpen, Target, FlaskConical, BarChart3, AlertTriangle, CheckCircle2,
  Download,
} from "lucide-react";
import api from "@/lib/api";
import { apiPost } from "@/lib/api";
import { API_ROUTES } from "@/lib/constants";

interface KeyPoint {
  category: string;
  category_label: string;
  text: string;
}

interface SummarizeResponse {
  summary: string;
  sentences: string[];
  key_points: KeyPoint[];
  grouped_points: Record<string, KeyPoint[]>;
  n_sentences_input: number;
  n_sentences_output: number;
  compression_ratio: number;
  model_version: string;
  source?: "local" | "gemini" | "fallback";
  filename?: string | null;
  pdf_text_length?: number | null;
}

type Mode = "text" | "upload";
type Length = "quick" | "standard" | "detailed" | "extensive";

const LENGTH_OPTIONS: { id: Length; label: string; sub: string }[] = [
  { id: "quick",     label: "Quick",     sub: "4–5 key points" },
  { id: "standard",  label: "Standard",  sub: "8–10 key points" },
  { id: "detailed",  label: "Detailed",  sub: "12–15 in-depth points" },
  { id: "extensive", label: "Extensive", sub: "18–20 comprehensive points" },
];

const CATEGORY_DISPLAY_ORDER = [
  "background", "objective", "methodology", "results", "limitations", "conclusion", "general",
];

const CATEGORY_META: Record<string, { color: string; icon: typeof BookOpen }> = {
  background:  { color: "bg-slate-100 text-slate-700 border-slate-200",     icon: BookOpen },
  objective:   { color: "bg-indigo-100 text-indigo-700 border-indigo-200",  icon: Target },
  methodology: { color: "bg-blue-100 text-blue-700 border-blue-200",        icon: FlaskConical },
  results:     { color: "bg-emerald-100 text-emerald-700 border-emerald-200", icon: BarChart3 },
  limitations: { color: "bg-amber-100 text-amber-700 border-amber-200",     icon: AlertTriangle },
  conclusion:  { color: "bg-purple-100 text-purple-700 border-purple-200",  icon: CheckCircle2 },
  general:     { color: "bg-gray-100 text-gray-700 border-gray-200",        icon: FileText },
};

export default function SummarizePage() {
  const [mode, setMode] = useState<Mode>("text");

  // Text-input state
  const [text, setText] = useState("");

  // Upload-input state
  const [file, setFile] = useState<File | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Shared state
  const [length, setLength] = useState<Length>("standard");
  const [result, setResult] = useState<SummarizeResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [copied, setCopied] = useState(false);

  const canSummarizeText = text.trim().length >= 100;
  const canSummarizeFile = !!file && file.size > 0;
  const canSubmit = (mode === "text" && canSummarizeText) || (mode === "upload" && canSummarizeFile);

  const handleSummarize = async () => {
    if (!canSubmit) return;
    setLoading(true);
    setError("");
    setResult(null);
    try {
      let data: SummarizeResponse;
      if (mode === "text") {
        data = await apiPost<SummarizeResponse>(API_ROUTES.module3.summarize, { text, length });
      } else {
        const fd = new FormData();
        fd.append("file", file as File);
        fd.append("length", length);
        // Use raw axios instance directly so it auto-detects multipart;
        // do NOT pass an explicit Content-Type header — axios needs to set
        // the boundary itself when the body is FormData.
        const resp = await api.post<SummarizeResponse>(API_ROUTES.module3.summarizeUpload, fd, {
          timeout: 120_000,
        });
        data = resp.data;
      }
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Summarization failed");
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadReport = async () => {
    if (!result) return;
    try {
      const r = await api.post(API_ROUTES.module3.summarizeReport, {
        summary: result.summary,
        key_points: result.key_points,
        grouped_points: result.grouped_points,
        sentences: result.sentences,
        n_sentences_input: result.n_sentences_input,
        n_sentences_output: result.n_sentences_output,
        compression_ratio: result.compression_ratio,
        model_version: result.model_version,
        source: result.source ?? "unknown",
        filename: result.filename,
        pdf_text_length: result.pdf_text_length,
        title: result.filename ? `Summary — ${result.filename}` : "Research Paper Summary",
      }, { responseType: "text" });
      const blob = new Blob([r.data as string], { type: "text/html" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      const safeName = (result.filename || "summary").replace(/\.pdf$/i, "").replace(/[^a-z0-9]+/gi, "_");
      a.download = `summary-${safeName}-${Date.now()}.html`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not download the report");
    }
  };

  const handleCopy = () => {
    if (!result) return;
    // Build a markdown-like list from key_points
    const md = result.key_points
      .map((kp) => `• [${kp.category_label}] ${kp.text}`)
      .join("\n");
    navigator.clipboard.writeText(md || result.summary);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0] || null;
    if (f && !f.name.toLowerCase().endsWith(".pdf")) {
      setError("Only PDF files are supported.");
      setFile(null);
      return;
    }
    if (f && f.size > 25 * 1024 * 1024) {
      setError("PDF must be under 25 MB.");
      setFile(null);
      return;
    }
    setFile(f);
    setError("");
  };

  const handleClearFile = () => {
    setFile(null);
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  // Sort groups by display order
  const orderedGroups = result
    ? CATEGORY_DISPLAY_ORDER
        .filter((cat) => result.grouped_points?.[cat]?.length)
        .map((cat) => [cat, result.grouped_points[cat]] as const)
    : [];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <FileText className="h-6 w-6" /> Research Summarizer
        </h1>
        <p className="text-muted-foreground">
          Save reading time — paste text or upload a PDF; the local extractive model picks the most important sentences and groups them by section.
        </p>
      </div>

      <div className="flex gap-2">
        <Button
          variant={mode === "text" ? "default" : "outline"}
          size="sm"
          onClick={() => { setMode("text"); setResult(null); setError(""); }}
        >
          <FileText className="mr-2 h-4 w-4" /> Paste Text
        </Button>
        <Button
          variant={mode === "upload" ? "default" : "outline"}
          size="sm"
          onClick={() => { setMode("upload"); setResult(null); setError(""); }}
        >
          <Upload className="mr-2 h-4 w-4" /> Upload PDF
        </Button>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">
            {mode === "text" ? "Input Paper Text" : "Upload Research Paper (PDF)"}
          </CardTitle>
          <CardDescription>
            {mode === "text"
              ? "Paste full text or just the abstract + introduction."
              : "Drop in a PDF (≤ 25 MB). The model extracts text and returns key points grouped by section."}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {mode === "text" ? (
            <div className="space-y-2">
              <Label htmlFor="sum-text">Paper text (minimum 100 characters)</Label>
              <textarea
                id="sum-text"
                className="flex min-h-[200px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                placeholder="Paste the full paper text or a large section..."
                value={text}
                onChange={(e) => setText(e.target.value)}
              />
              <p className="text-xs text-muted-foreground">{text.length} characters</p>
            </div>
          ) : (
            <div className="space-y-3">
              <Label htmlFor="pdf-file">PDF file</Label>
              <div className="flex items-center gap-3">
                <label
                  htmlFor="pdf-file"
                  className="flex flex-1 items-center justify-center gap-2 rounded-md border border-dashed border-input bg-background px-4 py-8 text-sm text-muted-foreground cursor-pointer hover:bg-accent transition-colors"
                >
                  <FileUp className="h-5 w-5" />
                  {file ? (
                    <span className="text-foreground font-medium">
                      {file.name}
                      <span className="ml-2 text-xs text-muted-foreground">
                        ({(file.size / 1024 / 1024).toFixed(2)} MB)
                      </span>
                    </span>
                  ) : (
                    <span>Click to choose a PDF research paper</span>
                  )}
                </label>
                <input
                  ref={fileInputRef}
                  id="pdf-file"
                  type="file"
                  accept=".pdf,application/pdf"
                  onChange={handleFileChange}
                  className="hidden"
                />
                {file && (
                  <Button type="button" variant="ghost" size="icon" onClick={handleClearFile} title="Remove file">
                    <X className="h-4 w-4" />
                  </Button>
                )}
              </div>
              <p className="text-xs text-muted-foreground">
                The PDF is held in memory only long enough to extract its text — the file itself is not stored.
              </p>
            </div>
          )}

          <div className="space-y-2">
            <Label>Detail level</Label>
            <div className="flex flex-wrap gap-2">
              {LENGTH_OPTIONS.map((l) => (
                <button
                  key={l.id}
                  onClick={() => setLength(l.id)}
                  className={`rounded-md border px-3 py-2 text-left transition-colors ${
                    length === l.id
                      ? "border-primary bg-primary/10"
                      : "border-input bg-background hover:bg-accent"
                  }`}
                >
                  <div className="text-sm font-medium">{l.label}</div>
                  <div className="text-xs text-muted-foreground">{l.sub}</div>
                </button>
              ))}
            </div>
          </div>

          <Button onClick={handleSummarize} disabled={loading || !canSubmit}>
            {loading
              ? (mode === "upload" ? "Extracting & summarizing…" : "Summarizing…")
              : "Generate Summary"}
          </Button>
          {error && (
            <div className="rounded-md border border-destructive/50 bg-destructive/10 p-3 text-sm text-destructive">
              {error}
            </div>
          )}
        </CardContent>
      </Card>

      {result && (result.key_points.length > 0 || result.summary) && (
        <>
          <Card className="bg-muted/30">
            <CardContent className="p-3 flex flex-wrap items-center gap-3 text-sm">
              <Badge variant="outline" className={
                result.source === "local"
                  ? "bg-emerald-100 text-emerald-700 border-emerald-200"
                  : "bg-blue-100 text-blue-700 border-blue-200"
              }>
                {result.source === "local" ? (
                  <span className="flex items-center gap-1"><Database className="h-3 w-3" /> Local extractive (SBERT)</span>
                ) : (
                  <span className="flex items-center gap-1"><Sparkles className="h-3 w-3" /> Gemini abstractive</span>
                )}
              </Badge>
              <span className="text-xs text-muted-foreground">{result.model_version}</span>
              {result.filename && (
                <span className="text-xs text-muted-foreground">
                  📄 <strong>{result.filename}</strong>
                  {result.pdf_text_length ? ` · ${result.pdf_text_length.toLocaleString()} chars extracted` : ""}
                </span>
              )}
              {result.n_sentences_input > 0 && (
                <span className="text-xs text-muted-foreground">
                  {result.n_sentences_input} → <strong>{result.key_points.length || result.n_sentences_output}</strong> key points
                  {" · "}{(result.compression_ratio * 100).toFixed(0)}% of original
                </span>
              )}
              <div className="ml-auto flex gap-2">
                <Button size="sm" variant="outline" onClick={handleDownloadReport}>
                  <Download className="mr-2 h-4 w-4" /> Download report
                </Button>
                <Button size="sm" variant="outline" onClick={handleCopy}>
                  {copied ? <Check className="mr-2 h-4 w-4 text-emerald-600" /> : <Copy className="mr-2 h-4 w-4" />}
                  {copied ? "Copied" : "Copy as bullets"}
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Grouped key points (preferred view) */}
          {orderedGroups.length > 0 ? (
            <div className="space-y-4">
              {orderedGroups.map(([cat, points]) => {
                const meta = CATEGORY_META[cat] || CATEGORY_META.general;
                const Icon = meta.icon;
                return (
                  <Card key={cat}>
                    <CardHeader className="pb-3">
                      <CardTitle className="text-base flex items-center gap-2">
                        <span className={`inline-flex h-7 w-7 items-center justify-center rounded-md border ${meta.color}`}>
                          <Icon className="h-4 w-4" />
                        </span>
                        {points[0].category_label}
                        <Badge variant="secondary" className="ml-1 text-[10px]">
                          {points.length} {points.length === 1 ? "point" : "points"}
                        </Badge>
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <ul className="space-y-2">
                        {points.map((p, i) => (
                          <li key={i} className="flex gap-2 text-sm leading-relaxed">
                            <span className="text-muted-foreground select-none mt-0.5">•</span>
                            <span>{p.text}</span>
                          </li>
                        ))}
                      </ul>
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          ) : (
            // Fallback: Gemini path returns plain `summary` text; render it.
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Summary</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm leading-relaxed whitespace-pre-wrap">{result.summary}</p>
              </CardContent>
            </Card>
          )}
        </>
      )}
    </div>
  );
}
