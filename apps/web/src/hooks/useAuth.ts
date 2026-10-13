"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { createClient } from "@/lib/supabase/client";
import { useAuthStore } from "@/stores/authStore";

/**
 * Auth bootstrap runs ONCE per page load, no matter how many components call
 * useAuth() (Navbar, Sidebar, Dashboard…).
 *
 * Important: Supabase holds an internal auth lock while it runs
 * onAuthStateChange callbacks. Awaiting another Supabase call (e.g. a
 * `profiles` query) inside that callback deadlocks the lock, after which every
 * later getSession() hangs forever — that is what left the Profile page stuck
 * on "Loading profile…". So the callback stays synchronous and the profile
 * fetch is deferred with setTimeout.
 */
let authInitialised = false;

function initAuth() {
  if (authInitialised || typeof window === "undefined") return;
  authInitialised = true;

  const supabase = createClient();
  const { setUser, setProfile, setLoading, reset } = useAuthStore.getState();

  const fetchProfile = async (userId: string) => {
    try {
      const { data } = await supabase
        .from("profiles")
        .select("id, full_name, role, department, research_interests, avatar_url")
        .eq("id", userId)
        .limit(1);
      const row = (data && data.length > 0 ? data[0] : null) as Record<string, unknown> | null;
      setProfile(row as never);
    } catch {
      /* keep whatever profile we already have */
    }
  };

  supabase.auth
    .getSession()
    .then(async ({ data: { session } }) => {
      if (session?.user) {
        setUser(session.user);
        await fetchProfile(session.user.id);
      } else {
        reset();
      }
    })
    .catch(() => reset())
    .finally(() => setLoading(false));

  supabase.auth.onAuthStateChange((event, session) => {
    setUser(session?.user ?? null);
    if (!session?.user) {
      setProfile(null);
      return;
    }
    // Token refreshes don't change the profile — skip the extra query
    if (event === "TOKEN_REFRESHED") return;
    const userId = session.user.id;
    // Defer so the Supabase auth lock is released before we query again
    setTimeout(() => {
      void fetchProfile(userId);
    }, 0);
  });
}

export function useAuth() {
  const router = useRouter();
  const { user, profile, loading, reset } = useAuthStore();

  useEffect(() => {
    initAuth();
  }, []);

  const signOut = async () => {
    const supabase = createClient();
    await supabase.auth.signOut();
    reset();
    router.replace("/login");
    router.refresh();
  };

  return { user, profile, loading, signOut };
}
