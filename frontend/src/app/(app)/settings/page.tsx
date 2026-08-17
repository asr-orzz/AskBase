"use client";

import { useState, useEffect } from "react";
import { useSession } from "next-auth/react";
import { Key, Eye, EyeOff, Check, ExternalLink, Shield } from "lucide-react";

export default function SettingsPage() {
  const { data: session } = useSession();
  const [useCustomKey, setUseCustomKey] = useState(false);
  const [apiKey, setApiKey] = useState("");
  const [hasExistingKey, setHasExistingKey] = useState(false);
  const [showKey, setShowKey] = useState(false);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState("");

  const apiBase = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

  useEffect(() => {
    if (!(session as any)?.backendToken) return;
    fetch(`${apiBase}/auth/settings/api-key`, {
      headers: { Authorization: `Bearer ${(session as any).backendToken}` },
    })
      .then((r) => r.json())
      .then((data) => {
        setUseCustomKey(data.use_custom_key);
        setHasExistingKey(data.has_custom_key);
      })
      .catch(() => {});
  }, [session, apiBase]);

  const handleSave = async () => {
    setError("");
    setSaving(true);
    setSaved(false);

    try {
      const body: any = { use_custom_key: useCustomKey };
      if (useCustomKey && apiKey) {
        body.custom_api_key = apiKey;
      }

      const res = await fetch(`${apiBase}/auth/settings/api-key`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${(session as any).backendToken}`,
        },
        body: JSON.stringify(body),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || "Failed to save");
      }

      const data = await res.json();
      setHasExistingKey(data.has_custom_key);
      setUseCustomKey(data.use_custom_key);
      setApiKey("");
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="max-w-2xl">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white tracking-tight">Settings</h1>
        <p className="mt-1 text-sm text-zinc-500">
          Manage your API keys and preferences
        </p>
      </div>

      <div className="rounded-2xl border border-zinc-800/80 bg-zinc-900/30 overflow-hidden">
        <div className="border-b border-zinc-800/80 px-6 py-5 flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-600/10">
            <Key className="h-5 w-5 text-indigo-400" />
          </div>
          <div>
            <h2 className="text-sm font-semibold text-white">Google Gemini API Key</h2>
            <p className="text-xs text-zinc-500">Used for embeddings and answer generation</p>
          </div>
        </div>

        <div className="p-6 space-y-5">
          <div className="grid grid-cols-2 gap-3">
            <button
              onClick={() => setUseCustomKey(false)}
              className={`rounded-xl border px-4 py-4 text-left transition-all ${
                !useCustomKey
                  ? "border-indigo-500/50 bg-indigo-600/5 ring-1 ring-indigo-500/20"
                  : "border-zinc-800 bg-zinc-900/50 hover:border-zinc-700"
              }`}
            >
              <div className="flex items-center gap-2 mb-1">
                <Shield className={`h-4 w-4 ${!useCustomKey ? "text-indigo-400" : "text-zinc-500"}`} />
                <p className={`text-sm font-medium ${!useCustomKey ? "text-indigo-300" : "text-white"}`}>
                  Use Default
                </p>
              </div>
              <p className="text-xs text-zinc-500 pl-6">
                Platform&apos;s shared API key
              </p>
            </button>

            <button
              onClick={() => setUseCustomKey(true)}
              className={`rounded-xl border px-4 py-4 text-left transition-all ${
                useCustomKey
                  ? "border-indigo-500/50 bg-indigo-600/5 ring-1 ring-indigo-500/20"
                  : "border-zinc-800 bg-zinc-900/50 hover:border-zinc-700"
              }`}
            >
              <div className="flex items-center gap-2 mb-1">
                <Key className={`h-4 w-4 ${useCustomKey ? "text-indigo-400" : "text-zinc-500"}`} />
                <p className={`text-sm font-medium ${useCustomKey ? "text-indigo-300" : "text-white"}`}>
                  Use My API Key
                </p>
              </div>
              <p className="text-xs text-zinc-500 pl-6">
                Your own Gemini key
              </p>
            </button>
          </div>

          {useCustomKey && (
            <div className="space-y-2">
              <label className="flex items-center justify-between text-sm font-medium text-zinc-300">
                <span>
                  Gemini API Key
                  {hasExistingKey && (
                    <span className="ml-2 inline-flex items-center gap-1 text-xs font-normal text-emerald-400">
                      <Check className="h-3 w-3" /> Key saved
                    </span>
                  )}
                </span>
              </label>
              <div className="relative">
                <input
                  type={showKey ? "text" : "password"}
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                  placeholder={hasExistingKey ? "Enter new key to update..." : "AIza..."}
                  className="w-full rounded-xl border border-zinc-800 bg-zinc-950 px-4 py-3 pr-11 text-sm text-white placeholder-zinc-600 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                />
                <button
                  type="button"
                  onClick={() => setShowKey(!showKey)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-zinc-500 hover:text-zinc-300 transition-colors"
                >
                  {showKey ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
              <p className="flex items-center gap-1 text-xs text-zinc-600">
                Get your key from{" "}
                <a
                  href="https://aistudio.google.com/apikey"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-0.5 text-indigo-400 hover:text-indigo-300 transition-colors"
                >
                  Google AI Studio <ExternalLink className="h-3 w-3" />
                </a>
              </p>
            </div>
          )}

          {error && (
            <div className="rounded-lg bg-red-500/10 border border-red-500/20 px-4 py-3">
              <p className="text-sm text-red-400">{error}</p>
            </div>
          )}

          <div className="pt-2">
            <button
              onClick={handleSave}
              disabled={saving}
              className="flex items-center gap-2 rounded-xl bg-indigo-600 px-5 py-2.5 text-sm font-medium text-white shadow-lg shadow-indigo-600/10 transition-all hover:bg-indigo-500 hover:shadow-indigo-500/20 disabled:opacity-50 disabled:shadow-none"
            >
              {saved ? (
                <>
                  <Check className="h-4 w-4" />
                  Saved
                </>
              ) : saving ? (
                "Saving..."
              ) : (
                "Save Changes"
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
