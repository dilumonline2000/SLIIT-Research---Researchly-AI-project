import { createClient, SupabaseClient } from "@supabase/supabase-js";
import { env } from "./env";

// Service-role client — has full database access (use with care, bypasses RLS).
export const supabaseAdmin: SupabaseClient = createClient(
  env.SUPABASE_URL,
  env.SUPABASE_SERVICE_ROLE_KEY,
  {
    auth: { autoRefreshToken: false, persistSession: false },
  },
);

// Anon client — respects RLS.
export const supabaseAnon: SupabaseClient = createClient(
  env.SUPABASE_URL,
  env.SUPABASE_ANON_KEY,
);
