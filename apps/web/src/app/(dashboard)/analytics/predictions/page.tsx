"use client";

import { useState, useRef } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Upload, FileText, Sparkles, AlertCircle, CheckCircle2, TrendingUp, AlertTriangle } from "lucide-react";
import { API_ROUTES, API_GATEWAY_URL } from "@/lib/constants";
import { apiPost } from "@/lib/api";
import { createClient } from "@/lib/supabase/client";

interface PredictResponse {
  title?: string;
  success_probability: number;
  prediction: string;
  confidence: number;
  risk_level: string;
  recommendations: string[];
  features: Record<string, number>;
  model_version: string;
}

const RISK_INFO: Record<string, { color: string; bg: string; icon: React.ComponentType<{ className?: string }>; label: string }> = {
  low: { color: "text-emerald-600", bg: "bg-emerald-50 border-emerald-200", icon: CheckCircle2, label: "Low Risk" },
  medium: { color: "text-amber-600", bg: "bg-amber-50 border-amber-200", icon: AlertTriangle, label: "Medium Risk" },
  high: { color: "text-rose-600", bg: "bg-rose-50 border-rose-200", icon: AlertCircle, label: "High Risk" },
  unknown: { color: "text-muted-foreground", bg: "bg-muted", icon: AlertCircle, label: "Unknown" },
};

export default function PredictPage() {
  const [mode, setMode] = useState<"upload" | "text">("upload");
  const [file, setFile] = useState<File | null>(null);
  const [title, setTitle] = useState("");
  const [abstract, setAbstract] = useState("");
  const [authors, setAuthors] = useState("");
  const [year, setYear] = useState("");
  const [result, setResult] = useState<PredictResponse | null>(null);
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

  const handlePredictText = async () => {
    if (!title.trim() || abstract.length < 50) {
      setError("Title and abstract (≥ 50 characters) are required");
      return;
    }
    setLoading(true);
    setError("");
    setResult(null);
    try {
      const data = await apiPost<PredictResponse>(API_ROUTES.module4.predict, {
        title: title.trim(),
        abstract: abstract.trim(),
        authors: authors ? authors.split(",").map((s) => s.trim()) : undefined,
        year: year ? parseInt(year, 10) : undefined,
      });
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Prediction failed");
    } finally {
      setLoading(false);
    }
  };

  const handlePredictFile = async () => {
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

      const res = await fetch(`${API_GATEWAY_URL}${API_ROUTES.module4.predictUpload}`, {
        method: "POST",
        headers: token ? { Authorization: `Bearer ${token}` } : {},
        body: formData,
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({ message: res.statusText }));
        throw new Error(err.message || err.detail || "Upload failed");
      }
      const data = (await res.json()) as PredictResponse;
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload prediction failed");
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = () => (mode === "text" ? handlePredictText() : handlePredictFile());

  const riskInfo = result ? (RISK_INFO[result.risk_level] || RISK_INFO.unknown) : null;
  const RiskIcon = riskInfo?.icon;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Success Prediction</h1>
        <p className="text-muted-foreground">
          Predicts the probability that a research paper or proposal will be{" "}
          <strong>successful</strong> (high quality, methodologically sound, publishable).
          Uses an XGBoost classifier trained on 3,860 SLIIT papers (98% accuracy, ROC-AUC 0.9994).
        </p>
      </div>

      <Card className="border-blue-200 bg-blue-50/50">
        <CardHeader>
          <CardTitle className="text-lg">📊 What does &ldquo;Success&rdquo; mean here?</CardTitle>
        </CardHeader>
        <CardContent className="text-sm space-y-2">
          <p>The model predicts whether a paper meets all 3 quality bars:</p>
          <ul className="ml-4 list-disc space-y-1">
            <li>Overall quality score ≥ 62%</li>
            <li>Substantial abstract (≥ 500 chars)</li>
            <li>Clear methodology (≥ 2 method keywords)</li>
          </ul>
          <p className="pt-2">
            High-risk papers usually need more methodology detail, citations, or longer abstracts.
            The page gives <strong>actionable recommendations</strong> to improve.
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Submit Paper for Prediction</CardTitle>
          <CardDescription>Upload a file (PDF/TXT) or paste text directly</CardDescription>
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
                  <span className="font-medium">{file.name} ({(file.size / 1024).toFixed(1)} KB)</span>
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
              <Label htmlFor="authors">Authors</Label>
              <Input id="authors" placeholder="Smith J, Doe A" value={authors} onChange={(e) => setAuthors(e.target.value)} />
            </div>
            <div className="space-y-1">
              <Label htmlFor="year">Year</Label>
              <Input id="year" type="number" placeholder="2024" value={year} onChange={(e) => setYear(e.target.value)} />
            </div>
          </div>

          <Button onClick={handleSubmit} disabled={loading} className="w-full md:w-auto">
            {loading ? "Predicting..." : (
              <>
                <Sparkles className="mr-2 h-4 w-4" /> Predict Success Probability
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

      {result && riskInfo && RiskIcon && (
        <>
          <Card className={`border-2 ${riskInfo.bg}`}>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between gap-4">
                <div>
                  <p className="text-sm text-muted-foreground">Success Probability</p>
                  <p className={`text-5xl font-bold ${riskInfo.color}`}>
                    {(result.success_probability * 100).toFixed(0)}%
                  </p>
                  <p className="mt-1 text-sm">
                    Prediction:{" "}
                    <strong className="capitalize">{result.prediction.replace("_", " ")}</strong>
                    {" · "}
                    Confidence: {(result.confidence * 100).toFixed(0)}%
                  </p>
                </div>
                <div className={`flex flex-col items-center gap-2 rounded-lg p-4 ${riskInfo.bg}`}>
                  <RiskIcon className={`h-10 w-10 ${riskInfo.color}`} />
                  <span className={`font-semibold ${riskInfo.color}`}>{riskInfo.label}</span>
                </div>
              </div>
              <div className="mt-4 h-3 rounded-full bg-muted overflow-hidden">
                <div
                  className={`h-full transition-all ${
                    result.success_probability >= 0.7 ? "bg-emerald-500"
                    : result.success_probability >= 0.4 ? "bg-amber-500"
                    : "bg-rose-500"
                  }`}
                  style={{ width: `${result.success_probability * 100}%` }}
                />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-lg">
                <TrendingUp className="h-5 w-5" /> Recommendations to Improve
              </CardTitle>
              <CardDescription>Actionable steps based on the model&apos;s analysis</CardDescription>
            </CardHeader>
            <CardContent>
              {result.recommendations.length === 0 ? (
                <p className="text-sm text-emerald-600">No issues detected.</p>
              ) : (
                <ul className="space-y-2 text-sm">
                  {result.recommendations.map((rec, i) => (
                    <li key={i} className="flex items-start gap-2">
                      <span className="mt-1 h-2 w-2 rounded-full bg-primary shrink-0" />
                      <span>{rec}</span>
                    </li>
                  ))}
                </ul>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Extracted Features</CardTitle>
              <CardDescription>Inputs to the trained classifier</CardDescription>
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
              <p className="mt-3 text-xs text-muted-foreground">
                Model: XGBoost · v{result.model_version} · Trained on 3,860 SLIIT papers
              </p>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}
