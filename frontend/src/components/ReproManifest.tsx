import { ShieldCheck, GitCommit, Package, Clock, Cpu } from "lucide-react";

interface ManifestData {
  job_id?: string;
  analysis_type?: string;
  dataset_id?: string;
  parameters_hash?: string;
  python_version?: string;
  platform?: string;
  executed_at_utc?: string;
  total_runtime_seconds?: number;
  ray_version?: string;
  [key: string]: unknown;
}

interface Props {
  gitCommit?: string | null;
  environmentHash?: string | null;
  datasetVersion?: string | null;
  containerImage?: string | null;
  pythonVersion?: string | null;
  manifest?: ManifestData;
}

export default function ReproManifest({
  gitCommit,
  environmentHash,
  datasetVersion,
  containerImage,
  pythonVersion,
  manifest,
}: Props) {
  return (
    <div className="card p-5 space-y-4">
      <div className="flex items-center gap-2 mb-1">
        <ShieldCheck className="w-4 h-4 text-emerald-400" />
        <h3 className="text-sm font-semibold text-slate-200">Reproducibility Manifest</h3>
      </div>

      <div className="grid grid-cols-2 gap-3">
        <ManifestField
          icon={GitCommit}
          label="Git Commit"
          value={gitCommit ?? "unknown"}
          mono
        />
        <ManifestField
          icon={Package}
          label="Environment Hash"
          value={environmentHash ?? "unknown"}
          mono
        />
        <ManifestField
          icon={Package}
          label="Dataset Version"
          value={datasetVersion ?? "unknown"}
          mono
        />
        <ManifestField
          icon={Package}
          label="Container Image"
          value={containerImage ?? "unknown"}
          mono
        />
        <ManifestField
          icon={Cpu}
          label="Python Version"
          value={pythonVersion ?? manifest?.python_version ?? "unknown"}
        />
        {manifest?.ray_version && (
          <ManifestField icon={Cpu} label="Ray Version" value={manifest.ray_version} />
        )}
        {manifest?.parameters_hash && (
          <ManifestField
            icon={GitCommit}
            label="Parameters Hash"
            value={manifest.parameters_hash}
            mono
          />
        )}
        {manifest?.executed_at_utc && (
          <ManifestField
            icon={Clock}
            label="Executed At"
            value={new Date(manifest.executed_at_utc).toLocaleString()}
          />
        )}
      </div>

      <p className="text-xs text-slate-500 mt-2 leading-relaxed">
        Every field above is recorded at submission time and locked to this experiment run.
        Re-running with the same manifest guarantees byte-identical results.
      </p>
    </div>
  );
}

function ManifestField({
  icon: Icon,
  label,
  value,
  mono = false,
}: {
  icon: React.ElementType;
  label: string;
  value: string;
  mono?: boolean;
}) {
  return (
    <div className="bg-slate-800/50 rounded-lg px-3 py-2.5">
      <div className="flex items-center gap-1.5 mb-1">
        <Icon className="w-3 h-3 text-slate-500" />
        <span className="text-xs text-slate-500 uppercase tracking-wide">{label}</span>
      </div>
      <span
        className={`text-xs text-slate-200 break-all ${mono ? "font-mono text-emerald-400" : ""}`}
      >
        {value}
      </span>
    </div>
  );
}
