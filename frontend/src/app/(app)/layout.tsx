"use client";

import { Sidebar } from "@/components/sidebar";
import { AuthGuard } from "@/components/auth-guard";

export default function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <AuthGuard>
      <Sidebar />
      <main className="ml-60 min-h-screen px-10 py-8">{children}</main>
    </AuthGuard>
  );
}
