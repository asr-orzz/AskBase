"use client";

import { useState } from "react";
import { Send, Bot, User, FileText, Clock, Coins } from "lucide-react";
import { useKnowledgeBases, useRAGQuery } from "@/lib/hooks";
import { cn } from "@/lib/utils";
import type { ChunkResponse } from "@/lib/types";

interface Message {
  role: "user" | "assistant";
  content: string;
  chunks?: ChunkResponse[];
  metadata?: {
    model: string;
    tokens: number;
    latency: number;
  };
}

export default function PlaygroundPage() {
  const { data: kbData } = useKnowledgeBases();
  const [selectedKb, setSelectedKb] = useState("");
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [activeChunks, setActiveChunks] = useState<ChunkResponse[]>([]);

  const queryMutation = useRAGQuery(selectedKb);

  const handleSend = async () => {
    if (!input.trim() || !selectedKb) return;

    const question = input;
    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: question }]);

    try {
      const result = await queryMutation.mutateAsync(question);
      const assistantMsg: Message = {
        role: "assistant",
        content: result.answer,
        chunks: result.chunks,
        metadata: {
          model: result.model,
          tokens: result.total_tokens,
          latency: result.total_latency_ms,
        },
      };
      setMessages((prev) => [...prev, assistantMsg]);
      setActiveChunks(result.chunks);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: `Error: ${err instanceof Error ? err.message : "Query failed"}` },
      ]);
    }
  };

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-white">Playground</h1>
        <p className="mt-1 text-sm text-zinc-400">
          Test your RAG pipeline with interactive queries
        </p>
      </div>

      {/* KB selector */}
      <div className="mb-6">
        <select
          value={selectedKb}
          onChange={(e) => setSelectedKb(e.target.value)}
          className="rounded-lg border border-zinc-700 bg-zinc-800 px-4 py-2 text-sm text-white focus:border-indigo-500 focus:outline-none"
        >
          <option value="">Select a Knowledge Base</option>
          {kbData?.items?.map((kb) => (
            <option key={kb.id} value={kb.id}>
              {kb.name} ({kb.document_count} docs)
            </option>
          ))}
        </select>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Chat */}
        <div className="lg:col-span-2 rounded-xl border border-zinc-800 bg-zinc-900/50">
          <div className="flex h-[600px] flex-col">
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              {messages.length === 0 ? (
                <p className="text-center text-sm text-zinc-600 mt-48">
                  {selectedKb ? "Ask a question to get started" : "Select a knowledge base first"}
                </p>
              ) : (
                messages.map((msg, i) => (
                  <div key={i} className={cn("flex gap-3", msg.role === "user" && "justify-end")}>
                    {msg.role === "assistant" && (
                      <div className="mt-1 rounded-lg bg-indigo-600/10 p-1.5 text-indigo-400 h-fit">
                        <Bot className="h-4 w-4" />
                      </div>
                    )}
                    <div
                      className={cn(
                        "max-w-[80%] rounded-xl px-4 py-3 text-sm",
                        msg.role === "user"
                          ? "bg-indigo-600 text-white"
                          : "bg-zinc-800 text-zinc-200"
                      )}
                    >
                      <p className="whitespace-pre-wrap">{msg.content}</p>
                      {msg.metadata && (
                        <div className="mt-2 flex gap-3 text-xs text-zinc-500">
                          <span className="flex items-center gap-1">
                            <Clock className="h-3 w-3" />
                            {msg.metadata.latency.toFixed(0)}ms
                          </span>
                          <span className="flex items-center gap-1">
                            <Coins className="h-3 w-3" />
                            {msg.metadata.tokens} tokens
                          </span>
                          <span>{msg.metadata.model}</span>
                        </div>
                      )}
                    </div>
                    {msg.role === "user" && (
                      <div className="mt-1 rounded-lg bg-zinc-800 p-1.5 text-zinc-400 h-fit">
                        <User className="h-4 w-4" />
                      </div>
                    )}
                  </div>
                ))
              )}
              {queryMutation.isPending && (
                <div className="flex gap-3">
                  <div className="mt-1 rounded-lg bg-indigo-600/10 p-1.5 text-indigo-400 h-fit">
                    <Bot className="h-4 w-4" />
                  </div>
                  <div className="rounded-xl bg-zinc-800 px-4 py-3">
                    <div className="flex gap-1">
                      <span className="h-2 w-2 rounded-full bg-zinc-500 animate-bounce" />
                      <span className="h-2 w-2 rounded-full bg-zinc-500 animate-bounce [animation-delay:150ms]" />
                      <span className="h-2 w-2 rounded-full bg-zinc-500 animate-bounce [animation-delay:300ms]" />
                    </div>
                  </div>
                </div>
              )}
            </div>

            <div className="border-t border-zinc-800 p-4">
              <div className="flex gap-3">
                <input
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && handleSend()}
                  placeholder={selectedKb ? "Ask a question..." : "Select a knowledge base first"}
                  disabled={!selectedKb}
                  className="flex-1 rounded-lg border border-zinc-700 bg-zinc-800 px-4 py-2.5 text-sm text-white placeholder-zinc-500 focus:border-indigo-500 focus:outline-none disabled:opacity-50"
                />
                <button
                  onClick={handleSend}
                  disabled={!selectedKb || !input.trim() || queryMutation.isPending}
                  className="rounded-lg bg-indigo-600 px-4 py-2.5 text-white hover:bg-indigo-500 disabled:opacity-50 transition-colors"
                >
                  <Send className="h-4 w-4" />
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Sources panel */}
        <div className="space-y-4">
          <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-6">
            <h3 className="text-sm font-medium text-white">Retrieved Sources</h3>
            {activeChunks.length === 0 ? (
              <p className="mt-3 text-sm text-zinc-500">Sources will appear here after a query</p>
            ) : (
              <div className="mt-3 space-y-3">
                {activeChunks.map((chunk, i) => (
                  <div key={chunk.chunk_id} className="rounded-lg border border-zinc-800 bg-zinc-800/50 p-3">
                    <div className="flex items-center justify-between">
                      <span className="flex items-center gap-1.5 text-xs font-medium text-indigo-400">
                        <FileText className="h-3 w-3" />
                        {chunk.document_title}
                      </span>
                      <span className="text-xs text-zinc-500">
                        {(chunk.score * 100).toFixed(1)}%
                      </span>
                    </div>
                    <p className="mt-2 text-xs text-zinc-400 line-clamp-4">
                      {chunk.content}
                    </p>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
