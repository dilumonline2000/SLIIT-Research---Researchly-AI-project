"use client";

import { useEffect, useMemo, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import {
  BookOpen, Quote, FileText, Search, Copy, Check, AlertCircle, Plus, Trash2,
  Download, ExternalLink, History, Sparkles, Wand2, Database, Edit3,
  ListOrdered, Link2,
} from "lucide-react";
import { API_ROUTES } from "@/lib/constants";
import { apiPost } from "@/lib/api";

// ─── Types ────────────────────────────────────────────────────────────────

type SourceType = "journal" | "conference" | "book" | "website";
type Style = "apa" | "ieee";

interface ParsedCitation {
  raw: string;
  source_type: SourceType;
  authors: string[];
  title: string;
  year: number | null;
  journal: string | null;
  conference: string | null;
  publisher: string | null;
  url: string | null;
  volume: string | null;
  issue: string | null;
  pages: string | null;
  doi: string | null;
  edition: string | null;
}

interface ParseResponse {
  parsed: ParsedCitation;
  formatted_apa: string;
  formatted_ieee: string;
  in_text_apa: string;
  in_text_ieee: string;
  warnings: string[];
  confidence: number;
  source: "regex" | "crossref";
}

interface SimilarPaper {
  paper_id: string;
  title: string;
  authors: string[];
  year: number | null;
  url: string;
  similarity: number;
  abstract_excerpt: string;
}

interface SavedEntry {
  id: string;
  parsed: ParsedCitation;
  formatted_apa: string;
  formatted_ieee: string;
  in_text_apa: string;
  in_text_ieee: string;
  saved_at: string;
}

const HISTORY_KEY = "researchly:citation-history";
const SAMPLE_TEXTS = [
  {
    label: "Journal article (APA-shaped)",
    text:
      "Smith, J., & Doe, A. (2020). Machine learning approaches in healthcare. Journal of Biomedical Informatics, 105, 103-118. https://doi.org/10.1016/j.jbi.2020.103456",
  },
  {
    label: "Book",
    text: "Goodfellow, I., Bengio, Y., & Courville, A. (2016). Deep Learning. MIT Press.",
  },
  {
    label: "Conference paper",
    text:
      "Devlin J, Chang M-W, Lee K, Toutanova K. BERT: Pre-training of Deep Bidirectional Transformers. Proceedings of NAACL-HLT 2019, pp. 4171-4186.",
  },
  {
    label: "Website",
    text: "OpenAI. (2023). GPT-4 Technical Report. https://openai.com/research/gpt-4",
  },
  {
    label: "IEEE-shaped",
    text:
      "K. He, X. Zhang, S. Ren, and J. Sun, \"Deep residual learning for image recognition,\" in Proc. IEEE CVPR, 2016, pp. 770-778.",
  },
];

// ─── Helpers ──────────────────────────────────────────────────────────────

/** Render `*italic*` markers as <em> while keeping the rest plain. */
function FormattedText({ text }: { text: string }) {
  const parts: React.ReactNode[] = [];
  let i = 0;
  let key = 0;
  const re = /\*([^*]+)\*/g;
  let match: RegExpExecArray | null;
  while ((match = re.exec(text)) !== null) {
    if (match.index > i) parts.push(<span key={key++}>{text.slice(i, match.index)}</span>);
    parts.push(<em key={key++} style={{ fontStyle: "italic" }}>{match[1]}</em>);
    i = match.index + match[0].length;
  }
  if (i < text.length) parts.push(<span key={key++}>{text.slice(i)}</span>);
  return <>{parts}</>;
}

/** Strip the *italic* markers when copying/exporting plain text. */
const stripStars = (s: string) => s.replace(/\*([^*]+)\*/g, "$1");

const SOURCE_META: Record<SourceType, { color: string; Icon: typeof BookOpen; label: string }> = {
  journal:    { color: "bg-blue-50 text-blue-700 border-blue-200",          Icon: FileText, label: "Journal article" },
  conference: { color: "bg-purple-50 text-purple-700 border-purple-200",    Icon: Quote,    label: "Conference paper" },
  book:       { color: "bg-amber-50 text-amber-700 border-amber-200",       Icon: BookOpen, label: "Book" },
  website:    { color: "bg-emerald-50 text-emerald-700 border-emerald-200", Icon: Link2,    label: "Website" },
};

// ─── Component ────────────────────────────────────────────────────────────

type Tab = "parse" | "doi" | "list";

export default function CitationParserPage() {
  const [tab, setTab] = useState<Tab>("parse");
  const [style, setStyle] = useState<Style>("apa");

  // Parse-tab state
  const [text, setText] = useState("");
  const [parsing, setParsing] = useState(false);
  const [result, setResult] = useState<ParseResponse | null>(null);
  const [error, setError] = useState("");
  const [editing, setEditing] = useState(false);

  // DOI-tab state
  const [doi, setDoi] = useState("");
  const [doiLoading, setDoiLoading] = useState(false);
  const [doiError, setDoiError] = useState("");

  // Similar SLIIT papers
  const [similar, setSimilar] = useState<SimilarPaper[]>([]);

  // Reference list state
  const [list, setList] = useState<SavedEntry[]>([]);
  const [listRendered, setListRendered] = useState<string[]>([]);

  // Saved citations history
  const [history, setHistory] = useState<SavedEntry[]>([]);

  // Copy feedback
  const [copiedKey, setCopiedKey] = useState<string | null>(null);

  // Load history once
  useEffect(() => {
    if (typeof window === "undefined") return;
    try {
      const raw = localStorage.getItem(HISTORY_KEY);
      if (raw) setHistory(JSON.parse(raw));
    } catch { /* ignore */ }
  }, []);

  const persistHistory = (next: SavedEntry[]) => {
    setHistory(next);
    try { localStorage.setItem(HISTORY_KEY, JSON.stringify(next.slice(0, 50))); } catch { /* ignore */ }
  };

  // ─── Actions ──────────────────────────────────────────────────────────

  const runParse = async () => {
    if (!text.trim()) return;
    setParsing(true);
    setError("");
    setResult(null);
    setSimilar([]);
    try {
      const res = await apiPost<ParseResponse>(API_ROUTES.module1.parseCitation, { raw_text: text });
      setResult(res);
      void loadSimilar(res.parsed.title || text);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Parse failed");
    } finally {
      setParsing(false);
    }
  };

  const loadSimilar = async (query: string) => {
    if (query.trim().length < 5) return;
    try {
      const res = await apiPost<{ papers: SimilarPaper[] }>(
        API_ROUTES.module1.citationSimilarPapers,
        { query, top_k: 5 },
      );
      setSimilar(res.papers || []);
    } catch { /* ignore */ }
  };

  const reformat = async (parsed: ParsedCitation) => {
    try {
      const apa = await apiPost<{ formatted: string; in_text: string }>(
        API_ROUTES.module1.formatCitation, { parsed, style: "apa" });
      const ieee = await apiPost<{ formatted: string; in_text: string }>(
        API_ROUTES.module1.formatCitation, { parsed, style: "ieee" });
      setResult((prev) => prev && {
        ...prev,
        parsed,
        formatted_apa: apa.formatted,
        formatted_ieee: ieee.formatted,
        in_text_apa: apa.in_text,
        in_text_ieee: ieee.in_text,
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Reformat failed");
    }
  };

  const lookupDoi = async () => {
    const v = doi.trim();
    if (!v) return;
    setDoiLoading(true);
    setDoiError("");
    setResult(null);
    setSimilar([]);
    try {
      const res = await apiPost<ParseResponse>(API_ROUTES.module1.citationDoiLookup, { doi: v });
      setResult(res);
      setText(`DOI: ${v}`);
      void loadSimilar(res.parsed.title);
      setTab("parse");
    } catch (err) {
      setDoiError(err instanceof Error ? err.message : "DOI lookup failed");
    } finally {
      setDoiLoading(false);
    }
  };

  const saveCurrent = () => {
    if (!result) return;
    const entry: SavedEntry = {
      id: `c-${Date.now()}`,
      parsed: result.parsed,
      formatted_apa: result.formatted_apa,
      formatted_ieee: result.formatted_ieee,
      in_text_apa: result.in_text_apa,
      in_text_ieee: result.in_text_ieee,
      saved_at: new Date().toISOString(),
    };
    persistHistory([entry, ...history]);
  };

  const addToList = () => {
    if (!result) return;
    const entry: SavedEntry = {
      id: `r-${Date.now()}`,
      parsed: result.parsed,
      formatted_apa: result.formatted_apa,
      formatted_ieee: result.formatted_ieee,
      in_text_apa: result.in_text_apa,
      in_text_ieee: result.in_text_ieee,
      saved_at: new Date().toISOString(),
    };
    setList((prev) => [...prev, entry]);
  };

  const buildList = async () => {
    if (list.length === 0) return;
    try {
      const res = await apiPost<{ entries: string[] }>(API_ROUTES.module1.referenceList, {
        entries: list.map((e) => e.parsed),
        style,
      });
      setListRendered(res.entries);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to build reference list");
    }
  };

  useEffect(() => {
    if (list.length > 0) void buildList();
    else setListRendered([]);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [list, style]);

  const copy = async (key: string, value: string) => {
    await navigator.clipboard.writeText(stripStars(value));
    setCopiedKey(key);
    setTimeout(() => setCopiedKey(null), 1500);
  };

  const downloadList = (kind: "txt" | "html") => {
    const filename = `references-${style}.${kind}`;
    const plain = listRendered.map(stripStars).join("\n\n");
    let blob: Blob;
    if (kind === "html") {
      const body = listRendered
        .map((line) => `<p>${line.replace(/\*([^*]+)\*/g, "<em>$1</em>")}</p>`).join("\n");
      const html = `<!doctype html><html><head><meta charset="utf-8"><title>References (${style.toUpperCase()})</title>
<style>body{font-family:Georgia,serif;max-width:780px;margin:2rem auto;padding:0 1rem;line-height:1.55;color:#222}</style>
</head><body><h1>References (${style.toUpperCase()})</h1>${body}</body></html>`;
      blob = new Blob([html], { type: "text/html" });
    } else {
      blob = new Blob([plain], { type: "text/plain" });
    }
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url; a.download = filename; a.click();
    URL.revokeObjectURL(url);
  };

  // ─── Derived ──────────────────────────────────────────────────────────

  const formatted = result ? (style === "apa" ? result.formatted_apa : result.formatted_ieee) : "";
  const inText = result ? (style === "apa" ? result.in_text_apa : result.in_text_ieee) : "";

  const warningsByField = useMemo(() => {
    if (!result) return {} as Record<string, string>;
    const out: Record<string, string> = {};
    for (const w of result.warnings) {
      if (/author/i.test(w)) out.authors = w;
      else if (/year/i.test(w)) out.year = w;
      else if (/title/i.test(w)) out.title = w;
      else if (/journal/i.test(w)) out.journal = w;
      else if (/conference/i.test(w)) out.conference = w;
      else if (/publisher/i.test(w)) out.publisher = w;
      else if (/url/i.test(w)) out.url = w;
    }
    return out;
  }, [result]);

  const updateField = <K extends keyof ParsedCitation>(field: K, value: ParsedCitation[K]) => {
    if (!result) return;
    setResult({ ...result, parsed: { ...result.parsed, [field]: value } });
  };

  // ─── Render ───────────────────────────────────────────────────────────

  return (
    <div className="space-y-6">
      <div className="rounded-2xl bg-gradient-to-br from-blue-600 via-indigo-600 to-purple-600 p-6 text-white shadow-lg">
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <Quote className="h-7 w-7" /> Citation Parser & Generator
        </h1>
        <p className="mt-1 text-sm text-white/85 max-w-3xl">
          Paste raw text, look up a DOI, or assemble a full reference list. The system extracts
          fields, formats them in IEEE or APA, and shows similar SLIIT papers for context.
        </p>
      </div>

      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex gap-2">
          <Button variant={tab === "parse" ? "default" : "outline"} size="sm" onClick={() => setTab("parse")}>
            <Wand2 className="mr-2 h-4 w-4" /> Parse Raw Text
          </Button>
          <Button variant={tab === "doi" ? "default" : "outline"} size="sm" onClick={() => setTab("doi")}>
            <Search className="mr-2 h-4 w-4" /> DOI Lookup
          </Button>
          <Button variant={tab === "list" ? "default" : "outline"} size="sm" onClick={() => setTab("list")}>
            <ListOrdered className="mr-2 h-4 w-4" /> Reference List
            {list.length > 0 && <Badge variant="secondary" className="ml-2 text-[10px]">{list.length}</Badge>}
          </Button>
        </div>
        <div className="flex items-center gap-2 rounded-md border bg-card p-1">
          <span className="px-2 text-xs text-muted-foreground">Style:</span>
          {(["apa", "ieee"] as const).map((s) => (
            <button
              key={s}
              onClick={() => setStyle(s)}
              className={`rounded px-3 py-1 text-xs font-medium transition-colors ${
                style === s ? "bg-primary text-primary-foreground" : "hover:bg-accent"
              }`}
            >
              {s.toUpperCase()}
            </button>
          ))}
        </div>
      </div>

      {tab === "parse" && (
        <>
          <Card>
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <Wand2 className="h-5 w-5" /> Raw text input
              </CardTitle>
              <CardDescription>
                Paste any citation form — APA, IEEE, BibTeX-shaped text, or a single line from a paper.
                The engine auto-detects the source type.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              <textarea
                className="flex min-h-[120px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                placeholder="Paste a raw citation here…"
                value={text}
                onChange={(e) => setText(e.target.value)}
              />
              <div className="flex flex-wrap gap-2">
                <span className="text-xs text-muted-foreground self-center">Try a sample:</span>
                {SAMPLE_TEXTS.map((s) => (
                  <button
                    key={s.label}
                    onClick={() => setText(s.text)}
                    className="rounded-full border bg-muted/50 px-3 py-1 text-xs hover:bg-accent transition-colors"
                  >
                    {s.label}
                  </button>
                ))}
              </div>
              <div className="flex gap-2">
                <Button onClick={runParse} disabled={parsing || !text.trim()}>
                  <Sparkles className="mr-2 h-4 w-4" />
                  {parsing ? "Parsing…" : "Parse Citation"}
                </Button>
                {result && (
                  <Button variant="outline" onClick={addToList}>
                    <Plus className="mr-2 h-4 w-4" /> Add to reference list
                  </Button>
                )}
              </div>
              {error && (
                <div className="flex items-start gap-2 rounded-md border border-destructive/50 bg-destructive/10 p-3 text-sm text-destructive">
                  <AlertCircle className="h-4 w-4 mt-0.5 flex-shrink-0" />
                  <span>{error}</span>
                </div>
              )}
            </CardContent>
          </Card>

          {result && (
            <>
              <Card className="bg-muted/30">
                <CardContent className="p-3 flex flex-wrap items-center gap-3 text-sm">
                  {(() => {
                    const meta = SOURCE_META[result.parsed.source_type];
                    const Icon = meta.Icon;
                    return (
                      <Badge variant="outline" className={meta.color}>
                        <Icon className="h-3 w-3 mr-1 inline" /> {meta.label}
                      </Badge>
                    );
                  })()}
                  <Badge variant="outline" className={
                    result.source === "crossref"
                      ? "bg-emerald-50 text-emerald-700 border-emerald-200"
                      : "bg-slate-50 text-slate-700 border-slate-200"
                  }>
                    {result.source === "crossref" ? "From CrossRef" : "Parsed locally"}
                  </Badge>
                  <span className="text-xs text-muted-foreground">
                    Confidence <strong>{(result.confidence * 100).toFixed(0)}%</strong>
                  </span>
                  {result.warnings.length > 0 && (
                    <Badge variant="outline" className="bg-amber-50 text-amber-700 border-amber-200">
                      <AlertCircle className="h-3 w-3 mr-1 inline" />
                      {result.warnings.length} warning{result.warnings.length > 1 ? "s" : ""}
                    </Badge>
                  )}
                  <Button size="sm" variant="ghost" className="ml-auto" onClick={() => setEditing(!editing)}>
                    <Edit3 className="mr-2 h-4 w-4" /> {editing ? "Done editing" : "Edit fields"}
                  </Button>
                  <Button size="sm" variant="outline" onClick={saveCurrent}>
                    <History className="mr-2 h-4 w-4" /> Save
                  </Button>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-base">Formatted ({style.toUpperCase()})</CardTitle>
                    <Button size="sm" variant="outline" onClick={() => copy("formatted", formatted)}>
                      {copiedKey === "formatted"
                        ? <><Check className="mr-2 h-4 w-4 text-emerald-600" /> Copied</>
                        : <><Copy className="mr-2 h-4 w-4" /> Copy</>}
                    </Button>
                  </div>
                </CardHeader>
                <CardContent className="space-y-3">
                  <p className="text-sm leading-relaxed font-serif">
                    <FormattedText text={formatted} />
                  </p>
                  <div className="flex items-center gap-2 text-xs text-muted-foreground border-t pt-3">
                    In-text:
                    <code className="rounded bg-muted px-2 py-0.5">{inText}</code>
                    <button
                      onClick={() => copy("intext", inText)}
                      className="ml-auto inline-flex items-center gap-1 rounded border px-2 py-0.5 hover:bg-accent"
                    >
                      {copiedKey === "intext"
                        ? <><Check className="h-3 w-3 text-emerald-600" /> Copied</>
                        : <><Copy className="h-3 w-3" /> Copy</>}
                    </button>
                  </div>
                </CardContent>
              </Card>

              {editing && (
                <Card>
                  <CardHeader>
                    <CardTitle className="text-base">Edit extracted fields</CardTitle>
                    <CardDescription>
                      Tweak any value and click Re-format to refresh the output above.
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <FieldRow label="Authors (one per line, format: 'Last, F.')" warning={warningsByField.authors}>
                      <textarea
                        className="flex min-h-[80px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                        value={result.parsed.authors.join("\n")}
                        onChange={(e) => updateField("authors", e.target.value.split("\n").map((s) => s.trim()).filter(Boolean))}
                      />
                    </FieldRow>

                    <div className="grid gap-3 md:grid-cols-2">
                      <FieldRow label="Source type">
                        <select
                          value={result.parsed.source_type}
                          onChange={(e) => updateField("source_type", e.target.value as SourceType)}
                          className="rounded-md border bg-background px-3 py-2 text-sm w-full"
                        >
                          <option value="journal">Journal article</option>
                          <option value="conference">Conference paper</option>
                          <option value="book">Book</option>
                          <option value="website">Website</option>
                        </select>
                      </FieldRow>
                      <FieldRow label="Year" warning={warningsByField.year}>
                        <Input
                          type="number"
                          value={result.parsed.year ?? ""}
                          onChange={(e) => updateField("year", e.target.value ? Number(e.target.value) : null)}
                        />
                      </FieldRow>
                    </div>

                    <FieldRow label="Title" warning={warningsByField.title}>
                      <Input value={result.parsed.title} onChange={(e) => updateField("title", e.target.value)} />
                    </FieldRow>

                    {result.parsed.source_type === "journal" && (
                      <div className="grid gap-3 md:grid-cols-2">
                        <FieldRow label="Journal" warning={warningsByField.journal}>
                          <Input value={result.parsed.journal ?? ""} onChange={(e) => updateField("journal", e.target.value || null)} />
                        </FieldRow>
                        <FieldRow label="Volume / Issue">
                          <div className="flex gap-2">
                            <Input placeholder="vol" value={result.parsed.volume ?? ""} onChange={(e) => updateField("volume", e.target.value || null)} />
                            <Input placeholder="issue" value={result.parsed.issue ?? ""} onChange={(e) => updateField("issue", e.target.value || null)} />
                          </div>
                        </FieldRow>
                      </div>
                    )}
                    {result.parsed.source_type === "conference" && (
                      <FieldRow label="Conference" warning={warningsByField.conference}>
                        <Input value={result.parsed.conference ?? ""} onChange={(e) => updateField("conference", e.target.value || null)} />
                      </FieldRow>
                    )}
                    {result.parsed.source_type === "book" && (
                      <div className="grid gap-3 md:grid-cols-2">
                        <FieldRow label="Publisher" warning={warningsByField.publisher}>
                          <Input value={result.parsed.publisher ?? ""} onChange={(e) => updateField("publisher", e.target.value || null)} />
                        </FieldRow>
                        <FieldRow label="Edition">
                          <Input value={result.parsed.edition ?? ""} onChange={(e) => updateField("edition", e.target.value || null)} />
                        </FieldRow>
                      </div>
                    )}
                    {result.parsed.source_type === "website" && (
                      <FieldRow label="URL" warning={warningsByField.url}>
                        <Input value={result.parsed.url ?? ""} onChange={(e) => updateField("url", e.target.value || null)} />
                      </FieldRow>
                    )}

                    <div className="grid gap-3 md:grid-cols-2">
                      <FieldRow label="Pages">
                        <Input value={result.parsed.pages ?? ""} onChange={(e) => updateField("pages", e.target.value || null)} />
                      </FieldRow>
                      <FieldRow label="DOI">
                        <Input value={result.parsed.doi ?? ""} onChange={(e) => updateField("doi", e.target.value || null)} />
                      </FieldRow>
                    </div>

                    <Button onClick={() => reformat(result.parsed)} variant="outline">
                      <Wand2 className="mr-2 h-4 w-4" /> Re-format with edits
                    </Button>
                  </CardContent>
                </Card>
              )}

              {result.warnings.length > 0 && (
                <Card className="border-amber-200 bg-amber-50/50">
                  <CardContent className="pt-4 space-y-1.5 text-sm">
                    <div className="flex items-center gap-2 font-medium text-amber-800">
                      <AlertCircle className="h-4 w-4" /> Suggestions
                    </div>
                    <ul className="list-disc pl-5 space-y-0.5 text-amber-900">
                      {result.warnings.map((w, i) => <li key={i}>{w}</li>)}
                    </ul>
                  </CardContent>
                </Card>
              )}

              {similar.length > 0 && (
                <Card>
                  <CardHeader>
                    <CardTitle className="text-base flex items-center gap-2">
                      <Database className="h-4 w-4" /> Similar SLIIT papers
                    </CardTitle>
                    <CardDescription>
                      Top SBERT matches against the SLIIT corpus (3,858 abstracts). Useful for finding related work.
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-2">
                    {similar.map((p) => (
                      <div key={p.paper_id} className="rounded-md border bg-muted/30 p-3 text-sm space-y-1">
                        <div className="flex items-start justify-between gap-2">
                          <p className="font-medium flex-1">{p.title}</p>
                          <Badge variant="secondary" className="shrink-0 text-[10px]">
                            {(p.similarity * 100).toFixed(0)}% match
                          </Badge>
                        </div>
                        <p className="text-xs text-muted-foreground">
                          {(p.authors || []).slice(0, 3).join(", ")}{p.year ? ` · ${p.year}` : ""}
                        </p>
                        {p.abstract_excerpt && <p className="text-xs italic">{p.abstract_excerpt}</p>}
                        {p.url && (
                          <a href={p.url} target="_blank" rel="noopener noreferrer"
                             className="inline-flex items-center gap-1 text-xs text-primary hover:underline">
                            View on SLIIT RDA <ExternalLink className="h-3 w-3" />
                          </a>
                        )}
                      </div>
                    ))}
                  </CardContent>
                </Card>
              )}
            </>
          )}
        </>
      )}

      {tab === "doi" && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <Search className="h-5 w-5" /> DOI Lookup
            </CardTitle>
            <CardDescription>
              Enter a DOI to fetch authoritative metadata from CrossRef. Returns publisher, authors,
              journal, volume, pages, and full IEEE / APA formatting.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="space-y-2">
              <Label htmlFor="doi-input">DOI</Label>
              <Input
                id="doi-input"
                placeholder="e.g. 10.1145/3411764.3445610"
                value={doi}
                onChange={(e) => setDoi(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && lookupDoi()}
              />
              <p className="text-xs text-muted-foreground">
                Try: <code className="rounded bg-muted px-1.5 py-0.5">10.1145/3411764.3445610</code>{" or "}
                <code className="rounded bg-muted px-1.5 py-0.5">10.1038/s41586-020-2649-2</code>
              </p>
            </div>
            <Button onClick={lookupDoi} disabled={doiLoading || !doi.trim()}>
              <Search className="mr-2 h-4 w-4" />
              {doiLoading ? "Looking up…" : "Fetch from CrossRef"}
            </Button>
            {doiError && (
              <div className="flex items-start gap-2 rounded-md border border-destructive/50 bg-destructive/10 p-3 text-sm text-destructive">
                <AlertCircle className="h-4 w-4 mt-0.5 flex-shrink-0" />
                <span>{doiError}</span>
              </div>
            )}
            <p className="text-xs text-muted-foreground">
              On success you&apos;ll be flipped to the Parse tab with all fields populated.
            </p>
          </CardContent>
        </Card>
      )}

      {tab === "list" && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between gap-3 flex-wrap">
              <div>
                <CardTitle className="text-lg flex items-center gap-2">
                  <ListOrdered className="h-5 w-5" /> Reference List
                </CardTitle>
                <CardDescription>
                  {list.length === 0
                    ? "Parse citations on the first tab and click Add to build a list."
                    : `${list.length} entr${list.length > 1 ? "ies" : "y"} · ${style === "apa" ? "alphabetical (APA)" : "numbered (IEEE)"}`}
                </CardDescription>
              </div>
              {list.length > 0 && (
                <div className="flex gap-2 flex-wrap">
                  <Button size="sm" variant="outline"
                    onClick={() => copy("list", listRendered.map(stripStars).join("\n\n"))}>
                    {copiedKey === "list"
                      ? <><Check className="mr-2 h-4 w-4 text-emerald-600" /> Copied</>
                      : <><Copy className="mr-2 h-4 w-4" /> Copy all</>}
                  </Button>
                  <Button size="sm" variant="outline" onClick={() => downloadList("txt")}>
                    <Download className="mr-2 h-4 w-4" /> .txt
                  </Button>
                  <Button size="sm" variant="outline" onClick={() => downloadList("html")}>
                    <Download className="mr-2 h-4 w-4" /> .html
                  </Button>
                  <Button size="sm" variant="ghost" onClick={() => setList([])}>
                    <Trash2 className="mr-2 h-4 w-4" /> Clear
                  </Button>
                </div>
              )}
            </div>
          </CardHeader>
          <CardContent>
            {list.length === 0 ? (
              <div className="py-8 text-center text-sm text-muted-foreground">
                <ListOrdered className="mx-auto h-10 w-10 text-muted-foreground/40 mb-2" />
                <p>No entries yet.</p>
                <p className="text-xs mt-1">
                  Parse a citation on the first tab and click <strong>Add to reference list</strong>.
                </p>
              </div>
            ) : (
              <div className="space-y-2">
                {listRendered.map((line, i) => (
                  <div key={i} className="rounded-md border bg-muted/30 p-3 text-sm font-serif flex items-start gap-3">
                    <FormattedText text={line} />
                  </div>
                ))}
                <p className="text-xs text-muted-foreground pt-2">
                  Note: removing individual entries — use Clear to start over, or remove from the parser tab&apos;s history.
                </p>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {history.length > 0 && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-base flex items-center gap-2">
                <History className="h-4 w-4" /> Saved citations ({history.length})
              </CardTitle>
              <Button size="sm" variant="ghost" onClick={() => persistHistory([])}>
                <Trash2 className="mr-2 h-4 w-4" /> Clear all
              </Button>
            </div>
            <CardDescription>Stored locally in your browser.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-2">
            {history.slice(0, 8).map((h) => (
              <div key={h.id} className="rounded-md border bg-muted/30 p-3 text-sm flex items-start gap-3">
                <div className="flex-1 min-w-0">
                  <p className="font-serif line-clamp-2">
                    <FormattedText text={style === "apa" ? h.formatted_apa : h.formatted_ieee} />
                  </p>
                  <p className="text-xs text-muted-foreground mt-1">
                    {new Date(h.saved_at).toLocaleDateString()} · {h.parsed.source_type}
                  </p>
                </div>
                <div className="flex gap-1 shrink-0">
                  <Button size="sm" variant="ghost"
                    onClick={() => {
                      setResult({
                        parsed: h.parsed,
                        formatted_apa: h.formatted_apa,
                        formatted_ieee: h.formatted_ieee,
                        in_text_apa: h.in_text_apa,
                        in_text_ieee: h.in_text_ieee,
                        warnings: [],
                        confidence: 1,
                        source: "regex",
                      });
                      setText(h.parsed.raw || "");
                      setTab("parse");
                    }}
                  >
                    Load
                  </Button>
                  <Button size="sm" variant="ghost" onClick={() => persistHistory(history.filter((x) => x.id !== h.id))}>
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      )}
    </div>
  );
}

function FieldRow({
  label, warning, children,
}: { label: string; warning?: string; children: React.ReactNode }) {
  return (
    <div className="space-y-1.5">
      <div className="flex items-center justify-between">
        <Label className="text-xs">{label}</Label>
        {warning && (
          <span className="text-xs text-amber-700 inline-flex items-center gap-1">
            <AlertCircle className="h-3 w-3" /> {warning}
          </span>
        )}
      </div>
      {children}
    </div>
  );
}
