"""
Ray-based distributed job runner.

Each submitted experiment dispatches a Ray remote task that:
  1. Runs the appropriate analysis function in an isolated worker process
  2. Collects CPU/memory metrics every ~second via psutil
  3. Returns a structured result with artifacts + reproducibility manifest

Falls back to a ThreadPoolExecutor if Ray is not installed.
"""

import hashlib
import json
import platform
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

import psutil

try:
    import ray

    _RAY_AVAILABLE = True
except ImportError:
    _RAY_AVAILABLE = False


# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------


@dataclass
class JobResult:
    success: bool
    logs: str
    artifacts: Dict[str, Any]
    metrics: List[Dict[str, Any]]
    peak_cpu: float = 0.0
    peak_memory_mb: float = 0.0
    avg_cpu: float = 0.0
    total_runtime_seconds: float = 0.0
    error: Optional[str] = None
    reproducibility_manifest: Dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Core execution logic (runs inside the Ray worker process)
# ---------------------------------------------------------------------------


def _run_job_core(
    job_id: str,
    analysis_type: str,
    dataset_id: str,
    parameters: Dict[str, Any],
) -> Dict[str, Any]:
    """Execute the analysis and return a serialisable result dict."""
    # Import analyses here so they run in the worker process
    from worker.analyses.housing_acs import run_housing_affordability
    from worker.analyses.labor import run_labor_trends
    from worker.analyses.census import run_census_demographics
    from worker.analyses.world_bank import run_world_bank_indicators

    ANALYSES: Dict[str, Callable] = {
        "housing_affordability": run_housing_affordability,
        "labor_trends": run_labor_trends,
        "census_demographics": run_census_demographics,
        "world_bank_indicators": run_world_bank_indicators,
    }

    start = time.time()
    proc = psutil.Process()
    metrics: List[Dict[str, Any]] = []
    log_lines: List[str] = []

    def log(msg: str) -> None:
        ts = datetime.utcnow().strftime("%H:%M:%S.%f")[:-3]
        log_lines.append(f"[{ts}] {msg}")

    def collect_metric(rows_processed: Optional[int] = None) -> None:
        elapsed = time.time() - start
        cpu = proc.cpu_percent(interval=0.05)
        mem_mb = proc.memory_info().rss / 1_048_576
        throughput = rows_processed / elapsed if rows_processed and elapsed > 0 else None
        metrics.append(
            {
                "elapsed_seconds": round(elapsed, 2),
                "cpu_percent": round(cpu, 1),
                "memory_mb": round(mem_mb, 1),
                # Simulated GPU metrics — in prod swap with pynvml / DCGM
                "gpu_memory_mb": round(min(mem_mb * 0.6, 4096), 1),
                "gpu_util_percent": round(min(cpu * 0.85, 98), 1),
                "throughput_rows_per_sec": round(throughput, 1) if throughput else None,
            }
        )

    try:
        log(f"Job {job_id} started — analysis_type={analysis_type} dataset={dataset_id}")
        log(f"Parameters: {json.dumps(parameters)}")
        collect_metric()

        if analysis_type not in ANALYSES:
            raise ValueError(f"Unknown analysis_type: {analysis_type!r}")

        result_data = ANALYSES[analysis_type](
            dataset_id=dataset_id,
            parameters=parameters,
            log_fn=log,
            metric_fn=collect_metric,
        )

        total_runtime = time.time() - start
        collect_metric()
        log(f"Analysis finished in {total_runtime:.2f}s")

        manifest = {
            "job_id": job_id,
            "analysis_type": analysis_type,
            "dataset_id": dataset_id,
            "parameters": parameters,
            "parameters_hash": hashlib.sha256(
                json.dumps(parameters, sort_keys=True).encode()
            ).hexdigest()[:16],
            "python_version": sys.version.split()[0],
            "platform": platform.platform(),
            "executed_at_utc": datetime.utcnow().isoformat(),
            "total_runtime_seconds": round(total_runtime, 3),
            "ray_version": ray.__version__ if _RAY_AVAILABLE else "n/a (thread-pool mode)",
        }

        return {
            "success": True,
            "logs": "\n".join(log_lines),
            "artifacts": result_data,
            "metrics": metrics,
            "peak_cpu": max((m["cpu_percent"] for m in metrics), default=0.0),
            "peak_memory_mb": max((m["memory_mb"] for m in metrics), default=0.0),
            "avg_cpu": (
                sum(m["cpu_percent"] for m in metrics) / len(metrics) if metrics else 0.0
            ),
            "total_runtime_seconds": round(total_runtime, 3),
            "error": None,
            "reproducibility_manifest": manifest,
        }

    except Exception as exc:
        import traceback

        log(f"ERROR: {exc}")
        return {
            "success": False,
            "logs": "\n".join(log_lines),
            "artifacts": {},
            "metrics": metrics,
            "peak_cpu": 0.0,
            "peak_memory_mb": 0.0,
            "avg_cpu": 0.0,
            "total_runtime_seconds": time.time() - start,
            "error": traceback.format_exc(),
            "reproducibility_manifest": {},
        }


# ---------------------------------------------------------------------------
# Ray remote task (used when Ray is available)
# ---------------------------------------------------------------------------

if _RAY_AVAILABLE:

    @ray.remote
    def _ray_execute(
        job_id: str,
        analysis_type: str,
        dataset_id: str,
        parameters: Dict[str, Any],
    ) -> Dict[str, Any]:
        return _run_job_core(job_id, analysis_type, dataset_id, parameters)


# ---------------------------------------------------------------------------
# Public API used by FastAPI routers
# ---------------------------------------------------------------------------


def submit_job(
    job_id: str,
    analysis_type: str,
    dataset_id: str,
    parameters: Dict[str, Any],
) -> Any:
    """
    Submit a job for async execution.

    Returns a Ray ObjectRef when Ray is available, or a Future from
    concurrent.futures otherwise. Callers use `resolve_job()` to get results.
    """
    if _RAY_AVAILABLE:
        return _ray_execute.remote(job_id, analysis_type, dataset_id, parameters)
    else:
        from concurrent.futures import ThreadPoolExecutor

        executor = ThreadPoolExecutor(max_workers=4)
        return executor.submit(_run_job_core, job_id, analysis_type, dataset_id, parameters)


def poll_job(future: Any, timeout: float = 0.0) -> Optional[Dict[str, Any]]:
    """
    Non-blocking poll. Returns the result dict if ready, else None.
    Timeout=0 means don't wait at all.
    """
    if _RAY_AVAILABLE:
        import ray as _ray

        ready, _ = _ray.wait([future], timeout=timeout)
        if ready:
            return _ray.get(future)
        return None
    else:
        if future.done():
            return future.result()
        return None


def init_ray() -> None:
    """Initialise Ray in local mode (idempotent)."""
    if _RAY_AVAILABLE:
        ray.init(ignore_reinit_error=True, num_cpus=None)
