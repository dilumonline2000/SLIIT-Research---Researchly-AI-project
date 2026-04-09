"use client";

import { LogOut, Search } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useAuth } from "@/hooks/useAuth";

export function Navbar() {
  const { profile, signOut } = useAuth();

  return (
    <header className="flex h-16 items-center justify-between border-b bg-card px-6">
      <div className="relative w-full max-w-md">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <Input placeholder="Search papers, authors, topics…" className="pl-10" />
      </div>
      <div className="flex items-center gap-4">
        <div className="hidden text-right sm:block">
          <p className="text-sm font-medium">{profile?.full_name ?? "User"}</p>
          <p className="text-xs text-muted-foreground capitalize">
            {profile?.role ?? "student"}
          </p>
        </div>
        <Button variant="ghost" size="icon" onClick={signOut} title="Sign out">
          <LogOut className="h-4 w-4" />
        </Button>
      </div>
    </header>
  );
}
