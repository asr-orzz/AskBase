"use client";

import { useState } from "react";
import Link from "next/link";
import { Database, Plus, Trash2, FileText, Layers } from "lucide-react";
import { useKnowledgeBases, useCreateKnowledgeBase, useDeleteKnowledgeBase } from "@/lib/hooks";
import { cn } from "@/lib/utils";

export default function KnowledgeBasesPage() {
  const { data, isLoading } = useKnowledgeBases();
  const createMutation = useCreateKnowledgeBase();
  const deleteMutation = useDeleteKnowledgeBase();

  const [showCreate, setShowCreate] = useState(false);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");

  const handleCreate = async () => {
    if (!name.trim()) return;
    await createMutation.mutateAsync({ name, description: description || undefined });
    setName("");
    setDescription("");
    setShowCreate(false);
  };

  return (
    <div>
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Knowledge Bases</h1>
          <p className="mt-1 text-sm text-zinc-400">
            Manage your knowledge bases and data sources
          </p>
        </div>
        <button
          onClick={() => setShowCreate(true)}
          className="flex items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-500 transition-colors"
        >
          <Plus className="h-4 w-4" />
          Create Knowledge Base
        </button>
      </div>

      {/* Create Modal */}
      {showCreate && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60">
          <div className="w-full max-w-md rounded-xl border border-zinc-700 bg-zinc-900 p-6">
            <h2 className="text-lg font-semibold text-white">Create Knowledge Base</h2>
            <div className="mt-4 space-y-4">
              <div>
                <label className="block text-sm text-zinc-400">Name</label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="mt-1 w-full rounded-lg border border-zinc-700 bg-zinc-800 px-3 py-2 text-sm text-white focus:border-indigo-500 focus:outline-none"
                  placeholder="e.g., Engineering Docs"
                />
              </div>
              <div>
                <label className="block text-sm text-zinc-400">Description</label>
                <textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  rows={3}
                  className="mt-1 w-full rounded-lg border border-zinc-700 bg-zinc-800 px-3 py-2 text-sm text-white focus:border-indigo-500 focus:outline-none"
                  placeholder="Optional description..."
                />
              </div>
            </div>
            <div className="mt-6 flex justify-end gap-3">
              <button
                onClick={() => setShowCreate(false)}
                className="rounded-lg px-4 py-2 text-sm text-zinc-400 hover:text-white"
              >
                Cancel
              </button>
              <button
                onClick={handleCreate}
                disabled={!name.trim() || createMutation.isPending}
                className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-500 disabled:opacity-50"
              >
                {createMutation.isPending ? "Creating..." : "Create"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* List */}
      {isLoading ? (
        <div className="text-center text-zinc-500 py-12">Loading...</div>
      ) : !data?.items?.length ? (
        <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-12 text-center">
          <Database className="mx-auto h-12 w-12 text-zinc-700" />
          <p className="mt-4 text-zinc-500">No knowledge bases yet. Create one to get started.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
          {data.items.map((kb) => (
            <Link
              key={kb.id}
              href={`/knowledge-bases/${kb.id}`}
              className="group rounded-xl border border-zinc-800 bg-zinc-900/50 p-6 transition-colors hover:border-zinc-700"
            >
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                  <div className="rounded-lg bg-indigo-600/10 p-2 text-indigo-400">
                    <Database className="h-5 w-5" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-white">{kb.name}</h3>
                    <span
                      className={cn(
                        "mt-1 inline-block rounded-full px-2 py-0.5 text-xs",
                        kb.status === "active" && "bg-emerald-900/50 text-emerald-400",
                        kb.status === "syncing" && "bg-amber-900/50 text-amber-400",
                        kb.status === "error" && "bg-red-900/50 text-red-400"
                      )}
                    >
                      {kb.status}
                    </span>
                  </div>
                </div>
                <button
                  onClick={(e) => {
                    e.preventDefault();
                    if (confirm("Delete this knowledge base?")) {
                      deleteMutation.mutate(kb.id);
                    }
                  }}
                  className="rounded p-1 text-zinc-600 opacity-0 transition-opacity hover:text-red-400 group-hover:opacity-100"
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>
              {kb.description && (
                <p className="mt-3 text-sm text-zinc-500 line-clamp-2">{kb.description}</p>
              )}
              <div className="mt-4 flex gap-4 text-xs text-zinc-500">
                <span className="flex items-center gap-1">
                  <FileText className="h-3.5 w-3.5" /> {kb.document_count} docs
                </span>
                <span className="flex items-center gap-1">
                  <Layers className="h-3.5 w-3.5" /> {kb.chunk_count} chunks
                </span>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
