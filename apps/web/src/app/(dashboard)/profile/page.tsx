"use client";

import { useEffect, useRef, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { User, Mail, Briefcase, AlertCircle } from "lucide-react";
import { createClient } from "@/lib/supabase/client";

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

  useEffect(() => {
    // Guard against React Strict Mode double-invoke
    if (loadedRef.current) return;
    loadedRef.current = true;

    const load = async () => {
      try {
        const supabase = createClient();

        // getSession() reads from localStorage — no network request, never hangs
        const { data: { session } } = await supabase.auth.getSession();

        if (!session?.user) {
          setError("Not signed in. Please log in to view your profile.");
          setLoading(false);
          return;
        }

        const user = session.user;
        setEmail(user.email || "");

        // Fetch profile row — use maybeSingle via raw fetch to avoid type issues
        const { data, error: profileError } = await supabase
          .from("profiles")
          .select("id, full_name, role, department, research_interests, avatar_url")
          .eq("id", user.id)
          .limit(1);

        if (profileError) {
          console.warn("Profile fetch warning:", profileError.message);
        }

        const row = (data && data.length > 0 ? data[0] : null) as ProfileRow | null;

        const p: ProfileRow = {
          id: user.id,
          full_name: row?.full_name ?? (user.user_metadata?.full_name as string | undefined) ?? "",
          role: row?.role ?? "student",
          department: row?.department ?? "",
          research_interests: row?.research_interests ?? [],
          avatar_url: row?.avatar_url ?? null,
        };

        setProfile(p);
        setFullName(p.full_name || "");
        setDepartment(p.department || "");
        setInterests((p.research_interests || []).join(", "));
      } catch (err) {
        console.error("Profile load error:", err);
        setError(err instanceof Error ? err.message : "Failed to load profile");
      } finally {
        setLoading(false);
      }
    };

    load();
  }, []);

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

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">Profile</h1>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <User className="h-5 w-5" /> Personal Details
          </CardTitle>
          <CardDescription>Update your name, department, and research interests.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
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
            <Label htmlFor="email" className="flex items-center gap-1.5">
              <Mail className="h-3.5 w-3.5" /> Email
            </Label>
            <Input id="email" value={email} disabled className="bg-muted" />
          </div>

          <div className="space-y-2">
            <Label htmlFor="role" className="flex items-center gap-1.5">
              <Briefcase className="h-3.5 w-3.5" /> Role
            </Label>
            <Input id="role" value={profile?.role || "student"} disabled className="bg-muted" />
          </div>

          <div className="space-y-2">
            <Label htmlFor="department">Department</Label>
            <Input
              id="department"
              placeholder="e.g., Computer Science"
              value={department}
              onChange={(e) => setDepartment(e.target.value)}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="interests">Research Interests (comma-separated)</Label>
            <Input
              id="interests"
              placeholder="e.g., Machine Learning, NLP, IoT"
              value={interests}
              onChange={(e) => setInterests(e.target.value)}
            />
          </div>

          <div className="flex items-center gap-3 pt-2">
            <Button onClick={handleSave} disabled={saving}>
              {saving ? "Saving…" : "Save Changes"}
            </Button>
            {message && <p className="text-sm text-green-600">{message}</p>}
            {error && <p className="text-sm text-destructive">{error}</p>}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
