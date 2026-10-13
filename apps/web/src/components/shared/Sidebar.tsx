"use client";

import { useEffect } from "react";
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
  LogOut,
  X,
  Compass,
  Library,
  ShieldCheck,
  Handshake,
  Archive,
  Telescope,
  UserCircle2,
  type LucideIcon,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { APP_NAME } from "@/lib/constants";
import { useAuth } from "@/hooks/useAuth";

interface NavItem {
  href: string;
  label: string;
  icon?: LucideIcon;
}

interface NavGroup {
  label: string;
  /** Short hint shown under the group name */
  hint: string;
  groupIcon: LucideIcon;
  /** Tailwind gradient for the group's icon chip */
  accent: string;
  items: NavItem[];
}

const navGroups: NavGroup[] = [
  {
    label: "Home Base",
    hint: "Your research at a glance",
    groupIcon: Compass,
    accent: "from-sky-500 to-indigo-500",
    items: [{ href: "/dashboard", label: "Dashboard", icon: LayoutDashboard }],
  },
  {
    label: "Research Library",
    hint: "Papers, chat & training",
    groupIcon: Library,
    accent: "from-indigo-500 to-violet-500",
    items: [
      { href: "/papers", label: "My Papers", icon: FileText },
      { href: "/papers/upload", label: "Upload PDF" },
      { href: "/chat", label: "Research Chat", icon: MessageSquare },
      { href: "/chat/history", label: "Chat History" },
      { href: "/training", label: "Continuous Training", icon: Sparkles },
    ],
  },
  {
    label: "Integrity Lab",
    hint: "Citations, gaps & proposals",
    groupIcon: ShieldCheck,
    accent: "from-blue-500 to-cyan-500",
    items: [
      { href: "/citations", label: "Citations", icon: BookOpen },
      { href: "/citations/parser", label: "Parser" },
      { href: "/citations/gaps", label: "Gap Analysis" },
      { href: "/citations/proposal", label: "Proposal Generator" },
      // { href: "/citations/plagiarism", label: "Plagiarism Checker" },
      { href: "/citations/mindmap", label: "Mind Map" },
    ],
  },
  {
    label: "Mentor Network",
    hint: "Supervisors, peers & feedback",
    groupIcon: Handshake,
    accent: "from-emerald-500 to-teal-500",
    items: [
      { href: "/collaboration", label: "Collaboration", icon: Users },
      { href: "/collaboration/supervisor-match", label: "Supervisor Match" },
      { href: "/collaboration/peer-connect", label: "Peer Connect" },
      { href: "/collaboration/feedback", label: "Feedback Sentiment" },
      { href: "/collaboration/effectiveness", label: "Effectiveness" },
    ],
  },
  {
    label: "Knowledge Vault",
    hint: "Organise & summarise data",
    groupIcon: Archive,
    accent: "from-amber-500 to-orange-500",
    items: [
      { href: "/data-management", label: "Data Management", icon: Database },
      // { href: "/data-management/pipeline", label: "Pipeline" },
      { href: "/data-management/categorization", label: "Categorization" },
      { href: "/data-management/plagiarism-trends", label: "Plagiarism Trends" },
      { href: "/data-management/summarizer", label: "Summarizer" },
    ],
  },
  {
    label: "Insight Studio",
    hint: "Quality, success & trends",
    groupIcon: Telescope,
    accent: "from-purple-500 to-fuchsia-500",
    items: [
      { href: "/analytics", label: "Analytics", icon: LineChart },
      { href: "/analytics/quality-scores", label: "Paper Quality Scoring" },
      { href: "/analytics/predictions", label: "Success Prediction" },
      { href: "/analytics/trends", label: "Trend Forecast" },
      // { href: "/analytics/dashboards", label: "Dashboards" },
      // { href: "/analytics/mind-maps", label: "Concept Maps" },
    ],
  },
  {
    label: "Your Space",
    hint: "Profile & preferences",
    groupIcon: UserCircle2,
    accent: "from-slate-500 to-slate-700",
    items: [
      { href: "/profile", label: "Profile", icon: User },
      { href: "/settings", label: "Settings", icon: Settings },
    ],
  },
];

interface SidebarProps {
  open?: boolean;
  onClose?: () => void;
}

function Brand() {
  return (
    <Link href="/dashboard" className="flex items-center gap-2.5 min-w-0">
      <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-500 via-violet-500 to-fuchsia-500 font-display text-base font-bold text-white shadow-glow">
        R
      </span>
      <span className="min-w-0 leading-tight">
        <span className="block truncate font-display text-[17px] font-bold tracking-tight">
          {APP_NAME}
        </span>
        <span className="block text-[11px] font-medium text-muted-foreground">
          Learn · Research · Grow
        </span>
      </span>
    </Link>
  );
}

// Shared nav list — used by both desktop and mobile drawer
function NavLinks({ pathname, onLinkClick }: { pathname: string; onLinkClick?: () => void }) {
  return (
    <nav className="flex-1 space-y-5 overflow-y-auto px-3 py-4 text-sm">
      {navGroups.map((group) => {
        const GroupIcon = group.groupIcon;
        return (
          <div key={group.label}>
            <div className="mb-1.5 flex items-center gap-2.5 px-2">
              <span
                className={cn(
                  "flex h-6 w-6 shrink-0 items-center justify-center rounded-md bg-gradient-to-br text-white shadow-sm",
                  group.accent,
                )}
              >
                <GroupIcon className="h-3.5 w-3.5" />
              </span>
              <div className="min-w-0">
                <p className="truncate font-display text-[13px] font-semibold tracking-tight text-foreground/90">
                  {group.label}
                </p>
                <p className="truncate text-[11px] leading-tight text-muted-foreground">
                  {group.hint}
                </p>
              </div>
            </div>
            <ul className="space-y-0.5">
              {group.items.map((item) => {
                const Icon = item.icon;
                const active = pathname === item.href;
                return (
                  <li key={item.href}>
                    <Link
                      href={item.href}
                      onClick={onLinkClick}
                      aria-current={active ? "page" : undefined}
                      className={cn(
                        "group relative flex items-center gap-2.5 rounded-lg px-3 py-2 text-[14px] transition-all",
                        active
                          ? "bg-primary/10 font-semibold text-primary dark:bg-primary/15"
                          : "text-foreground/75 hover:bg-accent hover:text-accent-foreground",
                        !Icon && "pl-[2.6rem]",
                      )}
                    >
                      {active && (
                        <span className="absolute left-0 top-1/2 h-5 w-1 -translate-y-1/2 rounded-r-full bg-gradient-to-b from-indigo-500 to-fuchsia-500" />
                      )}
                      {Icon && (
                        <Icon
                          className={cn(
                            "h-4 w-4 shrink-0",
                            active ? "text-primary" : "text-muted-foreground group-hover:text-accent-foreground",
                          )}
                        />
                      )}
                      <span className="truncate">{item.label}</span>
                    </Link>
                  </li>
                );
              })}
            </ul>
          </div>
        );
      })}
    </nav>
  );
}

export function Sidebar({ open = false, onClose }: SidebarProps) {
  const pathname = usePathname();
  const { signOut, profile } = useAuth();

  // Close the mobile drawer with Escape
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && onClose?.();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  const handleSignOut = async () => {
    if (window.confirm("Sign out of Researchly AI?")) {
      await signOut();
    }
  };

  const name = profile?.full_name || "User";
  const initials = name
    .split(" ")
    .filter(Boolean)
    .slice(0, 2)
    .map((n) => n[0]?.toUpperCase())
    .join("");

  const footer = (
    <div className="shrink-0 border-t p-3">
      {profile && (
        <div className="mb-2 flex items-center gap-3 rounded-xl bg-muted/60 px-3 py-2.5">
          <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-indigo-500 to-fuchsia-500 text-xs font-bold text-white">
            {initials || "U"}
          </span>
          <div className="min-w-0 text-sm">
            <p className="truncate font-semibold">{name}</p>
            <p className="text-xs capitalize text-muted-foreground">{profile.role || "student"}</p>
          </div>
        </div>
      )}
      <button
        onClick={handleSignOut}
        className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium text-rose-600 transition-colors hover:bg-rose-50 dark:text-rose-400 dark:hover:bg-rose-950/40"
      >
        <LogOut className="h-4 w-4" />
        <span>Sign Out</span>
      </button>
    </div>
  );

  return (
    <>
      {/* ── DESKTOP sidebar ── */}
      <aside className="hidden h-screen w-64 shrink-0 flex-col border-r bg-[hsl(var(--sidebar))] md:flex lg:w-[17rem]">
        <div className="flex h-16 shrink-0 items-center border-b px-5">
          <Brand />
        </div>
        <NavLinks pathname={pathname} />
        {footer}
      </aside>

      {/* ── MOBILE drawer — only shown when open=true, hidden on md+ ── */}
      {open && (
        <div className="fixed inset-0 z-50 md:hidden" role="dialog" aria-modal="true">
          {/* Backdrop */}
          <div
            className="animate-fade-in absolute inset-0 bg-slate-950/60 backdrop-blur-sm"
            onClick={onClose}
            aria-hidden="true"
          />
          {/* Drawer panel */}
          <aside className="animate-drawer-in absolute inset-y-0 left-0 flex w-[86vw] max-w-[20rem] flex-col border-r bg-[hsl(var(--sidebar))] shadow-2xl">
            <div className="flex h-16 shrink-0 items-center gap-2 border-b px-4">
              <div className="flex-1 min-w-0">
                <Brand />
              </div>
              <button
                onClick={onClose}
                className="flex h-10 w-10 items-center justify-center rounded-lg hover:bg-accent"
                aria-label="Close menu"
              >
                <X className="h-5 w-5" />
              </button>
            </div>
            <NavLinks pathname={pathname} onLinkClick={onClose} />
            {footer}
          </aside>
        </div>
      )}
    </>
  );
}
