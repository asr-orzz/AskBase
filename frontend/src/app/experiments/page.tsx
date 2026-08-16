"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import {
  Plus,
  Play,
  Trophy,
  Loader2,
  CheckCircle2,
  XCircle,
  Clock,
  FlaskConical,
} from "lucide-react";

interface ExperimentSummary {
  id: string;
  name: string;
  description: string | null;
  status: string;
  winner: string | null;
  created_at: string;
}

interface VariantResult {
  run_id: string;
  config_id: string;
  composite_score: number;
  recall_at_k: number | null;
  precision_at_k: number | null;
  mrr: number | null;
  ndcg: number | null;
  faithfulness: number | null;
  answer_relevance: number | null;
  avg_latency_ms: number | null;
}

interface ExperimentDetail {
  id: string;
  name: string;
  description: string | null;
  status: string;
  knowledge_base_id: string;
  dataset_id: string;
  variant_a_config_id: string;
  variant_b_config_id: string;
  variant_a_run_id: string | null;
  variant_b_run_id: string | null;
  winner: string | null;
  results: {
    variant_a?: VariantResult;
    variant_b?: VariantResult;
    score_diff?: number;
    error?: string;
  } | null;
  created_at: string;
}

function StatusBadge({ status }: { status: string }) {
  const config: Record<string, { icon: React.ReactNode; color: string }> = {
    completed: {
      icon: <CheckCircle2 className="h-3 w-3" />,
      color: "text-emerald-400 bg-emerald-400/10 border-emerald-400/20",
    },
    running: {
      icon: <Loader2 className="h-3 w-3 animate-spin" />,
      color: "text-blue-400 bg-blue-400/10 border-blue-400/20",
    },
    cancelled: {
      icon: <XCircle className="h-3 w-3" />,
      color: "text-red-400 bg-red-400/10 border-red-400/20",
    },
    draft: {
      icon: <Clock className="h-3 w-3" />,
      color: "text-zinc-400 bg-zinc-400/10 border-zinc-400/20",
    },
  };
  const c = config[status] || config.draft;
  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-xs ${c.color}`}
    >
      {c.icon}
      {status}
    </span>
  );
}

function MetricRow({
  label,
  a,
  b,
}: {
  label: string;
  a: number | null;
  b: number | null;
}) {
  const fmt = (v: number | null) =>
    v !== null && v !== undefined ? v.toFixed(3) : "—";
  const better =
    a !== null && b !== null
      ? label === "Latency"
        ? a < b
          ? "a"
          : b < a
          ? "b"
          : null
        : a > b
        ? "a"
        : b > a
        ? "b"
        : null
      : null;

  return (
    <tr className="border-b border-zinc-800/50">
      <td className="px-4 py-2 text-sm text-zinc-400">{label}</td>
      <td
        className={`px-4 py-2 text-sm text-right ${
          better === "a" ? "text-emerald-400 font-semibold" : "text-zinc-300"
        }`}
      >
        {fmt(a)}
      </td>
      <td
        className={`px-4 py-2 text-sm text-right ${
          better === "b" ? "text-emerald-400 font-semibold" : "text-zinc-300"
        }`}
      >
        {fmt(b)}
      </td>
    </tr>
  );
}

export default function ExperimentsPage() {
  const queryClient = useQueryClient();
  const [showCreate, setShowCreate] = useState(false);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [form, setForm] = useState({
    name: "",
    description: "",
    knowledge_base_id: "",
    dataset_id: "",
    variant_a_config_id: "",
    variant_b_config_id: "",
  });

  const { data: experiments = [] } = useQuery<ExperimentSummary[]>({
    queryKey: ["experiments"],
    queryFn: () => api.get<ExperimentSummary[]>("/experiments"),
  });

  const { data: detail } = useQuery<ExperimentDetail>({
    queryKey: ["experiment", selectedId],
    queryFn: () => api.get<ExperimentDetail>(`/experiments/${selectedId}`),
    enabled: !!selectedId,
    refetchInterval: 5000,
  });

  const createExperiment = useMutation({
    mutationFn: (data: typeof form) => api.post("/experiments", data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["experiments"] });
      setShowCreate(false);
      setForm({
        name: "",
        description: "",
        knowledge_base_id: "",
        dataset_id: "",
        variant_a_config_id: "",
        variant_b_config_id: "",
      });
    },
  });

  const runExperiment = useMutation({
    mutationFn: (id: string) => api.post(`/experiments/${id}/run`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["experiments"] });
      queryClient.invalidateQueries({ queryKey: ["experiment", selectedId] });
    },
  });

  const va = detail?.results?.variant_a;
  const vb = detail?.results?.variant_b;

  return (
    <div>
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Experiments</h1>
          <p className="mt-1 text-sm text-zinc-400">
            A/B test RAG configurations to find the best pipeline
          </p>
        </div>
        <button
          onClick={() => setShowCreate(true)}
          className="flex items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2 text-sm text-white hover:bg-indigo-500"
        >
          <Plus className="h-4 w-4" />
          New Experiment
        </button>
      </div>

      {/* Create form */}
      {showCreate && (
        <div className="mb-6 rounded-xl border border-zinc-800 bg-zinc-900/50 p-6">
          <h3 className="mb-4 text-lg font-semibold text-white">
            Create Experiment
          </h3>
          <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
            <input
              placeholder="Experiment name"
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              className="rounded-lg border border-zinc-700 bg-zinc-800 px-3 py-2 text-sm text-white placeholder-zinc-500"
            />
            <input
              placeholder="Description (optional)"
              value={form.description}
              onChange={(e) =>
                setForm({ ...form, description: e.target.value })
              }
              className="rounded-lg border border-zinc-700 bg-zinc-800 px-3 py-2 text-sm text-white placeholder-zinc-500"
            />
            <input
              placeholder="Knowledge Base ID"
              value={form.knowledge_base_id}
              onChange={(e) =>
                setForm({ ...form, knowledge_base_id: e.target.value })
              }
              className="rounded-lg border border-zinc-700 bg-zinc-800 px-3 py-2 text-sm text-white placeholder-zinc-500"
            />
            <input
              placeholder="Dataset ID"
              value={form.dataset_id}
              onChange={(e) =>
                setForm({ ...form, dataset_id: e.target.value })
              }
              className="rounded-lg border border-zinc-700 bg-zinc-800 px-3 py-2 text-sm text-white placeholder-zinc-500"
            />
            <input
              placeholder="Variant A — RAG Config ID"
              value={form.variant_a_config_id}
              onChange={(e) =>
                setForm({ ...form, variant_a_config_id: e.target.value })
              }
              className="rounded-lg border border-zinc-700 bg-zinc-800 px-3 py-2 text-sm text-white placeholder-zinc-500"
            />
            <input
              placeholder="Variant B — RAG Config ID"
              value={form.variant_b_config_id}
              onChange={(e) =>
                setForm({ ...form, variant_b_config_id: e.target.value })
              }
              className="rounded-lg border border-zinc-700 bg-zinc-800 px-3 py-2 text-sm text-white placeholder-zinc-500"
            />
          </div>
          <div className="mt-4 flex gap-2">
            <button
              onClick={() => createExperiment.mutate(form)}
              disabled={
                !form.name ||
                !form.knowledge_base_id ||
                !form.dataset_id ||
                !form.variant_a_config_id ||
                !form.variant_b_config_id
              }
              className="rounded-lg bg-indigo-600 px-4 py-2 text-sm text-white hover:bg-indigo-500 disabled:opacity-50"
            >
              Create
            </button>
            <button
              onClick={() => setShowCreate(false)}
              className="rounded-lg bg-zinc-800 px-4 py-2 text-sm text-zinc-400 hover:bg-zinc-700"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* Experiment list */}
      {experiments.length === 0 ? (
        <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-12 text-center">
          <FlaskConical className="mx-auto h-10 w-10 text-zinc-600" />
          <p className="mt-3 text-zinc-500">
            No experiments yet. Create one to compare RAG configs.
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {experiments.map((exp) => (
            <div
              key={exp.id}
              onClick={() => setSelectedId(exp.id)}
              className="cursor-pointer rounded-xl border border-zinc-800 bg-zinc-900/50 p-4 hover:border-zinc-700"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <FlaskConical className="h-5 w-5 text-zinc-500" />
                  <div>
                    <p className="font-medium text-white">{exp.name}</p>
                    {exp.description && (
                      <p className="text-xs text-zinc-500">
                        {exp.description}
                      </p>
                    )}
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  {exp.winner && (
                    <span className="flex items-center gap-1 text-sm font-semibold text-amber-400">
                      <Trophy className="h-4 w-4" />
                      Variant {exp.winner}
                    </span>
                  )}
                  <StatusBadge status={exp.status} />
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Detail panel */}
      {selectedId && detail && (
        <div className="mt-6 rounded-xl border border-zinc-800 bg-zinc-900/50 p-6">
          <div className="mb-4 flex items-center justify-between">
            <div>
              <h3 className="text-lg font-semibold text-white">
                {detail.name}
              </h3>
              <StatusBadge status={detail.status} />
            </div>
            <div className="flex gap-2">
              {(detail.status === "draft" ||
                detail.status === "completed" ||
                detail.status === "cancelled") && (
                <button
                  onClick={() => runExperiment.mutate(detail.id)}
                  disabled={runExperiment.isPending}
                  className="flex items-center gap-2 rounded-lg bg-indigo-600 px-3 py-1.5 text-sm text-white hover:bg-indigo-500 disabled:opacity-50"
                >
                  <Play className="h-4 w-4" />
                  {detail.status === "completed" ? "Re-run" : "Run"}
                </button>
              )}
              <button
                onClick={() => setSelectedId(null)}
                className="text-sm text-zinc-400 hover:text-white"
              >
                Close
              </button>
            </div>
          </div>

          {/* Winner banner */}
          {detail.winner && (
            <div className="mb-4 flex items-center gap-2 rounded-lg bg-amber-400/10 border border-amber-400/20 px-4 py-3">
              <Trophy className="h-5 w-5 text-amber-400" />
              <span className="text-sm font-semibold text-amber-400">
                Variant {detail.winner} wins
              </span>
              {detail.results?.score_diff !== undefined && (
                <span className="text-xs text-amber-400/70">
                  (score diff: {detail.results.score_diff.toFixed(4)})
                </span>
              )}
            </div>
          )}

          {detail.results?.error && (
            <p className="mb-4 text-sm text-red-400">
              Error: {detail.results.error}
            </p>
          )}

          {/* Comparison table */}
          {va && vb && (
            <div className="overflow-hidden rounded-lg border border-zinc-800">
              <table className="w-full text-left">
                <thead className="bg-zinc-900">
                  <tr className="border-b border-zinc-800 text-xs text-zinc-400">
                    <th className="px-4 py-2">Metric</th>
                    <th className="px-4 py-2 text-right">
                      Variant A
                      {detail.winner === "A" && (
                        <Trophy className="ml-1 inline h-3 w-3 text-amber-400" />
                      )}
                    </th>
                    <th className="px-4 py-2 text-right">
                      Variant B
                      {detail.winner === "B" && (
                        <Trophy className="ml-1 inline h-3 w-3 text-amber-400" />
                      )}
                    </th>
                  </tr>
                </thead>
                <tbody className="text-sm">
                  <MetricRow
                    label="Composite Score"
                    a={va.composite_score}
                    b={vb.composite_score}
                  />
                  <MetricRow
                    label="Recall@K"
                    a={va.recall_at_k}
                    b={vb.recall_at_k}
                  />
                  <MetricRow
                    label="Precision@K"
                    a={va.precision_at_k}
                    b={vb.precision_at_k}
                  />
                  <MetricRow label="MRR" a={va.mrr} b={vb.mrr} />
                  <MetricRow label="NDCG" a={va.ndcg} b={vb.ndcg} />
                  <MetricRow
                    label="Faithfulness"
                    a={va.faithfulness}
                    b={vb.faithfulness}
                  />
                  <MetricRow
                    label="Relevance"
                    a={va.answer_relevance}
                    b={vb.answer_relevance}
                  />
                  <MetricRow
                    label="Latency"
                    a={va.avg_latency_ms}
                    b={vb.avg_latency_ms}
                  />
                </tbody>
              </table>
            </div>
          )}

          {/* Config IDs */}
          <div className="mt-4 grid grid-cols-2 gap-4 text-xs text-zinc-500">
            <div>
              <p className="font-medium text-zinc-400">Variant A Config</p>
              <p className="mt-0.5 font-mono">
                {detail.variant_a_config_id.slice(0, 8)}...
              </p>
            </div>
            <div>
              <p className="font-medium text-zinc-400">Variant B Config</p>
              <p className="mt-0.5 font-mono">
                {detail.variant_b_config_id.slice(0, 8)}...
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
