"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useSession, signOut } from "next-auth/react";
import { LogOut, Database, MessageSquare, Settings } from "lucide-react";
import { cn } from "@/lib/utils";

export function Sidebar() {
  const { data: session } = useSession();
  const pathname = usePathname();

  return (
    <aside className="fixed inset-y-0 left-0 z-50 flex w-60 flex-col border-r border-zinc-800/80 bg-zinc-950">
      <div className="flex h-16 items-center gap-2.5 border-b border-zinc-800/80 px-5">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-indigo-600 text-sm font-bold text-white">
          A
        </div>
        <span className="text-base font-semibold text-white tracking-tight">AskBase</span>
      </div>

      <nav className="flex-1 space-y-1 px-3 py-4">
        <NavLink href="/knowledge-bases" active={pathname.startsWith("/knowledge-bases")}>
          <Database className="h-4 w-4" />
          Knowledge Bases
        </NavLink>
        <NavLink href="/playground" active={pathname === "/playground"}>
          <MessageSquare className="h-4 w-4" />
          Playground
        </NavLink>
        <NavLink href="/settings" active={pathname === "/settings"}>
          <Settings className="h-4 w-4" />
          Settings
        </NavLink>
      </nav>

      {session?.user && (
        <div className="border-t border-zinc-800/80 px-3 py-4">
          <div className="flex items-center gap-3 px-3 py-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 text-xs font-semibold text-white">
              {session.user.name?.[0]?.toUpperCase() || session.user.email?.[0]?.toUpperCase() || "U"}
            </div>
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-medium text-white">
                {session.user.name || "User"}
              </p>
              <p className="truncate text-xs text-zinc-500">
                {session.user.email}
              </p>
            </div>
          </div>
          <button
            onClick={() => signOut({ callbackUrl: "/login" })}
            className="mt-1 flex w-full items-center gap-2 rounded-lg px-3 py-2 text-sm text-zinc-500 transition-colors hover:bg-zinc-800/80 hover:text-white"
          >
            <LogOut className="h-4 w-4" />
            Sign out
          </button>
        </div>
      )}
    </aside>
  );
}

function NavLink({
  href,
  active,
  children,
}: {
  href: string;
  active: boolean;
  children: React.ReactNode;
}) {
  return (
    <Link
      href={href}
      className={cn(
        "flex items-center gap-2.5 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors",
        active
          ? "bg-indigo-600/10 text-indigo-400"
          : "text-zinc-400 hover:bg-zinc-800/60 hover:text-white"
      )}
    >
      {children}
    </Link>
  );
}
