#!/usr/bin/env python3
"""Pre-compute PH vs EM comparison scores for all jurisdictions.

Run this script to populate the scores cache. The export route will then
serve the pre-computed data instantly.

Usage: python scripts/precompute_em_comparison.py
"""
import os
import sys
import json
import time
import tempfile
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('SESSION_SECRET', 'precompute')

from main import app

DOMAINS = [
    ("total_risk_score", "Overall PHRAT Score"),
    ("natural_hazards_risk", "Natural Hazards"),
    ("flood_risk", "Flood"),
    ("tornado_risk", "Tornado"),
    ("winter_storm_risk", "Winter Storm"),
    ("thunderstorm_risk", "Thunderstorm"),
    ("health_risk", "Health Metrics"),
    ("active_shooter_risk", "Active Shooter"),
    ("air_quality_risk", "Air Quality"),
    ("extreme_heat_risk", "Extreme Heat"),
    ("utilities_risk", "Utilities"),
]

CACHE_PATH = os.path.join(tempfile.gettempdir(), "cara_em_comparison_scores.json")
PARTIAL_PATH = CACHE_PATH + ".partial"


def main():
    with app.app_context():
        from utils.data_processor import get_em_jurisdictions, process_risk_data

        em_jurs = get_em_jurisdictions()
        em_sorted = sorted(em_jurs, key=lambda x: x.get("em_name", x["name"]))

        existing_rows = {}
        if os.path.exists(PARTIAL_PATH):
            with open(PARTIAL_PATH) as f:
                partial = json.load(f)
                for row in partial.get("rows", []):
                    existing_rows[row["name"]] = row
            print(f"Resuming from {len(existing_rows)} previously computed jurisdictions")

        rows = []
        total = len(em_sorted)
        start = time.time()

        for idx, j in enumerate(em_sorted):
            jid = j["id"]
            em_name = j.get("em_name", j["name"])

            if em_name in existing_rows:
                rows.append(existing_rows[em_name])
                continue

            try:
                ph = process_risk_data(jid, discipline="public_health")
                em = process_risk_data(jid, discipline="em")
            except Exception as e:
                print(f"  ERROR {em_name}: {e}")
                continue

            if ph and em:
                ph_scores = {k: float(ph.get(k, 0) or 0) for k, _ in DOMAINS}
                em_scores = {k: float(em.get(k, 0) or 0) for k, _ in DOMAINS}
                rows.append({"name": em_name, "ph": ph_scores, "em": em_scores})

            if (idx + 1) % 5 == 0:
                elapsed = time.time() - start
                print(f"  {idx + 1}/{total} done ({elapsed:.0f}s)")
                with open(PARTIAL_PATH, "w") as f:
                    json.dump({"rows": rows}, f)

        result = {
            "generated": datetime.now().isoformat(),
            "count": len(rows),
            "rows": rows,
        }

        with open(CACHE_PATH, "w") as f:
            json.dump(result, f)

        if os.path.exists(PARTIAL_PATH):
            os.remove(PARTIAL_PATH)

        elapsed = time.time() - start
        print(f"\nDone! {len(rows)} jurisdictions computed in {elapsed:.0f}s")
        print(f"Saved to: {CACHE_PATH}")


if __name__ == "__main__":
    main()
