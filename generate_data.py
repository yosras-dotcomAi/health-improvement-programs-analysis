"""Synthetic data generator for the Health Improvement Program (HIP) analysis.

The generator plants a KNOWN program effect and a realistic CONFOUNDER:
healthier (lower comorbidity) patients are more likely to enrol, and sicker
patients drift towards worse values anyway. A naive participant vs
non-participant comparison therefore overstates the benefit, which lets us
show how adjustment and matching recover the true effect.
"""
import numpy as np
import pandas as pd

TRUE_EFFECTS = {"bmi": -1.5, "sbp": -8.0, "hba1c": -0.6, "ldl": -12.0}  # change units
TRUE_READMIT_LOG_OR = -0.9  # odds ratio ~ 0.41 at reference adherence
DOSE_REF = 78.0             # adherence (%) at which the full effect applies
DEPARTMENTS = ["Cardiology", "Endocrinology", "Internal Medicine", "Family Medicine"]


def _sigmoid(x):
    return 1 / (1 + np.exp(-x))


def generate(n: int = 2000, seed: int = 42, selection_strength: float = 0.7,
             drift: float = 0.25) -> pd.DataFrame:
    """selection_strength: how strongly low severity predicts enrolment (0 = random).
    drift: how much sicker patients worsen on their own (0 = no confounding via outcomes)."""
    rng = np.random.default_rng(seed)
    age = np.clip(rng.normal(55, 12, n), 25, 90).round().astype(int)
    gender = rng.choice(["Female", "Male"], n)
    dept = rng.choice(DEPARTMENTS, n, p=[0.25, 0.25, 0.30, 0.20])
    severity = np.clip(rng.normal(0, 1, n) + (age - 55) / 25, -3, 4)  # comorbidity z-score

    base = {
        "bmi": np.clip(rng.normal(30 + 0.8 * severity, 4.5), 18, 50),
        "sbp": rng.normal(135 + 4 * severity, 14),
        "hba1c": np.clip(rng.normal(7.4 + 0.35 * severity, 1.0), 5, 13),
        "ldl": rng.normal(130 + 6 * severity, 25),
    }
    participant = rng.binomial(1, _sigmoid(-0.2 - selection_strength * severity))
    adherence = np.where(participant == 1, np.clip(rng.normal(78, 12, n), 30, 100), np.nan)
    dose = np.nan_to_num(adherence / DOSE_REF, nan=0.0)

    noise = {"bmi": 1.2, "sbp": 7.0, "hba1c": 0.4, "ldl": 10.0}
    natural = {"bmi": 0.3, "sbp": 1.0, "hba1c": 0.1, "ldl": 0.5}  # average natural drift
    scale = {"bmi": 1.0, "sbp": 6.0, "hba1c": 0.35, "ldl": 8.0}   # drift per severity unit
    data = {
        "patient_id": np.arange(1, n + 1), "age": age, "gender": gender,
        "department": dept, "comorbidity_score": severity.round(3),
        "participant": participant, "adherence_pct": adherence.round(1),
        "followup_months": rng.integers(6, 13, n),
    }
    for m in TRUE_EFFECTS:
        change = (TRUE_EFFECTS[m] * dose + natural[m] + drift * scale[m] * severity
                  + rng.normal(0, noise[m], n))
        data[f"{m}_baseline"] = base[m].round(2)
        data[f"{m}_followup"] = (base[m] + change).round(2)

    logit = -1.6 + 0.6 * severity + 0.01 * (age - 55) + TRUE_READMIT_LOG_OR * dose
    data["readmit_90d"] = rng.binomial(1, _sigmoid(logit))
    sat = np.clip(rng.normal(7.7, 1.2, n), 1, 10).round(1)
    data["satisfaction_score"] = np.where(participant == 1, sat, np.nan)
    return pd.DataFrame(data)


def true_effects(df: pd.DataFrame) -> dict:
    """Planted average effect among participants (scaled by their actual adherence)."""
    dose = (df.loc[df.participant == 1, "adherence_pct"] / DOSE_REF).mean()
    out = {m: v * dose for m, v in TRUE_EFFECTS.items()}
    out["readmit"] = float(np.exp(TRUE_READMIT_LOG_OR * dose))  # odds ratio
    return out


if __name__ == "__main__":
    df = generate(n=2000)
    df.to_csv("data/health_improvement_programs_data.csv", index=False)
    print(f"Saved {len(df)} synthetic patients "
          f"({int(df.participant.sum())} participants) to data/")
