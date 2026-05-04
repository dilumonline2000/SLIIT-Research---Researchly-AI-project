"use client";

import { LogOut, Search } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useAuth } from "@/hooks/useAuth";
import { AIProviderToggle } from "./AIProviderToggle";

export function Navbar() {
  const { profile, signOut } = useAuth();

  const handleSignOut = async () => {
    if (window.confirm("Are you sure you want to sign out?")) {
      await signOut();
    }
  };

  return (
    <header className="flex h-16 items-center justify-between border-b bg-card px-6">
      <div className="relative w-full max-w-md">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <Input placeholder="Search papers, authors, topics…" className="pl-10" />
      </div>
      <div className="flex items-center gap-3">
        <AIProviderToggle compact={true} />
        <div className="hidden text-right sm:block">
          <p className="text-sm font-medium">{profile?.full_name ?? "User"}</p>
          <p className="text-xs text-muted-foreground capitalize">
            {profile?.role ?? "student"}
          </p>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={handleSignOut}
          title="Sign out"
          className="gap-2 border-rose-200 text-rose-600 hover:bg-rose-50 hover:text-rose-700"
        >
          <LogOut className="h-4 w-4" />
          <span className="hidden sm:inline">Sign Out</span>
        </Button>
      </div>
    </header>
  );
}
