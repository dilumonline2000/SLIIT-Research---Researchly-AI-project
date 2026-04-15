"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  BookOpen,
  Users,
  Database,
  LineChart,
  Settings,
  User,
  FileText,
  MessageSquare,
  Sparkles,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { APP_NAME } from "@/lib/constants";

const navGroups = [
  {
    label: "Overview",
    items: [{ href: "/dashboard", label: "Dashboard", icon: LayoutDashboard }],
  },
  {
    label: "Papers & Chat",
    items: [
      { href: "/papers", label: "My Papers", icon: FileText },
      { href: "/papers/upload", label: "Upload PDF" },
      { href: "/chat", label: "Research Chat", icon: MessageSquare },
      { href: "/chat/history", label: "Chat History" },
      { href: "/training", label: "Continuous Training", icon: Sparkles },
    ],
  },
  {
    label: "Module 1 — Integrity",
    items: [
      { href: "/citations", label: "Citations", icon: BookOpen },
      { href: "/citations/parser", label: "Parser" },
      { href: "/citations/gaps", label: "Gap Analysis" },
      { href: "/citations/proposal", label: "Proposal Generator" },
      { href: "/citations/plagiarism", label: "Plagiarism Checker" },
      { href: "/citations/mindmap", label: "Mind Map" },
    ],
  },
  {
    label: "Module 2 — Collaboration",
    items: [
      { href: "/collaboration", label: "Collaboration", icon: Users },
      { href: "/collaboration/supervisor-match", label: "Supervisor Match" },
      { href: "/collaboration/peer-connect", label: "Peer Connect" },
      { href: "/collaboration/feedback", label: "Feedback Sentiment" },
      { href: "/collaboration/effectiveness", label: "Effectiveness" },
    ],
  },
  {
    label: "Module 3 — Data Management",
    items: [
      { href: "/data-management", label: "Data Management", icon: Database },
      { href: "/data-management/pipeline", label: "Pipeline" },
      { href: "/data-management/categorization", label: "Categorization" },
      { href: "/data-management/plagiarism-trends", label: "Plagiarism Trends" },
      { href: "/data-management/summarizer", label: "Summarizer" },
    ],
  },
  {
    label: "Module 4 — Analytics",
    items: [
      { href: "/analytics", label: "Analytics", icon: LineChart },
      { href: "/analytics/trends", label: "Trend Forecast" },
      { href: "/analytics/quality-scores", label: "Quality Scores" },
      { href: "/analytics/dashboards", label: "Dashboards" },
      { href: "/analytics/mind-maps", label: "Concept Maps" },
      { href: "/analytics/predictions", label: "Success Predictions" },
    ],
  },
  {
    label: "Account",
    items: [
      { href: "/profile", label: "Profile", icon: User },
      { href: "/settings", label: "Settings", icon: Settings },
    ],
  },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="hidden h-screen w-64 shrink-0 flex-col border-r bg-card md:flex">
      <div className="flex h-16 shrink-0 items-center gap-2 border-b px-6 font-bold">
        <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-primary-foreground">
          R
        </span>
        {APP_NAME}
      </div>
      <nav className="flex-1 space-y-6 overflow-y-auto p-4 text-sm">
        {navGroups.map((group) => (
          <div key={group.label}>
            <p className="mb-2 px-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              {group.label}
            </p>
            <ul className="space-y-1">
              {group.items.map((item) => {
                const Icon = "icon" in item ? item.icon : null;
                const active = pathname === item.href;
                return (
                  <li key={item.href}>
                    <Link
                      href={item.href}
                      className={cn(
                        "flex items-center gap-2 rounded-md px-3 py-2 transition-colors",
                        active
                          ? "bg-primary text-primary-foreground"
                          : "hover:bg-accent hover:text-accent-foreground",
                        !Icon && "pl-9",
                      )}
                    >
                      {Icon && <Icon className="h-4 w-4" />}
                      <span>{item.label}</span>
                    </Link>
                  </li>
                );
              })}
            </ul>
          </div>
        ))}
      </nav>
    </aside>
  );
}
