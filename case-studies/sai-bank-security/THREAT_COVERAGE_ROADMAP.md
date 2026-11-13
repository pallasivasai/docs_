# Threat Coverage Roadmap — Current Evidence vs Planned Defense

**Scope:** 12 predefined threat and control scenarios from the SAI Bank repository review.  
**Status:** Design roadmap only. Proposed controls are not represented as implemented, deployed or tested unless the current-evidence column explicitly says so.

## Executive threat-coverage statistics

| Measure | Current repository evidence | Planned roadmap |
|---|---:|---:|
| Scenarios assessed | 12 | 12 |
| Current mitigation evidence | 3 mitigated (25.0%); 4 partial (33.3%) | 12 (100%) have a proposed workstream |
| Scenarios with no specific control evidenced | 5 (41.7%) | 0 unmapped in this planning matrix |
| Verified attack-prevention rate | Not measured | Not measured |
| Production efficacy | Not measured | Not measured |

**Interpretation:** The 12/12 figure means every scenario has a recommended control or validation workstream assigned. It does **not** mean 12/12 attacks are prevented, nor that the proposed controls have been built or tested. The current code-review evidence remains 3 mitigated, 4 partial and 5 not evidenced.

## Scenario-by-scenario roadmap

| Threat scenario | Current evidence | Proposed defense workstream | Required verification |
|---|---|---|---|
| Concurrent overspending | Mitigated by row locks and balance validation, subject to all paths using guarded procedure | Atomic DB-only money movement, deterministic lock order, deadlock retry | Parallel opposing transfers; reconcile balances and ledger |
| Wrong-recipient payment | Partial: 24-hour internal-ledger recovery | Payee confirmation, risk-based cooling-off, auditable recovery workflow | User-journey tests and recovery boundary tests |
| Duplicate reversal | Mitigated in code review; concurrent behavior unverified | Idempotency key plus unique reversal constraint | Concurrent duplicate requests; exactly one effective reversal |
| Recipient already spent funds | Mitigated for internal ledger deficit handling | Freeze, future-credit clearing, alerts and clear customer messaging | Partial-balance and future-credit tests |
| Cross-account data access | Partial: initial RLS and ownership checks | Full RLS/grant/privileged-function audit; least privilege | Negative authorization tests for every table and RPC |
| Hijacked session | No dedicated device/session-risk control evidenced | MFA/passkeys, session revocation, step-up authentication | Expired, revoked and stolen-session test cases |
| Account takeover | MFA/passkeys and anti-automation controls not evidenced | MFA/passkeys, credential-stuffing protection, risk alerts | Controlled authentication-abuse tests |
| Phishing/social engineering | Scam intervention not evidenced | Beneficiary confirmation, scam warnings, cooling-off and risk holds | Adversarial customer-journey testing |
| API rate abuse | Explicit rate limits not evidenced | Per-user/IP/device quotas, bot controls and alerting | Burst, distributed and bypass tests |
| Replay attempt | Idempotency key not evidenced in inspected SQL | Unique idempotency keys, nonce/expiry and replay-safe RPCs | Re-submit and concurrent replay tests |
| Privilege abuse | SECURITY DEFINER functions exist; grants require review | Least privilege, fixed search path, execute-grant audit, secrets controls | Role matrix and privilege-escalation tests |
| SQL injection surface | Main transfer function uses parameterized arguments; broader paths need audit | Parameterized query review, input validation, exposed-RPC audit | SAST plus controlled injection tests |

## What can be said today

- SAI Bank has evidence of useful controls for selected internal transaction-integrity and wrong-payment-recovery scenarios.
- The repository review currently maps direct mitigation evidence to 3 of 12 predefined scenarios (25.0%), with 4 partial (33.3%) and 5 not evidenced (41.7%).
- The roadmap assigns a proposed control and validation plan to all 12 scenarios (12/12 planned; 100% planning coverage).
- No measured percentage of cyberattacks prevented can be claimed from this review.

## Release gates before claiming broad protection

1. Implement the proposed controls and remove or retire unsafe legacy money-movement paths.
2. Run repeatable integration, authorization, concurrency, replay, abuse and session tests.
3. Preserve test logs, environment versions, denominators, expected/actual outcomes and independent review.
4. Conduct an independent penetration test and remediate findings.
5. Publish attack-class-specific detection/prevention rates with confidence intervals only when supported by an appropriate test design.

**Recommended public wording:** “SAI Bank is being engineered toward defense-in-depth across 12 defined threat scenarios. Current repository evidence supports mitigation in 3 scenarios, partial controls in 4, and identifies 5 areas requiring additional controls. A complete roadmap assigns a proposed control and validation plan to all 12; prevention efficacy remains unmeasured pending implementation and testing.”
