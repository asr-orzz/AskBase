"use client";

import {
  Rocket,
  Server,
  CheckCircle2,
  Clock,
  AlertTriangle,
  ExternalLink,
} from "lucide-react";

interface DeploymentInfo {
  name: string;
  service: string;
  status: "running" | "pending" | "error";
  port: string;
  description: string;
}

const SERVICES: DeploymentInfo[] = [
  {
    name: "API Server",
    service: "api",
    status: "running",
    port: "8000",
    description: "FastAPI backend — handles all REST endpoints, RAG queries, auth",
  },
  {
    name: "Celery Worker",
    service: "celery-worker",
    status: "running",
    port: "—",
    description: "Background task processing — ingestion, sync, evaluations, experiments",
  },
  {
    name: "Celery Beat",
    service: "celery-beat",
    status: "running",
    port: "—",
    description: "Periodic task scheduler for scheduled syncs and cleanup",
  },
  {
    name: "Frontend",
    service: "frontend",
    status: "running",
    port: "3000",
    description: "Next.js dashboard — knowledge base management, playground, observability",
  },
  {
    name: "PostgreSQL",
    service: "postgres",
    status: "running",
    port: "5432",
    description: "Primary database — metadata, configs, users, evaluations",
  },
  {
    name: "Qdrant",
    service: "qdrant",
    status: "running",
    port: "6333",
    description: "Vector database — document embeddings and similarity search",
  },
  {
    name: "Redis",
    service: "redis",
    status: "running",
    port: "6379",
    description: "Celery broker and result backend, caching layer",
  },
  {
    name: "Kafka",
    service: "kafka",
    status: "running",
    port: "9092",
    description: "Event streaming — document events, query events, sync events",
  },
  {
    name: "MinIO",
    service: "minio",
    status: "running",
    port: "9000 / 9001",
    description: "S3-compatible object storage for raw document files",
  },
  {
    name: "Prometheus",
    service: "prometheus",
    status: "running",
    port: "9090",
    description: "Metrics collection — scrapes /metrics from API and OTel collector",
  },
  {
    name: "Grafana",
    service: "grafana",
    status: "running",
    port: "3001",
    description: "Dashboards and alerting — visualize metrics, traces, and logs",
  },
  {
    name: "OTel Collector",
    service: "otel-collector",
    status: "running",
    port: "4317 / 4318",
    description: "OpenTelemetry Collector — receives traces and exports to backends",
  },
];

function StatusIcon({ status }: { status: string }) {
  if (status === "running")
    return <CheckCircle2 className="h-4 w-4 text-emerald-400" />;
  if (status === "pending")
    return <Clock className="h-4 w-4 text-amber-400" />;
  return <AlertTriangle className="h-4 w-4 text-red-400" />;
}

export default function DeploymentsPage() {
  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white">Deployments</h1>
        <p className="mt-1 text-sm text-zinc-400">
          Platform services managed by Docker Compose
        </p>
      </div>

      {/* Quick start */}
      <div className="mb-6 rounded-xl border border-zinc-800 bg-zinc-900/50 p-6">
        <h2 className="mb-3 flex items-center gap-2 text-lg font-semibold text-white">
          <Rocket className="h-5 w-5 text-indigo-400" />
          Quick Start
        </h2>
        <div className="space-y-2 font-mono text-sm">
          <div className="rounded-lg bg-zinc-800 px-4 py-2 text-zinc-300">
            <span className="text-zinc-500">$</span> git clone
            https://github.com/your-org/ragops.git && cd ragops
          </div>
          <div className="rounded-lg bg-zinc-800 px-4 py-2 text-zinc-300">
            <span className="text-zinc-500">$</span> cp
            backend/.env.example backend/.env
          </div>
          <div className="rounded-lg bg-zinc-800 px-4 py-2 text-zinc-300">
            <span className="text-zinc-500">$</span> docker compose up -d
          </div>
          <div className="rounded-lg bg-zinc-800 px-4 py-2 text-zinc-300">
            <span className="text-zinc-500">$</span> docker compose exec api
            alembic upgrade head
          </div>
        </div>
      </div>

      {/* Service grid */}
      <div className="grid grid-cols-1 gap-3 md:grid-cols-2 lg:grid-cols-3">
        {SERVICES.map((svc) => (
          <div
            key={svc.service}
            className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-4"
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Server className="h-4 w-4 text-zinc-500" />
                <h3 className="font-medium text-white">{svc.name}</h3>
              </div>
              <StatusIcon status={svc.status} />
            </div>
            <p className="mt-2 text-xs text-zinc-400">{svc.description}</p>
            <div className="mt-3 flex items-center justify-between text-xs">
              <span className="font-mono text-zinc-500">{svc.service}</span>
              {svc.port !== "—" && (
                <span className="rounded bg-zinc-800 px-2 py-0.5 text-zinc-400">
                  :{svc.port}
                </span>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Links */}
      <div className="mt-6 rounded-xl border border-zinc-800 bg-zinc-900/50 p-6">
        <h2 className="mb-3 text-lg font-semibold text-white">
          Service URLs (local)
        </h2>
        <div className="grid grid-cols-1 gap-2 md:grid-cols-2 text-sm">
          {[
            { label: "API Docs", url: "http://localhost:8000/docs" },
            { label: "Frontend", url: "http://localhost:3000" },
            { label: "Grafana", url: "http://localhost:3001" },
            { label: "Prometheus", url: "http://localhost:9090" },
            { label: "MinIO Console", url: "http://localhost:9001" },
            { label: "Qdrant Dashboard", url: "http://localhost:6333/dashboard" },
          ].map((link) => (
            <a
              key={link.label}
              href={link.url}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center justify-between rounded-lg border border-zinc-800 px-4 py-2 text-zinc-300 hover:border-zinc-700 hover:text-white"
            >
              {link.label}
              <ExternalLink className="h-3 w-3 text-zinc-500" />
            </a>
          ))}
        </div>
      </div>
    </div>
  );
}
