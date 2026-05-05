"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { createClient } from "@/lib/supabase/client";
import { useAuthStore } from "@/stores/authStore";

export function useAuth() {
  const router = useRouter();
  const { user, profile, loading, setUser, setProfile, setLoading, reset } =
    useAuthStore();

  useEffect(() => {
    const supabase = createClient();

    const fetchProfile = async (userId: string) => {
      try {
        const { data } = await supabase
          .from("profiles")
          .select("id, full_name, role, department, research_interests, avatar_url")
          .eq("id", userId)
          .limit(1);
        return (data && data.length > 0 ? data[0] : null) as Record<string, unknown> | null;
      } catch {
        return null;
      }
    };

    const fetchSession = async () => {
      const { data: { session } } = await supabase.auth.getSession();
      if (session?.user) {
        setUser(session.user);
        const profileData = await fetchProfile(session.user.id);
        setProfile(profileData as never);
      } else {
        reset();
      }
      setLoading(false);
    };

    fetchSession();

    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange(async (_event, session) => {
      setUser(session?.user ?? null);
      if (session?.user) {
        const profileData = await fetchProfile(session.user.id);
        setProfile(profileData as never);
      } else {
        setProfile(null);
      }
    });

    return () => subscription.unsubscribe();
  }, [setUser, setProfile, setLoading, reset]);

  const signOut = async () => {
    const supabase = createClient();
    await supabase.auth.signOut();
    reset();
    router.replace("/login");
    router.refresh();
  };

  return { user, profile, loading, signOut };
}
