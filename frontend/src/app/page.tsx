import {
  Database,
  FileText,
  Activity,
  DollarSign,
} from "lucide-react";

const stats = [
  { name: "Knowledge Bases", value: "—", icon: Database, color: "text-indigo-400" },
  { name: "Documents", value: "—", icon: FileText, color: "text-emerald-400" },
  { name: "Queries Today", value: "—", icon: Activity, color: "text-amber-400" },
  { name: "Cost (MTD)", value: "—", icon: DollarSign, color: "text-rose-400" },
];

export default function DashboardPage() {
  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white">Dashboard</h1>
        <p className="mt-1 text-sm text-zinc-400">
          Overview of your RAG platform
        </p>
      </div>

      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat) => (
          <div
            key={stat.name}
            className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-6"
          >
            <div className="flex items-center gap-3">
              <div className={`rounded-lg bg-zinc-800 p-2 ${stat.color}`}>
                <stat.icon className="h-5 w-5" />
              </div>
              <span className="text-sm text-zinc-400">{stat.name}</span>
            </div>
            <p className="mt-4 text-3xl font-semibold text-white">
              {stat.value}
            </p>
          </div>
        ))}
      </div>

      <div className="mt-8 grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-6">
          <h2 className="text-lg font-semibold text-white">Recent Activity</h2>
          <p className="mt-4 text-sm text-zinc-500">
            No activity yet. Create a knowledge base to get started.
          </p>
        </div>

        <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-6">
          <h2 className="text-lg font-semibold text-white">System Health</h2>
          <div className="mt-4 space-y-3">
            {["API", "PostgreSQL", "Qdrant", "Redis"].map((service) => (
              <div
                key={service}
                className="flex items-center justify-between text-sm"
              >
                <span className="text-zinc-400">{service}</span>
                <span className="flex items-center gap-2 text-zinc-500">
                  <span className="h-2 w-2 rounded-full bg-zinc-600" />
                  Unknown
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
