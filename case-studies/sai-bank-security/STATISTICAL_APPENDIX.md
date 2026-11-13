# Statistical Appendix — SAI Bank Synthetic Transfer Study

**Dataset seed:** 20261113  
**Observation window:** 1 January–31 December 2025 (synthetic timestamps)  
**Population:** 40,000 generated transfers across 2,500 fictional account identifiers  
**Evidence class:** Reproducible synthetic simulation; not production banking telemetry.

## 1. Dataset integrity and label prevalence

| Measure | Result |
|---|---:|
| Generated transfers | 40,000 |
| Normal-labelled transfers | 37,597 |
| Suspicious-labelled transfers | 2,403 |
| Suspicious-label share | 6.0075% |
| Wilson 95% interval for generated-label share | 5.78%–6.24% |
| Unique synthetic account identifiers | 2,500 |
| Total simulated transfer notional | ₹7,27,94,601.54 |
| Suspicious-labelled notional | ₹43,92,674.92 (₹43.93 lakh) |

The Wilson interval describes sampling variation around the generator's planted-label proportion in this synthetic sample. It is **not** a confidence interval for real-world fraud prevalence. The suspicious label is assigned by the generator; it is not a confirmed incident.

## 2. Transaction amount distribution

| Statistic | All transfers | Suspicious-labelled transfers |
|---|---:|---:|
| Mean | ₹1,819.87 | ₹1,828.00 |
| Median (P50) | ₹1,094.48 | ₹1,145.73 |
| P90 | ₹4,001.65 | ₹3,952.12 |
| P95 | ₹5,715.43 | ₹5,460.76 |
| P99 | ₹11,251.88 | ₹11,885.89 |
| Maximum | ₹72,907.36 | ₹28,210.72 |

The distribution is right-skewed by construction (log-normal amounts with clipping). Percentiles describe the generated sample only.

## 3. Planted suspicious-label composition

| Generator label | Events | Share of all transfers | Share of suspicious-labelled events |
|---|---:|---:|---:|
| Wrong recipient | 731 | 1.828% | 30.42% |
| Stolen session | 473 | 1.182% | 19.68% |
| Rapid mule outflow | 360 | 0.900% | 14.98% |
| Account takeover | 328 | 0.820% | 13.65% |
| Replay attempt | 286 | 0.715% | 11.90% |
| Privilege abuse | 225 | 0.562% | 9.36% |

These are mutually exclusive synthetic generator labels. In particular, “wrong recipient” may represent user error and must not automatically be counted as malicious fraud.

## 4. Temporal variability

The generated timestamps span 12 synthetic calendar months. Monthly transfer volume has a mean of 3,333.3, standard deviation of 111.9, minimum of 3,071 and maximum of 3,495. Monthly suspicious-label share ranges from 5.13% to 6.42%.

The generator samples timestamps uniformly over a year. Therefore, this monthly pattern is a simulation artifact, not evidence of seasonality, operational load or a real-world trend.

## 5. Sender concentration diagnostic

Using total outgoing notional per synthetic sender identifier:

| Concentration measure | Result |
|---|---:|
| Top 1 sender share of total notional | 0.149% |
| Top 10 senders share | 1.168% |
| Top 25 senders share | 2.609% |
| HHI (10,000-point scale) | 4.70 |

This low concentration is a property of the synthetic account/amount generator. It is not a calibrated mule-account or customer-concentration benchmark. HHI is included as a descriptive diagnostic, not a fraud score.

## 6. Control coverage (repository review, not statistical efficacy)

The 12-scenario qualitative review currently maps 3 scenarios as mitigated (25.0%), 4 as partial/review required (33.3%) and 5 as having no specific control evidenced in the inspected application code (41.7%). These proportions summarize the reviewer's classification of a small, predefined scenario set. They are not probabilities, attack-block rates or an independently validated security score.

## 7. Test evidence and reporting guardrails

The seven rows in `synthetic_control_tests.csv` are deterministic fixtures with assumed outcomes. They do not represent 7,000 executed requests, live penetration tests or observed pass rates. No precision, recall, ROC-AUC, false-positive rate, detection latency, recovery success rate or loss-prevention KPI is reported because there is no labelled real-world test set or executed system-test telemetry supporting those metrics.

To publish operational KPIs, collect controlled test runs with run IDs, software/database versions, timestamps, input cases, expected and actual outcomes, raw logs, denominators and reproducible scripts. Report confidence intervals only when the sampling design supports them.

## 8. Reproduction

From the repository root:

```bash
python -m pip install -r case-studies/sai-bank-security/requirements.txt
python case-studies/sai-bank-security/src/generate_data.py
python case-studies/sai-bank-security/src/analyze.py
python case-studies/sai-bank-security/src/advanced_analysis.py
python case-studies/sai-bank-security/src/render_svg_charts.py
```

`advanced_analysis.py` exports `results/advanced_metrics.json`, `results/advanced_monthly_statistics.csv` and `results/advanced_scenario_statistics.csv`. Regenerate the data and results after changing the seed, generator probabilities or amount distribution.
