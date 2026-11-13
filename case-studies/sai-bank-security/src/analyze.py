"""Analyze synthetic banking events and export tables, metrics and PNG charts."""
from pathlib import Path
import json
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
DATA, IMG, RES = ROOT/"data", ROOT/"images", ROOT/"results"
IMG.mkdir(exist_ok=True); RES.mkdir(exist_ok=True)
tx = pd.read_csv(DATA/"synthetic_transfers.csv", parse_dates=["timestamp"])
cov = pd.read_csv(DATA/"control_coverage.csv")
tests = pd.read_csv(DATA/"synthetic_control_tests.csv")
susp = tx[tx.is_suspicious_simulated].copy()
exposure = susp.groupby("scenario").agg(
    attempts=("transfer_id","count"), notional_inr=("amount_inr","sum"),
    avg_amount_inr=("amount_inr","mean")).sort_values("notional_inr", ascending=False)
exposure.to_csv(RES/"scenario_exposure.csv")
tx["month"] = tx.timestamp.dt.to_period("M").astype(str)
monthly = tx.groupby("month").agg(
    transfers=("transfer_id","count"),
    flagged=("is_suspicious_simulated","sum"),
    flagged_notional_inr=("amount_inr", lambda s:s[tx.loc[s.index,"is_suspicious_simulated"]].sum()))
monthly["flagged_rate_pct"] = monthly.flagged/monthly.transfers*100
monthly.to_csv(RES/"monthly_activity.csv")
tests["control_test_pass_rate_pct"] = np.where(
    tests.simulated_attempts>0,
    tests.blocked_or_rejected_by_documented_control/tests.simulated_attempts*100, 0)
tests.to_csv(RES/"control_test_results.csv", index=False)
metrics = {
 "dataset_type":"synthetic_simulation_only","random_seed":20261113,
 "total_synthetic_transfers":int(len(tx)),
 "synthetic_accounts":int(pd.concat([tx.sender_account_id,tx.recipient_account_id]).nunique()),
 "simulated_suspicious_attempts":int(len(susp)),
 "simulated_suspicious_attempt_share_pct":round(len(susp)/len(tx)*100,2),
 "normal_synthetic_transfers":int((tx.scenario=="normal").sum()),
 "suspicious_attempt_notional_inr":round(float(susp.amount_inr.sum()),2),
 "warning":"Notional is not confirmed fraud loss, prevented loss or actual bank telemetry.",
 "coverage_counts":cov.coverage_assessment.value_counts().to_dict(),
 "documented_control_test_cases":int(len(tests)),
 "test_results_are":"deterministic synthetic fixtures; not production efficacy estimates"}
(RES/"key_metrics.json").write_text(json.dumps(metrics,indent=2))
plt.rcParams.update({"figure.dpi":130,"axes.spines.top":False,"axes.spines.right":False})
# 1. Activity
fig,ax=plt.subplots(figsize=(10,4.8)); x=np.arange(len(monthly))
ax.plot(x,monthly.transfers,marker="o",label="All transfers")
ax.plot(x,monthly.flagged,marker="o",label="Planted suspicious labels")
ax.set_xticks(x); ax.set_xticklabels(pd.to_datetime(monthly.index).strftime("%b %y"),rotation=35,ha="right")
ax.set_ylabel("Synthetic transfer count"); ax.set_title("Synthetic banking activity"); ax.legend(frameon=False)
fig.tight_layout(); fig.savefig(IMG/"01_synthetic_activity.png",bbox_inches="tight"); plt.close(fig)
# 2. Event counts
s=exposure.sort_values("attempts")
fig,ax=plt.subplots(figsize=(9,4.8)); b=ax.barh(s.index,s.attempts)
ax.bar_label(b,padding=3); ax.set_xlabel("Synthetic events"); ax.set_title("Planted suspicious-event categories")
fig.tight_layout(); fig.savefig(IMG/"02_attack_scenarios.png",bbox_inches="tight"); plt.close(fig)
# 3. Notional
s=exposure.sort_values("notional_inr")
fig,ax=plt.subplots(figsize=(9,4.8)); v=s.notional_inr/100000; b=ax.barh(s.index,v)
ax.bar_label(b,labels=[f"₹{z:.2f}L" for z in v],padding=3)
ax.set_xlabel("Synthetic notional (₹ lakh)"); ax.set_title("Notional represented by suspicious synthetic events")
fig.text(.01,.01,"Not actual fraud losses or prevented losses",fontsize=8)
fig.tight_layout(rect=(0,.04,1,1)); fig.savefig(IMG/"03_simulated_exposure.png",bbox_inches="tight"); plt.close(fig)
# 4. Coverage
c=cov.coverage_assessment.value_counts().reindex(["mitigates","partial","not_covered"],fill_value=0)
fig,ax=plt.subplots(figsize=(8,4.5)); b=ax.bar(c.index,c.values)
ax.bar_label(b,padding=4); ax.set_ylabel("Threat scenarios"); ax.set_title("Control coverage in inspected code")
fig.tight_layout(); fig.savefig(IMG/"04_control_coverage.png",bbox_inches="tight"); plt.close(fig)
# 5. Test fixtures
fig,ax=plt.subplots(figsize=(10,5)); y=np.arange(len(tests))
ax.barh(y,tests.blocked_or_rejected_by_documented_control,label="Fixture rejected")
ax.barh(y,tests.not_covered_or_unverified,left=tests.blocked_or_rejected_by_documented_control,label="Not covered / unverified")
ax.set_yticks(y); ax.set_yticklabels(tests.test_case,fontsize=8); ax.set_xlabel("Synthetic attempts")
ax.set_title("Deterministic test fixtures (not measured efficacy)"); ax.legend(frameon=False)
fig.tight_layout(); fig.savefig(IMG/"05_control_test_matrix.png",bbox_inches="tight"); plt.close(fig)
# 6. Recovery path
fig,ax=plt.subplots(figsize=(10,3.8)); ax.axis("off")
labels=[("Transfer","Atomic debit + credit"),("0–24 hours","Authenticate + ownership"),("Recovery","Lock accounts + reverse ledger"),("Deficit?","Freeze recipient"),("Future credits","Clear deficit + unfreeze")]
for i,(a,b) in enumerate(labels):
 x=.02+i*.198
 ax.add_patch(plt.Rectangle((x,.36),.17,.38,transform=ax.transAxes,fill=False,linewidth=1.5))
 ax.text(x+.085,.59,a,ha="center",transform=ax.transAxes,weight="bold",fontsize=9)
 ax.text(x+.085,.45,b,ha="center",transform=ax.transAxes,fontsize=7,wrap=True)
 if i<4: ax.annotate("",xy=(x+.195,.55),xytext=(x+.173,.55),xycoords=ax.transAxes,arrowprops={"arrowstyle":"->"})
ax.set_title("SAI Bank documented 24-hour recovery flow")
fig.tight_layout(); fig.savefig(IMG/"06_24h_recovery_flow.png",bbox_inches="tight"); plt.close(fig)
print(json.dumps(metrics,indent=2))
