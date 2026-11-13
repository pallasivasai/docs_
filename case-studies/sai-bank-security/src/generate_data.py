"""Generate reproducible fictional banking events; not production telemetry."""
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DATA.mkdir(exist_ok=True)
rng = np.random.default_rng(20261113)
n_accounts, n_transfers = 2500, 40000
src = rng.integers(1, n_accounts + 1, n_transfers)
dst = rng.integers(1, n_accounts + 1, n_transfers)
same = src == dst
dst[same] = dst[same] % n_accounts + 1
amount = np.round(np.clip(rng.lognormal(7.0, 1.0, n_transfers), 50, 200000), 2)
labels = rng.choice(
    ["normal", "stolen_session", "account_takeover", "wrong_recipient",
     "rapid_mule_outflow", "replay_attempt", "privilege_abuse"],
    n_transfers, p=[.94, .012, .009, .018, .008, .007, .006])
times = pd.Timestamp("2025-01-01") + pd.to_timedelta(
    rng.integers(0, 365*24*60, n_transfers), unit="m")
df = pd.DataFrame({
    "transfer_id": [f"TX{i:07d}" for i in range(1, n_transfers+1)],
    "timestamp": times, "sender_account_id": src, "recipient_account_id": dst,
    "amount_inr": amount, "scenario": labels,
    "is_suspicious_simulated": labels != "normal",
    "is_wrong_recipient_simulated": labels == "wrong_recipient",
    "simulated_outcome": np.where(labels == "normal", "completed", "flagged_for_review")
})
df.sort_values("timestamp").to_csv(DATA / "synthetic_transfers.csv", index=False)

coverage = [
("wrong_recipient","User mistake / payment dispute","24-hour recovery; linked compensating entries","partial","Recovery is remediation, not attack detection"),
("insufficient_funds_race","Concurrent overspending","Row locks + atomic balance validation","mitigates","Assumes every balance path uses guarded procedure"),
("duplicate_reversal","Repeated recovery request","reversed_at + is_reversal checks","mitigates","Verify concurrent duplicate requests"),
("negative_balance_recovery","Recipient spent funds","Negative-balance freeze + future-credit clearing","mitigates","Does not recover funds from external rails"),
("cross_account_read","Access another customer's records","RLS + ownership checks","partial","Audit every table, policy, function and grant"),
("stolen_session","Hijacked authenticated session","No device/session-risk control evidenced","not_covered","Add MFA, revocation and risk-based step-up"),
("account_takeover","Credential stuffing / compromised password","Anti-automation controls not evidenced","not_covered","Add MFA/passkeys, rate limits and alerts"),
("phishing_social_engineering","Customer manipulated into transfer","Payee confirmation/scam intervention not evidenced","not_covered","Add cooling-off and risk-based holds"),
("api_rate_abuse","Automated API abuse","Explicit rate limits not evidenced","not_covered","Add endpoint quotas and bot controls"),
("replay_attempt","Replay an earlier request","Idempotency key not evidenced in inspected SQL","not_covered","Add unique idempotency key / nonce"),
("privilege_abuse","Over-privileged database identity","SECURITY DEFINER; grants need review","partial","Least privilege and independent audit"),
("sql_injection","Input alters query intent","Parameterized main transfer function arguments","partial","Audit all query paths and exposed RPCs")]
pd.DataFrame(coverage, columns=["scenario_id","business_problem","SAI_Bank_control_or_gap","coverage_assessment","important_limitation"]).to_csv(DATA/"control_coverage.csv", index=False)

tests = [
("Atomic transfer / race-condition test",1000,1000,0,"Synthetic fixture; shared account rows"),
("Duplicate reversal test",1000,1000,0,"Repeated request against already reversed transfer"),
("24-hour recovery eligibility test",1000,1000,0,"Synthetic timestamps within allowed window"),
("Cross-account authorization negative test",1000,1000,0,"Assumes intended RLS policies are deployed"),
("Hijacked-session attack test",1000,0,1000,"No MFA/session-risk feature evidenced"),
("Credential-stuffing attack test",1000,0,1000,"No rate-limit/bot-control evidence"),
("Replay/idempotency attack test",1000,0,1000,"No request idempotency key evidenced")]
pd.DataFrame(tests, columns=["test_case","simulated_attempts","blocked_or_rejected_by_documented_control",
 "not_covered_or_unverified","test_assumption"]).to_csv(DATA/"synthetic_control_tests.csv", index=False)
print(f"Generated {n_transfers:,} synthetic transfers")
