"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import {
  Key,
  Plus,
  Trash2,
  Copy,
  Check,
  Shield,
  AlertTriangle,
} from "lucide-react";

interface ApiKeyRecord {
  id: string;
  name: string;
  prefix: string;
  is_active: boolean;
  last_used_at: string | null;
  expires_at: string | null;
  created_at: string;
}

export default function SettingsPage() {
  const queryClient = useQueryClient();
  const [showCreate, setShowCreate] = useState(false);
  const [keyName, setKeyName] = useState("");
  const [newKey, setNewKey] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  const { data: keys = [] } = useQuery<ApiKeyRecord[]>({
    queryKey: ["api-keys"],
    queryFn: () => api.get<ApiKeyRecord[]>("/api-keys"),
  });

  const createKey = useMutation({
    mutationFn: (name: string) =>
      api.post<{ key: string; id: string }>("/api-keys", { name }),
    onSuccess: (data) => {
      setNewKey(data.key);
      setShowCreate(false);
      setKeyName("");
      queryClient.invalidateQueries({ queryKey: ["api-keys"] });
    },
  });

  const deleteKey = useMutation({
    mutationFn: (id: string) => api.delete(`/api-keys/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["api-keys"] });
    },
  });

  const copyKey = () => {
    if (newKey) {
      navigator.clipboard.writeText(newKey);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white">Settings</h1>
        <p className="mt-1 text-sm text-zinc-400">
          Manage API keys, organization, and platform configuration
        </p>
      </div>

      {/* New key reveal banner */}
      {newKey && (
        <div className="mb-6 rounded-xl border border-amber-400/30 bg-amber-400/5 p-4">
          <div className="flex items-start gap-3">
            <AlertTriangle className="mt-0.5 h-5 w-5 flex-shrink-0 text-amber-400" />
            <div className="flex-1">
              <p className="text-sm font-medium text-amber-400">
                Save your API key now — it won&apos;t be shown again
              </p>
              <div className="mt-2 flex items-center gap-2">
                <code className="flex-1 rounded-lg bg-zinc-900 px-3 py-2 font-mono text-sm text-white">
                  {newKey}
                </code>
                <button
                  onClick={copyKey}
                  className="flex items-center gap-1 rounded-lg bg-zinc-800 px-3 py-2 text-sm text-white hover:bg-zinc-700"
                >
                  {copied ? (
                    <Check className="h-4 w-4 text-emerald-400" />
                  ) : (
                    <Copy className="h-4 w-4" />
                  )}
                </button>
              </div>
              <button
                onClick={() => setNewKey(null)}
                className="mt-2 text-xs text-zinc-400 hover:text-white"
              >
                Dismiss
              </button>
            </div>
          </div>
        </div>
      )}

      {/* API Keys */}
      <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-6">
        <div className="mb-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Shield className="h-5 w-5 text-zinc-400" />
            <h2 className="text-lg font-semibold text-white">API Keys</h2>
          </div>
          <button
            onClick={() => setShowCreate(true)}
            className="flex items-center gap-2 rounded-lg bg-indigo-600 px-3 py-1.5 text-sm text-white hover:bg-indigo-500"
          >
            <Plus className="h-4 w-4" />
            Create Key
          </button>
        </div>

        <p className="mb-4 text-sm text-zinc-400">
          API keys authenticate external requests to the RAG API. Include the
          key in the <code className="text-zinc-300">X-API-Key</code> header.
        </p>

        {/* Create form */}
        {showCreate && (
          <div className="mb-4 flex items-center gap-2 rounded-lg border border-zinc-700 bg-zinc-800 p-3">
            <input
              autoFocus
              placeholder="Key name (e.g. production-backend)"
              value={keyName}
              onChange={(e) => setKeyName(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && keyName) createKey.mutate(keyName);
              }}
              className="flex-1 bg-transparent text-sm text-white placeholder-zinc-500 outline-none"
            />
            <button
              onClick={() => createKey.mutate(keyName)}
              disabled={!keyName || createKey.isPending}
              className="rounded-lg bg-indigo-600 px-3 py-1 text-sm text-white hover:bg-indigo-500 disabled:opacity-50"
            >
              Create
            </button>
            <button
              onClick={() => {
                setShowCreate(false);
                setKeyName("");
              }}
              className="text-sm text-zinc-400 hover:text-white"
            >
              Cancel
            </button>
          </div>
        )}

        {/* Keys table */}
        {keys.length === 0 ? (
          <div className="rounded-lg border border-zinc-800 p-8 text-center">
            <Key className="mx-auto h-8 w-8 text-zinc-600" />
            <p className="mt-2 text-sm text-zinc-500">
              No API keys yet. Create one to authenticate API requests.
            </p>
          </div>
        ) : (
          <div className="overflow-hidden rounded-lg border border-zinc-800">
            <table className="w-full text-left text-sm">
              <thead className="bg-zinc-900 text-xs text-zinc-400">
                <tr className="border-b border-zinc-800">
                  <th className="px-4 py-3">Name</th>
                  <th className="px-4 py-3">Key</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3">Last Used</th>
                  <th className="px-4 py-3">Created</th>
                  <th className="px-4 py-3" />
                </tr>
              </thead>
              <tbody>
                {keys.map((k) => (
                  <tr
                    key={k.id}
                    className="border-b border-zinc-800/50 text-zinc-300"
                  >
                    <td className="px-4 py-3 font-medium text-white">
                      {k.name}
                    </td>
                    <td className="px-4 py-3 font-mono text-xs text-zinc-500">
                      {k.prefix}...
                    </td>
                    <td className="px-4 py-3">
                      {k.is_active ? (
                        <span className="inline-flex items-center rounded-full border border-emerald-400/20 bg-emerald-400/10 px-2 py-0.5 text-xs text-emerald-400">
                          Active
                        </span>
                      ) : (
                        <span className="inline-flex items-center rounded-full border border-red-400/20 bg-red-400/10 px-2 py-0.5 text-xs text-red-400">
                          Revoked
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-xs text-zinc-500">
                      {k.last_used_at
                        ? new Date(k.last_used_at).toLocaleDateString()
                        : "Never"}
                    </td>
                    <td className="px-4 py-3 text-xs text-zinc-500">
                      {k.created_at
                        ? new Date(k.created_at).toLocaleDateString()
                        : ""}
                    </td>
                    <td className="px-4 py-3 text-right">
                      {k.is_active && (
                        <button
                          onClick={() => deleteKey.mutate(k.id)}
                          className="rounded p-1 text-zinc-500 hover:bg-zinc-800 hover:text-red-400"
                          title="Revoke key"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Auth info */}
      <div className="mt-6 rounded-xl border border-zinc-800 bg-zinc-900/50 p-6">
        <h2 className="mb-3 text-lg font-semibold text-white">
          Authentication
        </h2>
        <div className="space-y-3 text-sm text-zinc-400">
          <div>
            <p className="font-medium text-zinc-300">JWT Bearer Token</p>
            <p>
              Obtain a token via{" "}
              <code className="text-zinc-300">POST /api/v1/auth/login</code>{" "}
              and pass it as{" "}
              <code className="text-zinc-300">
                Authorization: Bearer &lt;token&gt;
              </code>
            </p>
          </div>
          <div>
            <p className="font-medium text-zinc-300">API Key</p>
            <p>
              Create a key above and pass it as{" "}
              <code className="text-zinc-300">
                X-API-Key: rag_...
              </code>
            </p>
          </div>
          <div>
            <p className="font-medium text-zinc-300">Roles</p>
            <p>
              <span className="text-white">Admin</span> — full access |{" "}
              <span className="text-white">Developer</span> — read/write |{" "}
              <span className="text-white">Viewer</span> — read only
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
