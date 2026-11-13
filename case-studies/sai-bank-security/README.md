# SAI Bank: Can Database-Level Payment Protection Reduce Digital-Banking Risk?

A reproducible security and business-risk case study based on [SAI Bank](https://github.com/pallasivasai/saibank). It defines the business problem, explains the product workflow, inspects implementation evidence, generates a synthetic dataset, quantifies risk scenarios and prioritizes security improvements.

> **Scope:** SAI Bank is a demonstration application, not a production bank or certified security product. No software can eliminate every cyber risk. The statistics are synthetic or repository-review counts, not real customer telemetry, confirmed fraud losses, or measured attack-prevention rates.

## 1. Executive summary

SAI Bank focuses on a specific high-value banking problem: protecting the integrity of money movement and providing a controlled recovery path for eligible wrong payments.

The inspected repository demonstrates:
- Atomic transfer processing with caller checks, validation, account-row locks, balance changes and linked ledger entries.
- A 24-hour wrong-payment recovery procedure with identity, ownership, transaction-type and duplicate-reversal checks.
- Negative-balance handling that freezes an account while a recovery deficit remains; later incoming credits can clear the deficit.
- Initial Row-Level Security (RLS) policies for profiles, accounts and transactions.

These are useful controls for transaction integrity and customer remediation. They do **not** independently prevent phishing, malware, credential theft, account takeover, insider misuse, denial of service or every API attack.

## 2. Business problem

**Question:** How can a digital bank reduce the impact of incorrect or unauthorized transfers without corrupting balances or losing the audit trail?

| Risk | Business consequence | SAI Bank relevance |
|---|---|---|
| Concurrent transfer race | Overspending / inconsistent balances | Atomic database function and row locks |
| Wrong recipient | Dispute and customer remediation | 24-hour recovery workflow |
| Duplicate reversal | Double credit / ledger inconsistency | Reversal markers and prior-reversal checks |
| Recipient spent funds | Recovery deficit | Negative-balance freeze and future-credit clearing |
| Cross-account access | Privacy breach | RLS and ownership checks; full audit still needed |
| Account takeover / credential stuffing | Unauthorized transfers | Not evidenced in inspected application code |
| API abuse / replay | Automated abuse or duplicate requests | Rate limits and idempotency not evidenced |

### What happens in a concrete example?

Suppose customer A sends ₹5,000 to customer B by mistake. A requests recovery two hours later.

1. The procedure authenticates A and checks that the original debit belongs to A.
2. It checks the 24-hour deadline, transaction type and whether a reversal already exists.
3. It locks the relevant account rows before changing balances.
4. It writes compensating ledger entries and marks the original transaction as reversed.
5. If B's balance cannot cover the debit, the negative-balance protection freezes B's account until future credits clear the deficit.

This is an internal-ledger recovery flow. It does not guarantee reversal through an external bank, UPI rail or payment provider.

![Wrong-payment problem and recovery workflow](images/07_wrong_payment_problem_flow.svg)

## 3. Why database-level processing matters

Money movement should be one indivisible database operation. If the sender balance changes but the recipient balance or ledger write fails separately, records can disagree.

![Atomic transfer and ledger sequence](images/08_atomic_transfer_sequence.svg)

The inspected `transfer_money()` procedure performs authentication checks, validation, account-row locking, balance changes and linked debit/credit ledger writes inside one database function/transaction. The inspected `reverse_transaction()` procedure checks eligibility and writes compensating entries under account locks.

This is protective only when every money-changing route uses the guarded procedures. The repository also contains a legacy Edge Function that appears to make balance and ledger changes as separate requests; if still reachable, it should be retired or refactored to call the atomic procedure.

## 4. Repository review and engineering caveats

Inspected files:
- `drizzle/migrations/0000_transfer_and_24h_reversal_with_freeze.sql`
- `supabase/migrations/20251124144103_42d0ffa9-ef97-4422-863c-ed276f9c8fcb.sql`
- `supabase/functions/wrong-payment-reversal/index.ts` (legacy path)

Important follow-ups:
1. Route all money movement through the same atomic database procedures; verify the legacy path is unreachable or retire it.
2. Review table grants, RLS policies, `SECURITY DEFINER` ownership, fixed `search_path` and function execute permissions together.
3. Test deterministic lock ordering, deadlock retry and idempotency under concurrent requests.
4. Add MFA/passkeys, rate limiting, device/session risk, customer alerts, session revocation and fraud monitoring.
5. Perform independent threat modelling and penetration testing.

“Not evidenced in inspected files” does not prove a control is absent from every deployment layer. This is a scoped code review, not a production audit.

## 5. Synthetic dataset and headline statistics

The generator uses NumPy and pandas with fixed seed `20261113`. It creates 40,000 fictional transfers and 2,500 synthetic account identifiers. Suspicious labels are deliberately planted for analysis; they are not observed attacks.

| Metric | Result | What it means |
|---|---:|---|
| Synthetic transfers | 40,000 | Generated test records |
| Synthetic account identifiers | 2,500 | Fictional IDs in generated dataset |
| Planted suspicious labels | 2,412 (6.03%) | Labels selected by generator, not real attack prevalence |
| Notional attached to labelled events | ₹45.43 lakh | Simulated transfer value, not fraud loss |
| Risk scenarios reviewed | 12 | Rows in the repository control-coverage map |
| Scenarios mapped as mitigated | 3 / 12 (25.0%) | Specific code evidence mapped to named risks |
| Partial coverage / review required | 4 / 12 (33.3%) | Some relevant control evidence, further validation needed |
| No specific control evidenced | 5 / 12 (41.7%) | Gap in inspected application evidence |

![SAI Bank security coverage scorecard](images/09_security_coverage_scorecard.svg)

The 25% / 33.3% / 41.7% values are **scenario classifications**, not an overall security score or attack-blocking percentage. The ₹45.43 lakh notional is not actual fraud loss, recovered money, loss avoided or ROI.

## 6. Control-test fixture interpretation

The repository contains seven deterministic illustrative test-fixture rows, each with 1,000 hypothetical attempts. Four rows assume a control rejects the named scenario; three rows represent scenarios for which no corresponding control was evidenced. These are **designed fixture assumptions**, not 7,000 live requests, executed penetration tests, or measured production pass rates.

| Fixture group | Rows | Interpretation |
|---|---:|---|
| Atomic race, duplicate reversal, 24-hour eligibility, cross-account negative test | 4 | Expected control outcome under stated assumptions; must be run against a deployed test environment |
| Hijacked session, credential stuffing, replay/idempotency | 3 | No dedicated control evidenced in inspected code; implementation and testing required |

Do not interpret the fixture values as proof that SAI Bank blocks 100% of these attacks. Actual effectiveness requires executable tests against the deployed application and database.

## 7. Visual analysis

### 7.1 Synthetic transfer activity
![Synthetic transfer activity](images/01_synthetic_activity.svg)

### 7.2 Planted suspicious-event categories
![Planted suspicious-event categories](images/02_attack_scenarios.svg)

### 7.3 Simulated transaction notional
![Simulated notional exposure; not actual fraud loss](images/03_simulated_exposure.svg)

### 7.4 Evidence-based control coverage
![Control coverage from inspected code](images/04_control_coverage.svg)

### 7.5 Deterministic fixture assumptions
![Illustrative control-test matrix](images/05_control_test_matrix.svg)

### 7.6 24-hour recovery lifecycle
![24-hour recovery lifecycle](images/06_24h_recovery_flow.svg)

## 8. Recommendations by priority

| Priority | Improvement | Expected value | Verification |
|---|---|---|---|
| P0 | Retire legacy multi-request money-movement path | Prevent split balance/ledger updates | Deployed-route review + integration tests |
| P0 | Audit RLS, grants and privileged functions | Reduce unauthorized data/function access | Negative authorization and SQL privilege tests |
| P0 | Add idempotency, deterministic lock ordering and deadlock retry | Safer retries and concurrent requests | Parallel transfer and replay tests |
| P1 | MFA/passkeys and step-up confirmation | Reduce account-takeover impact | Authentication journey tests |
| P1 | Login/OTP/transfer rate limits and bot controls | Reduce automated abuse | Abuse and load tests |
| P1 | Device/session anomaly signals, alerts and revocation | Faster detection and containment | New-device/session simulations |
| P1 | Scam warnings and beneficiary cooling-off | Reduce social-engineering impact | Controlled journey tests |
| P2 | Tamper-resistant audit stream and operational alerts | Better investigation and response | Alert and retention tests |
| P2 | Independent penetration test and retest | Validate assumptions beyond code review | External assessment |

## 9. Limitations

- SAI Bank is a demo application, not production-readiness certification.
- Repository inspection does not prove which code paths are deployed or reachable.
- Synthetic data has planted labels and simplified behaviour; it cannot estimate real fraud prevalence.
- A scenario marked “mitigates” applies only to its stated assumptions.
- No live attack simulation, independent penetration test, or production efficacy study was performed.
- Internal-ledger recovery cannot guarantee funds can be retrieved from external banks or payment rails.

## 10. Reproduce

```bash
python -m pip install -r requirements.txt
python src/generate_data.py
python src/analyze.py
python src/render_svg_charts.py
```

The scripts regenerate the synthetic data, result tables and chart files with a fixed seed.

## 11. Links

- SAI Bank source: https://github.com/pallasivasai/saibank
- SAI Bank demo: https://saibank.lovable.app/
- Companion analytics repository: https://github.com/pallasivasai/docs_

**Conclusion:** SAI Bank demonstrates useful database-level patterns for safer transfers and a bounded wrong-payment recovery workflow. It can be developed into a broader banking-security product, but comprehensive protection requires additional identity, fraud, API, device, monitoring and operational controls plus independent validation.
