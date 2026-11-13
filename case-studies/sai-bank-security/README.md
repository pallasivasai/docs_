# SAI Bank: Can Database-Level Payment Protection Reduce Digital-Banking Risk?

A reproducible security and business-risk case study based on [SAI Bank](https://github.com/pallasivasai/saibank). It follows the analytics format of this repository: define a business problem, inspect the implementation, generate a synthetic dataset, quantify scenarios, produce charts, and prioritize improvements.

> **Scope:** SAI Bank is a demonstration banking application, not a production bank or a certified security product. This study does not claim that it prevents most cyberattacks. Simulated values are not real bank telemetry, actual fraud losses, or measured prevention rates.

## 1. Executive summary

Digital banks face transaction-integrity risks (concurrent spending, duplicate reversals, incorrect payments) and cyber risks (account takeover, credential stuffing, session theft, API abuse, replay and privilege misuse). A single payment-recovery feature cannot stop all of them.

The inspected SAI Bank repository demonstrates database-first safeguards:
- `transfer_money()` authenticates the caller, validates amount and balance, checks freeze status and self-transfer, locks account rows, updates balances and writes linked debit/credit entries inside one database function.
- `reverse_transaction()` checks caller identity, transaction ownership, debit type, prior reversal and the 24-hour window; it locks accounts and writes compensating ledger entries.
- A trigger freezes an account when recovery creates a negative balance; future credits can clear the deficit.
- Initial migrations enable Row-Level Security (RLS) for profiles, accounts and transactions.

These controls are relevant to transaction integrity, bounded authorization and mistaken-payment recovery. They do not replace MFA/passkeys, bot and rate controls, session/device risk, fraud monitoring, operational security or independent testing.

## 2. Business problem

**Question:** How can a digital bank reduce the financial and operational impact of unauthorized or erroneous transfers without corrupting balances or losing its audit trail?

| Risk | Business consequence | SAI Bank relevance |
|---|---|---|
| Concurrent transfer race | Overspending, inconsistent balances | Atomic database function and row locks |
| Wrong recipient | Complaints and dispute cost | 24-hour recovery mechanism |
| Duplicate reversal | Double credit / ledger inconsistency | `reversed_at`, `is_reversal`, linked ledger entries |
| Recipient spent funds | Recovery deficit | Negative-balance freeze and future-credit clearing |
| Cross-account access | Privacy breach | RLS and ownership checks; full policy audit still required |
| Account takeover / credential stuffing | Unauthorized transfers | Not evidenced in inspected application code |
| API abuse / replay | Automated abuse or duplicate requests | Rate limits and idempotency not evidenced |

### What happens in a concrete example?

Suppose customer A sends ₹5,000 to customer B by mistake. A requests recovery 2 hours later.

1. The procedure authenticates A and checks that the original debit belongs to A.
2. It checks the 24-hour deadline, transaction type and whether a reversal already exists.
3. It locks the relevant account rows before changing balances.
4. It writes compensating ledger entries and marks the original transaction as reversed.
5. If B's balance cannot cover the debit, the negative-balance protection freezes B's account until future credits clear the deficit.

This is an internal-ledger recovery flow. It does not guarantee reversal through an external bank, UPI rail or payment provider.

![Wrong-payment problem and recovery workflow](images/07_wrong_payment_problem_flow.svg)

## 3. Repository review

Primary source: [pallasivasai/saibank](https://github.com/pallasivasai/saibank)

Inspected files:
- `README.md`
- `drizzle/migrations/0000_transfer_and_24h_reversal_with_freeze.sql`
- `supabase/migrations/20251124144103_42d0ffa9-ef97-4422-863c-ed276f9c8fcb.sql`
- `supabase/functions/wrong-payment-reversal/index.ts` (legacy path)

### Engineering caveats found

1. The repository also contains a legacy Edge Function that performs balance and ledger changes as separate requests. If still reachable, it should be disabled or refactored to call the atomic database procedure.
2. Table grants and RLS policies must be reviewed together. Grants alone do not constitute safe authorization.
3. `SECURITY DEFINER` functions require review of ownership, `EXECUTE` grants, fixed `search_path`, and bypass paths.
4. Lock ordering should be deterministic and tested. Opposing transfers that acquire locks in inconsistent order can deadlock; atomic rollback protects data consistency, but retry and ordering strategies still matter.
5. MFA/passkeys, rate limiting, idempotency keys, device/session anomaly controls and centralized fraud alerting were not evidenced in the inspected files. “Not evidenced” does not prove they are absent from every deployment layer.

## 4. How the controls work

![Atomic transfer and ledger sequence](images/08_atomic_transfer_sequence.svg)

### Atomic transfer
`Authenticate → lock sender and recipient → validate funds/state → update both balances → write linked entries → commit`

The shared `transfer_group` UUID links the debit and credit ledger rows. Keeping balance changes and ledger writes inside one database transaction is safer than separate frontend or Edge Function requests.

### Wrong-payment recovery
The database procedure checks ownership, debit type, prior reversal and the 24-hour deadline. It locks the accounts, restores the sender, debits the recipient, marks original entries reversed and writes compensating entries.

### Recipient already spent the funds
The recipient balance may become negative. A trigger freezes the account while the deficit remains; later incoming funds can clear it. This does not guarantee recovery from an external bank or payment rail.

## 5. Synthetic experiment design

The generator uses NumPy and pandas with fixed seed `20261113`. It creates 40,000 fictional transfers, 2,500 account identifiers and planted suspicious labels (stolen session, account takeover, wrong recipient, rapid mule-style outflow, replay and privilege abuse). These are teaching labels, not observations from SAI Bank, real customers or real attackers.

Metrics:
- Transfer volume and planted suspicious-event mix.
- Notional amount associated with suspicious synthetic events.
- Evidence-based control coverage (`mitigates`, `partial`, `not_covered`).
- Deterministic test-fixture outcomes.

**The suspicious-event notional is not realized fraud loss, loss avoided or ROI.** Fixture pass/fail counts are not production attack-block rates.

## 6. Generated results

| Metric | Synthetic result |
|---|---:|
| Transfers generated | 40,000 |
| Synthetic account identifiers | 2,500 |
| Planted suspicious scenarios | 2,412 (6.03%) |
| Suspicious-event transfer notional | ₹45.43 lakh |
| Scenarios mapped as mitigated by evidenced control | 3 |
| Partial coverage / review required | 4 |
| No specific control evidenced in inspected code | 5 |

All results above are generated data and repository-review outputs, not measurements of real attack frequency or effectiveness.

## 7. Visual analysis

### 7.1 Synthetic activity
![Synthetic activity](images/01_synthetic_activity.svg)

### 7.2 Planted suspicious-event categories
![Attack scenarios](images/02_attack_scenarios.svg)

### 7.3 Simulated notional exposure
![Simulated exposure](images/03_simulated_exposure.svg)

### 7.4 Evidence-based control coverage
![Control coverage](images/04_control_coverage.svg)

### 7.5 Deterministic test fixture outcomes
![Control test matrix](images/05_control_test_matrix.svg)

### 7.6 24-hour recovery lifecycle
![Recovery flow](images/06_24h_recovery_flow.svg)

## 8. Recommendations

| Priority | Improvement | Business value | Verification |
|---|---|---|---|
| P0 | Route every transfer/reversal through the same atomic database procedures; retire legacy multi-step path | Avoid split updates and inconsistent ledgers | Integration tests and deployed-route review |
| P0 | Audit RLS, table grants, `SECURITY DEFINER` ownership and execute privileges | Reduce unauthorized access and privilege abuse | Negative authorization tests and SQL privilege audit |
| P0 | Deterministic lock order, deadlock retry and idempotency key | Safer concurrency and duplicate-request handling | Parallel opposing transfers and replay tests |
| P1 | MFA/passkeys and step-up confirmation for new payees/high-risk transfers | Reduce account-takeover impact | Authentication and risk journey tests |
| P1 | Rate-limit login, OTP, payee lookup and transfer endpoints | Reduce credential stuffing and API abuse | Load and abuse tests |
| P1 | Device/session anomaly signals, customer alerts and session revocation | Faster detection and containment | New-device and unusual-session simulations |
| P1 | Scam warnings, beneficiary cooling-off and unusual-transfer confirmation | Reduce social-engineering risk | Journey experiments and fraud-ops review |
| P2 | Centralized tamper-resistant audit stream and operational alerts | Better incident response and evidence retention | Alert, tamper and retention tests |
| P2 | Independent threat model and penetration test | Validate assumptions beyond code review | External assessment and retest |

## 9. Limitations

- SAI Bank is a demo app, not a production-readiness certification.
- Repository inspection does not prove which code paths are deployed or reachable.
- Synthetic data has planted labels and simplified behaviour; it cannot estimate real fraud prevalence.
- A control marked `mitigates` applies only to the named scenario and assumptions.
- No penetration test, live attack simulation, database execution test or independent audit was performed.

## 10. Reproduce

```bash
python -m pip install -r requirements.txt
python src/generate_data.py
python src/analyze.py
python src/render_svg_charts.py
```

The scripts regenerate data, images (PNG and SVG) and results with a fixed seed.

## 11. Links

- SAI Bank source: https://github.com/pallasivasai/saibank
- SAI Bank demo: https://saibank.lovable.app/
- Companion business analytics repo: https://github.com/pallasivasai/docs_

**Conclusion:** SAI Bank demonstrates useful database-level transaction-integrity and wrong-payment recovery patterns. The defensible claim is that these controls can mitigate specific transaction-integrity and recovery risks when every money-movement path enforces them. They do not, on their own, stop most cyberattacks.
