// Generated Supabase types — regenerate with:
// pnpm supabase gen types typescript --project-id <id> > src/lib/supabase/types.ts
// This is a minimal manual stub until the CLI generation is wired up.

export type Json =
  | string
  | number
  | boolean
  | null
  | { [key: string]: Json | undefined }
  | Json[];

export interface Database {
  public: {
    Tables: {
      profiles: {
        Row: {
          id: string;
          full_name: string;
          email: string;
          role: "student" | "supervisor" | "admin" | "coordinator";
          department: string | null;
          faculty: string | null;
          student_id: string | null;
          bio: string | null;
          research_interests: string[] | null;
          skills: string[] | null;
          avatar_url: string | null;
          created_at: string;
          updated_at: string;
        };
        Insert: Partial<Database["public"]["Tables"]["profiles"]["Row"]> & {
          id: string;
          full_name: string;
          email: string;
        };
        Update: Partial<Database["public"]["Tables"]["profiles"]["Row"]>;
      };
      research_proposals: {
        Row: {
          id: string;
          user_id: string;
          title: string;
          abstract: string | null;
          keywords: string[] | null;
          full_text: string | null;
          file_url: string | null;
          status: "draft" | "submitted" | "reviewed" | "approved" | "rejected";
          embedding: number[] | null;
          created_at: string;
          updated_at: string;
        };
        Insert: Partial<Database["public"]["Tables"]["research_proposals"]["Row"]> & {
          title: string;
        };
        Update: Partial<Database["public"]["Tables"]["research_proposals"]["Row"]>;
      };
    };
    Views: Record<string, never>;
    Functions: Record<string, never>;
    Enums: Record<string, never>;
  };
}
