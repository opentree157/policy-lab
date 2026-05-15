import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { Database, ArrowRight, Tag, Calendar, MapPin, BarChart3 } from "lucide-react";
import { api } from "../api/client";

const CATEGORY_COLORS: Record<string, string> = {
  housing: "bg-blue-500/15 text-blue-400",
  labor: "bg-amber-500/15 text-amber-400",
  demographics: "bg-purple-500/15 text-purple-400",
  healthcare: "bg-rose-500/15 text-rose-400",
  elections: "bg-red-500/15 text-red-400",
  climate: "bg-emerald-500/15 text-emerald-400",
};

function fmt(bytes: number): string {
  if (bytes >= 1e9) return `${(bytes / 1e9).toFixed(1)} GB`;
  if (bytes >= 1e6) return `${(bytes / 1e6).toFixed(0)} MB`;
  return `${(bytes / 1e3).toFixed(0)} KB`;
}

function fmtRows(n: number): string {
  if (n >= 1e6) return `${(n / 1e6).toFixed(1)}M rows`;
  if (n >= 1e3) return `${(n / 1e3).toFixed(0)}K rows`;
  return `${n} rows`;
}

export default function Datasets() {
  const { data: datasets = [], isLoading } = useQuery({
    queryKey: ["datasets"],
    queryFn: api.datasets.list,
  });

  if (isLoading) return <LoadingSkeleton />;

  return (
    <div className="space-y-6 max-w-5xl">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Datasets</h1>
          <p className="text-sm text-slate-400 mt-1">
            {datasets.length} public policy datasets — Census, BLS, HUD, CMS & more
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4">
        {datasets.map((ds) => (
          <div key={ds.id} className="card p-5 hover:border-slate-700 transition-colors">
            <div className="flex items-start justify-between gap-4">
              <div className="flex items-start gap-3 flex-1 min-w-0">
                <div className="w-9 h-9 bg-slate-800 rounded-lg flex items-center justify-center shrink-0 mt-0.5">
                  <Database className="w-4.5 h-4.5 text-brand-400" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <h3 className="text-base font-semibold text-white">{ds.name}</h3>
                    <span
                      className={`badge text-xs ${CATEGORY_COLORS[ds.category] ?? "bg-slate-700 text-slate-400"}`}
                    >
                      {ds.category}
                    </span>
                  </div>
                  <p className="text-xs text-slate-500 mt-0.5">{ds.source}</p>
                  <p className="text-sm text-slate-400 mt-2 leading-relaxed line-clamp-2">
                    {ds.description}
                  </p>

                  <div className="flex flex-wrap gap-3 mt-3">
                    <Meta icon={BarChart3} value={fmtRows(ds.row_count)} />
                    <Meta icon={Database} value={fmt(ds.size_bytes)} />
                    <Meta
                      icon={Calendar}
                      value={
                        ds.years_available.length > 1
                          ? `${ds.years_available[0]}–${ds.years_available[ds.years_available.length - 1]}`
                          : String(ds.years_available[0])
                      }
                    />
                    <Meta icon={MapPin} value={ds.geographic_level} />
                  </div>

                  <div className="flex flex-wrap gap-1.5 mt-3">
                    {ds.tags.map((tag) => (
                      <span
                        key={tag}
                        className="inline-flex items-center gap-1 px-2 py-0.5 bg-slate-800 text-slate-400 rounded text-xs"
                      >
                        <Tag className="w-2.5 h-2.5" />
                        {tag}
                      </span>
                    ))}
                  </div>
                </div>
              </div>

              <Link
                to={`/experiments/new?dataset=${ds.id}`}
                className="btn-secondary flex items-center gap-1.5 shrink-0 whitespace-nowrap"
              >
                Use dataset
                <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function Meta({ icon: Icon, value }: { icon: React.ElementType; value: string }) {
  return (
    <span className="flex items-center gap-1 text-xs text-slate-500">
      <Icon className="w-3 h-3" />
      {value}
    </span>
  );
}

function LoadingSkeleton() {
  return (
    <div className="space-y-4 max-w-5xl">
      {[...Array(4)].map((_, i) => (
        <div key={i} className="card p-5 animate-pulse">
          <div className="flex gap-3">
            <div className="w-9 h-9 bg-slate-800 rounded-lg" />
            <div className="flex-1 space-y-2">
              <div className="h-4 bg-slate-800 rounded w-48" />
              <div className="h-3 bg-slate-800 rounded w-72" />
              <div className="h-3 bg-slate-800 rounded w-full" />
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
