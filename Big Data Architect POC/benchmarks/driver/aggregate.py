"""Aggregate per-vendor Locust CSVs into a single comparison table."""
from pathlib import Path
import pandas as pd

RESULTS = Path(__file__).parent.parent / "results"

def load_vendor(vendor: str) -> pd.DataFrame:
    csv = RESULTS / f"{vendor}_stats.csv"
    df = pd.read_csv(csv)
    df["vendor"] = vendor
    return df

def main() -> None:
    vendors = ["gcp", "aws", "azure", "databricks"]
    frames = []

    for v in vendors:
        f = RESULTS / f"{v}_stats.csv"
        if f.exists():
            frames.append(load_vendor(v))

    if not frames:
        print("No results found. Run benchmarks first.")
        return

    df = pd.concat(frames, ignore_index=True)
    df = df[["vendor", "Name", "Request Count", "Failure Count",
             "Median Response Time", "Average Response Time",
             "95%", "99%", "Requests/s"]]

    print("\n=== Cross-Vendor Benchmark Results ===\n")
    print(df.to_string(index=False))

    out = RESULTS / "comparison.csv"
    df.to_csv(out, index=False)
    print(f"\n✓ Saved to {out}")

if __name__ == "__main__":
    main()
