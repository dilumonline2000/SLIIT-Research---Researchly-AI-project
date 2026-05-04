"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Download, FileText, Sparkles, AlertCircle, FileDown, Copy, Check } from "lucide-react";
import { API_ROUTES } from "@/lib/constants";
import { apiPost } from "@/lib/api";

interface GeneratedProposal {
  problem_statement: string;
  objectives: string[];
  methodology: string;
  expected_outcomes: string;
  retrieved_paper_ids: string[];
}

export default function ProposalGeneratorPage() {
  const [topic, setTopic] = useState("");
  const [domain, setDomain] = useState("");
  const [authorName, setAuthorName] = useState("");
  const [result, setResult] = useState<GeneratedProposal | null>(null);
  const [loading, setLoading] = useState(false);
  const [downloading, setDownloading] = useState(false);
  const [error, setError] = useState("");
  const [copied, setCopied] = useState(false);

  const handleGenerate = async () => {
    if (!topic.trim()) {
      setError("Please enter a research topic");
      return;
    }
    setLoading(true);
    setError("");
    setResult(null);
    try {
      const data = await apiPost<GeneratedProposal>(API_ROUTES.module1.generateProposal, {
        topic,
        domain: domain || undefined,
        user_id: "current",
      });
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Generation failed");
    } finally {
      setLoading(false);
    }
  };

  const handleCopyAll = () => {
    if (!result) return;
    const text = formatProposalText(topic, result, authorName);
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownloadPDF = async () => {
    if (!result) return;
    setDownloading(true);
    try {
      // Dynamic import to avoid SSR issues
      const { default: jsPDF } = await import("jspdf");
      const doc = new jsPDF({ unit: "pt", format: "a4" });

      const pageWidth = doc.internal.pageSize.getWidth();
      const margin = 50;
      const usableWidth = pageWidth - margin * 2;
      let y = margin;

      // Title
      doc.setFontSize(18);
      doc.setFont("helvetica", "bold");
      const titleLines = doc.splitTextToSize(`Research Proposal: ${topic}`, usableWidth);
      doc.text(titleLines, margin, y);
      y += titleLines.length * 22;

      // Author + Date
      doc.setFontSize(10);
      doc.setFont("helvetica", "normal");
      doc.setTextColor(100);
      if (authorName) {
        doc.text(`Author: ${authorName}`, margin, y);
        y += 14;
      }
      doc.text(`Generated: ${new Date().toLocaleDateString()}`, margin, y);
      if (domain) {
        doc.text(`Domain: ${domain}`, margin + 200, y);
      }
      y += 24;

      // Helper for sections
      const addSection = (title: string, body: string | string[]) => {
        // Page break check
        if (y > 740) {
          doc.addPage();
          y = margin;
        }

        doc.setFontSize(13);
        doc.setFont("helvetica", "bold");
        doc.setTextColor(0);
        doc.text(title, margin, y);
        y += 18;

        doc.setFontSize(11);
        doc.setFont("helvetica", "normal");
        doc.setTextColor(40);

        if (Array.isArray(body)) {
          body.forEach((item, idx) => {
            const lines = doc.splitTextToSize(`${idx + 1}. ${item}`, usableWidth - 10);
            if (y + lines.length * 14 > 800) {
              doc.addPage();
              y = margin;
            }
            doc.text(lines, margin + 5, y);
            y += lines.length * 14 + 4;
          });
        } else {
          const lines = doc.splitTextToSize(body, usableWidth);
          for (let i = 0; i < lines.length; i++) {
            if (y > 800) {
              doc.addPage();
              y = margin;
            }
            doc.text(lines[i], margin, y);
            y += 14;
          }
        }
        y += 12;
      };

      addSection("1. Problem Statement", result.problem_statement || "—");
      if (result.objectives.length > 0) {
        addSection("2. Objectives", result.objectives);
      }
      if (result.methodology) {
        addSection("3. Methodology", result.methodology);
      }
      if (result.expected_outcomes) {
        addSection("4. Expected Outcomes", result.expected_outcomes);
      }

      // Footer with paper count
      if (result.retrieved_paper_ids.length > 0) {
        if (y > 760) {
          doc.addPage();
          y = margin;
        }
        doc.setFontSize(9);
        doc.setTextColor(120);
        doc.text(
          `Generated based on ${result.retrieved_paper_ids.length} retrieved papers from corpus.`,
          margin,
          y,
        );
      }

      // Page numbers
      const pageCount = doc.getNumberOfPages();
      for (let i = 1; i <= pageCount; i++) {
        doc.setPage(i);
        doc.setFontSize(8);
        doc.setTextColor(150);
        doc.text(
          `Page ${i} of ${pageCount} · Researchly AI`,
          pageWidth / 2,
          820,
          { align: "center" },
        );
      }

      const safeFilename = topic.replace(/[^a-z0-9]/gi, "_").slice(0, 50);
      doc.save(`proposal_${safeFilename}_${Date.now()}.pdf`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "PDF generation failed");
    } finally {
      setDownloading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <FileText className="h-6 w-6" /> Research Proposal Generator
        </h1>
        <p className="text-muted-foreground">
          Generate a structured research proposal with problem statement, objectives,
          methodology, and expected outcomes. Export as PDF for submission.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Research Details</CardTitle>
          <CardDescription>Provide your research topic and optional context</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="topic">Research Topic *</Label>
            <Input
              id="topic"
              placeholder="e.g., Privacy-preserving federated learning for healthcare"
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
            />
          </div>
          <div className="grid gap-3 md:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="domain">Domain (optional)</Label>
              <Input
                id="domain"
                placeholder="e.g., Computer Science, Healthcare"
                value={domain}
                onChange={(e) => setDomain(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="author">Author Name (for PDF)</Label>
              <Input
                id="author"
                placeholder="Your full name"
                value={authorName}
                onChange={(e) => setAuthorName(e.target.value)}
              />
            </div>
          </div>
          <Button onClick={handleGenerate} disabled={loading || !topic.trim()}>
            {loading ? "Generating..." : (
              <>
                <Sparkles className="mr-2 h-4 w-4" /> Generate Proposal
              </>
            )}
          </Button>
          {error && (
            <div className="flex items-start gap-2 rounded-md border border-destructive/50 bg-destructive/10 p-3 text-sm text-destructive">
              <AlertCircle className="h-4 w-4 mt-0.5" />
              <span>{error}</span>
            </div>
          )}
        </CardContent>
      </Card>

      {result && (
        <>
          <Card className="border-emerald-200 bg-emerald-50/50">
            <CardContent className="pt-6">
              <div className="flex items-center justify-between flex-wrap gap-3">
                <div>
                  <p className="text-sm font-medium text-emerald-800">
                    Proposal generated successfully ✓
                  </p>
                  <p className="text-xs text-emerald-700">
                    {result.retrieved_paper_ids.length > 0
                      ? `Based on ${result.retrieved_paper_ids.length} papers from your corpus`
                      : "No relevant corpus papers found — using model knowledge only"}
                  </p>
                </div>
                <div className="flex gap-2">
                  <Button size="sm" variant="outline" onClick={handleCopyAll}>
                    {copied ? <Check className="mr-2 h-4 w-4 text-emerald-600" /> : <Copy className="mr-2 h-4 w-4" />}
                    {copied ? "Copied!" : "Copy All"}
                  </Button>
                  <Button size="sm" onClick={handleDownloadPDF} disabled={downloading}>
                    <FileDown className="mr-2 h-4 w-4" />
                    {downloading ? "Generating PDF..." : "Download PDF"}
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-lg">1. Problem Statement</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm leading-relaxed whitespace-pre-wrap">{result.problem_statement}</p>
            </CardContent>
          </Card>

          {result.objectives.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">2. Objectives</CardTitle>
              </CardHeader>
              <CardContent>
                <ol className="list-decimal list-inside space-y-2 text-sm leading-relaxed">
                  {result.objectives.map((obj, i) => (
                    <li key={i}>{obj}</li>
                  ))}
                </ol>
              </CardContent>
            </Card>
          )}

          {result.methodology && (
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">3. Methodology</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm leading-relaxed whitespace-pre-wrap">{result.methodology}</p>
              </CardContent>
            </Card>
          )}

          {result.expected_outcomes && (
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">4. Expected Outcomes</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm leading-relaxed whitespace-pre-wrap">{result.expected_outcomes}</p>
              </CardContent>
            </Card>
          )}

          <div className="flex justify-center pt-4">
            <Button size="lg" onClick={handleDownloadPDF} disabled={downloading}>
              <Download className="mr-2 h-5 w-5" />
              {downloading ? "Generating PDF..." : "Download as PDF"}
            </Button>
          </div>
        </>
      )}
    </div>
  );
}

function formatProposalText(topic: string, p: GeneratedProposal, author: string): string {
  let txt = `RESEARCH PROPOSAL\n${"=".repeat(60)}\n`;
  txt += `Topic: ${topic}\n`;
  if (author) txt += `Author: ${author}\n`;
  txt += `Generated: ${new Date().toLocaleDateString()}\n\n`;
  txt += `1. PROBLEM STATEMENT\n${"-".repeat(40)}\n${p.problem_statement}\n\n`;
  if (p.objectives.length > 0) {
    txt += `2. OBJECTIVES\n${"-".repeat(40)}\n`;
    p.objectives.forEach((o, i) => (txt += `${i + 1}. ${o}\n`));
    txt += "\n";
  }
  if (p.methodology) {
    txt += `3. METHODOLOGY\n${"-".repeat(40)}\n${p.methodology}\n\n`;
  }
  if (p.expected_outcomes) {
    txt += `4. EXPECTED OUTCOMES\n${"-".repeat(40)}\n${p.expected_outcomes}\n\n`;
  }
  return txt;
}
