"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { API_ROUTES } from "@/lib/constants";
import { apiPost } from "@/lib/api";

interface ParsedCitation {
  authors: string[];
  title: string;
  journal: string | null;
  year: number | null;
  volume: string | null;
  pages: string | null;
  doi: string | null;
}

interface ParseResponse {
  parsed: ParsedCitation;
  formatted_apa: string;
  formatted_ieee: string;
  confidence: number;
}

export default function CitationParserPage() {
  const [rawText, setRawText] = useState("");
  const [result, setResult] = useState<ParseResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleParse = async () => {
    if (!rawText.trim()) return;
    setLoading(true);
    setError("");
    try {
      const data = await apiPost<ParseResponse>(API_ROUTES.module1.parseCitation, { raw_text: rawText });
      setResult(data);
    } catch (err: any) {
      setError(err.message || "Failed to parse citation");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Citation Parser</h1>
        <p className="text-muted-foreground">Paste a raw citation to extract structured fields and format as APA/IEEE.</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Input Citation</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="raw-citation">Raw citation text</Label>
            <textarea
              id="raw-citation"
              className="flex min-h-[120px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              placeholder="Smith, J. and Doe, A. (2023). Deep learning for NLP tasks. Journal of AI Research, 45(2), 123-145. doi:10.1234/jair.2023.001"
              value={rawText}
              onChange={(e) => setRawText(e.target.value)}
            />
          </div>
          <Button onClick={handleParse} disabled={loading || !rawText.trim()}>
            {loading ? "Parsing..." : "Parse Citation"}
          </Button>
          {error && <p className="text-sm text-destructive">{error}</p>}
        </CardContent>
      </Card>

      {result && (
        <>
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">
                Extracted Fields
                <span className="ml-2 text-sm font-normal text-muted-foreground">
                  Confidence: {(result.confidence * 100).toFixed(0)}%
                </span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <dl className="grid gap-2 sm:grid-cols-2">
                {result.parsed.authors.length > 0 && (
                  <div>
                    <dt className="text-sm font-medium text-muted-foreground">Authors</dt>
                    <dd className="text-sm">{result.parsed.authors.join("; ")}</dd>
                  </div>
                )}
                {result.parsed.title && (
                  <div>
                    <dt className="text-sm font-medium text-muted-foreground">Title</dt>
                    <dd className="text-sm">{result.parsed.title}</dd>
                  </div>
                )}
                {result.parsed.journal && (
                  <div>
                    <dt className="text-sm font-medium text-muted-foreground">Journal</dt>
                    <dd className="text-sm">{result.parsed.journal}</dd>
                  </div>
                )}
                {result.parsed.year && (
                  <div>
                    <dt className="text-sm font-medium text-muted-foreground">Year</dt>
                    <dd className="text-sm">{result.parsed.year}</dd>
                  </div>
                )}
                {result.parsed.volume && (
                  <div>
                    <dt className="text-sm font-medium text-muted-foreground">Volume</dt>
                    <dd className="text-sm">{result.parsed.volume}</dd>
                  </div>
                )}
                {result.parsed.pages && (
                  <div>
                    <dt className="text-sm font-medium text-muted-foreground">Pages</dt>
                    <dd className="text-sm">{result.parsed.pages}</dd>
                  </div>
                )}
                {result.parsed.doi && (
                  <div>
                    <dt className="text-sm font-medium text-muted-foreground">DOI</dt>
                    <dd className="text-sm">{result.parsed.doi}</dd>
                  </div>
                )}
              </dl>
            </CardContent>
          </Card>

          <div className="grid gap-4 md:grid-cols-2">
            <Card>
              <CardHeader><CardTitle className="text-lg">APA Format</CardTitle></CardHeader>
              <CardContent>
                <p className="text-sm rounded bg-muted p-3">{result.formatted_apa || "—"}</p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader><CardTitle className="text-lg">IEEE Format</CardTitle></CardHeader>
              <CardContent>
                <p className="text-sm rounded bg-muted p-3">{result.formatted_ieee || "—"}</p>
              </CardContent>
            </Card>
          </div>
        </>
      )}
    </div>
  );
}
