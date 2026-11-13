# SAI Bank — 24-Hour Wrong-Payment Recovery & Transaction Security

**A business-problem and security case study** based on the SAI Bank demonstration application: [github.com/pallasivasai/saibank](https://github.com/pallasivasai/saibank).

This project explains the customer problem, shows how SAI Bank's database-level workflow is designed to address it, reviews the implementation evidence, and analyses reproducible synthetic transaction scenarios.

> **Important:** SAI Bank is a demonstration application, not a production bank. No product can eliminate every cyber risk. Statistics below are synthetic simulations and repository-review counts, not real customer activity, confirmed fraud, or measured attack-prevention rates.

## 1. The banking problem

A customer sends money to the wrong person, discovers an incorrect transfer, or reports a transaction after the money has moved. If the recipient has already spent the funds, simply crediting the sender can create an unsupported balance. Poorly designed recovery can also cause duplicate reversals or mismatched ledger entries.

**SAI Bank's focus:** safer internal money movement and a controlled recovery request for eligible wrong transfers within 24 hours.

## 2. How SAI Bank works

![SAI Bank wrong-payment recovery workflow](case-studies/sai-bank-security/images/07_wrong_payment_problem_flow.svg)

Example: A sends ₹5,000 to B by mistake and requests recovery two hours later. The procedure authenticates A, checks ownership and eligibility, prevents a second reversal, locks the accounts, and writes compensating ledger entries. If B has already spent the funds, a negative balance can trigger an account freeze; future incoming credits can clear the deficit.

The 24-hour period is a request window, not a guarantee that every payment can be recovered. This is an internal-ledger workflow; it cannot guarantee reversal through an external bank, UPI rail or payment provider.

### Why atomic database processing matters

![SAI Bank atomic transfer and ledger sequence](case-studies/sai-bank-security/images/08_atomic_transfer_sequence.svg)

The inspected transfer procedure validates and locks the accounts, updates both balances and writes linked debit/credit entries inside one database transaction. This helps prevent partial money movement, provided every money-changing route uses the guarded procedure.

## 3. What the code evidence covers — and what it does not

![SAI Bank security coverage scorecard](case-studies/sai-bank-security/images/09_security_coverage_scorecard.svg)

| Risk area | SAI Bank evidence |
|---|---|
| Concurrent spending | Atomic database function and row locks |
| Duplicate reversal | Reversal markers and prior-reversal checks |
| Wrong payment | 24-hour recovery workflow |
| Recipient already spent funds | Negative-balance freeze and future-credit clearing |
| Cross-account access | RLS and ownership checks; full audit required |
| Account takeover / phishing | Additional controls needed |
| Stolen sessions / API abuse / replay | MFA, rate limits, session-risk and idempotency controls need implementation/verification |

## 4. SAI Bank synthetic statistics

The reproducible generator uses a fixed seed and creates a fictional dataset.

| Metric | Synthetic result |
|---|---:|
| Generated transfers | 40,000 |
| Synthetic account identifiers | 2,500 |
| Planted suspicious-event labels | 2,412 (6.03%) |
| Simulated transaction notional for labelled events | ₹45.43 lakh |
| Risk scenarios mapped as mitigated | 3 of 12 (25.0%) |
| Partial coverage / review required | 4 of 12 (33.3%) |
| No specific control evidenced in inspected code | 5 of 12 (41.7%) |

These percentages classify reviewed risk scenarios; they are **not** an overall security score or attack-block rate. ₹45.43 lakh is simulated transfer value, not actual fraud loss, recovered funds, loss avoided or ROI.

### Generated statistical charts

### 4.1 Synthetic banking activity
![Synthetic SAI Bank transfer activity](case-studies/sai-bank-security/images/01_synthetic_activity.svg)

### 4.2 Suspicious-event categories
![Synthetic suspicious-event categories](case-studies/sai-bank-security/images/02_attack_scenarios.svg)

### 4.3 Simulated transaction notional
![Simulated notional exposure, not actual fraud loss](case-studies/sai-bank-security/images/03_simulated_exposure.svg)

### 4.4 Evidence-based control coverage
![Control coverage](case-studies/sai-bank-security/images/04_control_coverage.svg)

### 4.5 Illustrative control-test fixtures
![Control-test fixture matrix](case-studies/sai-bank-security/images/05_control_test_matrix.svg)

The seven test-fixture rows contain hypothetical expected outcomes, not live or production test results. Four assume an expected rejection under stated conditions; three represent controls not evidenced in inspected code. They must be executed against a deployed test environment before any efficacy claim.

### 4.6 24-hour recovery lifecycle
![24-hour recovery lifecycle](case-studies/sai-bank-security/images/06_24h_recovery_flow.svg)

## 5. Product improvements required for broader protection

1. Retire or refactor the legacy multi-request money-movement path.
2. Audit RLS, table grants, privileged functions and execute permissions.
3. Add idempotency keys, deterministic lock ordering and deadlock retry.
4. Add MFA/passkeys, rate limiting, bot controls and step-up verification.
5. Add device/session anomaly detection, alerts, session revocation and fraud monitoring.
6. Add scam warnings, beneficiary cooling-off and unusual-transfer checks.
7. Complete independent threat modelling, penetration testing and retesting.

## 6. Full case study and source

- [Full SAI Bank security case study](case-studies/sai-bank-security/README.md)
- [SAI Bank source repository](https://github.com/pallasivasai/saibank)
- [SAI Bank demo](https://saibank.lovable.app/)
- [All generated SAI Bank charts](case-studies/sai-bank-security/images/)

**Bottom line:** SAI Bank currently demonstrates transaction-integrity and wrong-payment recovery controls. It is a foundation for a broader security product, not a claim that every cyberattack is prevented. The next step is to implement the missing controls and validate the complete system with executable tests and independent security assessment.
