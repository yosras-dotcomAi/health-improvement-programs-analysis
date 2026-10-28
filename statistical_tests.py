"""
Statistical tests for the Health Improvement Programs Analysis
--------------------------------------------------------------
Input : health_improvement_programs_data.csv  (SYNTHETIC data)
Output: statistical_results.csv, adjusted_results.csv, adherence_results.csv

1. Baseline balance: are the two groups similar before the program?
2. Change from baseline: Welch t-test, 95% confidence interval, Cohen's d.
3. 90-day readmission: chi-square test.
4. Adjusted analysis (ANCOVA): follow-up value compared between groups after
   adjusting for the baseline value and age.
5. Dose-response: among participants, does higher adherence go with
   greater improvement? (A real program would be expected to show this.)
"""

import numpy as np
import pandas as pd
from scipy import stats

DATA_FILE = "health_improvement_programs_data.csv"

df = pd.read_csv(DATA_FILE)
participants = df["program_participant"] == "Yes"

# ---------- 1. Baseline balance ----------
print("BASELINE BALANCE (participants vs non-participants)")
baseline_cols = ["age", "baseline_bmi", "baseline_systolic_bp",
                 "baseline_hba1c", "baseline_ldl"]
for col in baseline_cols:
    a, b = df.loc[participants, col], df.loc[~participants, col]
    _, p = stats.ttest_ind(a, b, equal_var=False)
    print(f"  {col:22s} {a.mean():7.2f} vs {b.mean():7.2f}   p = {p:.3f}")

# ---------- 2. Change from baseline ----------
metrics = {
    "BMI (kg/m2)": ("baseline_bmi", "followup_bmi"),
    "Systolic BP (mmHg)": ("baseline_systolic_bp", "followup_systolic_bp"),
    "HbA1c (%)": ("baseline_hba1c", "followup_hba1c"),
    "LDL Cholesterol (mg/dL)": ("baseline_ldl", "followup_ldl"),
}

rows = []
print("\nCHANGE FROM BASELINE (participants minus non-participants)")
for name, (base, follow) in metrics.items():
    change = df[follow] - df[base]
    a, b = change[participants], change[~participants]
    diff = a.mean() - b.mean()
    se = np.sqrt(a.var(ddof=1) / len(a) + b.var(ddof=1) / len(b))
    pooled_sd = np.sqrt((a.var(ddof=1) + b.var(ddof=1)) / 2)
    _, p = stats.ttest_ind(a, b, equal_var=False)
    rows.append({
        "Metric": name,
        "Difference": round(diff, 2),
        "CI_95_low": round(diff - 1.96 * se, 2),
        "CI_95_high": round(diff + 1.96 * se, 2),
        "Cohens_d": round(diff / pooled_sd, 2),
        "p_value": float(f"{p:.2g}"),
    })

results = pd.DataFrame(rows)
print(results.to_string(index=False))
results.to_csv("statistical_results.csv", index=False)

# ---------- 3. Readmission ----------
table = pd.crosstab(df["program_participant"], df["readmitted_90d"])
_, p_readmit, _, _ = stats.chi2_contingency(table)
print(f"\n90-DAY READMISSION: chi-square p = {p_readmit:.2g}")

# ---------- 4. Adjusted analysis (ANCOVA) ----------
# follow-up = intercept + group + baseline value + age
print("\nADJUSTED DIFFERENCE (ANCOVA: adjusted for baseline value and age)")
adj_rows = []
for name, (base, follow) in metrics.items():
    X = np.column_stack([
        np.ones(len(df)),
        participants.astype(float),
        df[base].to_numpy(),
        df["age"].to_numpy(),
    ])
    y = df[follow].to_numpy()
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    resid = y - X @ beta
    dof = len(y) - X.shape[1]
    cov = (resid @ resid / dof) * np.linalg.inv(X.T.dot(X))
    se = np.sqrt(cov[1, 1])
    p = 2 * stats.t.sf(abs(beta[1] / se), dof)
    adj_rows.append({
        "Metric": name,
        "Adjusted_difference": round(beta[1], 2),
        "CI_95_low": round(beta[1] - 1.96 * se, 2),
        "CI_95_high": round(beta[1] + 1.96 * se, 2),
        "p_value": float(f"{p:.2g}"),
    })

adjusted = pd.DataFrame(adj_rows)
print(adjusted.to_string(index=False))
adjusted.to_csv("adjusted_results.csv", index=False)

# ---------- 5. Adherence vs improvement (participants only) ----------
print("\nADHERENCE VS CHANGE (participants only, Pearson correlation)")
enrolled = df[participants]
dose_rows = []
for name, (base, follow) in metrics.items():
    change = enrolled[follow] - enrolled[base]
    r, p = stats.pearsonr(enrolled["program_adherence_pct"], change)
    dose_rows.append({"Metric": name, "Correlation_r": round(r, 2),
                      "p_value": round(p, 3)})
    print(f"  {name:25s} r = {r:5.2f}   p = {p:.3f}")

pd.DataFrame(dose_rows).to_csv("adherence_results.csv", index=False)
print("  Note: all four metrics are expected to fall, so a negative r means "
      "higher adherence goes with a bigger reduction.")

print("\nDone: statistical_results.csv, adjusted_results.csv and "
      "adherence_results.csv saved.")
