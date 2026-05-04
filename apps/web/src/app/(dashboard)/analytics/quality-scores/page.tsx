"use client";

import { useState, useRef } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Upload, FileText, Sparkles, AlertCircle, CheckCircle2 } from "lucide-react";
import { API_ROUTES, API_GATEWAY_URL } from "@/lib/constants";
import { apiPost } from "@/lib/api";
import { createClient } from "@/lib/supabase/client";

interface TopicPrediction {
  label: string;
  confidence: number;
}

interface AnalysisResponse {
  title?: string;
  proposal_id?: string;
  overall_score: number;
  originality_score: number;
  citation_impact_score: number;
  methodology_score: number;
  clarity_score: number;
  topic?: {
    primary_topic: string;
    confidence: number;
    top_predictions: TopicPrediction[];
  };
  features?: Record<string, number>;
  recommendations?: string[];
  model_info?: { quality_model?: string; topic_model?: string };
  model_version?: string;
}

const DIMENSIONS = [
  { key: "originality_score" as const, label: "Originality", weight: 30, color: "from-purple-500 to-purple-600" },
  { key: "citation_impact_score" as const, label: "Citation Impact", weight: 25, color: "from-blue-500 to-blue-600" },
  { key: "methodology_score" as const, label: "Methodology", weight: 25, color: "from-green-500 to-green-600" },
  { key: "clarity_score" as const, label: "Clarity", weight: 20, color: "from-amber-500 to-amber-600" },
];

function scoreLabel(score: number): { label: string; color: string } {
  if (score >= 0.75) return { label: "Excellent", color: "text-emerald-600" };
  if (score >= 0.6) return { label: "Good", color: "text-blue-600" };
  if (score >= 0.4) return { label: "Fair", color: "text-amber-600" };
  return { label: "Needs Work", color: "text-rose-600" };
}

export default function QualityScoresPage() {
  const [mode, setMode] = useState<"upload" | "text">("upload");
  const [file, setFile] = useState<File | null>(null);
  const [title, setTitle] = useState("");
  const [abstract, setAbstract] = useState("");
  const [authors, setAuthors] = useState("");
  const [year, setYear] = useState("");
  const [result, setResult] = useState<AnalysisResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    if (f) {
      setFile(f);
      if (!title) setTitle(f.name.replace(/\.[^.]+$/, ""));
    }
  };

  const handleAnalyzeText = async () => {
    if (!title.trim() || abstract.length < 50) {
      setError("Title and abstract (≥ 50 characters) required");
      return;
    }
    setLoading(true);
    setError("");
    setResult(null);
    try {
      const data = await apiPost<AnalysisResponse>(API_ROUTES.module4.paperAnalyzeText, {
        title: title.trim(),
        abstract: abstract.trim(),
        authors: authors ? authors.split(",").map((s) => s.trim()) : undefined,
        year: year ? parseInt(year, 10) : undefined,
      });
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Analysis failed");
    } finally {
      setLoading(false);
    }
  };

  const handleAnalyzeFile = async () => {
    if (!file) {
      setError("Please choose a file");
      return;
    }
    setLoading(true);
    setError("");
    setResult(null);
    try {
      const supabase = createClient();
      const { data: { session } } = await supabase.auth.getSession();
      const token = session?.access_token;

      const formData = new FormData();
      formData.append("file", file);
      if (title) formData.append("title", title);
      if (authors) formData.append("authors", authors);
      if (year) formData.append("year", year);

      const res = await fetch(`${API_GATEWAY_URL}${API_ROUTES.module4.paperUpload}`, {
        method: "POST",
        headers: token ? { Authorization: `Bearer ${token}` } : {},
        body: formData,
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({ message: res.statusText }));
        throw new Error(err.message || err.detail || "Upload failed");
      }
      const data = (await res.json()) as AnalysisResponse;
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload analysis failed");
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = () => (mode === "text" ? handleAnalyzeText() : handleAnalyzeFile());

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Quality Scoring</h1>
        <p className="text-muted-foreground">
          Upload a paper (PDF/TXT) or paste abstract text. Get instant quality scores
          across 4 dimensions, computed by an XGBoost model trained on 3,860 SLIIT papers
          (R² &gt; 0.99).
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Submit Paper</CardTitle>
          <CardDescription>Upload a file or paste text directly — no Proposal ID needed.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex gap-2">
            <Button
              variant={mode === "upload" ? "default" : "outline"}
              onClick={() => setMode("upload")}
              size="sm"
            >
              <Upload className="mr-2 h-4 w-4" /> Upload File
            </Button>
            <Button
              variant={mode === "text" ? "default" : "outline"}
              onClick={() => setMode("text")}
              size="sm"
            >
              <FileText className="mr-2 h-4 w-4" /> Paste Text
            </Button>
          </div>

          {mode === "upload" ? (
            <div
              className="rounded-lg border-2 border-dashed p-6 text-center cursor-pointer hover:bg-muted/50"
              onClick={() => fileInputRef.current?.click()}
            >
              <Upload className="mx-auto h-8 w-8 text-muted-foreground" />
              <p className="mt-2 text-sm">
                {file ? (
                  <span className="font-medium">
                    {file.name} ({(file.size / 1024).toFixed(1)} KB)
                  </span>
                ) : (
                  <>Click to upload PDF or TXT (max 20MB)</>
                )}
              </p>
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf,.txt,.md"
                className="hidden"
                onChange={handleFileChange}
              />
            </div>
          ) : (
            <div className="space-y-1">
              <Label htmlFor="abstract">Abstract / Body Text</Label>
              <textarea
                id="abstract"
                className="min-h-[160px] w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm"
                placeholder="Paste paper abstract here (≥ 50 characters)..."
                value={abstract}
                onChange={(e) => setAbstract(e.target.value)}
              />
              <p className="text-xs text-muted-foreground">{abstract.length} characters</p>
            </div>
          )}

          <div className="grid gap-3 md:grid-cols-3">
            <div className="space-y-1">
              <Label htmlFor="title">Title</Label>
              <Input id="title" placeholder="Paper title" value={title} onChange={(e) => setTitle(e.target.value)} />
            </div>
            <div className="space-y-1">
              <Label htmlFor="authors">Authors (comma-separated)</Label>
              <Input id="authors" placeholder="Smith J, Doe A" value={authors} onChange={(e) => setAuthors(e.target.value)} />
            </div>
            <div className="space-y-1">
              <Label htmlFor="year">Year</Label>
              <Input id="year" type="number" placeholder="2024" value={year} onChange={(e) => setYear(e.target.value)} />
            </div>
          </div>

          <Button onClick={handleSubmit} disabled={loading} className="w-full md:w-auto">
            {loading ? "Analyzing..." : (
              <>
                <Sparkles className="mr-2 h-4 w-4" /> Analyze Paper Quality
              </>
            )}
          </Button>

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
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <span className="text-lg">{result.title || "Quality Analysis"}</span>
                <span className={`text-3xl font-bold ${scoreLabel(result.overall_score).color}`}>
                  {(result.overall_score * 100).toFixed(0)}
                  <span className="text-base font-normal text-muted-foreground"> / 100</span>
                </span>
              </CardTitle>
              <CardDescription className={scoreLabel(result.overall_score).color}>
                Overall: {scoreLabel(result.overall_score).label}
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {DIMENSIONS.map((dim) => {
                const score = result[dim.key];
                const pct = Math.round(score * 100);
                return (
                  <div key={dim.key} className="space-y-1">
                    <div className="flex items-center justify-between text-sm">
                      <span className="font-medium">
                        {dim.label}{" "}
                        <span className="text-xs text-muted-foreground">({dim.weight}% weight)</span>
                      </span>
                      <span className={`font-semibold ${scoreLabel(score).color}`}>{pct}%</span>
                    </div>
                    <div className="h-2 rounded-full bg-muted overflow-hidden">
                      <div className={`h-full bg-gradient-to-r ${dim.color}`} style={{ width: `${pct}%` }} />
                    </div>
                  </div>
                );
              })}
            </CardContent>
          </Card>

          {result.topic && (
            <div className="grid gap-4 md:grid-cols-2">
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">Topic Classification</CardTitle>
                  <CardDescription>SBERT trained on 1,533 SLIIT abstracts</CardDescription>
                </CardHeader>
                <CardContent>
                  <p className="text-2xl font-bold capitalize">
                    {result.topic.primary_topic.replace("_", " ")}
                  </p>
                  <p className="mb-3 text-sm text-muted-foreground">
                    {(result.topic.confidence * 100).toFixed(1)}% confidence
                  </p>
                  <div className="space-y-2">
                    {result.topic.top_predictions.map((p) => (
                      <div key={p.label}>
                        <div className="flex justify-between text-xs">
                          <span className="capitalize">{p.label.replace("_", " ")}</span>
                          <span>{(p.confidence * 100).toFixed(1)}%</span>
                        </div>
                        <div className="h-1.5 rounded-full bg-muted overflow-hidden">
                          <div
                            className="h-full bg-gradient-to-r from-emerald-500 to-emerald-600"
                            style={{ width: `${p.confidence * 100}%` }}
                          />
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>

              {result.recommendations && (
                <Card>
                  <CardHeader>
                    <CardTitle className="text-lg">Recommendations</CardTitle>
                    <CardDescription>Improvements suggested by the model</CardDescription>
                  </CardHeader>
                  <CardContent>
                    {result.recommendations.length === 0 ? (
                      <div className="flex items-center gap-2 text-sm text-emerald-600">
                        <CheckCircle2 className="h-4 w-4" /> Strong across all dimensions
                      </div>
                    ) : (
                      <ul className="space-y-2 text-sm">
                        {result.recommendations.map((rec, i) => (
                          <li key={i} className="flex items-start gap-2">
                            <AlertCircle className="h-4 w-4 mt-0.5 flex-shrink-0 text-amber-500" />
                            <span>{rec}</span>
                          </li>
                        ))}
                      </ul>
                    )}
                  </CardContent>
                </Card>
              )}
            </div>
          )}

          {result.features && (
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Extracted Features</CardTitle>
                <CardDescription>Used by the trained quality model</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 gap-2 text-sm md:grid-cols-3 lg:grid-cols-4">
                  {Object.entries(result.features).map(([key, value]) => (
                    <div key={key} className="rounded-md border p-2">
                      <p className="text-xs text-muted-foreground capitalize">{key.replace(/_/g, " ")}</p>
                      <p className="font-mono font-semibold">{value}</p>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </>
      )}
    </div>
  );
}
