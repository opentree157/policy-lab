import { NavLink, useLocation } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import {
  LayoutDashboard,
  Database,
  FlaskConical,
  Plus,
  Activity,
  GitBranch,
  Zap,
} from "lucide-react";
import { api } from "../api/client";

const NAV = [
  { to: "/", icon: LayoutDashboard, label: "Dashboard" },
  { to: "/datasets", icon: Database, label: "Datasets" },
  { to: "/experiments", icon: FlaskConical, label: "Experiments" },
];

export default function Layout({ children }: { children: React.ReactNode }) {
  const { data: sys } = useQuery({
    queryKey: ["system-metrics"],
    queryFn: api.metrics.system,
    refetchInterval: 8_000,
  });

  const location = useLocation();

  return (
    <div className="flex h-screen overflow-hidden">
      {/* Sidebar */}
      <aside className="w-56 bg-slate-950 border-r border-slate-800 flex flex-col shrink-0">
        {/* Logo */}
        <div className="px-5 py-4 border-b border-slate-800">
          <div className="flex items-center gap-2.5">
            <div className="w-7 h-7 bg-brand-600 rounded-lg flex items-center justify-center">
              <Zap className="w-4 h-4 text-white" />
            </div>
            <span className="font-semibold text-white tracking-tight">PolicyLab</span>
          </div>
          <p className="text-xs text-slate-500 mt-1">Research Platform</p>
        </div>

        {/* Nav */}
        <nav className="flex-1 px-3 py-4 space-y-0.5">
          {NAV.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              end={to === "/"}
              className={({ isActive }) =>
                `flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                  isActive
                    ? "bg-slate-800 text-white"
                    : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/60"
                }`
              }
            >
              <Icon className="w-4 h-4" />
              {label}
            </NavLink>
          ))}

          <div className="pt-3">
            <NavLink
              to="/experiments/new"
              className={({ isActive }) =>
                `flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                  isActive
                    ? "bg-brand-700 text-white"
                    : "bg-brand-600/20 text-brand-400 hover:bg-brand-600/30 hover:text-brand-300 border border-brand-600/30"
                }`
              }
            >
              <Plus className="w-4 h-4" />
              New Experiment
            </NavLink>
          </div>
        </nav>

        {/* System stats */}
        <div className="px-4 py-3 border-t border-slate-800 space-y-2">
          <p className="text-xs text-slate-500 uppercase tracking-wide font-medium">System</p>
          <MetricRow
            label="CPU"
            value={sys ? `${sys.cpu_percent.toFixed(0)}%` : "—"}
            pct={sys?.cpu_percent ?? 0}
            color="bg-brand-500"
          />
          <MetricRow
            label="RAM"
            value={sys ? `${sys.memory_percent.toFixed(0)}%` : "—"}
            pct={sys?.memory_percent ?? 0}
            color="bg-emerald-500"
          />
        </div>

        {/* Ray indicator */}
        <div className="px-4 py-3 border-t border-slate-800">
          <div className="flex items-center gap-2">
            <div className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
            <span className="text-xs text-slate-500">Ray local cluster</span>
          </div>
          <div className="flex items-center gap-2 mt-1">
            <GitBranch className="w-3 h-3 text-slate-600" />
            <span className="text-xs text-slate-600 font-mono">main</span>
          </div>
        </div>
      </aside>

      {/* Main */}
      <main className="flex-1 overflow-auto bg-slate-950">
        {/* Top bar */}
        <header className="sticky top-0 z-10 bg-slate-950/80 backdrop-blur-sm border-b border-slate-800 px-6 py-3 flex items-center gap-3">
          <Activity className="w-4 h-4 text-slate-500" />
          <span className="text-sm text-slate-400">
            {getPageTitle(location.pathname)}
          </span>
        </header>
        <div className="p-6">{children}</div>
      </main>
    </div>
  );
}

function MetricRow({
  label,
  value,
  pct,
  color,
}: {
  label: string;
  value: string;
  pct: number;
  color: string;
}) {
  return (
    <div>
      <div className="flex justify-between text-xs mb-0.5">
        <span className="text-slate-500">{label}</span>
        <span className="text-slate-300 tabular-nums">{value}</span>
      </div>
      <div className="h-1 bg-slate-800 rounded-full overflow-hidden">
        <div
          className={`h-full ${color} rounded-full transition-all duration-700`}
          style={{ width: `${Math.min(pct, 100)}%` }}
        />
      </div>
    </div>
  );
}

function getPageTitle(path: string): string {
  if (path === "/") return "Dashboard";
  if (path === "/datasets") return "Datasets";
  if (path === "/experiments/new") return "New Experiment";
  if (path.startsWith("/experiments/")) return "Experiment Detail";
  if (path === "/experiments") return "Experiments";
  return "PolicyLab";
}
