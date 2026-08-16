export default function EvaluationsPage() {
  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white">Evaluations</h1>
        <p className="mt-1 text-sm text-zinc-400">
          Evaluate RAG quality with datasets and metrics
        </p>
      </div>
      <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-12 text-center">
        <p className="text-zinc-500">No evaluation runs yet.</p>
      </div>
    </div>
  );
}
