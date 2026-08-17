import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { Providers } from "@/components/providers";
import Link from "next/link";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "RAGOps",
  description: "Upload documents and query them with AI",
};

function Sidebar() {
  return (
    <aside className="fixed inset-y-0 left-0 z-50 flex w-56 flex-col border-r border-zinc-800 bg-zinc-950">
      <div className="flex h-14 items-center gap-2 border-b border-zinc-800 px-4">
        <div className="flex h-7 w-7 items-center justify-center rounded-md bg-indigo-600 text-xs font-bold text-white">
          R
        </div>
        <span className="text-sm font-semibold text-white">RAGOps</span>
      </div>
      <nav className="flex-1 space-y-1 px-3 py-4">
        <NavLink href="/knowledge-bases">Knowledge Bases</NavLink>
        <NavLink href="/playground">Playground</NavLink>
      </nav>
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

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className={`${inter.className} bg-zinc-950 text-white antialiased`}>
        <Providers>
          <Sidebar />
          <main className="ml-56 min-h-screen px-8 py-6">{children}</main>
        </Providers>
      </body>
    </html>
  );
}
