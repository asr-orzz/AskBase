"use client";

import Link from "next/link";
import { useSession, signOut } from "next-auth/react";
import { LogOut, Database, MessageSquare } from "lucide-react";

export function Sidebar() {
  const { data: session } = useSession();

  return (
    <aside className="fixed inset-y-0 left-0 z-50 flex w-56 flex-col border-r border-zinc-800 bg-zinc-950">
      <div className="flex h-14 items-center gap-2 border-b border-zinc-800 px-4">
        <div className="flex h-7 w-7 items-center justify-center rounded-md bg-indigo-600 text-xs font-bold text-white">
          R
        </div>
        <span className="text-sm font-semibold text-white">RAGOps</span>
      </div>

      <nav className="flex-1 space-y-1 px-3 py-4">
        <NavLink href="/knowledge-bases">
          <Database className="h-4 w-4" />
          Knowledge Bases
        </NavLink>
        <NavLink href="/playground">
          <MessageSquare className="h-4 w-4" />
          Playground
        </NavLink>
      </nav>

      {session?.user && (
        <div className="border-t border-zinc-800 px-3 py-3">
          <div className="flex items-center gap-2 px-3 py-2">
            <div className="flex h-7 w-7 items-center justify-center rounded-full bg-indigo-600/20 text-xs font-medium text-indigo-400">
              {session.user.name?.[0]?.toUpperCase() || session.user.email?.[0]?.toUpperCase() || "U"}
            </div>
            <div className="min-w-0 flex-1">
              <p className="truncate text-xs font-medium text-white">
                {session.user.name || "User"}
              </p>
              <p className="truncate text-[11px] text-zinc-500">
                {session.user.email}
              </p>
            </div>
          </div>
          <button
            onClick={() => signOut({ callbackUrl: "/login" })}
            className="mt-1 flex w-full items-center gap-2 rounded-lg px-3 py-2 text-sm text-zinc-400 transition-colors hover:bg-zinc-800 hover:text-white"
          >
            <LogOut className="h-4 w-4" />
            Sign out
          </button>
        </div>
      )}
    </aside>
  );
}

function NavLink({ href, children }: { href: string; children: React.ReactNode }) {
  return (
    <Link
      href={href}
      className="flex items-center gap-2 rounded-lg px-3 py-2 text-sm text-zinc-400 transition-colors hover:bg-zinc-800 hover:text-white"
    >
      {children}
    </Link>
  );
}
