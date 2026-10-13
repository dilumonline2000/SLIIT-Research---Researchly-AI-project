"use client";

import { useEffect, useRef, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { User, Mail, Briefcase, AlertCircle, Building2, Sparkles, CheckCircle2 } from "lucide-react";
import { createClient } from "@/lib/supabase/client";
import { useAuthStore } from "@/stores/authStore";

/** Resolve to the promise's value, or null if it takes longer than `ms`. */
function withTimeout<T>(promise: Promise<T>, ms: number): Promise<T | null> {
  return new Promise((resolve, reject) => {
    const t = setTimeout(() => resolve(null), ms);
    promise.then(
      (v) => { clearTimeout(t); resolve(v); },
      (e) => { clearTimeout(t); reject(e); },
    );
  });
}

interface ProfileRow {
  id: string;
  full_name: string | null;
  role: string | null;
  department: string | null;
  research_interests: string[] | null;
  avatar_url: string | null;
}

export default function ProfilePage() {
  const [profile, setProfile] = useState<ProfileRow | null>(null);
  const [email, setEmail] = useState("");
  const [fullName, setFullName] = useState("");
  const [department, setDepartment] = useState("");
  const [interests, setInterests] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const loadedRef = useRef(false);
  const storeUser = useAuthStore((s) => s.user);
  const storeProfile = useAuthStore((s) => s.profile);
  const setStoreProfile = useAuthStore((s) => s.setProfile);

  const applyProfile = (user: { id: string; email?: string | null; user_metadata?: Record<string, unknown> }, row: ProfileRow | null) => {
    const p: ProfileRow = {
      id: user.id,
      full_name: row?.full_name ?? (user.user_metadata?.full_name as string | undefined) ?? "",
      role: row?.role ?? "student",
      department: row?.department ?? "",
      research_interests: row?.research_interests ?? [],
      avatar_url: row?.avatar_url ?? null,
    };
    setEmail(user.email || "");
    setProfile(p);
    setFullName(p.full_name || "");
    setDepartment(p.department || "");
    setInterests((p.research_interests || []).join(", "));
  };

  useEffect(() => {
    // Wait until we know who the user is (from the shared auth store, or a
    // bounded session lookup below) — then load exactly once.
    if (loadedRef.current) return;

    // 1) Instant render from the auth store the Navbar/Sidebar already filled
    if (storeUser) {
      loadedRef.current = true;
      applyProfile(storeUser, (storeProfile as unknown as ProfileRow | null) ?? null);
      setLoading(false);
    }

    // 2) Refresh from the database in the background (bounded by a timeout so
    //    the page can never spin forever)
    const refresh = async () => {
      const supabase = createClient();
      let user = storeUser;
      if (!user) {
        const session = await withTimeout(supabase.auth.getSession(), 6000);
        user = session?.data.session?.user ?? null;
        if (!user) {
          if (session) {
            setError("Not signed in. Please log in to view your profile.");
            setLoading(false);
          }
          return; // timed out — the store will fill shortly and re-run this effect
        }
        loadedRef.current = true;
      }

      const res = await withTimeout(
        Promise.resolve(
          supabase
            .from("profiles")
            .select("id, full_name, role, department, research_interests, avatar_url")
            .eq("id", user.id)
            .limit(1),
        ),
        8000,
      );
      if (res?.error) console.warn("Profile fetch warning:", res.error.message);
      const row = (res?.data && res.data.length > 0 ? res.data[0] : null) as ProfileRow | null;
      // Only overwrite the form if we actually got fresh data (or had nothing)
      if (row || !storeUser) applyProfile(user, row);
      setLoading(false);
    };

    refresh().catch((err) => {
      console.error("Profile load error:", err);
      if (!storeUser) setError(err instanceof Error ? err.message : "Failed to load profile");
      setLoading(false);
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [storeUser]);

  const handleSave = async () => {
    if (!profile) return;
    setSaving(true);
    setMessage("");
    setError("");
    try {
      const supabase = createClient();
      // Cast to any to bypass strict generated-types check for untyped profiles table
      const { error: upsertError } = await (supabase.from("profiles") as any).upsert({
        id: profile.id,
        full_name: fullName,
        department,
        research_interests: interests.split(",").map((s: string) => s.trim()).filter(Boolean),
        role: profile.role || "student",
        updated_at: new Date().toISOString(),
      });
      if (upsertError) throw new Error(upsertError.message);
      setMessage("Profile updated successfully.");
      setProfile((p) => p ? { ...p, full_name: fullName, department } : p);
      // Keep the Navbar / Sidebar name in sync without a reload
      const interestsArr = interests.split(",").map((s: string) => s.trim()).filter(Boolean);
      const current = useAuthStore.getState().profile;
      setStoreProfile({
        ...(current ?? {}),
        id: profile.id,
        full_name: fullName,
        department,
        research_interests: interestsArr,
        role: profile.role || "student",
      } as never);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save");
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <h1 className="text-3xl font-bold">Profile</h1>
        <Card>
          <CardContent className="py-12 text-center text-muted-foreground">
            <div className="flex items-center justify-center gap-2">
              <div className="h-4 w-4 animate-spin rounded-full border-2 border-primary border-t-transparent" />
              Loading profile…
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (error && !profile) {
    return (
      <div className="space-y-6">
        <h1 className="text-3xl font-bold">Profile</h1>
        <Card>
          <CardContent className="py-8">
            <div className="flex items-start gap-2 text-destructive">
              <AlertCircle className="h-5 w-5 mt-0.5" />
              <div>
                <p className="font-semibold">Could not load profile</p>
                <p className="text-sm">{error}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  const displayName = fullName.trim() || "Your Name";
  const initials =
    displayName
      .split(/\s+/)
      .filter(Boolean)
      .slice(0, 2)
      .map((n) => n[0]?.toUpperCase())
      .join("") || "U";
  const interestList = interests
    .split(",")
    .map((s) => s.trim())
    .filter(Boolean);

  return (
    <div className="space-y-6 pb-8">
      {/* Identity card */}
      <section className="relative overflow-hidden rounded-2xl border bg-card shadow-soft">
        <div className="relative h-28 bg-gradient-to-br from-indigo-600 via-violet-600 to-fuchsia-600 sm:h-36">
          <div
            className="absolute inset-0 opacity-[0.12]"
            style={{
              backgroundImage: "radial-gradient(circle at 1px 1px, white 1px, transparent 0)",
              backgroundSize: "22px 22px",
            }}
          />
        </div>
        <div className="relative px-5 pb-5 sm:px-7 sm:pb-6">
          <div className="-mt-12 flex flex-col gap-4 sm:-mt-14 sm:flex-row sm:items-end">
            <span className="flex h-24 w-24 shrink-0 items-center justify-center rounded-2xl border-4 border-card bg-gradient-to-br from-indigo-500 to-fuchsia-500 font-display text-3xl font-bold text-white shadow-lg sm:h-28 sm:w-28">
              {initials}
            </span>
            <div className="min-w-0 flex-1 sm:pb-1">
              <h1 className="truncate text-2xl font-bold sm:text-3xl">{displayName}</h1>
              <div className="mt-1 flex flex-wrap items-center gap-x-4 gap-y-1 text-sm text-muted-foreground">
                <span className="inline-flex items-center gap-1.5 capitalize">
                  <Briefcase className="h-3.5 w-3.5" /> {profile?.role || "student"}
                </span>
                {department && (
                  <span className="inline-flex items-center gap-1.5">
                    <Building2 className="h-3.5 w-3.5" /> {department}
                  </span>
                )}
                {email && (
                  <span className="inline-flex min-w-0 items-center gap-1.5">
                    <Mail className="h-3.5 w-3.5 shrink-0" /> <span className="truncate">{email}</span>
                  </span>
                )}
              </div>
            </div>
          </div>
          {interestList.length > 0 && (
            <div className="mt-4 flex flex-wrap gap-2">
              {interestList.map((i) => (
                <span
                  key={i}
                  className="rounded-full bg-violet-500/10 px-3 py-1 text-xs font-medium text-violet-700 dark:text-violet-300"
                >
                  {i}
                </span>
              ))}
            </div>
          )}
        </div>
      </section>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2.5 text-lg">
            <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-slate-600 to-indigo-600 text-white">
              <User className="h-4 w-4" />
            </span>
            Personal Details
          </CardTitle>
          <CardDescription>Update your name, department, and research interests.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-5">
          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="fullName">Full Name</Label>
              <Input
                id="fullName"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                placeholder="Your full name"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="department" className="flex items-center gap-1.5">
                <Building2 className="h-3.5 w-3.5" /> Department
              </Label>
              <Input
                id="department"
                placeholder="e.g., Computer Science"
                value={department}
                onChange={(e) => setDepartment(e.target.value)}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="email" className="flex items-center gap-1.5">
                <Mail className="h-3.5 w-3.5" /> Email
              </Label>
              <Input id="email" value={email} disabled className="bg-muted" />
            </div>

            <div className="space-y-2">
              <Label htmlFor="role" className="flex items-center gap-1.5">
                <Briefcase className="h-3.5 w-3.5" /> Role
              </Label>
              <Input id="role" value={profile?.role || "student"} disabled className="bg-muted capitalize" />
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="interests" className="flex items-center gap-1.5">
              <Sparkles className="h-3.5 w-3.5" /> Research Interests (comma-separated)
            </Label>
            <Input
              id="interests"
              placeholder="e.g., Machine Learning, NLP, IoT"
              value={interests}
              onChange={(e) => setInterests(e.target.value)}
            />
            <p className="text-xs text-muted-foreground">
              Used to personalise supervisor matching and research suggestions.
            </p>
          </div>

          <div className="flex flex-col gap-3 border-t pt-4 sm:flex-row sm:items-center">
            <Button
              onClick={handleSave}
              disabled={saving}
              size="lg"
              className="w-full bg-gradient-to-r from-indigo-600 to-violet-600 text-white hover:from-indigo-500 hover:to-violet-500 sm:w-auto"
            >
              {saving ? "Saving…" : "Save Changes"}
            </Button>
            {message && (
              <p className="inline-flex items-center gap-1.5 text-sm font-medium text-emerald-600 dark:text-emerald-400">
                <CheckCircle2 className="h-4 w-4" /> {message}
              </p>
            )}
            {error && <p className="text-sm text-destructive">{error}</p>}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
