"use client";

import { useState } from "react";
import Link from "next/link";
import { BookOpen, Search, FileText, Shield, Network, ArrowRight } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

const features = [
  {
    title: "Citation Parser",
    desc: "Paste a raw citation to extract authors, title, journal, year, DOI and auto-format to APA/IEEE.",
    icon: BookOpen,
    href: "/citations/parser",
    color: "bg-blue-500",
  },
  {
    title: "Gap Analysis",
    desc: "Enter a research topic to discover under-explored areas using semantic search and clustering.",
    icon: Search,
    href: "/citations/gaps",
    color: "bg-indigo-500",
  },
  {
    title: "Proposal Generator",
    desc: "Generate a structured research proposal outline powered by RAG and LLM.",
    icon: FileText,
    href: "/citations/proposal",
    color: "bg-violet-500",
  },
  {
    title: "Plagiarism Checker",
    desc: "Check your text against the research paper corpus for potential similarity issues.",
    icon: Shield,
    href: "/citations/plagiarism",
    color: "bg-red-500",
  },
  {
    title: "Mind Map Builder",
    desc: "Extract key concepts from your text and visualize them as an interactive concept graph.",
    icon: Network,
    href: "/citations/mindmap",
    color: "bg-cyan-500",
  },
];

export default function CitationsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Research Integrity & Compliance</h1>
        <p className="text-muted-foreground">Module 1 · Owner: K D T Kariyawasam</p>
      </div>
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {features.map((f) => (
          <Link key={f.title} href={f.href}>
            <Card className="h-full transition-all hover:shadow-md hover:-translate-y-0.5 cursor-pointer">
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className={`flex h-10 w-10 items-center justify-center rounded-lg ${f.color} text-white`}>
                    <f.icon className="h-5 w-5" />
                  </div>
                  <ArrowRight className="h-4 w-4 text-muted-foreground" />
                </div>
                <CardTitle className="pt-3 text-lg">{f.title}</CardTitle>
                <CardDescription>{f.desc}</CardDescription>
              </CardHeader>
            </Card>
          </Link>
        ))}
      </div>
    </div>
  );
}
