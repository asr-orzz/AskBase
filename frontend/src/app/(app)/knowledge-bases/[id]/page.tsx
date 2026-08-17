"use client";

import { use, useRef, useState } from "react";
import { useKnowledgeBase, useDocuments, useUploadDocument, useDeleteDocument } from "@/lib/hooks";
import { cn } from "@/lib/utils";
import { Upload, FileText, Trash2, ArrowLeft, CheckCircle, XCircle, Clock, Loader2, CloudUpload, Layers } from "lucide-react";
import Link from "next/link";

const STATUS_ICON: Record<string, typeof Clock> = {
  pending: Clock,
  processing: Loader2,
  indexed: CheckCircle,
  failed: XCircle,
  deleted: XCircle,
};

const STATUS_COLOR: Record<string, string> = {
  pending: "text-zinc-400",
  processing: "text-amber-400 animate-spin",
  indexed: "text-emerald-400",
  failed: "text-red-400",
  deleted: "text-zinc-600",
};

function formatBytes(bytes: number | null) {
  if (!bytes) return "—";
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export default function KnowledgeBaseDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const { data: kb, isLoading: kbLoading } = useKnowledgeBase(id);
  const { data: docs, isLoading: docsLoading } = useDocuments(id);
  const uploadMutation = useUploadDocument(id);
  const deleteMutation = useDeleteDocument(id);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [dragOver, setDragOver] = useState(false);

  const handleUpload = async (files: FileList | null) => {
    if (!files) return;
    for (const file of Array.from(files)) {
      await uploadMutation.mutateAsync(file);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    handleUpload(e.dataTransfer.files);
  };

  if (kbLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="h-6 w-6 animate-spin rounded-full border-2 border-zinc-700 border-t-indigo-500" />
      </div>
    );
  }
  if (!kb) return <div className="text-zinc-500 py-12 text-center">Knowledge base not found</div>;

  return (
    <div className="max-w-4xl">
      <Link
        href="/knowledge-bases"
        className="mb-6 inline-flex items-center gap-1.5 text-sm text-zinc-500 hover:text-white transition-colors"
      >
        <ArrowLeft className="h-4 w-4" /> All Knowledge Bases
      </Link>

      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white tracking-tight">{kb.name}</h1>
        {kb.description && <p className="mt-1 text-sm text-zinc-400">{kb.description}</p>}
        <div className="mt-4 flex items-center gap-3">
          <span className="inline-flex items-center gap-1.5 rounded-lg bg-zinc-800/80 px-3 py-1.5 text-xs font-medium text-zinc-300">
            <FileText className="h-3.5 w-3.5 text-zinc-500" />
            {kb.document_count} documents
          </span>
          <span className="inline-flex items-center gap-1.5 rounded-lg bg-zinc-800/80 px-3 py-1.5 text-xs font-medium text-zinc-300">
            <Layers className="h-3.5 w-3.5 text-zinc-500" />
            {kb.chunk_count} chunks
          </span>
          <span className={cn(
            "inline-flex items-center rounded-lg px-3 py-1.5 text-xs font-medium",
            kb.status === "active" && "bg-emerald-500/10 text-emerald-400"
          )}>
            {kb.status}
          </span>
        </div>
      </div>

      {/* Upload zone */}
      <div
        onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
        className={cn(
          "mb-8 rounded-2xl border-2 border-dashed p-10 text-center transition-all",
          dragOver
            ? "border-indigo-500 bg-indigo-500/5 scale-[1.01]"
            : "border-zinc-800 hover:border-zinc-700 hover:bg-zinc-900/30"
        )}
      >
        <CloudUpload className={cn("mx-auto h-10 w-10", dragOver ? "text-indigo-400" : "text-zinc-600")} />
        <p className="mt-3 text-sm text-zinc-300">
          Drag & drop files here, or{" "}
          <button onClick={() => fileInputRef.current?.click()} className="font-medium text-indigo-400 hover:text-indigo-300">
            browse files
          </button>
        </p>
        <p className="mt-1.5 text-xs text-zinc-600">Supports PDF, DOCX, TXT, MD, HTML up to 50 MB</p>
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept=".pdf,.docx,.txt,.md,.html,.htm"
          onChange={(e) => handleUpload(e.target.files)}
          className="hidden"
        />
        {uploadMutation.isPending && (
          <div className="mt-4 inline-flex items-center gap-2 rounded-lg bg-amber-500/10 px-4 py-2 text-sm text-amber-400">
            <Loader2 className="h-4 w-4 animate-spin" />
            Processing document...
          </div>
        )}
      </div>

      {/* Documents list */}
      <div className="rounded-2xl border border-zinc-800/80 bg-zinc-900/30 overflow-hidden">
        <div className="border-b border-zinc-800/80 px-6 py-4">
          <h2 className="text-sm font-semibold text-white">Documents</h2>
        </div>

        {docsLoading ? (
          <div className="flex items-center justify-center p-12">
            <div className="h-5 w-5 animate-spin rounded-full border-2 border-zinc-700 border-t-indigo-500" />
          </div>
        ) : !docs?.items?.length ? (
          <div className="p-12 text-center">
            <FileText className="mx-auto h-8 w-8 text-zinc-700" />
            <p className="mt-3 text-sm text-zinc-500">No documents yet. Upload some files above.</p>
          </div>
        ) : (
          <div className="divide-y divide-zinc-800/60">
            {docs.items.map((doc) => {
              const Icon = STATUS_ICON[doc.status] || FileText;
              return (
                <div key={doc.id} className="flex items-center justify-between px-6 py-4 transition-colors hover:bg-zinc-800/20">
                  <div className="flex items-center gap-3">
                    <div className={cn("rounded-lg bg-zinc-800/60 p-2", STATUS_COLOR[doc.status])}>
                      <Icon className="h-4 w-4" />
                    </div>
                    <div>
                      <p className="text-sm font-medium text-white">{doc.title}</p>
                      <div className="flex gap-3 mt-0.5 text-xs text-zinc-500">
                        <span>{formatBytes(doc.file_size)}</span>
                        <span>{doc.chunk_count} chunks</span>
                        <span className={cn(
                          doc.status === "indexed" && "text-emerald-500",
                          doc.status === "failed" && "text-red-400",
                          doc.status === "processing" && "text-amber-400",
                        )}>
                          {doc.status}
                        </span>
                      </div>
                    </div>
                  </div>
                  <button
                    onClick={() => deleteMutation.mutate(doc.id)}
                    className="rounded-lg p-2 text-zinc-600 transition-colors hover:bg-red-500/10 hover:text-red-400"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
