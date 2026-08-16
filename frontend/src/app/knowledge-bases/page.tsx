export default function KnowledgeBasesPage() {
  return (
    <div>
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Knowledge Bases</h1>
          <p className="mt-1 text-sm text-zinc-400">
            Manage your knowledge bases and data sources
          </p>
        </div>
        <button className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-500 transition-colors">
          Create Knowledge Base
        </button>
      </div>

      <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-12 text-center">
        <p className="text-zinc-500">
          No knowledge bases yet. Create one to get started.
        </p>
      </div>
    </div>
  );
}
