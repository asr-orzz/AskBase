export default function DeploymentsPage() {
  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white">Deployments</h1>
        <p className="mt-1 text-sm text-zinc-400">
          Manage versioned RAG deployments and A/B tests
        </p>
      </div>
      <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-12 text-center">
        <p className="text-zinc-500">No deployments yet.</p>
      </div>
    </div>
  );
}
