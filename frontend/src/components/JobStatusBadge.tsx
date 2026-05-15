import { Loader2, CheckCircle2, XCircle, Clock } from "lucide-react";
import clsx from "clsx";

type Status = "pending" | "running" | "completed" | "failed";

const CONFIG: Record<Status, { label: string; className: string; icon: React.ElementType }> = {
  pending: { label: "Pending", className: "bg-amber-500/15 text-amber-400 border border-amber-500/20", icon: Clock },
  running: { label: "Running", className: "bg-blue-500/15 text-blue-400 border border-blue-500/20", icon: Loader2 },
  completed: { label: "Completed", className: "bg-emerald-500/15 text-emerald-400 border border-emerald-500/20", icon: CheckCircle2 },
  failed: { label: "Failed", className: "bg-red-500/15 text-red-400 border border-red-500/20", icon: XCircle },
};

export default function JobStatusBadge({ status }: { status: string }) {
  const cfg = CONFIG[status as Status] ?? CONFIG.pending;
  const Icon = cfg.icon;
  return (
    <span className={clsx("badge", cfg.className)}>
      <Icon className={clsx("w-3 h-3", status === "running" && "animate-spin")} />
      {cfg.label}
    </span>
  );
}
