import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { Providers } from "@/components/providers";
import { Sidebar } from "@/components/sidebar";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "RAGOps",
  description:
    "Production platform for building, deploying, evaluating, and operating RAG applications",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className={inter.className}>
        <Providers>
          <div className="flex min-h-screen">
            <Sidebar />
            <main className="ml-64 flex-1 transition-all duration-300">
              <div className="p-8">{children}</div>
            </main>
          </div>
        </Providers>
      </body>
    </html>
  );
}
