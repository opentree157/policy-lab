import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from "recharts";
import { FlaskConical, Database, CheckCircle2, Cpu, MemoryStick, Plus } from "lucide-react";
import { api } from "../api/client";
import JobStatusBadge from "../components/JobStatusBadge";
import { formatDistanceToNow } from "date-fns";

const ANALYSIS_LABELS: Record<string, string> = {
  housing_affordability: "Housing Affordability",
  labor_trends: "Labor Market Trends",
  census_demographics: "Census Demographics",
};

export default function Dashboard() {
  const { data: experiments = [] } = useQuery({
    queryKey: ["experiments"],
    queryFn: api.experiments.list,
    refetchInterval: 5_000,
  });

  const { data: datasets = [] } = useQuery({
    queryKey: ["datasets"],
    queryFn: api.datasets.list,
  });

  const { data: sys } = useQuery({
    queryKey: ["system-metrics"],
    queryFn: api.metrics.system,
    refetchInterval: 5_000,
  });

  const running = experiments.filter((e) => e.status === "running").length;
  const completed = experiments.filter((e) => e.status === "completed").length;
  const recent = experiments.slice(0, 8);

  // Build a simple sparkline from system metric snapshots
  const cpuHistory = useCpuHistory(sys?.cpu_percent ?? 0);

  return (
    <div className="space-y-6 max-w-6xl">
      <div>
        <h1 className="text-2xl font-bold text-white">Dashboard</h1>
        <p className="text-sm text-slate-400 mt-1">
          Reproducible policy research — powered by Ray distributed compute
        </p>
      </div>

      {/* Stats row */}
      <div className="grid grid-cols-4 gap-4">
        <StatCard
          icon={FlaskConical}
          label="Active Jobs"
          value={running}
          color="text-blue-400"
          bg="bg-blue-500/10"
        />
        <StatCard
          icon={CheckCircle2}
          label="Completed"
          value={completed}
          color="text-emerald-400"
          bg="bg-emerald-500/10"
        />
        <StatCard
          icon={Database}
          label="Datasets"
          value={datasets.length}
          color="text-brand-400"
          bg="bg-brand-500/10"
        />
        <StatCard
          icon={FlaskConical}
          label="Total Runs"
          value={experiments.length}
          color="text-slate-300"
          bg="bg-slate-800"
        />
      </div>

      <div className="grid grid-cols-3 gap-4">
        {/* CPU sparkline */}
        <div className="card p-4 col-span-2">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <Cpu className="w-4 h-4 text-brand-400" />
              <span className="text-sm font-medium text-slate-200">Host CPU Utilisation</span>
            </div>
            <span className="text-xs text-slate-500 tabular-nums">
              {sys ? `${sys.cpu_count} cores · ${sys.cpu_percent.toFixed(1)}%` : "loading..."}
            </span>
          </div>
          <ResponsiveContainer width="100%" height={100}>
            <AreaChart data={cpuHistory}>
              <defs>
                <linearGradient id="cpuGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#6366f1" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis dataKey="t" hide />
              <YAxis domain={[0, 100]} hide />
              <Tooltip
                content={({ payload }) =>
                  payload?.[0] ? (
                    <div className="bg-slate-800 border border-slate-700 rounded px-2 py-1 text-xs">
                      {(payload[0].value as number).toFixed(1)}%
                    </div>
                  ) : null
                }
              />
              <Area
                type="monotone"
                dataKey="cpu"
                stroke="#6366f1"
                strokeWidth={2}
                fill="url(#cpuGrad)"
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Memory */}
        <div className="card p-4">
          <div className="flex items-center gap-2 mb-3">
            <MemoryStick className="w-4 h-4 text-emerald-400" />
            <span className="text-sm font-medium text-slate-200">Memory</span>
          </div>
          {sys ? (
            <div className="space-y-3">
              <div className="text-3xl font-bold text-white tabular-nums">
                {sys.memory_percent.toFixed(0)}
                <span className="text-lg text-slate-400 font-normal">%</span>
              </div>
              <div className="h-2 bg-slate-800 rounded-full overflow-hidden">
                <div
                  className="h-full bg-emerald-500 rounded-full transition-all duration-700"
                  style={{ width: `${sys.memory_percent}%` }}
                />
              </div>
              <p className="text-xs text-slate-500 tabular-nums">
                {(sys.memory_used_mb / 1024).toFixed(1)} GB /{" "}
                {(sys.memory_total_mb / 1024).toFixed(1)} GB
              </p>
            </div>
          ) : (
            <div className="text-slate-500 text-sm">loading...</div>
          )}
        </div>
      </div>

      {/* Recent experiments */}
      <div className="card">
        <div className="px-5 py-4 border-b border-slate-800 flex items-center justify-between">
          <h2 className="text-sm font-semibold text-slate-200">Recent Experiments</h2>
          <Link to="/experiments/new" className="btn-primary flex items-center gap-1.5 py-1.5">
            <Plus className="w-3.5 h-3.5" />
            New
          </Link>
        </div>
        {recent.length === 0 ? (
          <div className="px-5 py-10 text-center">
            <p className="text-slate-500 text-sm">No experiments yet.</p>
            <Link to="/experiments/new" className="text-brand-400 text-sm hover:underline mt-1 inline-block">
              Run your first analysis →
            </Link>
          </div>
        ) : (
          <div className="divide-y divide-slate-800">
            {recent.map((exp) => (
              <Link
                key={exp.id}
                to={`/experiments/${exp.id}`}
                className="flex items-center px-5 py-3.5 hover:bg-slate-800/40 transition-colors"
              >
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-slate-200 truncate">{exp.name}</p>
                  <p className="text-xs text-slate-500 mt-0.5">
                    {ANALYSIS_LABELS[exp.analysis_type] ?? exp.analysis_type}
                    {exp.created_at && (
                      <> · {formatDistanceToNow(new Date(exp.created_at), { addSuffix: true })}</>
                    )}
                  </p>
                </div>
                <div className="flex items-center gap-3 ml-4 shrink-0">
                  {exp.jobs[0]?.total_runtime_seconds && (
                    <span className="text-xs text-slate-500 tabular-nums">
                      {exp.jobs[0].total_runtime_seconds.toFixed(1)}s
                    </span>
                  )}
                  <JobStatusBadge status={exp.status} />
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function StatCard({
  icon: Icon,
  label,
  value,
  color,
  bg,
}: {
  icon: React.ElementType;
  label: string;
  value: number;
  color: string;
  bg: string;
}) {
  return (
    <div className="card px-4 py-4">
      <div className={`w-8 h-8 ${bg} rounded-lg flex items-center justify-center mb-3`}>
        <Icon className={`w-4 h-4 ${color}`} />
      </div>
      <p className="text-2xl font-bold text-white tabular-nums">{value}</p>
      <p className="text-xs text-slate-500 mt-0.5">{label}</p>
    </div>
  );
}

// Rolling 30-point CPU history for sparkline
const _history: { t: number; cpu: number }[] = Array.from({ length: 30 }, (_, i) => ({
  t: i,
  cpu: 0,
}));
let _tick = 30;

function useCpuHistory(current: number) {
  if (current > 0) {
    _history.push({ t: _tick++, cpu: current });
    if (_history.length > 30) _history.shift();
  }
  return [..._history];
}
