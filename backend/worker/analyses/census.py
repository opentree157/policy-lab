"""Census demographic profile analysis using synthetic decennial census data."""

import time
from typing import Any, Callable, Dict, List

import numpy as np

_STATE_POPULATIONS: Dict[str, int] = {
    "CA": 39_538_223, "TX": 29_145_505, "FL": 21_538_187, "NY": 20_201_249,
    "PA": 13_002_700, "IL": 12_812_508, "OH": 11_799_448, "GA": 10_711_908,
    "NC": 10_439_388, "MI": 10_077_331, "NJ": 9_288_994, "VA": 8_631_393,
    "WA": 7_705_281, "AZ": 7_151_502, "TN": 6_910_840, "MA": 7_029_917,
    "IN": 6_785_528, "MO": 6_154_913, "MD": 6_177_224, "WI": 5_893_718,
    "CO": 5_773_714, "MN": 5_706_494, "SC": 5_118_425, "AL": 5_024_279,
    "LA": 4_657_757, "KY": 4_505_836, "OR": 4_237_256, "OK": 3_959_353,
    "CT": 3_605_944, "UT": 3_271_616, "IA": 3_190_369, "NV": 3_104_614,
    "AR": 3_011_524, "MS": 2_961_279, "KS": 2_937_880, "NM": 2_117_522,
    "NE": 1_961_504, "ID": 1_839_106, "WV": 1_793_716, "HI": 1_455_271,
    "NH": 1_377_529, "ME": 1_362_359, "MT": 1_084_225, "RI": 1_097_379,
    "DE": 989_948,  "SD": 886_667,  "ND": 779_094,  "AK": 733_391,
    "VT": 643_077,  "WY": 576_851,
}
_DEFAULT_POP = 2_000_000


def run_census_demographics(
    dataset_id: str,
    parameters: Dict[str, Any],
    log_fn: Callable,
    metric_fn: Callable,
) -> Dict[str, Any]:
    states: List[str] = parameters.get("states", list(_STATE_POPULATIONS.keys())[:10])
    breakdown: str = parameters.get("breakdown", "age")

    rng = np.random.default_rng(2020)

    log_fn(f"Loading 2020 Decennial Census SF1 data for {len(states)} states")
    time.sleep(0.45)
    metric_fn(rows_processed=100_000)

    log_fn("Applying disclosure avoidance noise (differential privacy)...")
    time.sleep(0.3)
    metric_fn(rows_processed=300_000)

    # Population by state
    pop_by_state = []
    total_pop = 0
    for state in states:
        pop = _STATE_POPULATIONS.get(state, _DEFAULT_POP)
        noise = int(rng.integers(-50_000, 50_001))
        pop = max(100_000, pop + noise)
        total_pop += pop

        # Demographic composition varies by state (rough approximations)
        pct_white = float(np.clip(rng.normal(0.62, 0.12), 0.25, 0.92))
        pct_black = float(np.clip(rng.normal(0.13, 0.08), 0.02, 0.38))
        pct_hispanic = float(np.clip(rng.normal(0.18, 0.12), 0.02, 0.55))
        pct_asian = float(np.clip(rng.normal(0.06, 0.04), 0.01, 0.22))
        median_age = float(np.clip(rng.normal(38.5, 3.0), 29, 47))

        pop_by_state.append({
            "state": state,
            "total_population": pop,
            "pct_under18": round(float(np.clip(rng.normal(0.222, 0.02), 0.17, 0.28)), 3),
            "pct_18to64": round(float(np.clip(rng.normal(0.611, 0.025), 0.55, 0.68)), 3),
            "pct_65plus": round(float(np.clip(rng.normal(0.167, 0.025), 0.10, 0.23)), 3),
            "median_age": round(median_age, 1),
            "pct_white_alone": round(pct_white, 3),
            "pct_black_alone": round(pct_black, 3),
            "pct_hispanic": round(pct_hispanic, 3),
            "pct_asian_alone": round(pct_asian, 3),
            "avg_household_size": round(float(np.clip(rng.normal(2.53, 0.15), 2.1, 3.2)), 2),
        })

    log_fn(f"Computing {breakdown} breakdown across {len(states)} states...")
    metric_fn(rows_processed=600_000)
    time.sleep(0.4)

    # National age distribution (pyramid)
    age_groups = [
        "0–4", "5–9", "10–14", "15–19", "20–24", "25–29", "30–34",
        "35–39", "40–44", "45–49", "50–54", "55–59", "60–64",
        "65–69", "70–74", "75–79", "80–84", "85+",
    ]
    age_pcts = [
        0.059, 0.061, 0.062, 0.064, 0.066, 0.072, 0.070,
        0.068, 0.064, 0.065, 0.066, 0.067, 0.062,
        0.055, 0.046, 0.033, 0.021, 0.019,
    ]
    age_distribution = [
        {
            "age_group": group,
            "population": int(total_pop * pct * (1 + rng.normal(0, 0.01))),
            "pct": round(pct + float(rng.normal(0, 0.001)), 4),
        }
        for group, pct in zip(age_groups, age_pcts)
    ]

    # Race/ethnicity national totals
    race_ethnicity = [
        {"group": "White alone (non-Hispanic)", "pct": 0.576, "population": int(total_pop * 0.576)},
        {"group": "Hispanic or Latino", "pct": 0.187, "population": int(total_pop * 0.187)},
        {"group": "Black or African American", "pct": 0.134, "population": int(total_pop * 0.134)},
        {"group": "Asian alone", "pct": 0.061, "population": int(total_pop * 0.061)},
        {"group": "Two or more races", "pct": 0.034, "population": int(total_pop * 0.034)},
        {"group": "Other", "pct": 0.008, "population": int(total_pop * 0.008)},
    ]

    log_fn("Computing urbanization index and population density...")
    metric_fn(rows_processed=800_000)
    time.sleep(0.25)

    summary = {
        "states_analyzed": len(states),
        "total_population": total_pop,
        "avg_median_age": round(float(np.mean([s["median_age"] for s in pop_by_state])), 1),
        "most_populous_state": max(pop_by_state, key=lambda x: x["total_population"])["state"],
        "youngest_state": min(pop_by_state, key=lambda x: x["median_age"])["state"],
        "oldest_state": max(pop_by_state, key=lambda x: x["median_age"])["state"],
        "pct_under18_avg": round(float(np.mean([s["pct_under18"] for s in pop_by_state])), 3),
        "pct_65plus_avg": round(float(np.mean([s["pct_65plus"] for s in pop_by_state])), 3),
        "key_finding": (
            f"Across the {len(states)} selected states, total analyzed population is "
            f"{total_pop:,}. The average median age is "
            f"{round(float(np.mean([s['median_age'] for s in pop_by_state])), 1)} years. "
            f"Senior population (65+) represents "
            f"{round(float(np.mean([s['pct_65plus'] for s in pop_by_state])) * 100, 1)}% on average, "
            f"with notable variation across states."
        ),
    }

    log_fn(
        f"Complete — {total_pop:,} total population, "
        f"avg median age {summary['avg_median_age']} yrs"
    )

    return {
        "chart_type": "census_demographics",
        "summary": summary,
        "population_by_state": pop_by_state,
        "age_distribution": age_distribution,
        "race_ethnicity": race_ethnicity,
    }
