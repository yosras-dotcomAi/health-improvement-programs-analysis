"""
Synthetic data generator for the Health Improvement Programs Analysis
---------------------------------------------------------------------
Creates 500 SIMULATED patient records (no real patient data) and saves them to
health_improvement_programs_data.csv.

Design assumptions (all invented for demonstration):
  - 260 program participants, 240 non-participants, similar at baseline.
  - Program effect is MODEST and grows with adherence (dose-response):
    at average adherence, roughly -0.7 BMI, -4 mmHg SBP, -0.4 HbA1c, -8 LDL.
  - Both groups have natural drift and regression to the mean.
  - Patient-level noise is large, as in real clinical data.
  - 90-day readmission risk depends on age and HbA1c, and is lowered by
    program adherence.

Change SEED to create a different random dataset.
"""

import numpy as np
import pandas as pd

SEED = 42
N_PARTICIPANTS = 260
N_CONTROLS = 240

rng = np.random.default_rng(SEED)
n = N_PARTICIPANTS + N_CONTROLS

# ---------- Patient characteristics ----------
program = np.array(["Yes"] * N_PARTICIPANTS + ["No"] * N_CONTROLS)
is_participant = program == "Yes"

age = np.clip(rng.normal(54, 12, n).round(), 22, 88).astype(int)
gender = rng.choice(["Male", "Female"], n)
department = rng.choice(
    ["Cardiology", "Endocrinology", "Internal Medicine", "Family Medicine"],
    n, p=[0.32, 0.24, 0.22, 0.22],
)

# ---------- Baseline measurements ----------
baseline_bmi = np.clip(rng.normal(31.5, 5.0, n), 19, 45)
baseline_sbp = np.clip(rng.normal(137, 14, n), 102, 175)
baseline_hba1c = np.clip(rng.normal(7.4, 1.1, n), 5.0, 10.5)
baseline_ldl = np.clip(rng.normal(135, 28, n), 70, 210)

# ---------- Program participation ----------
months_enrolled = np.where(is_participant, rng.integers(6, 13, n), 0)
adherence = np.where(
    is_participant, np.clip(rng.normal(70, 22, n), 20, 100).round(), np.nan
)
adherence_frac = np.nan_to_num(adherence / 100.0)       # 0 for non-participants
exposure = adherence_frac                               # 0 to 1

# ---------- Follow-up: drift + regression to the mean + program effect + noise
def follow_up(baseline, drift, regression, effect, noise_sd, lo, hi):
    change = (drift
              - regression * (baseline - baseline.mean())
              + effect * exposure
              + rng.normal(0, noise_sd, n))
    return np.clip(baseline + change, lo, hi)

followup_bmi = follow_up(baseline_bmi, 0.15, 0.05, -1.0, 1.2, 17, 50)
followup_sbp = follow_up(baseline_sbp, 1.0, 0.15, -5.7, 11.0, 95, 185)
followup_hba1c = follow_up(baseline_hba1c, 0.08, 0.10, -0.57, 0.55, 4.8, 12)
followup_ldl = follow_up(baseline_ldl, 1.0, 0.10, -11.4, 20.0, 55, 230)

# ---------- Satisfaction (participants only, loosely tied to adherence) ----
satisfaction = np.where(
    is_participant,
    np.clip((adherence_frac * 4 + 4.5 + rng.normal(0, 1.2, n)).round(), 1, 10),
    np.nan,
)

# ---------- 90-day readmission (logistic model) ----------
logit = (-2.0
         + 0.02 * (age - 54)
         + 0.35 * (baseline_hba1c - 7.4)
         - 1.2 * adherence_frac)
prob = 1 / (1 + np.exp(-logit))
readmitted = (rng.random(n) < prob).astype(int)

# ---------- Assemble and save ----------
df = pd.DataFrame({
    "patient_id": [f"P{1000 + i}" for i in range(n)],
    "age": age,
    "gender": gender,
    "department": department,
    "program_participant": program,
    "months_enrolled": months_enrolled,
    "baseline_bmi": baseline_bmi.round(1),
    "followup_bmi": followup_bmi.round(1),
    "baseline_systolic_bp": baseline_sbp.round(0),
    "followup_systolic_bp": followup_sbp.round(0),
    "baseline_hba1c": baseline_hba1c.round(1),
    "followup_hba1c": followup_hba1c.round(1),
    "baseline_ldl": baseline_ldl.round(0),
    "followup_ldl": followup_ldl.round(0),
    "program_adherence_pct": adherence,
    "satisfaction_score_10": satisfaction,
    "readmitted_90d": readmitted,
})

df = df.sample(frac=1, random_state=SEED).reset_index(drop=True)
df.to_csv("health_improvement_programs_data.csv", index=False)
print(f"Saved {len(df)} synthetic patients to health_improvement_programs_data.csv")
