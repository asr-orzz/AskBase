"use client";

import { useState } from "react";
import Link from "next/link";
import { Database, Plus, Trash2, FileText, Layers, X } from "lucide-react";
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
    <div className="max-w-6xl">
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Knowledge Bases</h1>
          <p className="mt-1 text-sm text-zinc-500">
            Create and manage your document collections
          </p>
        </div>
        <button
          onClick={() => setShowCreate(true)}
          className="flex items-center gap-2 rounded-xl bg-indigo-600 px-5 py-2.5 text-sm font-medium text-white shadow-lg shadow-indigo-600/10 transition-all hover:bg-indigo-500 hover:shadow-indigo-500/20"
        >
          <Plus className="h-4 w-4" />
          New Knowledge Base
        </button>
      </div>

      {showCreate && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm">
          <div className="w-full max-w-md rounded-2xl border border-zinc-800 bg-zinc-900 p-6 shadow-2xl">
            <div className="flex items-center justify-between mb-5">
              <h2 className="text-lg font-semibold text-white">New Knowledge Base</h2>
              <button onClick={() => setShowCreate(false)} className="text-zinc-500 hover:text-white">
                <X className="h-5 w-5" />
              </button>
            </div>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-zinc-300 mb-1.5">Name</label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full rounded-xl border border-zinc-800 bg-zinc-950 px-4 py-3 text-sm text-white placeholder-zinc-600 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                  placeholder="e.g., Product Documentation"
                  autoFocus
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-zinc-300 mb-1.5">Description</label>
                <textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  rows={3}
                  className="w-full rounded-xl border border-zinc-800 bg-zinc-950 px-4 py-3 text-sm text-white placeholder-zinc-600 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 resize-none"
                  placeholder="What kind of documents will this contain?"
                />
              </div>
            </div>
            <div className="mt-6 flex justify-end gap-3">
              <button
                onClick={() => setShowCreate(false)}
                className="rounded-xl px-4 py-2.5 text-sm font-medium text-zinc-400 hover:text-white transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleCreate}
                disabled={!name.trim() || createMutation.isPending}
                className="rounded-xl bg-indigo-600 px-5 py-2.5 text-sm font-medium text-white hover:bg-indigo-500 disabled:opacity-50 transition-colors"
              >
                {createMutation.isPending ? "Creating..." : "Create"}
              </button>
            </div>
          </div>
        </div>
      )}

      {isLoading ? (
        <div className="flex items-center justify-center py-20">
          <div className="h-6 w-6 animate-spin rounded-full border-2 border-zinc-700 border-t-indigo-500" />
        </div>
      ) : !data?.items?.length ? (
        <div className="rounded-2xl border border-dashed border-zinc-800 p-16 text-center">
          <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-zinc-900">
            <Database className="h-7 w-7 text-zinc-600" />
          </div>
          <h3 className="mt-4 text-base font-medium text-white">No knowledge bases yet</h3>
          <p className="mt-1 text-sm text-zinc-500">
            Create your first knowledge base to start uploading documents.
          </p>
          <button
            onClick={() => setShowCreate(true)}
            className="mt-6 inline-flex items-center gap-2 rounded-xl bg-indigo-600 px-5 py-2.5 text-sm font-medium text-white hover:bg-indigo-500 transition-colors"
          >
            <Plus className="h-4 w-4" />
            Create Knowledge Base
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
          {data.items.map((kb) => (
            <Link
              key={kb.id}
              href={`/knowledge-bases/${kb.id}`}
              className="group rounded-2xl border border-zinc-800/80 bg-zinc-900/30 p-6 transition-all hover:border-zinc-700 hover:bg-zinc-900/60 hover:shadow-lg hover:shadow-black/20"
            >
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                  <div className="rounded-xl bg-indigo-600/10 p-2.5 text-indigo-400 transition-colors group-hover:bg-indigo-600/15">
                    <Database className="h-5 w-5" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-white">{kb.name}</h3>
                    <span
                      className={cn(
                        "mt-1 inline-block rounded-full px-2 py-0.5 text-[11px] font-medium",
                        kb.status === "active" && "bg-emerald-500/10 text-emerald-400",
                        kb.status === "syncing" && "bg-amber-500/10 text-amber-400",
                        kb.status === "error" && "bg-red-500/10 text-red-400"
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
                  className="rounded-lg p-1.5 text-zinc-600 opacity-0 transition-all hover:bg-red-500/10 hover:text-red-400 group-hover:opacity-100"
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>
              {kb.description && (
                <p className="mt-3 text-sm text-zinc-500 line-clamp-2">{kb.description}</p>
              )}
              <div className="mt-5 flex gap-4 text-xs text-zinc-500">
                <span className="flex items-center gap-1.5">
                  <FileText className="h-3.5 w-3.5" /> {kb.document_count} docs
                </span>
                <span className="flex items-center gap-1.5">
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
