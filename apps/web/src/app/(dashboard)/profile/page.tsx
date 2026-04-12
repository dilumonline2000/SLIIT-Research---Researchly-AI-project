"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { createClient } from "@/lib/supabase/client";

interface Profile {
  id: string;
  full_name: string;
  role: string;
  department: string;
  research_interests: string[];
  avatar_url: string;
}

export default function ProfilePage() {
  const [profile, setProfile] = useState<Profile | null>(null);
  const [fullName, setFullName] = useState("");
  const [department, setDepartment] = useState("");
  const [interests, setInterests] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState("");

  useEffect(() => {
    const load = async () => {
      const supabase = createClient();
      const { data: { user } } = await supabase.auth.getUser();
      if (!user) return;

      const { data } = await supabase.from("profiles").select("*").eq("id", user.id).single();
      if (data) {
        setProfile(data as Profile);
        setFullName(data.full_name || "");
        setDepartment(data.department || "");
        setInterests((data.research_interests || []).join(", "));
      }
      setLoading(false);
    };
    load();
  }, []);

  const handleSave = async () => {
    if (!profile) return;
    setSaving(true);
    setMessage("");
    const supabase = createClient();
    const { error } = await supabase.from("profiles").update({
      full_name: fullName,
      department,
      research_interests: interests.split(",").map(s => s.trim()).filter(Boolean),
    }).eq("id", profile.id);

    if (error) {
      setMessage("Failed to save: " + error.message);
    } else {
      setMessage("Profile updated successfully.");
    }
    setSaving(false);
  };

  if (loading) {
    return <div className="space-y-6"><h1 className="text-3xl font-bold">Profile</h1><p className="text-muted-foreground">Loading...</p></div>;
  }

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">Profile</h1>

      <Card>
        <CardHeader><CardTitle>Personal Details</CardTitle></CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="fullName">Full Name</Label>
            <Input id="fullName" value={fullName} onChange={(e) => setFullName(e.target.value)} />
          </div>
          <div className="space-y-2">
            <Label htmlFor="email">Email</Label>
            <Input id="email" value={profile?.id ? "Loaded from auth" : ""} disabled className="bg-muted" />
          </div>
          <div className="space-y-2">
            <Label htmlFor="role">Role</Label>
            <Input id="role" value={profile?.role || "student"} disabled className="bg-muted" />
          </div>
          <div className="space-y-2">
            <Label htmlFor="department">Department</Label>
            <Input id="department" placeholder="e.g., Computer Science" value={department} onChange={(e) => setDepartment(e.target.value)} />
          </div>
          <div className="space-y-2">
            <Label htmlFor="interests">Research Interests (comma-separated)</Label>
            <Input id="interests" placeholder="e.g., Machine Learning, NLP, IoT" value={interests} onChange={(e) => setInterests(e.target.value)} />
          </div>
          <div className="flex items-center gap-3">
            <Button onClick={handleSave} disabled={saving}>
              {saving ? "Saving..." : "Save Changes"}
            </Button>
            {message && <p className={`text-sm ${message.includes("Failed") ? "text-destructive" : "text-green-600"}`}>{message}</p>}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
