import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  TooltipProps,
} from "recharts";
import type { JobMetric } from "../api/client";

interface Props {
  metrics: JobMetric[];
  showGpu?: boolean;
}

export default function MetricsChart({ metrics, showGpu = false }: Props) {
  if (metrics.length === 0) {
    return (
      <div className="h-48 flex items-center justify-center text-slate-500 text-sm">
        No metrics recorded
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={220}>
      <LineChart data={metrics} margin={{ top: 4, right: 8, left: -16, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
        <XAxis
          dataKey="elapsed_seconds"
          tickFormatter={(v: number) => `${v.toFixed(0)}s`}
          tick={{ fill: "#94a3b8", fontSize: 11 }}
        />
        <YAxis tick={{ fill: "#94a3b8", fontSize: 11 }} domain={[0, 100]} unit="%" />
        <Tooltip content={<CustomTooltip />} />
        <Legend />
        <Line
          type="monotone"
          dataKey="cpu_percent"
          name="CPU %"
          stroke="#6366f1"
          strokeWidth={2}
          dot={false}
          activeDot={{ r: 4 }}
        />
        <Line
          type="monotone"
          dataKey="memory_mb"
          name="Memory (MB)"
          stroke="#10b981"
          strokeWidth={2}
          dot={false}
          activeDot={{ r: 4 }}
          yAxisId={0}
          // Normalise memory to 0-100 scale visually — tooltip still shows raw value
        />
        {showGpu && (
          <Line
            type="monotone"
            dataKey="gpu_util_percent"
            name="GPU %"
            stroke="#f59e0b"
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 4 }}
          />
        )}
      </LineChart>
    </ResponsiveContainer>
  );
}

function CustomTooltip({ active, payload, label }: TooltipProps<number, string>) {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-xs shadow-xl">
      <p className="text-slate-400 mb-1">{`t = ${Number(label).toFixed(1)}s`}</p>
      {payload.map((entry) => (
        <p key={entry.name} style={{ color: entry.color }} className="tabular-nums">
          {entry.name}: <span className="font-medium">{Number(entry.value).toFixed(1)}</span>
          {entry.name === "Memory (MB)" ? " MB" : "%"}
        </p>
      ))}
    </div>
  );
}
