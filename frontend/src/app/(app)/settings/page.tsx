"use client";

import { useState, useEffect } from "react";
import { useSession } from "next-auth/react";
import { Key, Eye, EyeOff, Check } from "lucide-react";

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
    <div className="mx-auto max-w-2xl py-10 px-6">
      <h1 className="text-2xl font-bold text-white">Settings</h1>
      <p className="mt-1 text-sm text-zinc-400">
        Configure your API keys for LLM and embeddings.
      </p>

      <div className="mt-8 rounded-xl border border-zinc-800 bg-zinc-900 p-6">
        <div className="flex items-center gap-3 mb-4">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-indigo-600/20">
            <Key className="h-4 w-4 text-indigo-400" />
          </div>
          <div>
            <h2 className="text-sm font-semibold text-white">Google Gemini API Key</h2>
            <p className="text-xs text-zinc-500">Used for embeddings and answer generation</p>
          </div>
        </div>

        <div className="space-y-4">
          <div className="flex gap-3">
            <button
              onClick={() => setUseCustomKey(false)}
              className={`flex-1 rounded-lg border px-4 py-3 text-left transition-colors ${
                !useCustomKey
                  ? "border-indigo-500 bg-indigo-600/10"
                  : "border-zinc-700 bg-zinc-800 hover:border-zinc-600"
              }`}
            >
              <p className={`text-sm font-medium ${!useCustomKey ? "text-indigo-300" : "text-white"}`}>
                Use Default
              </p>
              <p className="mt-0.5 text-xs text-zinc-500">
                Platform&apos;s shared API key
              </p>
            </button>

            <button
              onClick={() => setUseCustomKey(true)}
              className={`flex-1 rounded-lg border px-4 py-3 text-left transition-colors ${
                useCustomKey
                  ? "border-indigo-500 bg-indigo-600/10"
                  : "border-zinc-700 bg-zinc-800 hover:border-zinc-600"
              }`}
            >
              <p className={`text-sm font-medium ${useCustomKey ? "text-indigo-300" : "text-white"}`}>
                Use My API Key
              </p>
              <p className="mt-0.5 text-xs text-zinc-500">
                Your own Gemini key
              </p>
            </button>
          </div>

          {useCustomKey && (
            <div>
              <label className="block text-sm text-zinc-400 mb-1">
                Gemini API Key
                {hasExistingKey && (
                  <span className="ml-2 text-xs text-green-400">(saved key exists)</span>
                )}
              </label>
              <div className="relative">
                <input
                  type={showKey ? "text" : "password"}
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                  placeholder={hasExistingKey ? "Enter new key to update..." : "AIza..."}
                  className="w-full rounded-lg border border-zinc-700 bg-zinc-800 px-3 py-2 pr-10 text-sm text-white placeholder-zinc-600 focus:border-indigo-500 focus:outline-none"
                />
                <button
                  type="button"
                  onClick={() => setShowKey(!showKey)}
                  className="absolute right-2 top-1/2 -translate-y-1/2 text-zinc-500 hover:text-zinc-300"
                >
                  {showKey ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
              <p className="mt-1.5 text-xs text-zinc-600">
                Get your key from{" "}
                <a
                  href="https://aistudio.google.com/apikey"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-indigo-400 hover:underline"
                >
                  Google AI Studio
                </a>
              </p>
            </div>
          )}

          {error && <p className="text-sm text-red-400">{error}</p>}

          <button
            onClick={handleSave}
            disabled={saving}
            className="flex items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-500 disabled:opacity-50 transition-colors"
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
  );
}
