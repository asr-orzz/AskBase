"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Database,
  FlaskConical,
  LayoutDashboard,
  MessageSquare,
  Activity,
  BarChart3,
  DollarSign,
  Rocket,
  Settings,
  ChevronLeft,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useAppStore } from "@/lib/store";

const navigation = [
  { name: "Dashboard", href: "/", icon: LayoutDashboard },
  { name: "Knowledge Bases", href: "/knowledge-bases", icon: Database },
  { name: "Playground", href: "/playground", icon: MessageSquare },
  { name: "Evaluations", href: "/evaluations", icon: FlaskConical },
  { name: "Experiments", href: "/experiments", icon: BarChart3 },
  { name: "Traces", href: "/traces", icon: Activity },
  { name: "Cost", href: "/cost", icon: DollarSign },
  { name: "Deployments", href: "/deployments", icon: Rocket },
  { name: "Settings", href: "/settings", icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();
  const { sidebarOpen, toggleSidebar } = useAppStore();

  return (
    <aside
      className={cn(
        "fixed left-0 top-0 z-40 h-screen border-r border-zinc-800 bg-zinc-950 transition-all duration-300",
        sidebarOpen ? "w-64" : "w-16"
      )}
    >
      <div className="flex h-14 items-center justify-between border-b border-zinc-800 px-4">
        {sidebarOpen && (
          <Link href="/" className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-indigo-600 text-sm font-bold text-white">
              R
            </div>
            <span className="text-lg font-semibold text-white">RAGOps</span>
          </Link>
        )}
        <button
          onClick={toggleSidebar}
          className="rounded-md p-1.5 text-zinc-400 hover:bg-zinc-800 hover:text-white"
        >
          <ChevronLeft
            className={cn(
              "h-4 w-4 transition-transform",
              !sidebarOpen && "rotate-180"
            )}
          />
        </button>
      </div>

      <nav className="mt-4 space-y-1 px-2">
        {navigation.map((item) => {
          const isActive =
            item.href === "/"
              ? pathname === "/"
              : pathname.startsWith(item.href);

          return (
            <Link
              key={item.name}
              href={item.href}
              className={cn(
                "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                isActive
                  ? "bg-indigo-600/10 text-indigo-400"
                  : "text-zinc-400 hover:bg-zinc-800 hover:text-white"
              )}
              title={!sidebarOpen ? item.name : undefined}
            >
              <item.icon className="h-5 w-5 shrink-0" />
              {sidebarOpen && <span>{item.name}</span>}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
