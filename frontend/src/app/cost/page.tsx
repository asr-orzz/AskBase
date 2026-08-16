"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { DollarSign, TrendingUp, BarChart3, Layers } from "lucide-react";

interface CostSummary {
  total_cost_usd: number;
  period_days: number;
  by_provider: Array<{
    provider: string;
    cost_usd: number;
    tokens: number;
    requests: number;
  }>;
  by_operation: Array<{
    operation: string;
    cost_usd: number;
    requests: number;
  }>;
  daily: Array<{
    date: string;
    cost_usd: number;
    tokens: number;
    requests: number;
  }>;
}

function ProviderColor(provider: string) {
  const colors: Record<string, string> = {
    openai: "bg-emerald-500",
    anthropic: "bg-amber-500",
    google: "bg-blue-500",
    cohere: "bg-purple-500",
  };
  return colors[provider] || "bg-zinc-500";
}

export default function CostPage() {
  const [days, setDays] = useState(30);

  const { data: summary, isLoading } = useQuery<CostSummary>({
    queryKey: ["cost-summary", days],
    queryFn: () => api.get<CostSummary>(`/cost/summary?days=${days}`),
    refetchInterval: 30000,
  });

  const maxDailyCost =
    summary?.daily?.reduce((m, d) => Math.max(m, d.cost_usd), 0) || 0;

  return (
    <div>
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Cost Tracking</h1>
          <p className="mt-1 text-sm text-zinc-400">
            Monitor LLM and embedding spend across all providers
          </p>
        </div>
        <select
          value={days}
          onChange={(e) => setDays(Number(e.target.value))}
          className="rounded-lg border border-zinc-700 bg-zinc-800 px-3 py-2 text-sm text-white"
        >
          <option value={7}>Last 7 days</option>
          <option value={14}>Last 14 days</option>
          <option value={30}>Last 30 days</option>
          <option value={90}>Last 90 days</option>
        </select>
      </div>

      {isLoading ? (
        <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-12 text-center">
          <p className="text-zinc-500">Loading cost data...</p>
        </div>
      ) : !summary ? (
        <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-12 text-center">
          <DollarSign className="mx-auto h-10 w-10 text-zinc-600" />
          <p className="mt-3 text-zinc-500">No cost data available.</p>
        </div>
      ) : (
        <>
          {/* Total cost hero */}
          <div className="mb-6 rounded-xl border border-zinc-800 bg-zinc-900/50 p-6">
            <div className="flex items-center gap-2 text-zinc-400">
              <DollarSign className="h-5 w-5" />
              <span className="text-sm">Total Cost ({days} days)</span>
            </div>
            <p className="mt-2 text-4xl font-bold text-white">
              ${summary.total_cost_usd.toFixed(4)}
            </p>
          </div>

          {/* Provider + Operation breakdown */}
          <div className="mb-6 grid grid-cols-1 gap-4 md:grid-cols-2">
            {/* By Provider */}
            <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-6">
              <div className="mb-4 flex items-center gap-2">
                <Layers className="h-4 w-4 text-zinc-400" />
                <h3 className="text-sm font-medium text-zinc-400">
                  By Provider
                </h3>
              </div>
              {summary.by_provider.length === 0 ? (
                <p className="text-sm text-zinc-500">No data</p>
              ) : (
                <div className="space-y-3">
                  {summary.by_provider.map((p) => (
                    <div key={p.provider}>
                      <div className="flex items-center justify-between text-sm">
                        <div className="flex items-center gap-2">
                          <div
                            className={`h-2.5 w-2.5 rounded-full ${ProviderColor(p.provider)}`}
                          />
                          <span className="capitalize text-white">
                            {p.provider}
                          </span>
                        </div>
                        <span className="tabular-nums text-emerald-400">
                          ${p.cost_usd.toFixed(4)}
                        </span>
                      </div>
                      <div className="mt-1 flex justify-between text-xs text-zinc-500">
                        <span>{p.tokens.toLocaleString()} tokens</span>
                        <span>{p.requests} requests</span>
                      </div>
                      {summary.total_cost_usd > 0 && (
                        <div className="mt-1 h-1.5 w-full rounded-full bg-zinc-800">
                          <div
                            className={`h-1.5 rounded-full ${ProviderColor(p.provider)}`}
                            style={{
                              width: `${(p.cost_usd / summary.total_cost_usd) * 100}%`,
                            }}
                          />
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* By Operation */}
            <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-6">
              <div className="mb-4 flex items-center gap-2">
                <BarChart3 className="h-4 w-4 text-zinc-400" />
                <h3 className="text-sm font-medium text-zinc-400">
                  By Operation
                </h3>
              </div>
              {summary.by_operation.length === 0 ? (
                <p className="text-sm text-zinc-500">No data</p>
              ) : (
                <div className="space-y-3">
                  {summary.by_operation.map((o) => (
                    <div key={o.operation}>
                      <div className="flex items-center justify-between text-sm">
                        <span className="capitalize text-white">
                          {o.operation}
                        </span>
                        <span className="tabular-nums text-emerald-400">
                          ${o.cost_usd.toFixed(4)}
                        </span>
                      </div>
                      <div className="mt-1 text-xs text-zinc-500">
                        {o.requests} requests
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Daily chart */}
          <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-6">
            <div className="mb-4 flex items-center gap-2">
              <TrendingUp className="h-4 w-4 text-zinc-400" />
              <h3 className="text-sm font-medium text-zinc-400">
                Daily Spend
              </h3>
            </div>
            {summary.daily.length === 0 ? (
              <p className="text-sm text-zinc-500">No daily data</p>
            ) : (
              <div className="flex items-end gap-1" style={{ height: 160 }}>
                {summary.daily.map((d, i) => {
                  const h =
                    maxDailyCost > 0
                      ? (d.cost_usd / maxDailyCost) * 140
                      : 0;
                  return (
                    <div
                      key={i}
                      className="group relative flex-1"
                      title={`${d.date?.slice(0, 10)}: $${d.cost_usd.toFixed(4)}`}
                    >
                      <div
                        className="mx-auto w-full max-w-[20px] rounded-t bg-indigo-500 transition-colors hover:bg-indigo-400"
                        style={{ height: Math.max(h, 2) }}
                      />
                      <div className="pointer-events-none absolute -top-8 left-1/2 -translate-x-1/2 rounded bg-zinc-800 px-2 py-1 text-xs text-white opacity-0 transition-opacity group-hover:opacity-100 whitespace-nowrap">
                        ${d.cost_usd.toFixed(4)}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
            {summary.daily.length > 0 && (
              <div className="mt-2 flex justify-between text-xs text-zinc-500">
                <span>{summary.daily[0]?.date?.slice(0, 10)}</span>
                <span>
                  {summary.daily[summary.daily.length - 1]?.date?.slice(0, 10)}
                </span>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}
