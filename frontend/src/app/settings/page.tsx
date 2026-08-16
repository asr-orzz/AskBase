export default function SettingsPage() {
  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white">Settings</h1>
        <p className="mt-1 text-sm text-zinc-400">
          Organization settings, API keys, and user management
        </p>
      </div>
      <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-6">
        <h3 className="text-sm font-medium text-white">General</h3>
        <p className="mt-3 text-sm text-zinc-500">Settings will appear here.</p>
      </div>
    </div>
  );
}
