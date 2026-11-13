# SAI Bank | Fintech Security Research

**24-Hour Wrong-Payment Recovery • Database-Level Transaction Integrity • Security Control Assessment**

A research-style case study of [SAI Bank](https://github.com/pallasivasai/saibank), covering the banking problem, product workflow, implementation evidence, synthetic scenario analysis, security gaps and validation roadmap.

> **Research integrity:** SAI Bank is a demonstration application, not a production bank or certified security product. The statistics are synthetic or repository-review counts—not real bank telemetry, confirmed fraud, recovered funds, or measured attack-prevention rates. No product can eliminate every cyber risk.

![SAI Bank executive security research dashboard](case-studies/sai-bank-security/images/10_executive_research_dashboard.svg)

## Research question

Can database-level controls make internal transfers safer and provide a controlled, auditable path to recover eligible wrong payments within 24 hours?

## 1. The business problem

A customer sends money to the wrong recipient. The recipient may already have spent the funds. Simply crediting the sender can create an unsupported balance; a poorly designed multi-step reversal can also leave account balances and ledger entries inconsistent.

SAI Bank's focus is safer internal money movement and a bounded wrong-payment recovery workflow—not a claim to stop every cyberattack.

## 2. How SAI Bank works

![Wrong-payment recovery workflow](case-studies/sai-bank-security/images/07_wrong_payment_problem_flow.svg)

The recovery procedure checks caller identity, ownership, transaction eligibility, prior reversal and the 24-hour deadline. It locks the relevant accounts and writes compensating ledger entries. If the recipient cannot cover the debit, negative-balance handling can freeze the account until future incoming credits clear the deficit.

The 24-hour period is a request window, not a guarantee of recovery. The workflow applies to the application's internal ledger; it cannot guarantee reversal through an external bank, UPI rail or payment provider.

### Transaction integrity

![Atomic transfer and ledger sequence](case-studies/sai-bank-security/images/08_atomic_transfer_sequence.svg)

The inspected transfer procedure validates and locks accounts, updates both balances and writes linked debit/credit ledger entries inside one database transaction. This depends on every money-changing route using the guarded procedure.

## 3. Executive statistics — synthetic experiment

| Metric | Result | Evidence type |
|---|---:|---|
| Generated transfers | 40,000 | Synthetic dataset |
| Synthetic account identifiers | 2,500 | Synthetic dataset |
| Planted suspicious labels | 2,412 (6.03%) | Generator-selected labels |
| Simulated notional on labelled events | ₹45.43 lakh | Synthetic transaction value |
| Risk scenarios reviewed | 12 | Repository code-review map |
| Scenarios mapped as mitigated | 3 / 12 | Qualitative code evidence |
| Partial / review required | 4 / 12 | Qualitative code evidence |
| No specific control evidenced in inspected app code | 5 / 12 | Scoped code-review gap |

The 6.03% is not real attack prevalence. ₹45.43 lakh is not fraud loss, money recovered, loss avoided or ROI. The 3/4/5 mapping is not an attack-block rate or an overall security score.

## 4. Security coverage

![Security coverage scorecard](case-studies/sai-bank-security/images/09_security_coverage_scorecard.svg)

**Evidence currently found:** atomic transfer logic, row locks, linked ledger entries, 24-hour recovery checks, duplicate-reversal checks, negative-balance freeze/future-credit clearing, and initial RLS policies.

**Important work still required:** audit RLS/grants/privileged functions, retire or refactor the legacy multi-request path, add idempotency, MFA/passkeys, rate limits, device/session risk, fraud alerts, scam intervention and independent penetration testing.

## 5. Statistical charts

### Synthetic transfer activity
![Synthetic transfer activity](case-studies/sai-bank-security/images/01_synthetic_activity.svg)

### Planted suspicious-event categories
![Suspicious-event categories](case-studies/sai-bank-security/images/02_attack_scenarios.svg)

### Simulated transaction notional
![Simulated notional exposure](case-studies/sai-bank-security/images/03_simulated_exposure.svg)

### Evidence-based control coverage
![Control coverage](case-studies/sai-bank-security/images/04_control_coverage.svg)

### Illustrative control-test fixtures
![Control-test fixture matrix](case-studies/sai-bank-security/images/05_control_test_matrix.svg)

The seven fixture rows describe hypothetical assumptions, not live requests or executed penetration tests. Actual pass rates require executable tests against a controlled deployment.

### Recovery lifecycle
![24-hour recovery lifecycle](case-studies/sai-bank-security/images/06_24h_recovery_flow.svg)

## 6. Validation roadmap

1. **P0:** Retire the legacy multi-request money-movement path; audit RLS, grants and privileged functions.
2. **P0:** Add idempotency, deterministic lock ordering and deadlock retry; execute concurrency and replay tests.
3. **P1:** Add MFA/passkeys, step-up checks, rate limits and bot controls.
4. **P1:** Add device/session anomaly detection, customer alerts and session revocation.
5. **P1:** Add scam warnings and beneficiary cooling-off for risky transfers.
6. **P2:** Add tamper-resistant audit monitoring and commission independent penetration testing.

## 7. Full research report

The [complete SAI Bank Security Research Report](case-studies/sai-bank-security/README.md) includes repository evidence, scenario mapping, test programme, business-impact KPIs, limitations and reproducibility instructions.

- [SAI Bank source repository](https://github.com/pallasivasai/saibank)
- [SAI Bank demo](https://saibank.lovable.app/)
- [Full research report](case-studies/sai-bank-security/README.md)
- [Chart assets](case-studies/sai-bank-security/images/)

**Conclusion:** SAI Bank demonstrates useful controls for internal transaction integrity and eligible wrong-payment recovery. It is a foundation for a broader fintech security platform, not a claim that all cyber issues are eliminated. Every broader security claim must be backed by implemented controls, executed tests and independent validation.
