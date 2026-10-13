"use client";

import { BookOpen, Search, FileText, Shield, Network, ShieldCheck } from "lucide-react";
import { FeatureHub, type HubFeature } from "@/components/shared/FeatureHub";

const features: HubFeature[] = [
  {
    title: "Citation Parser",
    desc: "Paste a raw citation to extract authors, title, journal, year, DOI and auto-format to APA/IEEE.",
    icon: BookOpen,
    href: "/citations/parser",
    gradient: "from-blue-500 to-cyan-500",
  },
  {
    title: "Gap Analysis",
    desc: "Enter a research topic to discover under-explored areas using semantic search and clustering.",
    icon: Search,
    href: "/citations/gaps",
    gradient: "from-indigo-500 to-blue-500",
  },
  {
    title: "Proposal Generator",
    desc: "Generate a structured research proposal outline powered by RAG and LLM.",
    icon: FileText,
    href: "/citations/proposal",
    gradient: "from-violet-500 to-indigo-500",
  },
  {
    title: "Plagiarism Checker",
    desc: "Check your text against the research paper corpus for potential similarity issues.",
    icon: Shield,
    href: "/citations/plagiarism",
    gradient: "from-rose-500 to-red-500",
  },
  {
    title: "Mind Map Builder",
    desc: "Extract key concepts from your text and visualize them as an interactive concept graph.",
    icon: Network,
    href: "/citations/mindmap",
    gradient: "from-cyan-500 to-teal-500",
  },
];

export default function CitationsPage() {
  return (
    <FeatureHub
      theme="integrity"
      icon={ShieldCheck}
      title="Research Integrity & Compliance"
      tagline="Cite accurately, uncover research gaps, and draft strong proposals — with confidence that your work stands on solid ground."
      owner="K D T Kariyawasam"
      features={features}
      stats={[
        { label: "Citation styles", value: "APA · IEEE" },
        { label: "Papers indexed", value: "4,200+" },
      ]}
    />
  );
}
