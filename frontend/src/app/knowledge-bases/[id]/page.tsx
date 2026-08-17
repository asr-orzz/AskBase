"use client";

import { use, useRef, useState } from "react";
import { useKnowledgeBase, useDocuments, useUploadDocument, useDeleteDocument } from "@/lib/hooks";
import { cn } from "@/lib/utils";
import { Upload, FileText, Trash2, ArrowLeft, CheckCircle, XCircle, Clock, Loader2 } from "lucide-react";
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

  if (kbLoading) return <div className="text-zinc-500 py-12 text-center">Loading...</div>;
  if (!kb) return <div className="text-zinc-500 py-12 text-center">Knowledge base not found</div>;

  return (
    <div>
      <Link href="/knowledge-bases" className="mb-4 inline-flex items-center gap-1 text-sm text-zinc-400 hover:text-white">
        <ArrowLeft className="h-4 w-4" /> Back
      </Link>

      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white">{kb.name}</h1>
        {kb.description && <p className="mt-1 text-sm text-zinc-400">{kb.description}</p>}
        <div className="mt-3 flex gap-4 text-sm text-zinc-500">
          <span>{kb.document_count} documents</span>
          <span>{kb.chunk_count} chunks</span>
          <span className={cn(
            "rounded-full px-2 py-0.5 text-xs",
            kb.status === "active" && "bg-emerald-900/50 text-emerald-400"
          )}>{kb.status}</span>
        </div>
      </div>

      {/* Upload zone */}
      <div
        onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
        className={cn(
          "mb-6 rounded-xl border-2 border-dashed p-8 text-center transition-colors",
          dragOver ? "border-indigo-500 bg-indigo-500/5" : "border-zinc-800 hover:border-zinc-700"
        )}
      >
        <Upload className="mx-auto h-8 w-8 text-zinc-600" />
        <p className="mt-2 text-sm text-zinc-400">
          Drag & drop files here, or{" "}
          <button
            onClick={() => fileInputRef.current?.click()}
            className="text-indigo-400 hover:underline"
          >
            browse
          </button>
        </p>
        <p className="mt-1 text-xs text-zinc-600">PDF, DOCX, TXT, MD, HTML — max 50 MB</p>
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept=".pdf,.docx,.txt,.md,.html,.htm"
          onChange={(e) => handleUpload(e.target.files)}
          className="hidden"
        />
        {uploadMutation.isPending && (
          <p className="mt-3 text-sm text-amber-400">Uploading & processing...</p>
        )}
      </div>

      {/* Documents table */}
      <div className="rounded-xl border border-zinc-800 bg-zinc-900/50">
        <div className="border-b border-zinc-800 px-6 py-4">
          <h2 className="text-sm font-medium text-white">Documents</h2>
        </div>

        {docsLoading ? (
          <div className="p-6 text-center text-zinc-500">Loading documents...</div>
        ) : !docs?.items?.length ? (
          <div className="p-12 text-center text-zinc-500">
            No documents yet. Upload some files above.
          </div>
        ) : (
          <div className="divide-y divide-zinc-800">
            {docs.items.map((doc) => {
              const Icon = STATUS_ICON[doc.status] || FileText;
              return (
                <div key={doc.id} className="flex items-center justify-between px-6 py-4">
                  <div className="flex items-center gap-3">
                    <Icon className={cn("h-4 w-4", STATUS_COLOR[doc.status])} />
                    <div>
                      <p className="text-sm font-medium text-white">{doc.title}</p>
                      <div className="flex gap-3 text-xs text-zinc-500">
                        <span>{formatBytes(doc.file_size)}</span>
                        <span>{doc.chunk_count} chunks</span>
                        <span>v{doc.version}</span>
                      </div>
                    </div>
                  </div>
                  <button
                    onClick={() => deleteMutation.mutate(doc.id)}
                    className="rounded p-1 text-zinc-600 hover:text-red-400"
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
