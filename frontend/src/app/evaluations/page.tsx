"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import {
  Plus,
  Play,
  ChevronRight,
  Loader2,
  CheckCircle2,
  XCircle,
  Clock,
  BarChart3,
  FileText,
} from "lucide-react";

interface Dataset {
  id: string;
  name: string;
  description: string | null;
  item_count: number;
  created_at: string;
}

interface EvalRun {
  id: string;
  dataset_id: string;
  rag_config_id: string;
  status: string;
  recall_at_k: number | null;
  precision_at_k: number | null;
  mrr: number | null;
  ndcg: number | null;
  faithfulness: number | null;
  answer_relevance: number | null;
  avg_latency_ms: number | null;
  total_items: number;
  completed_items: number;
  created_at: string;
}

interface RunDetail extends EvalRun {
  detailed_results: {
    items: Array<{
      question: string;
      answer: string;
      expected_answer: string | null;
      recall_at_k: number;
      precision_at_k: number;
      mrr: number;
      ndcg: number;
      faithfulness: number;
      answer_relevance: number;
      latency_ms: number;
      tokens: number;
      chunks_retrieved: number;
    }>;
  } | null;
  error_message: string | null;
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
    failed: {
      icon: <XCircle className="h-3 w-3" />,
      color: "text-red-400 bg-red-400/10 border-red-400/20",
    },
    pending: {
      icon: <Clock className="h-3 w-3" />,
      color: "text-zinc-400 bg-zinc-400/10 border-zinc-400/20",
    },
  };
  const c = config[status] || config.pending;
  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-xs ${c.color}`}
    >
      {c.icon}
      {status}
    </span>
  );
}

function MetricCard({
  label,
  value,
}: {
  label: string;
  value: number | null;
}) {
  return (
    <div className="rounded-lg border border-zinc-800 bg-zinc-900/50 p-3 text-center">
      <p className="text-xs text-zinc-500">{label}</p>
      <p className="mt-1 text-lg font-semibold text-white">
        {value !== null && value !== undefined ? value.toFixed(3) : "—"}
      </p>
    </div>
  );
}

export default function EvaluationsPage() {
  const queryClient = useQueryClient();
  const [showCreateDataset, setShowCreateDataset] = useState(false);
  const [showRunForm, setShowRunForm] = useState(false);
  const [newDataset, setNewDataset] = useState({ name: "", description: "", knowledge_base_id: "" });
  const [newRun, setNewRun] = useState({ dataset_id: "", rag_config_id: "" });
  const [selectedRun, setSelectedRun] = useState<string | null>(null);

  const { data: datasets = [] } = useQuery<Dataset[]>({
    queryKey: ["eval-datasets"],
    queryFn: () => api.get<Dataset[]>("/evaluations/datasets"),
  });

  const { data: runs = [] } = useQuery<EvalRun[]>({
    queryKey: ["eval-runs"],
    queryFn: () => api.get<EvalRun[]>("/evaluations/runs"),
    refetchInterval: 5000,
  });

  const { data: runDetail } = useQuery<RunDetail>({
    queryKey: ["eval-run", selectedRun],
    queryFn: () => api.get<RunDetail>(`/evaluations/runs/${selectedRun}`),
    enabled: !!selectedRun,
    refetchInterval: 5000,
  });

  const createDataset = useMutation({
    mutationFn: (data: typeof newDataset) =>
      api.post("/evaluations/datasets", data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["eval-datasets"] });
      setShowCreateDataset(false);
      setNewDataset({ name: "", description: "", knowledge_base_id: "" });
    },
  });

  const startRun = useMutation({
    mutationFn: (data: typeof newRun) =>
      api.post("/evaluations/runs", data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["eval-runs"] });
      setShowRunForm(false);
      setNewRun({ dataset_id: "", rag_config_id: "" });
    },
  });

  return (
    <div>
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Evaluations</h1>
          <p className="mt-1 text-sm text-zinc-400">
            Evaluate RAG quality with datasets and metrics
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => setShowCreateDataset(true)}
            className="flex items-center gap-2 rounded-lg bg-zinc-800 px-4 py-2 text-sm text-white hover:bg-zinc-700"
          >
            <FileText className="h-4 w-4" />
            New Dataset
          </button>
          <button
            onClick={() => setShowRunForm(true)}
            className="flex items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2 text-sm text-white hover:bg-indigo-500"
          >
            <Play className="h-4 w-4" />
            Run Evaluation
          </button>
        </div>
      </div>

      {/* Create dataset modal */}
      {showCreateDataset && (
        <div className="mb-6 rounded-xl border border-zinc-800 bg-zinc-900/50 p-6">
          <h3 className="mb-4 text-lg font-semibold text-white">
            Create Dataset
          </h3>
          <div className="space-y-3">
            <input
              placeholder="Dataset name"
              value={newDataset.name}
              onChange={(e) =>
                setNewDataset({ ...newDataset, name: e.target.value })
              }
              className="w-full rounded-lg border border-zinc-700 bg-zinc-800 px-3 py-2 text-sm text-white placeholder-zinc-500"
            />
            <input
              placeholder="Description (optional)"
              value={newDataset.description}
              onChange={(e) =>
                setNewDataset({ ...newDataset, description: e.target.value })
              }
              className="w-full rounded-lg border border-zinc-700 bg-zinc-800 px-3 py-2 text-sm text-white placeholder-zinc-500"
            />
            <input
              placeholder="Knowledge Base ID"
              value={newDataset.knowledge_base_id}
              onChange={(e) =>
                setNewDataset({
                  ...newDataset,
                  knowledge_base_id: e.target.value,
                })
              }
              className="w-full rounded-lg border border-zinc-700 bg-zinc-800 px-3 py-2 text-sm text-white placeholder-zinc-500"
            />
            <div className="flex gap-2">
              <button
                onClick={() => createDataset.mutate(newDataset)}
                disabled={!newDataset.name || !newDataset.knowledge_base_id}
                className="rounded-lg bg-indigo-600 px-4 py-2 text-sm text-white hover:bg-indigo-500 disabled:opacity-50"
              >
                Create
              </button>
              <button
                onClick={() => setShowCreateDataset(false)}
                className="rounded-lg bg-zinc-800 px-4 py-2 text-sm text-zinc-400 hover:bg-zinc-700"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Start run modal */}
      {showRunForm && (
        <div className="mb-6 rounded-xl border border-zinc-800 bg-zinc-900/50 p-6">
          <h3 className="mb-4 text-lg font-semibold text-white">
            Start Evaluation Run
          </h3>
          <div className="space-y-3">
            <select
              value={newRun.dataset_id}
              onChange={(e) =>
                setNewRun({ ...newRun, dataset_id: e.target.value })
              }
              className="w-full rounded-lg border border-zinc-700 bg-zinc-800 px-3 py-2 text-sm text-white"
            >
              <option value="">Select Dataset</option>
              {datasets.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.name} ({d.item_count} items)
                </option>
              ))}
            </select>
            <input
              placeholder="RAG Config ID"
              value={newRun.rag_config_id}
              onChange={(e) =>
                setNewRun({ ...newRun, rag_config_id: e.target.value })
              }
              className="w-full rounded-lg border border-zinc-700 bg-zinc-800 px-3 py-2 text-sm text-white placeholder-zinc-500"
            />
            <div className="flex gap-2">
              <button
                onClick={() => startRun.mutate(newRun)}
                disabled={!newRun.dataset_id || !newRun.rag_config_id}
                className="rounded-lg bg-indigo-600 px-4 py-2 text-sm text-white hover:bg-indigo-500 disabled:opacity-50"
              >
                Start
              </button>
              <button
                onClick={() => setShowRunForm(false)}
                className="rounded-lg bg-zinc-800 px-4 py-2 text-sm text-zinc-400 hover:bg-zinc-700"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Datasets */}
      <div className="mb-8">
        <h2 className="mb-4 text-lg font-semibold text-white">Datasets</h2>
        {datasets.length === 0 ? (
          <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-8 text-center">
            <p className="text-zinc-500">
              No datasets yet. Create one to start evaluating.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
            {datasets.map((d) => (
              <div
                key={d.id}
                className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-4"
              >
                <h3 className="font-medium text-white">{d.name}</h3>
                {d.description && (
                  <p className="mt-1 text-sm text-zinc-400">
                    {d.description}
                  </p>
                )}
                <div className="mt-3 flex items-center gap-3 text-xs text-zinc-500">
                  <span>{d.item_count} items</span>
                  <span>
                    {d.created_at
                      ? new Date(d.created_at).toLocaleDateString()
                      : ""}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Runs */}
      <div>
        <h2 className="mb-4 text-lg font-semibold text-white">
          Evaluation Runs
        </h2>
        {runs.length === 0 ? (
          <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-8 text-center">
            <p className="text-zinc-500">No evaluation runs yet.</p>
          </div>
        ) : (
          <div className="space-y-3">
            {runs.map((r) => (
              <div
                key={r.id}
                onClick={() => setSelectedRun(r.id)}
                className="cursor-pointer rounded-xl border border-zinc-800 bg-zinc-900/50 p-4 hover:border-zinc-700"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <BarChart3 className="h-5 w-5 text-zinc-500" />
                    <div>
                      <p className="text-sm font-medium text-white">
                        Run {r.id.slice(0, 8)}...
                      </p>
                      <p className="text-xs text-zinc-500">
                        {r.completed_items}/{r.total_items} items
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <StatusBadge status={r.status} />
                    <ChevronRight className="h-4 w-4 text-zinc-500" />
                  </div>
                </div>

                {r.status === "completed" && (
                  <div className="mt-3 grid grid-cols-3 gap-2 md:grid-cols-6">
                    <MetricCard label="Recall@K" value={r.recall_at_k} />
                    <MetricCard
                      label="Precision@K"
                      value={r.precision_at_k}
                    />
                    <MetricCard label="MRR" value={r.mrr} />
                    <MetricCard label="NDCG" value={r.ndcg} />
                    <MetricCard
                      label="Faithfulness"
                      value={r.faithfulness}
                    />
                    <MetricCard
                      label="Relevance"
                      value={r.answer_relevance}
                    />
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Run detail panel */}
      {selectedRun && runDetail && (
        <div className="mt-6 rounded-xl border border-zinc-800 bg-zinc-900/50 p-6">
          <div className="mb-4 flex items-center justify-between">
            <h3 className="text-lg font-semibold text-white">Run Details</h3>
            <button
              onClick={() => setSelectedRun(null)}
              className="text-sm text-zinc-400 hover:text-white"
            >
              Close
            </button>
          </div>
          <div className="grid grid-cols-3 gap-3 md:grid-cols-6">
            <MetricCard label="Recall@K" value={runDetail.recall_at_k} />
            <MetricCard
              label="Precision@K"
              value={runDetail.precision_at_k}
            />
            <MetricCard label="MRR" value={runDetail.mrr} />
            <MetricCard label="NDCG" value={runDetail.ndcg} />
            <MetricCard
              label="Faithfulness"
              value={runDetail.faithfulness}
            />
            <MetricCard
              label="Relevance"
              value={runDetail.answer_relevance}
            />
          </div>
          {runDetail.avg_latency_ms != null && (
            <p className="mt-3 text-sm text-zinc-400">
              Avg latency: {runDetail.avg_latency_ms.toFixed(1)} ms
            </p>
          )}
          {runDetail.error_message && (
            <p className="mt-2 text-sm text-red-400">
              Error: {runDetail.error_message}
            </p>
          )}
          {runDetail.detailed_results?.items && (
            <div className="mt-4">
              <h4 className="mb-2 text-sm font-medium text-white">
                Per-Item Results
              </h4>
              <div className="max-h-96 overflow-y-auto rounded-lg border border-zinc-800">
                <table className="w-full text-left text-xs">
                  <thead className="sticky top-0 bg-zinc-900">
                    <tr className="border-b border-zinc-800 text-zinc-400">
                      <th className="px-3 py-2">Question</th>
                      <th className="px-3 py-2">Recall</th>
                      <th className="px-3 py-2">Faith.</th>
                      <th className="px-3 py-2">Relev.</th>
                      <th className="px-3 py-2">Latency</th>
                    </tr>
                  </thead>
                  <tbody>
                    {runDetail.detailed_results.items.map((item, idx) => (
                        <tr
                          key={idx}
                          className="border-b border-zinc-800/50 text-zinc-300"
                        >
                          <td className="max-w-xs truncate px-3 py-2">
                            {item.question}
                          </td>
                          <td className="px-3 py-2">
                            {item.recall_at_k.toFixed(2)}
                          </td>
                          <td className="px-3 py-2">
                            {item.faithfulness.toFixed(2)}
                          </td>
                          <td className="px-3 py-2">
                            {item.answer_relevance.toFixed(2)}
                          </td>
                          <td className="px-3 py-2">
                            {item.latency_ms.toFixed(0)} ms
                          </td>
                        </tr>
                      ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
