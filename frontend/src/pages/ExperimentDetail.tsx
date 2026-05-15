import { useParams, Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  LineChart, Line, Legend, PieChart, Pie, Cell,
} from "recharts";
import {
  ArrowLeft, Clock, Cpu, MemoryStick, Timer, Terminal, ShieldCheck,
} from "lucide-react";
import { formatDistanceToNow, format } from "date-fns";
import { api, type Artifact } from "../api/client";
import JobStatusBadge from "../components/JobStatusBadge";
import MetricsChart from "../components/MetricsChart";
import ReproManifest from "../components/ReproManifest";

const ANALYSIS_LABELS: Record<string, string> = {
  housing_affordability: "Housing Affordability Analysis",
  labor_trends: "Labor Market Trends",
  census_demographics: "Census Demographic Profile",
};

export default function ExperimentDetail() {
  const { id } = useParams<{ id: string }>();

  const { data: exp } = useQuery({
    queryKey: ["experiment", id],
    queryFn: () => api.experiments.get(id!),
    refetchInterval: (q) =>
      q.state.data?.status === "running" ? 2_000 : false,
  });

  const job = exp?.jobs[0];
  const resultsArtifact = exp?.artifacts.find((a) => a.artifact_type === "chart_data");
  const manifestArtifact = exp?.artifacts.find((a) => a.artifact_type === "manifest");

  const { data: metrics = [] } = useQuery({
    queryKey: ["job-metrics", job?.id],
    queryFn: () => api.jobs.metrics(job!.id),
    enabled: !!job?.id && (job.status === "running" || job.status === "completed"),
    refetchInterval: job?.status === "running" ? 3_000 : false,
  });

  const { data: logs = "" } = useQuery({
    queryKey: ["job-logs", job?.id],
    queryFn: () => api.jobs.logs(job!.id),
    enabled: !!job?.id,
    refetchInterval: job?.status === "running" ? 2_000 : false,
  });

  if (!exp) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-slate-500 text-sm animate-pulse">Loading experiment…</div>
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-5xl">
      {/* Header */}
      <div>
        <Link
          to="/experiments"
          className="flex items-center gap-1.5 text-xs text-slate-500 hover:text-slate-300 mb-3 transition-colors"
        >
          <ArrowLeft className="w-3.5 h-3.5" /> Back to experiments
        </Link>
        <div className="flex items-start justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-white">{exp.name}</h1>
            {exp.description && (
              <p className="text-sm text-slate-400 mt-1">{exp.description}</p>
            )}
            <p className="text-xs text-slate-500 mt-1">
              {ANALYSIS_LABELS[exp.analysis_type] ?? exp.analysis_type} ·{" "}
              {formatDistanceToNow(new Date(exp.created_at), { addSuffix: true })}
            </p>
          </div>
          <JobStatusBadge status={exp.status} />
        </div>
      </div>

      {/* Job stats row */}
      {job && (
        <div className="grid grid-cols-4 gap-3">
          <StatChip icon={Timer} label="Runtime" value={job.total_runtime_seconds != null ? `${job.total_runtime_seconds.toFixed(2)}s` : "running…"} />
          <StatChip icon={Cpu} label="Peak CPU" value={job.peak_cpu_percent != null ? `${job.peak_cpu_percent.toFixed(1)}%` : "—"} />
          <StatChip icon={MemoryStick} label="Peak RAM" value={job.peak_memory_mb != null ? `${job.peak_memory_mb.toFixed(0)} MB` : "—"} />
          <StatChip icon={Clock} label="Worker" value={job.worker_id ?? "ray-local"} />
        </div>
      )}

      {/* CPU/Memory chart */}
      <div className="card p-5">
        <h2 className="text-sm font-semibold text-slate-200 mb-4">
          Compute Metrics — CPU & Memory Over Runtime
        </h2>
        <MetricsChart metrics={metrics} />
      </div>

      {/* Results */}
      {resultsArtifact && (
        <ResultsSection artifact={resultsArtifact} analysisType={exp.analysis_type} />
      )}

      {/* Logs */}
      <div className="card p-5">
        <div className="flex items-center gap-2 mb-3">
          <Terminal className="w-4 h-4 text-slate-400" />
          <h2 className="text-sm font-semibold text-slate-200">Job Logs</h2>
          {job?.status === "running" && (
            <span className="badge bg-blue-500/15 text-blue-400 border border-blue-500/20 ml-auto">
              <span className="animate-pulse">live</span>
            </span>
          )}
        </div>
        <div className="log-terminal">
          {logs || <span className="text-slate-600">No logs yet…</span>}
        </div>
        {job?.error && (
          <div className="mt-3 bg-red-500/10 border border-red-500/20 rounded-lg p-3">
            <p className="text-xs text-red-400 font-mono whitespace-pre-wrap">{job.error}</p>
          </div>
        )}
      </div>

      {/* Reproducibility */}
      <ReproManifest
        gitCommit={exp.git_commit}
        environmentHash={exp.environment_hash}
        datasetVersion={exp.dataset_version}
        containerImage={exp.container_image}
        pythonVersion={exp.python_version}
        manifest={manifestArtifact?.content as Record<string, unknown> | undefined}
      />

      {/* Raw parameters */}
      <div className="card p-5">
        <div className="flex items-center gap-2 mb-3">
          <ShieldCheck className="w-4 h-4 text-slate-400" />
          <h2 className="text-sm font-semibold text-slate-200">Experiment Parameters</h2>
        </div>
        <pre className="text-xs text-slate-400 font-mono leading-relaxed bg-slate-950 rounded-lg p-3 overflow-auto">
          {JSON.stringify(exp.parameters, null, 2)}
        </pre>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Result visualisations — dispatch on chart_type
// ---------------------------------------------------------------------------

function ResultsSection({ artifact, analysisType }: { artifact: Artifact; analysisType: string }) {
  const data = artifact.content as Record<string, unknown>;

  return (
    <div className="space-y-4">
      {/* Summary card */}
      {data.summary != null && <SummaryCard summary={data.summary as Record<string, unknown>} />}

      {analysisType === "housing_affordability" && (
        <HousingCharts data={data} />
      )}
      {analysisType === "labor_trends" && (
        <LaborCharts data={data} />
      )}
      {analysisType === "census_demographics" && (
        <CensusCharts data={data} />
      )}
    </div>
  );
}

function SummaryCard({ summary }: { summary: Record<string, unknown> }) {
  const { key_finding, ...rest } = summary;
  return (
    <div className="card p-5">
      <h2 className="text-sm font-semibold text-slate-200 mb-3">Key Findings</h2>
      {key_finding != null && (
        <p className="text-sm text-slate-300 leading-relaxed mb-4 border-l-2 border-brand-500 pl-3">
          {String(key_finding)}
        </p>
      )}
      <div className="grid grid-cols-3 gap-3">
        {Object.entries(rest).map(([k, v]) => (
          <div key={k} className="bg-slate-800/50 rounded-lg px-3 py-2">
            <p className="text-xs text-slate-500 mb-0.5 capitalize">
              {k.replace(/_/g, " ")}
            </p>
            <p className="text-sm font-medium text-slate-200 truncate">{String(v)}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

const PIE_COLORS = ["#6366f1", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6", "#06b6d4"];

function HousingCharts({ data }: { data: Record<string, unknown> }) {
  const byState = (data.burden_by_state ?? []) as Array<Record<string, unknown>>;
  const trend = (data.trend_by_quintile ?? []) as Array<Record<string, unknown>>;
  const severity = (data.severity_distribution ?? []) as Array<Record<string, unknown>>;

  // Pivot trend for multi-line chart
  const years = [...new Set(trend.map((r) => r.year as number))].sort();
  const quintiles = [...new Set(trend.map((r) => r.quintile as string))].sort();
  const trendPivot = years.map((y) => {
    const row: Record<string, unknown> = { year: y };
    quintiles.forEach((q) => {
      const match = trend.find((r) => r.year === y && r.quintile === q);
      if (match) row[q] = +(Number(match.burden_rate) * 100).toFixed(1);
    });
    return row;
  });

  const Q_COLORS: Record<string, string> = {
    Q1: "#ef4444", Q2: "#f59e0b", Q3: "#6366f1", Q4: "#10b981", Q5: "#06b6d4",
  };

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-4">
        <div className="card p-5">
          <h3 className="text-sm font-semibold text-slate-200 mb-1">
            Cost Burden Rate by State
          </h3>
          <p className="text-xs text-slate-500 mb-4">% of renters paying &gt;30% of income on housing</p>
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={byState.slice(0, 15)} layout="vertical" margin={{ left: 8, right: 24 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" horizontal={false} />
              <XAxis type="number" domain={[0, 0.7]} tickFormatter={(v) => `${(v * 100).toFixed(0)}%`} tick={{ fill: "#94a3b8", fontSize: 10 }} />
              <YAxis type="category" dataKey="state" tick={{ fill: "#94a3b8", fontSize: 11 }} width={28} />
              <Tooltip formatter={(v: number) => [`${(v * 100).toFixed(1)}%`, "Cost Burden"]} contentStyle={{ background: "#1e293b", border: "1px solid #334155" }} />
              <Bar dataKey="cost_burden_rate" fill="#6366f1" radius={[0, 3, 3, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="card p-5">
          <h3 className="text-sm font-semibold text-slate-200 mb-1">
            Burden by Income Quintile Over Time
          </h3>
          <p className="text-xs text-slate-500 mb-4">Q1 = lowest income, Q5 = highest</p>
          <ResponsiveContainer width="100%" height={240}>
            <LineChart data={trendPivot}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis dataKey="year" tick={{ fill: "#94a3b8", fontSize: 10 }} />
              <YAxis tickFormatter={(v) => `${v}%`} tick={{ fill: "#94a3b8", fontSize: 10 }} />
              <Tooltip formatter={(v: number) => [`${v}%`]} contentStyle={{ background: "#1e293b", border: "1px solid #334155" }} />
              <Legend />
              {quintiles.map((q) => (
                <Line key={q} type="monotone" dataKey={q} stroke={Q_COLORS[q] ?? "#6366f1"} strokeWidth={2} dot={false} />
              ))}
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="card p-5 flex items-center gap-8">
        <div>
          <h3 className="text-sm font-semibold text-slate-200 mb-1">Severity Distribution</h3>
          <p className="text-xs text-slate-500 mb-4">National average across selected states</p>
          <ResponsiveContainer width={200} height={160}>
            <PieChart>
              <Pie data={severity} dataKey="value" nameKey="category" cx="50%" cy="50%" outerRadius={70} paddingAngle={2}>
                {severity.map((_, i) => <Cell key={i} fill={PIE_COLORS[i]} />)}
              </Pie>
              <Tooltip formatter={(v: number) => `${(v * 100).toFixed(1)}%`} contentStyle={{ background: "#1e293b", border: "1px solid #334155" }} />
            </PieChart>
          </ResponsiveContainer>
        </div>
        <div className="space-y-2">
          {severity.map((s, i) => (
            <div key={i} className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-sm" style={{ background: PIE_COLORS[i] }} />
              <span className="text-xs text-slate-300">{String(s.category)}</span>
              <span className="text-xs text-slate-500 ml-auto tabular-nums">
                {(Number(s.value) * 100).toFixed(1)}%
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function LaborCharts({ data }: { data: Record<string, unknown> }) {
  const trend = (data.trend_by_year ?? []) as Array<Record<string, unknown>>;
  const bySector = (data.current_by_sector ?? []) as Array<Record<string, unknown>>;
  const edu = (data.education_breakdown ?? []) as Array<Record<string, unknown>>;

  const years = [...new Set(trend.map((r) => r.year as number))].sort();
  const sectors = [...new Set(trend.map((r) => r.sector as string))];
  const trendPivot = years.map((y) => {
    const row: Record<string, unknown> = { year: y };
    sectors.forEach((s) => {
      const match = trend.find((r) => r.year === y && r.sector === s);
      if (match) row[s] = match.u3_rate;
    });
    return row;
  });

  const SECTOR_COLORS = ["#6366f1", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6", "#06b6d4", "#f97316", "#84cc16"];

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-4">
        <div className="card p-5">
          <h3 className="text-sm font-semibold text-slate-200 mb-1">Unemployment by Sector (U-3)</h3>
          <p className="text-xs text-slate-500 mb-4">Current year snapshot — sorted ascending</p>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={bySector} margin={{ left: -8, right: 8 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis dataKey="sector" tick={{ fill: "#94a3b8", fontSize: 9 }} angle={-20} textAnchor="end" height={40} />
              <YAxis tickFormatter={(v) => `${v}%`} tick={{ fill: "#94a3b8", fontSize: 10 }} />
              <Tooltip formatter={(v: number) => [`${v}%`, "U-3 Rate"]} contentStyle={{ background: "#1e293b", border: "1px solid #334155" }} />
              <Bar dataKey="current_rate" fill="#6366f1" radius={[3, 3, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="card p-5">
          <h3 className="text-sm font-semibold text-slate-200 mb-1">Unemployment Trend by Sector</h3>
          <p className="text-xs text-slate-500 mb-4">Official U-3 rate over selected years</p>
          <ResponsiveContainer width="100%" height={220}>
            <LineChart data={trendPivot}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis dataKey="year" tick={{ fill: "#94a3b8", fontSize: 10 }} />
              <YAxis tickFormatter={(v) => `${v}%`} tick={{ fill: "#94a3b8", fontSize: 10 }} />
              <Tooltip formatter={(v: number) => [`${v}%`]} contentStyle={{ background: "#1e293b", border: "1px solid #334155" }} />
              <Legend />
              {sectors.map((s, i) => (
                <Line key={s} type="monotone" dataKey={s} stroke={SECTOR_COLORS[i % SECTOR_COLORS.length]} strokeWidth={2} dot={false} />
              ))}
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="card p-5">
        <h3 className="text-sm font-semibold text-slate-200 mb-1">Unemployment by Education Level</h3>
        <p className="text-xs text-slate-500 mb-4">Education premium — higher education correlates with lower unemployment</p>
        <ResponsiveContainer width="100%" height={140}>
          <BarChart data={edu} margin={{ left: -8, right: 8 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
            <XAxis dataKey="education_level" tick={{ fill: "#94a3b8", fontSize: 10 }} />
            <YAxis tickFormatter={(v) => `${v}%`} tick={{ fill: "#94a3b8", fontSize: 10 }} />
            <Tooltip formatter={(v: number) => [`${v}%`, "U-3 Rate"]} contentStyle={{ background: "#1e293b", border: "1px solid #334155" }} />
            <Bar dataKey="u3_rate" radius={[3, 3, 0, 0]}>
              {edu.map((_, i) => <Cell key={i} fill={`hsl(${230 + i * 15}, 70%, ${40 + i * 8}%)`} />)}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

function CensusCharts({ data }: { data: Record<string, unknown> }) {
  const ageData = (data.age_distribution ?? []) as Array<Record<string, unknown>>;
  const raceData = (data.race_ethnicity ?? []) as Array<Record<string, unknown>>;
  const stateData = (data.population_by_state ?? []) as Array<Record<string, unknown>>;

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-4">
        <div className="card p-5">
          <h3 className="text-sm font-semibold text-slate-200 mb-1">Age Distribution</h3>
          <p className="text-xs text-slate-500 mb-4">Population pyramid (combined states)</p>
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={ageData} margin={{ left: -8, right: 4 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis dataKey="age_group" tick={{ fill: "#94a3b8", fontSize: 9 }} angle={-40} textAnchor="end" height={48} />
              <YAxis tickFormatter={(v) => `${(v / 1e6).toFixed(0)}M`} tick={{ fill: "#94a3b8", fontSize: 10 }} />
              <Tooltip formatter={(v: number) => [`${(v / 1e6).toFixed(1)}M`, "Population"]} contentStyle={{ background: "#1e293b", border: "1px solid #334155" }} />
              <Bar dataKey="population" fill="#6366f1" radius={[2, 2, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="card p-5">
          <h3 className="text-sm font-semibold text-slate-200 mb-1">Race / Ethnicity</h3>
          <p className="text-xs text-slate-500 mb-4">National composition across selected states</p>
          <ResponsiveContainer width="100%" height={240}>
            <PieChart>
              <Pie data={raceData} dataKey="pct" nameKey="group" cx="50%" cy="50%" outerRadius={90} paddingAngle={2}>
                {raceData.map((_, i) => <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />)}
              </Pie>
              <Tooltip formatter={(v: number) => `${(v * 100).toFixed(1)}%`} contentStyle={{ background: "#1e293b", border: "1px solid #334155" }} />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="card p-5">
        <h3 className="text-sm font-semibold text-slate-200 mb-1">Median Age by State</h3>
        <p className="text-xs text-slate-500 mb-4">State-level median age from 2020 Census</p>
        <ResponsiveContainer width="100%" height={160}>
          <BarChart data={stateData.slice(0, 15)} margin={{ left: -8, right: 4 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
            <XAxis dataKey="state" tick={{ fill: "#94a3b8", fontSize: 11 }} />
            <YAxis domain={[25, 50]} tickFormatter={(v) => `${v}`} tick={{ fill: "#94a3b8", fontSize: 10 }} />
            <Tooltip formatter={(v: number) => [`${v} years`, "Median Age"]} contentStyle={{ background: "#1e293b", border: "1px solid #334155" }} />
            <Bar dataKey="median_age" fill="#10b981" radius={[2, 2, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

function StatChip({
  icon: Icon, label, value,
}: { icon: React.ElementType; label: string; value: string }) {
  return (
    <div className="card px-4 py-3 flex items-start gap-2.5">
      <Icon className="w-3.5 h-3.5 text-slate-500 mt-0.5 shrink-0" />
      <div>
        <p className="text-xs text-slate-500">{label}</p>
        <p className="text-sm font-semibold text-slate-200 tabular-nums mt-0.5">{value}</p>
      </div>
    </div>
  );
}
