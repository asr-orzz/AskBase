"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Activity, Clock, Zap, Server } from "lucide-react";

interface UsageRecord {
  id: string;
  operation: string;
  provider: string;
  model: string;
  input_tokens: number;
  output_tokens: number;
  total_tokens: number;
  latency_ms: number;
  cost_usd: number;
  created_at: string;
}

function formatLatency(ms: number) {
  if (ms < 1000) return `${ms.toFixed(0)} ms`;
  return `${(ms / 1000).toFixed(2)} s`;
}

function OperationBadge({ op }: { op: string }) {
  const colors: Record<string, string> = {
    query: "text-blue-400 bg-blue-400/10 border-blue-400/20",
    embedding: "text-purple-400 bg-purple-400/10 border-purple-400/20",
    generation: "text-emerald-400 bg-emerald-400/10 border-emerald-400/20",
    rerank: "text-amber-400 bg-amber-400/10 border-amber-400/20",
    ingestion: "text-cyan-400 bg-cyan-400/10 border-cyan-400/20",
  };
  const c = colors[op] || "text-zinc-400 bg-zinc-400/10 border-zinc-400/20";
  return (
    <span
      className={`inline-flex items-center rounded-full border px-2 py-0.5 text-xs ${c}`}
    >
      {op}
    </span>
  );
}

export default function TracesPage() {
  const { data: records = [], isLoading } = useQuery<UsageRecord[]>({
    queryKey: ["traces"],
    queryFn: () => api.get<UsageRecord[]>("/cost/usage?limit=200"),
    refetchInterval: 10000,
  });

  const totalTokens = records.reduce((s, r) => s + r.total_tokens, 0);
  const totalCost = records.reduce((s, r) => s + r.cost_usd, 0);
  const avgLatency =
    records.length > 0
      ? records.reduce((s, r) => s + r.latency_ms, 0) / records.length
      : 0;

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white">Traces</h1>
        <p className="mt-1 text-sm text-zinc-400">
          Request-level observability for every RAG operation
        </p>
      </div>

      {/* Summary cards */}
      <div className="mb-6 grid grid-cols-1 gap-4 md:grid-cols-4">
        <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-4">
          <div className="flex items-center gap-2 text-zinc-400">
            <Activity className="h-4 w-4" />
            <span className="text-xs">Total Requests</span>
          </div>
          <p className="mt-2 text-2xl font-bold text-white">
            {records.length}
          </p>
        </div>
        <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-4">
          <div className="flex items-center gap-2 text-zinc-400">
            <Zap className="h-4 w-4" />
            <span className="text-xs">Total Tokens</span>
          </div>
          <p className="mt-2 text-2xl font-bold text-white">
            {totalTokens.toLocaleString()}
          </p>
        </div>
        <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-4">
          <div className="flex items-center gap-2 text-zinc-400">
            <Clock className="h-4 w-4" />
            <span className="text-xs">Avg Latency</span>
          </div>
          <p className="mt-2 text-2xl font-bold text-white">
            {formatLatency(avgLatency)}
          </p>
        </div>
        <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-4">
          <div className="flex items-center gap-2 text-zinc-400">
            <Server className="h-4 w-4" />
            <span className="text-xs">Total Cost</span>
          </div>
          <p className="mt-2 text-2xl font-bold text-white">
            ${totalCost.toFixed(4)}
          </p>
        </div>
      </div>

      {/* Traces table */}
      {isLoading ? (
        <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-12 text-center">
          <p className="text-zinc-500">Loading traces...</p>
        </div>
      ) : records.length === 0 ? (
        <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-12 text-center">
          <Activity className="mx-auto h-10 w-10 text-zinc-600" />
          <p className="mt-3 text-zinc-500">
            No traces yet. Send a query to see operations here.
          </p>
        </div>
      ) : (
        <div className="overflow-hidden rounded-xl border border-zinc-800">
          <div className="max-h-[600px] overflow-y-auto">
            <table className="w-full text-left text-sm">
              <thead className="sticky top-0 bg-zinc-900 text-xs text-zinc-400">
                <tr className="border-b border-zinc-800">
                  <th className="px-4 py-3">Operation</th>
                  <th className="px-4 py-3">Provider</th>
                  <th className="px-4 py-3">Model</th>
                  <th className="px-4 py-3 text-right">Input</th>
                  <th className="px-4 py-3 text-right">Output</th>
                  <th className="px-4 py-3 text-right">Latency</th>
                  <th className="px-4 py-3 text-right">Cost</th>
                  <th className="px-4 py-3 text-right">Time</th>
                </tr>
              </thead>
              <tbody>
                {records.map((r) => (
                  <tr
                    key={r.id}
                    className="border-b border-zinc-800/50 text-zinc-300 hover:bg-zinc-800/30"
                  >
                    <td className="px-4 py-2">
                      <OperationBadge op={r.operation} />
                    </td>
                    <td className="px-4 py-2 text-zinc-400">{r.provider}</td>
                    <td className="px-4 py-2 font-mono text-xs">
                      {r.model.length > 25
                        ? r.model.slice(0, 25) + "..."
                        : r.model}
                    </td>
                    <td className="px-4 py-2 text-right tabular-nums">
                      {r.input_tokens.toLocaleString()}
                    </td>
                    <td className="px-4 py-2 text-right tabular-nums">
                      {r.output_tokens.toLocaleString()}
                    </td>
                    <td className="px-4 py-2 text-right tabular-nums">
                      {formatLatency(r.latency_ms)}
                    </td>
                    <td className="px-4 py-2 text-right tabular-nums text-emerald-400">
                      ${r.cost_usd.toFixed(6)}
                    </td>
                    <td className="px-4 py-2 text-right text-xs text-zinc-500">
                      {r.created_at
                        ? new Date(r.created_at).toLocaleTimeString()
                        : ""}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
