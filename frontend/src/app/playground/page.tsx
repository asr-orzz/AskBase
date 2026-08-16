export default function PlaygroundPage() {
  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white">Playground</h1>
        <p className="mt-1 text-sm text-zinc-400">
          Test your RAG pipeline with interactive queries
        </p>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2 rounded-xl border border-zinc-800 bg-zinc-900/50 p-6">
          <div className="flex h-[500px] flex-col">
            <div className="flex-1 overflow-y-auto p-4">
              <p className="text-center text-sm text-zinc-500 mt-40">
                Select a knowledge base and start asking questions
              </p>
            </div>
            <div className="border-t border-zinc-800 pt-4">
              <div className="flex gap-3">
                <input
                  type="text"
                  placeholder="Ask a question..."
                  className="flex-1 rounded-lg border border-zinc-700 bg-zinc-800 px-4 py-2.5 text-sm text-white placeholder-zinc-500 focus:border-indigo-500 focus:outline-none"
                />
                <button className="rounded-lg bg-indigo-600 px-6 py-2.5 text-sm font-medium text-white hover:bg-indigo-500 transition-colors">
                  Send
                </button>
              </div>
            </div>
          </div>
        </div>

        <div className="space-y-6">
          <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-6">
            <h3 className="text-sm font-medium text-white">Sources</h3>
            <p className="mt-3 text-sm text-zinc-500">
              Retrieved chunks will appear here
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
