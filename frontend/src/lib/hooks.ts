"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "./api";
import type {
  KnowledgeBase,
  KnowledgeBaseList,
  Document,
  DocumentList,
  RAGQueryResponse,
} from "./types";

// --- Knowledge Bases ---

export function useKnowledgeBases() {
  return useQuery<KnowledgeBaseList>({
    queryKey: ["knowledge-bases"],
    queryFn: () => api.get("/knowledge-bases"),
  });
}

export function useKnowledgeBase(id: string) {
  return useQuery<KnowledgeBase>({
    queryKey: ["knowledge-bases", id],
    queryFn: () => api.get(`/knowledge-bases/${id}`),
    enabled: !!id,
  });
}

export function useCreateKnowledgeBase() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: { name: string; description?: string }) =>
      api.post<KnowledgeBase>("/knowledge-bases", data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["knowledge-bases"] }),
  });
}

export function useDeleteKnowledgeBase() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.delete(`/knowledge-bases/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["knowledge-bases"] }),
  });
}

// --- Documents ---

export function useDocuments(kbId: string) {
  return useQuery<DocumentList>({
    queryKey: ["documents", kbId],
    queryFn: () => api.get(`/knowledge-bases/${kbId}/documents`),
    enabled: !!kbId,
  });
}

export function useUploadDocument(kbId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (file: File) => {
      const formData = new FormData();
      formData.append("file", file);
      return api.upload<Document>(
        `/knowledge-bases/${kbId}/documents/upload`,
        formData
      );
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["documents", kbId] });
      qc.invalidateQueries({ queryKey: ["knowledge-bases"] });
    },
  });
}

export function useDeleteDocument(kbId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (docId: string) =>
      api.delete(`/knowledge-bases/${kbId}/documents/${docId}`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["documents", kbId] });
      qc.invalidateQueries({ queryKey: ["knowledge-bases"] });
    },
  });
}

// --- RAG Query ---

export function useRAGQuery(kbId: string) {
  return useMutation({
    mutationFn: (question: string) =>
      api.post<RAGQueryResponse>(`/query/${kbId}`, {
        question,
        top_k: 10,
        similarity_threshold: 0.7,
      }),
  });
}
