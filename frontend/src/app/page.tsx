import Link from "next/link";

export default function Home() {
  return (
    <div className="flex min-h-[80vh] flex-col items-center justify-center">
      <h1 className="text-4xl font-bold text-white">RAGOps</h1>
      <p className="mt-3 text-lg text-zinc-400">
        Upload documents and query them with AI
      </p>
      <div className="mt-8 flex gap-4">
        <Link
          href="/knowledge-bases"
          className="rounded-lg bg-indigo-600 px-6 py-3 text-sm font-medium text-white hover:bg-indigo-500"
        >
          Get Started
        </Link>
      </div>
    </div>
  );
}
