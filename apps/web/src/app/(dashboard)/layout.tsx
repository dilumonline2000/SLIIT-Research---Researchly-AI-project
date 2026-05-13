import { redirect } from "next/navigation";
import { createClient } from "@/lib/supabase/server";
import { DashboardShell } from "@/components/shared/DashboardShell";
import { DashboardClientInit } from "@/components/shared/DashboardClientInit";

export default async function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const supabase = createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    redirect("/login");
  }

  return (
    <DashboardShell>
      <DashboardClientInit>{children}</DashboardClientInit>
    </DashboardShell>
  );
}
