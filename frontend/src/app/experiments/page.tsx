export default function ExperimentsPage() {
  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white">Experiments</h1>
        <p className="mt-1 text-sm text-zinc-400">
          Compare RAG configurations side by side
        </p>
      </div>
      <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-12 text-center">
        <p className="text-zinc-500">No experiments yet.</p>
      </div>
    </div>
  );
}
