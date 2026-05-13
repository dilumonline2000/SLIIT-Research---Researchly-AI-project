"use client";

import { LogOut, Menu, Search } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useAuth } from "@/hooks/useAuth";
// import { AIProviderToggle } from "./AIProviderToggle";
import { ThemeToggle } from "./ThemeToggle";

interface NavbarProps {
  onMenuClick?: () => void;
}

export function Navbar({ onMenuClick }: NavbarProps) {
  const { profile, signOut } = useAuth();

  const handleSignOut = async () => {
    if (window.confirm("Are you sure you want to sign out?")) {
      await signOut();
    }
  };

  return (
    // Original desktop classes preserved exactly — only the left group gets the hamburger
    <header className="flex h-16 items-center justify-between border-b bg-card px-6">
      {/* Left: hamburger (mobile only) + search */}
      <div className="flex items-center gap-2 min-w-0">
        <button
          onClick={onMenuClick}
          className="flex h-9 w-9 shrink-0 items-center justify-center rounded-md hover:bg-accent md:hidden"
          aria-label="Open menu"
        >
          <Menu className="h-5 w-5" />
        </button>
        <div className="relative w-full max-w-md">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input placeholder="Search papers, authors, topics…" className="pl-10" />
        </div>
      </div>

      {/* Right: original items unchanged */}
      <div className="flex items-center gap-3">
        <ThemeToggle compact />
        {/* <AIProviderToggle compact={true} /> */}
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
