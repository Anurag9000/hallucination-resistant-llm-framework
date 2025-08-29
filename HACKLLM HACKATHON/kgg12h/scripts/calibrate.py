"""
scripts/calibrate.py
Purpose: Fit a tiny calibration model (e.g., isotonic regression) on 20–30 labeled examples.
What to implement:
- Load a small JSON of {claim, status, raw_score} and learn mapping -> calibrated p.
Implementation notes:
- Keep it optional; pipeline falls back to heuristics if file not present.
"""
import json, os, argparse
from typing import List
try:
    from sklearn.isotonic import IsotonicRegression
except Exception:
    IsotonicRegression = None

def main(path_in: str, path_out: str):
    if IsotonicRegression is None:
        print("sklearn not installed; skipping calibration.")
        return
    data = json.load(open(path_in, "r", encoding="utf-8"))
    xs, ys = [], []
    for row in data:
        xs.append(float(row["raw_score"]))  # e.g., entailment prob or margin
        ys.append(1.0 if row["is_hallucination"] else 0.0)
    ir = IsotonicRegression(out_of_bounds="clip")
    ir.fit(xs, ys)
    import joblib
    joblib.dump(ir, path_out)
    print("Saved calibrated model to", path_out)

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, help="JSON lines or JSON list with raw_score/is_hallucination")
    ap.add_argument("--output", default="data/calibration.pkl")
    args = ap.parse_args()
    main(args.input, args.output)
