"use client";

import { useState, useRef, useEffect } from "react";
import { Send, Bot, User, FileText, Clock, Zap, Sparkles } from "lucide-react";
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
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const queryMutation = useRAGQuery(selectedKb);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

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
    <div className="max-w-7xl">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Playground</h1>
          <p className="mt-1 text-sm text-zinc-500">
            Ask questions against your knowledge bases
          </p>
        </div>
        <select
          value={selectedKb}
          onChange={(e) => setSelectedKb(e.target.value)}
          className="rounded-xl border border-zinc-800 bg-zinc-900 px-4 py-2.5 text-sm text-white focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
        >
          <option value="">Select Knowledge Base</option>
          {kbData?.items?.map((kb) => (
            <option key={kb.id} value={kb.id}>
              {kb.name} ({kb.document_count} docs)
            </option>
          ))}
        </select>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Chat panel */}
        <div className="lg:col-span-2 rounded-2xl border border-zinc-800/80 bg-zinc-900/30 overflow-hidden">
          <div className="flex h-[650px] flex-col">
            <div className="flex-1 overflow-y-auto p-6 space-y-6">
              {messages.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-full text-center">
                  <div className="rounded-2xl bg-indigo-600/10 p-4 mb-4">
                    <Sparkles className="h-8 w-8 text-indigo-400" />
                  </div>
                  <h3 className="text-base font-medium text-white">
                    {selectedKb ? "Ask anything about your documents" : "Select a knowledge base"}
                  </h3>
                  <p className="mt-1 text-sm text-zinc-500 max-w-sm">
                    {selectedKb
                      ? "Type a question below and AI will find relevant answers from your uploaded documents."
                      : "Choose a knowledge base from the dropdown above to get started."}
                  </p>
                </div>
              ) : (
                messages.map((msg, i) => (
                  <div key={i} className={cn("flex gap-3", msg.role === "user" && "justify-end")}>
                    {msg.role === "assistant" && (
                      <div className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-indigo-600/10 text-indigo-400">
                        <Bot className="h-4 w-4" />
                      </div>
                    )}
                    <div
                      className={cn(
                        "max-w-[80%] rounded-2xl px-4 py-3 text-sm leading-relaxed",
                        msg.role === "user"
                          ? "bg-indigo-600 text-white"
                          : "bg-zinc-800/80 text-zinc-200"
                      )}
                    >
                      <p className="whitespace-pre-wrap">{msg.content}</p>
                      {msg.metadata && (
                        <div className="mt-3 flex flex-wrap gap-3 text-[11px] text-zinc-500 border-t border-zinc-700/50 pt-2">
                          <span className="flex items-center gap-1">
                            <Clock className="h-3 w-3" />
                            {msg.metadata.latency.toFixed(0)}ms
                          </span>
                          <span className="flex items-center gap-1">
                            <Zap className="h-3 w-3" />
                            {msg.metadata.tokens} tokens
                          </span>
                          <span>{msg.metadata.model}</span>
                        </div>
                      )}
                    </div>
                    {msg.role === "user" && (
                      <div className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-zinc-800 text-zinc-400">
                        <User className="h-4 w-4" />
                      </div>
                    )}
                  </div>
                ))
              )}
              {queryMutation.isPending && (
                <div className="flex gap-3">
                  <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-indigo-600/10 text-indigo-400">
                    <Bot className="h-4 w-4" />
                  </div>
                  <div className="rounded-2xl bg-zinc-800/80 px-5 py-4">
                    <div className="flex gap-1.5">
                      <span className="h-2 w-2 rounded-full bg-zinc-500 animate-bounce" />
                      <span className="h-2 w-2 rounded-full bg-zinc-500 animate-bounce [animation-delay:150ms]" />
                      <span className="h-2 w-2 rounded-full bg-zinc-500 animate-bounce [animation-delay:300ms]" />
                    </div>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>

            <div className="border-t border-zinc-800/80 p-4 bg-zinc-900/50">
              <div className="flex gap-3">
                <input
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && handleSend()}
                  placeholder={selectedKb ? "Ask a question..." : "Select a knowledge base first"}
                  disabled={!selectedKb}
                  className="flex-1 rounded-xl border border-zinc-800 bg-zinc-950 px-4 py-3 text-sm text-white placeholder-zinc-600 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 disabled:opacity-40"
                />
                <button
                  onClick={handleSend}
                  disabled={!selectedKb || !input.trim() || queryMutation.isPending}
                  className="rounded-xl bg-indigo-600 px-4 py-3 text-white shadow-lg shadow-indigo-600/10 transition-all hover:bg-indigo-500 disabled:opacity-40 disabled:shadow-none"
                >
                  <Send className="h-4 w-4" />
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Sources panel */}
        <div className="rounded-2xl border border-zinc-800/80 bg-zinc-900/30 overflow-hidden h-fit max-h-[650px] flex flex-col">
          <div className="border-b border-zinc-800/80 px-5 py-4">
            <h3 className="text-sm font-semibold text-white">Retrieved Sources</h3>
            <p className="text-xs text-zinc-500 mt-0.5">Context used for the answer</p>
          </div>
          <div className="flex-1 overflow-y-auto p-4">
            {activeChunks.length === 0 ? (
              <div className="text-center py-12">
                <FileText className="mx-auto h-8 w-8 text-zinc-700" />
                <p className="mt-3 text-sm text-zinc-500">Sources will appear here after a query</p>
              </div>
            ) : (
              <div className="space-y-3">
                {activeChunks.map((chunk) => (
                  <div key={chunk.chunk_id} className="rounded-xl border border-zinc-800/60 bg-zinc-800/30 p-4">
                    <div className="flex items-center justify-between mb-2">
                      <span className="flex items-center gap-1.5 text-xs font-medium text-indigo-400">
                        <FileText className="h-3 w-3" />
                        {chunk.document_title}
                      </span>
                      <span className="rounded-md bg-indigo-500/10 px-2 py-0.5 text-[11px] font-medium text-indigo-300">
                        {(chunk.score * 100).toFixed(0)}%
                      </span>
                    </div>
                    <p className="text-xs text-zinc-400 leading-relaxed line-clamp-5">
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
