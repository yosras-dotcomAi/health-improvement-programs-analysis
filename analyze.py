"""
Health Improvement Programs Analysis
------------------------------------
Compares clinical outcomes between patients who joined a Health Improvement
Program (HIP) and those who did not, using a SYNTHETIC dataset (no real
patient data).

Input : health_improvement_programs_data.csv
Output: summary_results.csv, chart_metrics_comparison.png,
        chart_readmission_rate.png, chart_bmi_trajectory.png
"""

import pandas as pd
import matplotlib.pyplot as plt

DATA_FILE = "health_improvement_programs_data.csv"

METRICS = {
    "BMI (kg/m2)": ("baseline_bmi", "followup_bmi"),
    "Systolic BP (mmHg)": ("baseline_systolic_bp", "followup_systolic_bp"),
    "HbA1c (%)": ("baseline_hba1c", "followup_hba1c"),
    "LDL Cholesterol (mg/dL)": ("baseline_ldl", "followup_ldl"),
}

# ---------- 1. Load ----------
df = pd.read_csv(DATA_FILE)
df["group"] = df["program_participant"].map({"Yes": "Participants", "No": "Non-Participants"})

# ---------- 2. Change from baseline to follow-up ----------
for name, (base, follow) in METRICS.items():
    df[f"change_{base}"] = df[follow] - df[base]

rows = []
for name, (base, follow) in METRICS.items():
    change = df.groupby("group")[f"change_{base}"].mean()
    rows.append({
        "Metric": name,
        "Participants": round(change["Participants"], 2),
        "Non-Participants": round(change["Non-Participants"], 2),
        "Difference": round(change["Participants"] - change["Non-Participants"], 2),
    })

summary = pd.DataFrame(rows)
summary.to_csv("summary_results.csv", index=False)
print(summary.to_string(index=False))

# ---------- 3. Readmission, adherence, satisfaction ----------
readmit = df.groupby("group")["readmitted_90d"].mean() * 100
print(f"\n90-day readmission: Participants {readmit['Participants']:.1f}% | "
      f"Non-Participants {readmit['Non-Participants']:.1f}% | "
      f"Gap {readmit['Non-Participants'] - readmit['Participants']:.1f} points")

participants = df[df["group"] == "Participants"]
print(f"Average adherence: {participants['program_adherence_pct'].mean():.1f}%")
print(f"Average satisfaction: {participants['satisfaction_score_10'].mean():.1f} / 10")

# ---------- 4. Charts ----------
colors = {"Participants": "#2a9d8f", "Non-Participants": "#b0b0b0"}

# Chart 1: change in each metric
fig, axes = plt.subplots(1, 4, figsize=(14, 4))
for ax, (name, (base, _)) in zip(axes, METRICS.items()):
    vals = df.groupby("group")[f"change_{base}"].mean()
    ax.bar(vals.index, vals.values, color=[colors[g] for g in vals.index])
    ax.set_title(name, fontsize=10)
    ax.axhline(0, color="black", linewidth=0.8)
    ax.tick_params(axis="x", labelrotation=15)
fig.suptitle("Average Change from Baseline to Follow-up")
plt.tight_layout()
plt.savefig("chart_metrics_comparison.png", dpi=150)
plt.close()

# Chart 2: readmission rate
fig, ax = plt.subplots(figsize=(5, 4))
order = ["Participants", "Non-Participants"]
ax.bar(order, [readmit[g] for g in order], color=[colors[g] for g in order])
for i, g in enumerate(order):
    ax.text(i, readmit[g] + 0.5, f"{readmit[g]:.1f}%", ha="center")
ax.set_ylabel("Readmission rate (%)")
ax.set_title("90-Day Readmission Rate")
plt.tight_layout()
plt.savefig("chart_readmission_rate.png", dpi=150)
plt.close()

# Chart 3: BMI baseline vs follow-up
fig, ax = plt.subplots(figsize=(5, 4))
for g in order:
    sub = df[df["group"] == g]
    ax.plot(["Baseline", "Follow-up"],
            [sub["baseline_bmi"].mean(), sub["followup_bmi"].mean()],
            marker="o", label=g, color=colors[g])
ax.set_ylabel("Mean BMI (kg/m2)")
ax.set_title("BMI Trajectory")
ax.legend()
plt.tight_layout()
plt.savefig("chart_bmi_trajectory.png", dpi=150)
plt.close()

print("\nDone: summary_results.csv and 3 charts saved.")
