import { useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useNavigate, useSearchParams } from "react-router-dom";
import { ArrowRight, FlaskConical, Info } from "lucide-react";
import { api, type ExperimentCreate } from "../api/client";

const ANALYSIS_OPTIONS = [
  {
    value: "housing_affordability",
    label: "Housing Affordability Analysis",
    description: "Compute cost burden rates by income quintile, state, and year using ACS data.",
    datasets: ["acs-housing", "hud-fmr"],
  },
  {
    value: "labor_trends",
    label: "Labor Market Trends",
    description: "Analyze unemployment rates by sector using BLS Current Population Survey.",
    datasets: ["bls-unemployment"],
  },
  {
    value: "census_demographics",
    label: "Census Demographic Profile",
    description: "Population distribution, age structure, and demographic composition.",
    datasets: ["census-demographics"],
  },
];

export default function NewExperiment() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const qc = useQueryClient();

  const { data: datasets = [] } = useQuery({
    queryKey: ["datasets"],
    queryFn: api.datasets.list,
  });

  const [form, setForm] = useState<ExperimentCreate>({
    name: "",
    description: "",
    dataset_id: searchParams.get("dataset") ?? "",
    analysis_type: "",
    parameters: {},
  });

  const [errors, setErrors] = useState<Partial<Record<keyof ExperimentCreate, string>>>({});

  // Auto-select analysis type based on dataset
  useEffect(() => {
    if (!form.dataset_id) return;
    const ds = datasets.find((d) => d.id === form.dataset_id);
    if (!ds) return;
    const match = ANALYSIS_OPTIONS.find((a) => a.datasets.includes(ds.slug));
    if (match) setForm((f) => ({ ...f, analysis_type: match.value, parameters: defaultParams(match.value) }));
  }, [form.dataset_id, datasets]);

  const mutation = useMutation({
    mutationFn: api.experiments.create,
    onSuccess: (exp) => {
      qc.invalidateQueries({ queryKey: ["experiments"] });
      navigate(`/experiments/${exp.id}`);
    },
  });

  function validate(): boolean {
    const e: typeof errors = {};
    if (!form.name.trim()) e.name = "Name is required";
    if (!form.dataset_id) e.dataset_id = "Select a dataset";
    if (!form.analysis_type) e.analysis_type = "Select an analysis type";
    setErrors(e);
    return Object.keys(e).length === 0;
  }

  function handleSubmit(ev: React.FormEvent) {
    ev.preventDefault();
    if (!validate()) return;
    mutation.mutate(form);
  }

  const selectedAnalysis = ANALYSIS_OPTIONS.find((a) => a.value === form.analysis_type);

  return (
    <div className="max-w-2xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">New Experiment</h1>
        <p className="text-sm text-slate-400 mt-1">
          Configure and submit a distributed analysis job
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-5">
        {/* Name */}
        <div>
          <label className="label">Experiment Name</label>
          <input
            className="input"
            placeholder="e.g. Housing burden in Sun Belt states 2015–2023"
            value={form.name}
            onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
          />
          {errors.name && <p className="text-red-400 text-xs mt-1">{errors.name}</p>}
        </div>

        {/* Description */}
        <div>
          <label className="label">Description (optional)</label>
          <textarea
            className="input resize-none"
            rows={2}
            placeholder="Brief hypothesis or goal for this run..."
            value={form.description}
            onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))}
          />
        </div>

        {/* Dataset */}
        <div>
          <label className="label">Dataset</label>
          <select
            className="select"
            value={form.dataset_id}
            onChange={(e) => setForm((f) => ({ ...f, dataset_id: e.target.value }))}
          >
            <option value="">— Select a dataset —</option>
            {datasets.map((ds) => (
              <option key={ds.id} value={ds.id}>
                {ds.name} ({ds.source})
              </option>
            ))}
          </select>
          {errors.dataset_id && <p className="text-red-400 text-xs mt-1">{errors.dataset_id}</p>}
        </div>

        {/* Analysis type */}
        <div>
          <label className="label">Analysis Type</label>
          <div className="space-y-2">
            {ANALYSIS_OPTIONS.map((opt) => (
              <label
                key={opt.value}
                className={`flex items-start gap-3 p-3.5 rounded-lg border cursor-pointer transition-colors ${
                  form.analysis_type === opt.value
                    ? "border-brand-500 bg-brand-500/10"
                    : "border-slate-700 bg-slate-800/40 hover:border-slate-600"
                }`}
              >
                <input
                  type="radio"
                  name="analysis_type"
                  value={opt.value}
                  checked={form.analysis_type === opt.value}
                  onChange={() =>
                    setForm((f) => ({
                      ...f,
                      analysis_type: opt.value,
                      parameters: defaultParams(opt.value),
                    }))
                  }
                  className="mt-0.5 accent-brand-500"
                />
                <div>
                  <p className="text-sm font-medium text-slate-200">{opt.label}</p>
                  <p className="text-xs text-slate-500 mt-0.5">{opt.description}</p>
                </div>
              </label>
            ))}
          </div>
          {errors.analysis_type && (
            <p className="text-red-400 text-xs mt-1">{errors.analysis_type}</p>
          )}
        </div>

        {/* Dynamic parameter preview */}
        {selectedAnalysis && (
          <div className="card p-4 border-brand-500/20 bg-brand-500/5">
            <div className="flex items-center gap-2 mb-2">
              <Info className="w-3.5 h-3.5 text-brand-400" />
              <span className="text-xs font-medium text-brand-400">Default Parameters</span>
            </div>
            <pre className="text-xs text-slate-400 font-mono overflow-auto max-h-32">
              {JSON.stringify(form.parameters, null, 2)}
            </pre>
            <p className="text-xs text-slate-600 mt-2">
              Custom parameter overrides — full UI coming soon. These defaults produce a complete run.
            </p>
          </div>
        )}

        {/* Reproducibility note */}
        <div className="flex items-start gap-2 text-xs text-slate-500">
          <FlaskConical className="w-3.5 h-3.5 mt-0.5 text-emerald-400 shrink-0" />
          <p>
            Every run records git commit, environment hash, dataset version, and parameter
            fingerprint — ensuring byte-identical reproducibility.
          </p>
        </div>

        {mutation.isError && (
          <div className="bg-red-500/10 border border-red-500/20 rounded-lg px-4 py-3 text-sm text-red-400">
            {String(mutation.error)}
          </div>
        )}

        <button
          type="submit"
          className="btn-primary flex items-center gap-2 w-full justify-center py-2.5"
          disabled={mutation.isPending}
        >
          {mutation.isPending ? (
            "Submitting to Ray..."
          ) : (
            <>
              Launch Experiment <ArrowRight className="w-4 h-4" />
            </>
          )}
        </button>
      </form>
    </div>
  );
}

function defaultParams(analysisType: string): Record<string, unknown> {
  switch (analysisType) {
    case "housing_affordability":
      return {
        states: ["CA", "NY", "TX", "FL", "IL", "OH", "PA", "WA", "CO", "GA"],
        year_start: 2015,
        year_end: 2023,
      };
    case "labor_trends":
      return {
        sectors: ["Manufacturing", "Services", "Technology", "Healthcare"],
        year_start: 2010,
        year_end: 2024,
        measure: "u3",
      };
    case "census_demographics":
      return {
        states: ["CA", "TX", "FL", "NY", "PA", "IL", "OH", "GA", "NC", "MI"],
        breakdown: "age",
      };
    default:
      return {};
  }
}
