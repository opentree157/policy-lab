import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { Plus, ArrowRight, Clock } from "lucide-react";
import { formatDistanceToNow } from "date-fns";
import { api } from "../api/client";
import JobStatusBadge from "../components/JobStatusBadge";

const ANALYSIS_LABELS: Record<string, string> = {
  housing_affordability: "Housing Affordability",
  labor_trends: "Labor Market Trends",
  census_demographics: "Census Demographics",
};

export default function ExperimentsList() {
  const { data: experiments = [], isLoading } = useQuery({
    queryKey: ["experiments"],
    queryFn: api.experiments.list,
    refetchInterval: 5_000,
  });

  const running = experiments.filter((e) => e.status === "running");
  const rest = experiments.filter((e) => e.status !== "running");

  return (
    <div className="space-y-6 max-w-5xl">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Experiments</h1>
          <p className="text-sm text-slate-400 mt-1">
            {experiments.length} total · {running.length} running
          </p>
        </div>
        <Link to="/experiments/new" className="btn-primary flex items-center gap-1.5">
          <Plus className="w-4 h-4" />
          New Experiment
        </Link>
      </div>

      {isLoading && <div className="text-slate-500 text-sm animate-pulse">Loading...</div>}

      {!isLoading && experiments.length === 0 && (
        <div className="card px-6 py-16 text-center">
          <p className="text-slate-400 text-sm mb-3">No experiments yet.</p>
          <Link to="/experiments/new" className="btn-primary inline-flex items-center gap-2">
            <Plus className="w-4 h-4" />
            Run your first analysis
          </Link>
        </div>
      )}

      {running.length > 0 && (
        <Section title="Running" count={running.length}>
          <ExperimentTable rows={running} />
        </Section>
      )}

      {rest.length > 0 && (
        <Section title="History" count={rest.length}>
          <ExperimentTable rows={rest} />
        </Section>
      )}
    </div>
  );
}

function Section({ title, count, children }: { title: string; count: number; children: React.ReactNode }) {
  return (
    <div>
      <h2 className="text-xs text-slate-500 uppercase tracking-widest font-medium mb-3">
        {title} <span className="text-slate-600">({count})</span>
      </h2>
      {children}
    </div>
  );
}

function ExperimentTable({ rows }: { rows: ReturnType<typeof api.experiments.list> extends Promise<infer T> ? T : never }) {
  return (
    <div className="card divide-y divide-slate-800">
      {rows.map((exp) => {
        const job = exp.jobs[0];
        return (
          <Link
            key={exp.id}
            to={`/experiments/${exp.id}`}
            className="flex items-center gap-4 px-5 py-3.5 hover:bg-slate-800/40 transition-colors group"
          >
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-slate-200 truncate group-hover:text-white">
                {exp.name}
              </p>
              <p className="text-xs text-slate-500 mt-0.5 truncate">
                {ANALYSIS_LABELS[exp.analysis_type] ?? exp.analysis_type}
                {exp.description && ` · ${exp.description}`}
              </p>
            </div>

            <div className="flex items-center gap-4 shrink-0 text-xs text-slate-500">
              {job?.total_runtime_seconds != null && (
                <span className="tabular-nums">{job.total_runtime_seconds.toFixed(1)}s</span>
              )}
              {job?.peak_cpu_percent != null && (
                <span className="tabular-nums hidden sm:block">
                  CPU {job.peak_cpu_percent.toFixed(0)}% peak
                </span>
              )}
              <span className="flex items-center gap-1">
                <Clock className="w-3 h-3" />
                {formatDistanceToNow(new Date(exp.created_at), { addSuffix: true })}
              </span>
              <JobStatusBadge status={exp.status} />
              <ArrowRight className="w-3.5 h-3.5 text-slate-600 group-hover:text-slate-400 transition-colors" />
            </div>
          </Link>
        );
      })}
    </div>
  );
}
