"use client";

import { useEffect, useMemo, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Users, Plus, Mail, UserPlus, Loader2, AlertCircle, CheckCircle2,
  Search, X, Sparkles, Layers, Clock, Minus, ArrowLeft, Eye, Send,
  Rocket, Handshake,
} from "lucide-react";
import { API_ROUTES } from "@/lib/constants";
import { apiGet, apiPost } from "@/lib/api";
import { useAuthStore } from "@/stores/authStore";
import { cn } from "@/lib/utils";

// ─── Types ────────────────────────────────────────────────────────────────

interface PeerGroup {
  id: string;
  leader_id: string | null;
  project_title: string;
  project_description: string;
  research_area: string | null;
  current_members: string[];
  current_member_count: number;
  slots_needed: number;
  contact_email: string;
  status: string;
  created_at: string | null;
}

interface JoinResponse {
  request_id: string;
  group_id: string;
  leader_email: string;
  mailto_url: string;
  email_subject: string;
  email_body: string;
}

type Tab = "browse" | "create" | "join";

// ─── Presentation helpers ─────────────────────────────────────────────────

// Each group gets a stable accent colour derived from its id/title
const ACCENTS = [
  { bar: "from-emerald-500 to-teal-400", chip: "bg-emerald-500/10 text-emerald-600 dark:text-emerald-300", avatar: "from-emerald-500 to-teal-500" },
  { bar: "from-indigo-500 to-violet-500", chip: "bg-indigo-500/10 text-indigo-600 dark:text-indigo-300", avatar: "from-indigo-500 to-violet-500" },
  { bar: "from-sky-500 to-cyan-400", chip: "bg-sky-500/10 text-sky-600 dark:text-sky-300", avatar: "from-sky-500 to-cyan-500" },
  { bar: "from-fuchsia-500 to-pink-500", chip: "bg-fuchsia-500/10 text-fuchsia-600 dark:text-fuchsia-300", avatar: "from-fuchsia-500 to-pink-500" },
  { bar: "from-amber-500 to-orange-500", chip: "bg-amber-500/10 text-amber-600 dark:text-amber-300", avatar: "from-amber-500 to-orange-500" },
];

function accentFor(key: string) {
  let h = 0;
  for (let i = 0; i < key.length; i++) h = (h * 31 + key.charCodeAt(i)) >>> 0;
  return ACCENTS[h % ACCENTS.length];
}

function initials(name: string) {
  return name
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((n) => n[0]?.toUpperCase())
    .join("") || "?";
}

function timeAgo(iso: string | null) {
  if (!iso) return null;
  const diff = Date.now() - new Date(iso).getTime();
  if (Number.isNaN(diff)) return null;
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  const days = Math.floor(hrs / 24);
  if (days < 30) return `${days}d ago`;
  return new Date(iso).toLocaleDateString();
}

const textareaCls =
  "flex w-full rounded-lg border border-input bg-background px-3 py-2 text-sm transition-colors placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring";

// ─── Group card (used in browse + live preview) ───────────────────────────

function GroupCard({
  group,
  onJoin,
  preview = false,
}: {
  group: Pick<
    PeerGroup,
    "id" | "project_title" | "project_description" | "research_area" | "current_members" |
    "current_member_count" | "slots_needed" | "contact_email" | "created_at"
  >;
  onJoin?: () => void;
  preview?: boolean;
}) {
  const accent = accentFor(group.id || group.project_title || "x");
  const memberCount = group.current_member_count || group.current_members.length;
  const teamSize = memberCount + group.slots_needed;
  const fill = teamSize ? memberCount / teamSize : 0;
  const posted = timeAgo(group.created_at);

  return (
    <Card className="group relative flex h-full flex-col overflow-hidden transition-all duration-200 hover:-translate-y-0.5 hover:shadow-lg">
      <div className={cn("absolute inset-x-0 top-0 h-1.5 bg-gradient-to-r", accent.bar)} />

      <div className="flex flex-1 flex-col gap-4 p-5 pt-6">
        {/* Title row */}
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0">
            {group.research_area ? (
              <span className={cn("mb-2 inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-semibold", accent.chip)}>
                <Layers className="h-3 w-3" /> {group.research_area}
              </span>
            ) : (
              <span className="mb-2 inline-flex items-center gap-1 rounded-full bg-muted px-2.5 py-0.5 text-xs font-medium text-muted-foreground">
                <Layers className="h-3 w-3" /> Open topic
              </span>
            )}
            <h3 className="break-words text-lg font-bold leading-snug">
              {group.project_title || "Your project title"}
            </h3>
          </div>
          <div className="flex shrink-0 flex-col items-center rounded-xl border bg-muted/40 px-3 py-1.5 text-center">
            <span className="font-display text-xl font-bold leading-none text-emerald-600 dark:text-emerald-400">
              {group.slots_needed}
            </span>
            <span className="mt-0.5 text-[11px] font-medium uppercase tracking-wide text-muted-foreground">
              {group.slots_needed === 1 ? "slot" : "slots"}
            </span>
          </div>
        </div>

        {/* Description */}
        <p className="line-clamp-3 text-sm leading-relaxed text-muted-foreground">
          {group.project_description || "Describe your research question and the teammates you need."}
        </p>

        {/* Team progress */}
        <div className="mt-auto space-y-2.5 rounded-xl bg-muted/40 p-3">
          <div className="flex items-center justify-between gap-2">
            <div className="flex -space-x-2">
              {group.current_members.slice(0, 4).map((m) => (
                <span
                  key={m}
                  title={m}
                  className={cn(
                    "flex h-8 w-8 items-center justify-center rounded-full border-2 border-card bg-gradient-to-br text-[11px] font-bold text-white",
                    accent.avatar,
                  )}
                >
                  {initials(m)}
                </span>
              ))}
              {Array.from({ length: Math.min(group.slots_needed, 3) }).map((_, i) => (
                <span
                  key={`open-${i}`}
                  className="flex h-8 w-8 items-center justify-center rounded-full border-2 border-dashed border-muted-foreground/40 bg-card text-muted-foreground"
                  title="Open slot"
                >
                  <Plus className="h-3.5 w-3.5" />
                </span>
              ))}
            </div>
            <span className="text-xs font-medium text-muted-foreground">
              {memberCount}/{teamSize} members
            </span>
          </div>
          <div className="h-1.5 w-full overflow-hidden rounded-full bg-border">
            <div
              className={cn("h-full rounded-full bg-gradient-to-r transition-all", accent.bar)}
              style={{ width: `${Math.round(fill * 100)}%` }}
            />
          </div>
          {group.current_members.length > 0 && (
            <p className="truncate text-xs text-muted-foreground">
              {group.current_members.slice(0, 5).join(" · ")}
              {group.current_members.length > 5 && ` +${group.current_members.length - 5}`}
            </p>
          )}
        </div>

        {/* Footer */}
        <div className="flex flex-col gap-3 border-t pt-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="min-w-0 space-y-1 text-xs text-muted-foreground">
            <p className="flex min-w-0 items-center gap-1.5">
              <Mail className="h-3.5 w-3.5 shrink-0" />
              <span className="truncate">{group.contact_email || "leader@example.com"}</span>
            </p>
            {posted && (
              <p className="flex items-center gap-1.5">
                <Clock className="h-3.5 w-3.5 shrink-0" /> Posted {posted}
              </p>
            )}
          </div>
          <Button
            size="sm"
            onClick={onJoin}
            disabled={preview}
            className="w-full shrink-0 bg-gradient-to-r from-emerald-600 to-teal-600 text-white hover:from-emerald-500 hover:to-teal-500 sm:w-auto"
          >
            <UserPlus className="mr-2 h-4 w-4" /> Express Interest
          </Button>
        </div>
      </div>
    </Card>
  );
}

function GroupCardSkeleton() {
  return (
    <Card className="overflow-hidden p-5">
      <div className="space-y-4 animate-pulse">
        <div className="h-4 w-24 rounded-full bg-muted" />
        <div className="h-5 w-2/3 rounded bg-muted" />
        <div className="space-y-2">
          <div className="h-3 w-full rounded bg-muted" />
          <div className="h-3 w-5/6 rounded bg-muted" />
        </div>
        <div className="h-20 rounded-xl bg-muted" />
        <div className="h-9 rounded-lg bg-muted" />
      </div>
    </Card>
  );
}

// ─── Component ────────────────────────────────────────────────────────────

export default function PeerConnectPage() {
  const { user, profile } = useAuthStore();
  const [tab, setTab] = useState<Tab>("browse");

  // Browse state
  const [groups, setGroups] = useState<PeerGroup[]>([]);
  const [loadingGroups, setLoadingGroups] = useState(false);
  const [search, setSearch] = useState("");
  const [areaFilter, setAreaFilter] = useState<string | null>(null);

  // Create state
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [researchArea, setResearchArea] = useState("");
  const [members, setMembers] = useState<string[]>([]);
  const [memberInput, setMemberInput] = useState("");
  const [slotsNeeded, setSlotsNeeded] = useState(2);
  const [contactEmail, setContactEmail] = useState("");
  const [creating, setCreating] = useState(false);
  const [createError, setCreateError] = useState("");
  const [createSuccess, setCreateSuccess] = useState("");

  // Join state
  const [joinTarget, setJoinTarget] = useState<PeerGroup | null>(null);
  const [joinName, setJoinName] = useState("");
  const [joinEmail, setJoinEmail] = useState("");
  const [joinMessage, setJoinMessage] = useState("");
  const [joining, setJoining] = useState(false);
  const [joinError, setJoinError] = useState("");
  const [joinResult, setJoinResult] = useState<JoinResponse | null>(null);

  // Pre-fill from auth
  useEffect(() => {
    const profileObj = profile as { full_name?: string; email?: string } | null;
    if (profileObj?.full_name) {
      if (!members.length) setMembers([profileObj.full_name]);
      setJoinName((prev) => prev || profileObj.full_name || "");
    }
    const email = user?.email || profileObj?.email || "";
    if (email) {
      setContactEmail((prev) => prev || email);
      setJoinEmail((prev) => prev || email);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user?.email, profile]);

  const loadGroups = async () => {
    setLoadingGroups(true);
    try {
      const data = await apiGet<{ groups: PeerGroup[]; total: number }>(
        `${API_ROUTES.module2.listGroups}?status=open&limit=50`,
      );
      setGroups(data.groups);
    } catch {
      setGroups([]);
    } finally {
      setLoadingGroups(false);
    }
  };

  useEffect(() => {
    if (tab === "browse") loadGroups();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tab]);

  const filteredGroups = groups.filter((g) => {
    if (areaFilter && (g.research_area || "").trim() !== areaFilter) return false;
    if (!search.trim()) return true;
    const q = search.toLowerCase();
    return (
      g.project_title.toLowerCase().includes(q) ||
      (g.research_area || "").toLowerCase().includes(q) ||
      g.project_description.toLowerCase().includes(q)
    );
  });

  // Hero + filter stats
  const areas = useMemo(
    () =>
      Array.from(
        new Set(groups.map((g) => (g.research_area || "").trim()).filter(Boolean)),
      ).sort(),
    [groups],
  );
  const totalSlots = groups.reduce((n, g) => n + (g.slots_needed || 0), 0);
  const totalMembers = groups.reduce(
    (n, g) => n + (g.current_member_count || g.current_members.length || 0),
    0,
  );

  const handleAddMember = () => {
    const m = memberInput.trim();
    if (m && !members.includes(m)) {
      setMembers([...members, m]);
      setMemberInput("");
    }
  };

  const handleRemoveMember = (m: string) => {
    setMembers(members.filter((x) => x !== m));
  };

  const handleCreate = async () => {
    setCreateError("");
    setCreateSuccess("");
    if (!title.trim() || !description.trim() || !contactEmail.trim() || slotsNeeded < 1) {
      setCreateError("Fill in title, description, contact email, and at least one slot.");
      return;
    }
    setCreating(true);
    try {
      const profileObj = profile as { full_name?: string } | null;
      const created = await apiPost<PeerGroup>(API_ROUTES.module2.createGroup, {
        leader_id: user?.id ?? null,
        leader_name: profileObj?.full_name ?? null,
        project_title: title.trim(),
        project_description: description.trim(),
        research_area: researchArea.trim() || null,
        current_members: members,
        slots_needed: slotsNeeded,
        contact_email: contactEmail.trim(),
      });
      setCreateSuccess(`Group "${created.project_title}" published.`);
      // Reset form (keep email + name as next-time defaults)
      setTitle("");
      setDescription("");
      setResearchArea("");
      setSlotsNeeded(2);
      setTimeout(() => setTab("browse"), 800);
    } catch (err) {
      setCreateError(err instanceof Error ? err.message : "Could not create group.");
    } finally {
      setCreating(false);
    }
  };

  const openJoinDialog = (g: PeerGroup) => {
    setJoinTarget(g);
    setTab("join");
    setJoinError("");
    setJoinResult(null);
  };

  const handleJoinSubmit = async () => {
    if (!joinTarget) return;
    setJoinError("");
    if (!joinName.trim() || !joinEmail.trim()) {
      setJoinError("Please enter your name and email.");
      return;
    }
    setJoining(true);
    try {
      const data = await apiPost<JoinResponse>(API_ROUTES.module2.joinGroup(joinTarget.id), {
        requester_id: user?.id ?? null,
        requester_name: joinName.trim(),
        requester_email: joinEmail.trim(),
        message: joinMessage.trim() || null,
      });
      setJoinResult(data);
      // Open the user's email client
      window.location.href = data.mailto_url;
    } catch (err) {
      setJoinError(err instanceof Error ? err.message : "Could not send the request.");
    } finally {
      setJoining(false);
    }
  };

  const tabs: { id: Tab; label: string; icon: typeof Search; show: boolean }[] = [
    { id: "browse", label: "Browse Groups", icon: Search, show: true },
    { id: "create", label: "Create a Group", icon: Plus, show: true },
    { id: "join", label: joinTarget ? `Join: ${joinTarget.project_title.slice(0, 24)}` : "Join", icon: UserPlus, show: tab === "join" && !!joinTarget },
  ];

  return (
    <div className="space-y-6 pb-8">
      {/* ── Hero ─────────────────────────────────────────────── */}
      <section className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-emerald-600 via-teal-600 to-cyan-600 p-5 text-white shadow-lg sm:p-8">
        <div className="pointer-events-none absolute -right-20 -top-20 h-72 w-72 rounded-full bg-white/10 blur-2xl" />
        <div className="pointer-events-none absolute -bottom-24 left-1/4 h-60 w-60 rounded-full bg-cyan-300/20 blur-3xl" />
        {/* Decorative connected-nodes motif */}
        <svg className="pointer-events-none absolute right-6 top-1/2 hidden h-40 w-56 -translate-y-1/2 opacity-30 lg:block" viewBox="0 0 220 160" fill="none" aria-hidden="true">
          <path d="M30 120 L90 40 L160 90 L200 30 M90 40 L120 140 L160 90" stroke="white" strokeWidth="1.5" strokeDasharray="4 4" />
          {[[30, 120], [90, 40], [160, 90], [200, 30], [120, 140]].map(([x, y]) => (
            <circle key={`${x}-${y}`} cx={x} cy={y} r="9" fill="white" fillOpacity="0.85" />
          ))}
        </svg>

        <div className="relative max-w-2xl">
          <span className="inline-flex items-center gap-1.5 rounded-full bg-white/15 px-3 py-1 text-xs font-medium backdrop-blur-sm">
            <Handshake className="h-3.5 w-3.5" /> Mentor Network · Peer Connect
          </span>
          <h1 className="mt-3 text-2xl font-bold leading-tight sm:text-3xl lg:text-4xl">
            Find your research squad
          </h1>
          <p className="mt-2 text-sm leading-relaxed text-white/85 sm:text-base">
            Form a research group or join one that&apos;s open. Browse teams looking for members,
            or publish your own and let classmates apply.
          </p>
        </div>

        <div className="relative mt-5 grid grid-cols-3 gap-2 sm:flex sm:flex-wrap sm:gap-3">
          {[
            { label: "Open groups", value: groups.length, icon: Users },
            { label: "Open slots", value: totalSlots, icon: UserPlus },
            { label: "Researchers", value: totalMembers, icon: Sparkles },
          ].map((s) => (
            <div key={s.label} className="rounded-xl border border-white/20 bg-white/10 px-3 py-2.5 backdrop-blur-sm sm:min-w-[140px] sm:px-4">
              <p className="flex items-center gap-1.5 text-[11px] font-medium uppercase tracking-wide text-white/75">
                <s.icon className="h-3.5 w-3.5" /> <span className="truncate">{s.label}</span>
              </p>
              <p className="mt-0.5 font-display text-2xl font-bold tabular-nums">
                {loadingGroups && groups.length === 0 ? "…" : s.value}
              </p>
            </div>
          ))}
        </div>
      </section>

      {/* ── Segmented tabs ───────────────────────────────────── */}
      <div className="no-scrollbar flex w-full gap-1 overflow-x-auto rounded-xl border bg-card p-1 shadow-soft sm:w-fit">
        {tabs.filter((t) => t.show).map((t) => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            className={cn(
              "flex flex-1 shrink-0 items-center justify-center gap-2 whitespace-nowrap rounded-lg px-4 py-2 text-sm font-medium transition-all sm:flex-none",
              tab === t.id
                ? "bg-gradient-to-r from-emerald-600 to-teal-600 text-white shadow-sm"
                : "text-muted-foreground hover:bg-accent hover:text-accent-foreground",
            )}
          >
            <t.icon className="h-4 w-4" /> {t.label}
          </button>
        ))}
      </div>

      {/* ── Browse ───────────────────────────────────────────── */}
      {tab === "browse" && (
        <div className="space-y-4">
          <div className="space-y-3">
            <div className="relative">
              <Search className="pointer-events-none absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                placeholder="Search groups by title, research area, or description..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="h-12 rounded-xl bg-card pl-11 pr-28 shadow-soft"
              />
              <div className="absolute right-3 top-1/2 flex -translate-y-1/2 items-center gap-2">
                {loadingGroups && <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />}
                <span className="rounded-full bg-emerald-500/10 px-2.5 py-1 text-xs font-semibold text-emerald-600 dark:text-emerald-300">
                  {filteredGroups.length} open
                </span>
              </div>
            </div>

            {areas.length > 0 && (
              <div className="no-scrollbar -mx-1 flex gap-2 overflow-x-auto px-1 pb-1">
                <button
                  onClick={() => setAreaFilter(null)}
                  className={cn(
                    "shrink-0 rounded-full border px-3.5 py-1.5 text-xs font-medium transition-colors",
                    areaFilter === null
                      ? "border-transparent bg-foreground text-background"
                      : "bg-card hover:bg-accent",
                  )}
                >
                  All areas
                </button>
                {areas.map((a) => (
                  <button
                    key={a}
                    onClick={() => setAreaFilter(areaFilter === a ? null : a)}
                    className={cn(
                      "shrink-0 rounded-full border px-3.5 py-1.5 text-xs font-medium transition-colors",
                      areaFilter === a
                        ? "border-transparent bg-gradient-to-r from-emerald-600 to-teal-600 text-white"
                        : "bg-card hover:bg-accent",
                    )}
                  >
                    {a}
                  </button>
                ))}
              </div>
            )}
          </div>

          {loadingGroups && groups.length === 0 && (
            <div className="grid gap-4 md:grid-cols-2 2xl:grid-cols-3">
              <GroupCardSkeleton />
              <GroupCardSkeleton />
            </div>
          )}

          {filteredGroups.length === 0 && !loadingGroups && (
            <Card className="border-dashed">
              <CardContent className="flex flex-col items-center gap-3 py-12 text-center">
                <span className="flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-emerald-500 to-teal-500 text-white shadow-md">
                  <Users className="h-7 w-7" />
                </span>
                <div>
                  <p className="font-semibold">
                    No open groups{search || areaFilter ? " match your search" : " right now"}
                  </p>
                  <p className="mt-1 text-sm text-muted-foreground">
                    Start a team and let classmates with matching interests find you.
                  </p>
                </div>
                <Button onClick={() => setTab("create")} className="bg-gradient-to-r from-emerald-600 to-teal-600 text-white">
                  <Plus className="mr-2 h-4 w-4" /> Be the first to publish a group
                </Button>
              </CardContent>
            </Card>
          )}

          <div className="grid gap-4 md:grid-cols-2 2xl:grid-cols-3">
            {filteredGroups.map((g) => (
              <GroupCard key={g.id} group={g} onJoin={() => openJoinDialog(g)} />
            ))}
          </div>
        </div>
      )}

      {/* ── Create ───────────────────────────────────────────── */}
      {tab === "create" && (
        <div className="grid gap-6 lg:grid-cols-5">
          <Card className="lg:col-span-3">
            <CardHeader>
              <CardTitle className="flex items-center gap-2.5 text-lg">
                <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-emerald-500 to-teal-500 text-white">
                  <Rocket className="h-4 w-4" />
                </span>
                Publish a Research Group
              </CardTitle>
              <CardDescription>
                Tell other students about your project, who&apos;s already on board, and how many more
                members you need.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-5">
              <div className="space-y-2">
                <Label htmlFor="title">Project title *</Label>
                <Input
                  id="title"
                  placeholder="e.g., Federated learning for medical imaging"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="desc">Project description *</Label>
                <textarea
                  id="desc"
                  className={cn(textareaCls, "min-h-[120px]")}
                  placeholder="What's the research question? What will the team do? What kinds of teammates are you looking for?"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                />
              </div>

              <div className="grid gap-4 md:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="area">Research area</Label>
                  <Input
                    id="area"
                    placeholder="e.g., Machine Learning, IoT Security"
                    value={researchArea}
                    onChange={(e) => setResearchArea(e.target.value)}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="slots">More members needed *</Label>
                  <div className="flex items-center gap-2">
                    <Button
                      type="button"
                      variant="outline"
                      size="icon"
                      aria-label="Fewer slots"
                      onClick={() => setSlotsNeeded((n) => Math.max(1, n - 1))}
                    >
                      <Minus className="h-4 w-4" />
                    </Button>
                    <Input
                      id="slots"
                      type="number"
                      min={1}
                      max={10}
                      value={slotsNeeded}
                      onChange={(e) => setSlotsNeeded(Math.max(1, parseInt(e.target.value || "1", 10)))}
                      className="text-center font-semibold"
                    />
                    <Button
                      type="button"
                      variant="outline"
                      size="icon"
                      aria-label="More slots"
                      onClick={() => setSlotsNeeded((n) => Math.min(10, n + 1))}
                    >
                      <Plus className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              </div>

              <div className="space-y-2">
                <Label>Current members</Label>
                <div className="flex gap-2">
                  <Input
                    placeholder="Add a name and press Enter"
                    value={memberInput}
                    onChange={(e) => setMemberInput(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter") {
                        e.preventDefault();
                        handleAddMember();
                      }
                    }}
                  />
                  <Button type="button" variant="outline" onClick={handleAddMember}>
                    Add
                  </Button>
                </div>
                {members.length > 0 && (
                  <div className="flex flex-wrap gap-1.5 pt-1">
                    {members.map((m) => (
                      <span
                        key={m}
                        className="inline-flex items-center gap-1.5 rounded-full border bg-muted/50 py-1 pl-1 pr-2.5 text-xs font-medium"
                      >
                        <span className="flex h-5 w-5 items-center justify-center rounded-full bg-gradient-to-br from-emerald-500 to-teal-500 text-[10px] font-bold text-white">
                          {initials(m)}
                        </span>
                        {m}
                        <button
                          type="button"
                          onClick={() => handleRemoveMember(m)}
                          className="hover:text-destructive"
                          aria-label={`Remove ${m}`}
                        >
                          <X className="h-3 w-3" />
                        </button>
                      </span>
                    ))}
                  </div>
                )}
              </div>

              <div className="space-y-2">
                <Label htmlFor="contact">Contact email *</Label>
                <Input
                  id="contact"
                  type="email"
                  placeholder="leader@example.com"
                  value={contactEmail}
                  onChange={(e) => setContactEmail(e.target.value)}
                />
                <p className="text-xs text-muted-foreground">
                  Interested students will email you here when they want to join.
                </p>
              </div>

              <Button
                onClick={handleCreate}
                disabled={creating}
                size="lg"
                className="w-full bg-gradient-to-r from-emerald-600 to-teal-600 text-white hover:from-emerald-500 hover:to-teal-500 sm:w-auto"
              >
                {creating ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" /> Publishing…
                  </>
                ) : (
                  <>
                    <Rocket className="mr-2 h-4 w-4" /> Publish Group
                  </>
                )}
              </Button>

              {createError && (
                <div className="flex items-start gap-2 rounded-lg border border-destructive/50 bg-destructive/10 p-3 text-sm text-destructive">
                  <AlertCircle className="mt-0.5 h-4 w-4 flex-shrink-0" />
                  <span>{createError}</span>
                </div>
              )}
              {createSuccess && (
                <div className="flex items-start gap-2 rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-800 dark:border-emerald-900/60 dark:bg-emerald-950/30 dark:text-emerald-200">
                  <CheckCircle2 className="mt-0.5 h-4 w-4 flex-shrink-0" />
                  <span>{createSuccess}</span>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Live preview */}
          <div className="lg:col-span-2">
            <div className="space-y-3 lg:sticky lg:top-2">
              <p className="flex items-center gap-2 text-sm font-semibold text-muted-foreground">
                <Eye className="h-4 w-4" /> Live preview — how others will see it
              </p>
              <GroupCard
                preview
                group={{
                  id: title || "preview",
                  project_title: title,
                  project_description: description,
                  research_area: researchArea.trim() || null,
                  current_members: members,
                  current_member_count: members.length,
                  slots_needed: slotsNeeded,
                  contact_email: contactEmail,
                  created_at: null,
                }}
              />
              <div className="rounded-xl border border-dashed p-4 text-xs leading-relaxed text-muted-foreground">
                <p className="mb-1 font-semibold text-foreground">Tips for a great listing</p>
                Be specific about the research question, the skills you&apos;re missing
                (e.g. ML, UI, data collection), and your weekly time commitment.
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ── Join ─────────────────────────────────────────────── */}
      {tab === "join" && joinTarget && (
        <div className="grid gap-6 lg:grid-cols-5">
          {/* Group summary */}
          <div className="space-y-3 lg:col-span-2">
            <button
              onClick={() => setTab("browse")}
              className="inline-flex items-center gap-1.5 text-sm font-medium text-muted-foreground hover:text-foreground"
            >
              <ArrowLeft className="h-4 w-4" /> Back to groups
            </button>
            <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-slate-900 via-emerald-950 to-teal-900 p-5 text-white shadow-lg">
              <div className="pointer-events-none absolute -right-10 -top-10 h-40 w-40 rounded-full bg-emerald-400/20 blur-2xl" />
              <p className="relative text-xs font-semibold uppercase tracking-wider text-emerald-300">
                You&apos;re applying to
              </p>
              <h2 className="relative mt-1 text-xl font-bold leading-snug">{joinTarget.project_title}</h2>
              {joinTarget.research_area && (
                <span className="relative mt-2 inline-flex items-center gap-1 rounded-full bg-white/10 px-2.5 py-0.5 text-xs">
                  <Layers className="h-3 w-3" /> {joinTarget.research_area}
                </span>
              )}
              <p className="relative mt-3 text-sm leading-relaxed text-white/80">
                {joinTarget.project_description}
              </p>
              <div className="relative mt-4 flex flex-wrap gap-2 text-xs">
                <span className="rounded-full bg-white/10 px-2.5 py-1">
                  {joinTarget.current_member_count || joinTarget.current_members.length} member(s)
                </span>
                <span className="rounded-full bg-emerald-400/20 px-2.5 py-1 text-emerald-200">
                  {joinTarget.slots_needed} slot{joinTarget.slots_needed > 1 ? "s" : ""} open
                </span>
              </div>
              <p className="relative mt-4 flex min-w-0 items-center gap-1.5 border-t border-white/10 pt-3 text-xs text-white/75">
                <Mail className="h-3.5 w-3.5 shrink-0" /> Will email:
                <strong className="truncate text-white">{joinTarget.contact_email}</strong>
              </p>
            </div>
          </div>

          {/* Join form */}
          <Card className="lg:col-span-3">
            <CardHeader>
              <CardTitle className="flex items-center gap-2.5 text-lg">
                <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-emerald-500 to-teal-500 text-white">
                  <UserPlus className="h-4 w-4" />
                </span>
                Express Interest
              </CardTitle>
              <CardDescription>
                We&apos;ll record your request and open your email client to send a message to the
                group leader.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-4 md:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="join-name">Your name *</Label>
                  <Input
                    id="join-name"
                    value={joinName}
                    onChange={(e) => setJoinName(e.target.value)}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="join-email">Your email *</Label>
                  <Input
                    id="join-email"
                    type="email"
                    value={joinEmail}
                    onChange={(e) => setJoinEmail(e.target.value)}
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="join-msg">Optional message</Label>
                <textarea
                  id="join-msg"
                  className={cn(textareaCls, "min-h-[120px]")}
                  placeholder="Tell the leader why you'd be a good fit, what you bring, what your availability looks like..."
                  value={joinMessage}
                  onChange={(e) => setJoinMessage(e.target.value)}
                />
              </div>

              <div className="flex flex-col gap-2 sm:flex-row">
                <Button
                  onClick={handleJoinSubmit}
                  disabled={joining}
                  className="bg-gradient-to-r from-emerald-600 to-teal-600 text-white hover:from-emerald-500 hover:to-teal-500"
                >
                  {joining ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" /> Sending…
                    </>
                  ) : (
                    <>
                      <Send className="mr-2 h-4 w-4" /> Send Interest Email
                    </>
                  )}
                </Button>
                <Button variant="outline" onClick={() => setTab("browse")}>
                  Cancel
                </Button>
              </div>

              {joinError && (
                <div className="flex items-start gap-2 rounded-lg border border-destructive/50 bg-destructive/10 p-3 text-sm text-destructive">
                  <AlertCircle className="mt-0.5 h-4 w-4 flex-shrink-0" />
                  <span>{joinError}</span>
                </div>
              )}
              {joinResult && (
                <div className="space-y-2 rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-900 dark:border-emerald-900/60 dark:bg-emerald-950/30 dark:text-emerald-100">
                  <div className="flex items-center gap-2 font-medium">
                    <CheckCircle2 className="h-4 w-4" />
                    Request recorded.
                  </div>
                  <p className="text-xs">
                    We tried to open your default email client with a pre-filled message. If nothing
                    happened, click here to send manually:
                  </p>
                  <a
                    href={joinResult.mailto_url}
                    className="inline-flex items-center gap-1 rounded-md border border-emerald-300 bg-white px-2.5 py-1 text-xs font-medium text-emerald-800 hover:bg-emerald-100 dark:border-emerald-800 dark:bg-emerald-950 dark:text-emerald-200 dark:hover:bg-emerald-900"
                  >
                    <Mail className="h-3 w-3" /> Email {joinResult.leader_email}
                  </a>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
