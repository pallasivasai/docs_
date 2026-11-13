"""Export advanced descriptive statistics for the reproducible synthetic dataset.

All outputs describe generator-created records, not production bank telemetry.
"""
from pathlib import Path
import json
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA, RESULTS = ROOT / "data", ROOT / "results"
RESULTS.mkdir(exist_ok=True)
tx = pd.read_csv(DATA / "synthetic_transfers.csv", parse_dates=["timestamp"])
susp = tx[tx["is_suspicious_simulated"]].copy()
n, k = len(tx), len(susp)

# Wilson interval for the sample share of generator-planted labels.
z = 1.96
p = k / n
den = 1 + z*z/n
center = (p + z*z/(2*n)) / den
half = z * ((p*(1-p)/n + z*z/(4*n*n)) ** 0.5) / den
wilson_low, wilson_high = center-half, center+half

def distribution(frame):
    q = frame["amount_inr"].quantile([.50, .90, .95, .99])
    return {
        "count": int(len(frame)),
        "mean_inr": round(float(frame["amount_inr"].mean()), 2),
        "median_p50_inr": round(float(q.loc[.50]), 2),
        "p90_inr": round(float(q.loc[.90]), 2),
        "p95_inr": round(float(q.loc[.95]), 2),
        "p99_inr": round(float(q.loc[.99]), 2),
        "max_inr": round(float(frame["amount_inr"].max()), 2),
    }

monthly = tx.assign(month=tx["timestamp"].dt.to_period("M").astype(str)).groupby("month").agg(
    transfers=("transfer_id", "count"),
    suspicious=("is_suspicious_simulated", "sum"),
)
monthly["suspicious_label_share_pct"] = monthly["suspicious"] / monthly["transfers"] * 100
monthly.to_csv(RESULTS / "advanced_monthly_statistics.csv")

scenario = susp.groupby("scenario").agg(
    events=("transfer_id", "count"),
    notional_inr=("amount_inr", "sum"),
    mean_amount_inr=("amount_inr", "mean"),
    median_amount_inr=("amount_inr", "median"),
).sort_values("events", ascending=False)
scenario["share_of_all_transfers_pct"] = scenario["events"] / n * 100
scenario["share_of_suspicious_labels_pct"] = scenario["events"] / k * 100
scenario.to_csv(RESULTS / "advanced_scenario_statistics.csv")

sender_notional = tx.groupby("sender_account_id")["amount_inr"].sum()
shares = sender_notional / sender_notional.sum()
hhi = float((shares ** 2).sum() * 10000)
metrics = {
    "evidence_type": "synthetic_simulation_only",
    "seed": 20261113,
    "transfers": n,
    "unique_synthetic_accounts": int(pd.concat([tx.sender_account_id, tx.recipient_account_id]).nunique()),
    "normal_label_count": int(n-k),
    "suspicious_label_count": k,
    "suspicious_label_share_pct": round(p*100, 4),
    "wilson_95_interval_for_generator_label_share_pct": [round(wilson_low*100, 2), round(wilson_high*100, 2)],
    "total_transfer_notional_inr": round(float(tx.amount_inr.sum()), 2),
    "suspicious_label_notional_inr": round(float(susp.amount_inr.sum()), 2),
    "all_transfer_amount_distribution": distribution(tx),
    "suspicious_label_amount_distribution": distribution(susp),
    "monthly_transfer_count": {
        "mean": round(float(monthly.transfers.mean()), 1),
        "std": round(float(monthly.transfers.std()), 1),
        "min": int(monthly.transfers.min()),
        "max": int(monthly.transfers.max()),
    },
    "monthly_suspicious_label_share_pct": {
        "min": round(float(monthly.suspicious_label_share_pct.min()), 2),
        "max": round(float(monthly.suspicious_label_share_pct.max()), 2),
    },
    "sender_notional_concentration": {
        "top_1_sender_share_pct": round(float(shares.nlargest(1).sum()*100), 3),
        "top_10_senders_share_pct": round(float(shares.nlargest(10).sum()*100), 3),
        "top_25_senders_share_pct": round(float(shares.nlargest(25).sum()*100), 3),
        "hhi_10000_scale": round(hhi, 2),
    },
    "interpretation_warning": (
        "Generator-planted labels are not confirmed fraud. Wilson interval is not a "
        "real-world prevalence interval. Notional is not loss, recovery or loss avoided. "
        "HHI is a descriptive synthetic diagnostic, not a fraud score."
    ),
}
(RESULTS / "advanced_metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
print(json.dumps(metrics, indent=2))
