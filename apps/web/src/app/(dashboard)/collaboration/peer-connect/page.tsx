"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import {
  Users, Plus, Mail, UserPlus, Loader2, AlertCircle, CheckCircle2,
  Search, X,
} from "lucide-react";
import { API_ROUTES } from "@/lib/constants";
import { apiGet, apiPost } from "@/lib/api";
import { useAuthStore } from "@/stores/authStore";

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

// ─── Component ────────────────────────────────────────────────────────────

export default function PeerConnectPage() {
  const { user, profile } = useAuthStore();
  const [tab, setTab] = useState<Tab>("browse");

  // Browse state
  const [groups, setGroups] = useState<PeerGroup[]>([]);
  const [loadingGroups, setLoadingGroups] = useState(false);
  const [search, setSearch] = useState("");

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
    if (!search.trim()) return true;
    const q = search.toLowerCase();
    return (
      g.project_title.toLowerCase().includes(q) ||
      (g.research_area || "").toLowerCase().includes(q) ||
      g.project_description.toLowerCase().includes(q)
    );
  });

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

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="rounded-2xl bg-gradient-to-br from-emerald-600 via-teal-600 to-cyan-600 p-6 text-white shadow-lg">
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <Users className="h-7 w-7" /> Peer Connect
        </h1>
        <p className="mt-1 text-sm text-white/85 max-w-2xl">
          Form a research group or join one that&apos;s open. Browse groups looking for members, or
          publish your own and let others apply.
        </p>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 flex-wrap">
        <Button variant={tab === "browse" ? "default" : "outline"} size="sm" onClick={() => setTab("browse")}>
          <Search className="mr-2 h-4 w-4" /> Browse Groups
        </Button>
        <Button variant={tab === "create" ? "default" : "outline"} size="sm" onClick={() => setTab("create")}>
          <Plus className="mr-2 h-4 w-4" /> Create a Group
        </Button>
        {tab === "join" && joinTarget && (
          <Button variant="default" size="sm" onClick={() => setTab("join")}>
            <UserPlus className="mr-2 h-4 w-4" /> Join: {joinTarget.project_title.slice(0, 30)}
          </Button>
        )}
      </div>

      {/* ── Browse ───────────────────────────────────────────── */}
      {tab === "browse" && (
        <>
          <Card>
            <CardContent className="p-3 flex items-center gap-3">
              <Search className="h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search groups by title, research area, or description..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="flex-1 border-0 focus-visible:ring-0 shadow-none"
              />
              {loadingGroups && <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />}
              <Badge variant="outline" className="shrink-0">
                {filteredGroups.length} open
              </Badge>
            </CardContent>
          </Card>

          {filteredGroups.length === 0 && !loadingGroups && (
            <Card>
              <CardContent className="py-10 text-center space-y-2">
                <Users className="mx-auto h-8 w-8 text-muted-foreground/50" />
                <p className="text-sm text-muted-foreground">
                  No open groups{search ? " match your search" : " right now"}.
                </p>
                <Button variant="outline" size="sm" onClick={() => setTab("create")}>
                  <Plus className="mr-2 h-4 w-4" /> Be the first to publish a group
                </Button>
              </CardContent>
            </Card>
          )}

          <div className="grid gap-4 md:grid-cols-2">
            {filteredGroups.map((g) => (
              <Card key={g.id} className="hover:shadow-md transition-shadow">
                <CardHeader className="pb-3">
                  <div className="flex items-start justify-between gap-2">
                    <CardTitle className="text-base">{g.project_title}</CardTitle>
                    <Badge variant="secondary" className="shrink-0 bg-emerald-50 text-emerald-700 border-emerald-200">
                      {g.slots_needed} slot{g.slots_needed > 1 ? "s" : ""} open
                    </Badge>
                  </div>
                  {g.research_area && (
                    <CardDescription className="text-xs">{g.research_area}</CardDescription>
                  )}
                </CardHeader>
                <CardContent className="space-y-3 text-sm">
                  <p className="line-clamp-3 text-muted-foreground">{g.project_description}</p>

                  {g.current_members.length > 0 && (
                    <div className="space-y-1">
                      <p className="text-xs font-medium">
                        Members ({g.current_member_count}):
                      </p>
                      <div className="flex flex-wrap gap-1">
                        {g.current_members.slice(0, 5).map((m) => (
                          <span key={m} className="rounded-full bg-muted px-2 py-0.5 text-xs">
                            {m}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  <div className="flex items-center justify-between pt-2 border-t">
                    <span className="text-xs text-muted-foreground inline-flex items-center gap-1">
                      <Mail className="h-3 w-3" /> {g.contact_email}
                    </span>
                    <Button size="sm" onClick={() => openJoinDialog(g)}>
                      <UserPlus className="mr-2 h-4 w-4" /> Express Interest
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </>
      )}

      {/* ── Create ───────────────────────────────────────────── */}
      {tab === "create" && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <Plus className="h-5 w-5" /> Publish a Research Group
            </CardTitle>
            <CardDescription>
              Tell other students about your project, who&apos;s already on board, and how many more
              members you need.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
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
                className="flex min-h-[120px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
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
                <Input
                  id="slots"
                  type="number"
                  min={1}
                  max={10}
                  value={slotsNeeded}
                  onChange={(e) => setSlotsNeeded(Math.max(1, parseInt(e.target.value || "1", 10)))}
                />
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
                      className="inline-flex items-center gap-1 rounded-full border bg-muted/50 px-2.5 py-1 text-xs"
                    >
                      {m}
                      <button
                        type="button"
                        onClick={() => handleRemoveMember(m)}
                        className="hover:text-destructive"
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

            <Button onClick={handleCreate} disabled={creating} size="lg">
              {creating ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" /> Publishing…
                </>
              ) : (
                <>
                  <Plus className="mr-2 h-4 w-4" /> Publish Group
                </>
              )}
            </Button>

            {createError && (
              <div className="flex items-start gap-2 rounded-md border border-destructive/50 bg-destructive/10 p-3 text-sm text-destructive">
                <AlertCircle className="h-4 w-4 mt-0.5 flex-shrink-0" />
                <span>{createError}</span>
              </div>
            )}
            {createSuccess && (
              <div className="flex items-start gap-2 rounded-md border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-800">
                <CheckCircle2 className="h-4 w-4 mt-0.5 flex-shrink-0" />
                <span>{createSuccess}</span>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* ── Join ─────────────────────────────────────────────── */}
      {tab === "join" && joinTarget && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <UserPlus className="h-5 w-5" /> Express Interest
            </CardTitle>
            <CardDescription>
              You&apos;re applying to join <strong>{joinTarget.project_title}</strong>. We&apos;ll
              record your request and open your email client to send a message to the group leader.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="rounded-md border bg-muted/30 p-3 text-sm">
              <p className="font-medium">{joinTarget.project_title}</p>
              {joinTarget.research_area && (
                <p className="text-xs text-muted-foreground mt-0.5">{joinTarget.research_area}</p>
              )}
              <p className="text-xs text-muted-foreground mt-2">{joinTarget.project_description}</p>
              <p className="text-xs mt-2 inline-flex items-center gap-1">
                <Mail className="h-3 w-3" /> Will email: <strong>{joinTarget.contact_email}</strong>
              </p>
            </div>

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
                className="flex min-h-[100px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                placeholder="Tell the leader why you'd be a good fit, what you bring, what your availability looks like..."
                value={joinMessage}
                onChange={(e) => setJoinMessage(e.target.value)}
              />
            </div>

            <div className="flex gap-2">
              <Button onClick={handleJoinSubmit} disabled={joining}>
                {joining ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" /> Sending…
                  </>
                ) : (
                  <>
                    <Mail className="mr-2 h-4 w-4" /> Send Interest Email
                  </>
                )}
              </Button>
              <Button variant="outline" onClick={() => setTab("browse")}>
                Cancel
              </Button>
            </div>

            {joinError && (
              <div className="flex items-start gap-2 rounded-md border border-destructive/50 bg-destructive/10 p-3 text-sm text-destructive">
                <AlertCircle className="h-4 w-4 mt-0.5 flex-shrink-0" />
                <span>{joinError}</span>
              </div>
            )}
            {joinResult && (
              <div className="space-y-2 rounded-md border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-900">
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
                  className="inline-flex items-center gap-1 rounded-md border border-emerald-300 bg-white px-2.5 py-1 text-xs font-medium hover:bg-emerald-100"
                >
                  <Mail className="h-3 w-3" /> Email {joinResult.leader_email}
                </a>
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
