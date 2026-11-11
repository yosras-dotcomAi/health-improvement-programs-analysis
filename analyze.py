"""Statistical analysis: naive vs covariate-adjusted vs propensity-matched effects."""
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from scipy import stats
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from statsmodels.stats.multitest import multipletests

import generate_data as gd

METRICS = {"bmi": "BMI (kg/m²)", "sbp": "Systolic BP (mmHg)",
           "hba1c": "HbA1c (%)", "ldl": "LDL cholesterol (mg/dL)"}
COVARS = "age + C(gender) + C(department) + comorbidity_score"


def load_data(path) -> pd.DataFrame:
    df = pd.read_csv(path)
    for m in METRICS:
        df[f"{m}_change"] = df[f"{m}_followup"] - df[f"{m}_baseline"]
    return df


def add_changes(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for m in METRICS:
        df[f"{m}_change"] = df[f"{m}_followup"] - df[f"{m}_baseline"]
    return df


def _ols(df, y, extra=""):
    f = f"{y} ~ participant" + (f" + {extra}" if extra else "")
    r = smf.ols(f, df).fit(cov_type="HC3")
    lo, hi = r.conf_int().loc["participant"]
    return r.params["participant"], lo, hi, r.pvalues["participant"]


def _logit(df, extra=""):
    f = "readmit_90d ~ participant" + (f" + {extra}" if extra else "")
    r = smf.logit(f, df).fit(disp=0)
    lo, hi = r.conf_int().loc["participant"]
    return float(np.exp(r.params["participant"])), float(np.exp(lo)), float(np.exp(hi)), r.pvalues["participant"]


def propensity_match(df, caliper_sd=0.2, seed=42):
    """1:1 nearest-neighbour matching on the propensity score, without replacement."""
    X = pd.get_dummies(df[["age", "gender", "department", "comorbidity_score"]],
                       drop_first=True).astype(float)
    Xs = StandardScaler().fit_transform(X)
    ps = LogisticRegression(max_iter=1000).fit(Xs, df.participant).predict_proba(Xs)[:, 1]
    ps = np.clip(ps, 1e-4, 1 - 1e-4)
    logit = np.log(ps / (1 - ps))
    caliper = caliper_sd * logit.std()
    rng = np.random.default_rng(seed)
    treated = rng.permutation(np.where(df.participant.values == 1)[0])
    pool = list(np.where(df.participant.values == 0)[0])
    pairs = []
    for t in treated:
        if not pool:
            break
        d = np.abs(logit[pool] - logit[t])
        j = int(np.argmin(d))
        if d[j] <= caliper:
            pairs += [t, pool.pop(j)]
    return df.iloc[pairs].copy(), X


def smd_table(before, matched, X):
    """Standardised mean differences (participants - non-participants) before/after matching."""
    rows = []
    for name in X.columns:
        def smd(d):
            xs = X.loc[d.index, name]
            a, b = xs[d.participant == 1], xs[d.participant == 0]
            sd = np.sqrt((a.var() + b.var()) / 2)
            return (a.mean() - b.mean()) / sd if sd > 0 else 0.0
        rows.append({"covariate": name, "before": smd(before), "after": smd(matched)})
    return pd.DataFrame(rows)


def run_all(df: pd.DataFrame) -> dict:
    df = df.reset_index(drop=True)
    if "bmi_change" not in df:
        df = add_changes(df)
    matched, X = propensity_match(df)
    truth = gd.true_effects(df)
    rows = []
    for m, label in METRICS.items():
        y = f"{m}_change"
        for method, d, extra in [("Naive", df, ""),
                                 ("Adjusted", df, f"{COVARS} + {m}_baseline"),
                                 ("Matched", matched, "")]:
            est, lo, hi, p = _ols(d, y, extra)
            rows.append(dict(outcome=label, key=m, method=method, estimate=est,
                             lo=lo, hi=hi, p=p, true=truth[m]))
    for method, d, extra in [("Naive", df, ""),
                             ("Adjusted", df, f"{COVARS} + bmi_baseline + sbp_baseline"),
                             ("Matched", matched, "")]:
        est, lo, hi, p = _logit(d, extra)
        rows.append(dict(outcome="90-day readmission (odds ratio)", key="readmit",
                         method=method, estimate=est, lo=lo, hi=hi, p=p, true=truth["readmit"]))
    eff = pd.DataFrame(rows)
    # share of the true effect recovered (100% = unbiased)
    cont = eff.key != "readmit"
    eff["pct_of_true"] = eff.estimate / eff.true * 100
    eff.loc[~cont, "pct_of_true"] = (np.log(eff.loc[~cont, "estimate"])
                                     / np.log(eff.loc[~cont, "true"]) * 100)
    # Holm correction across the 5 adjusted tests
    adj = eff.method == "Adjusted"
    eff["p_holm"] = np.nan
    eff.loc[adj, "p_holm"] = multipletests(eff.loc[adj, "p"], method="holm")[1]
    return dict(effects=eff, matched=matched, smd=smd_table(df, matched, X),
                table1=table1(df), readmit=readmit_rates(df), data=df)


def table1(df):
    g = df.groupby("participant")
    out = pd.DataFrame({
        "Non-participants": [f"{df[df.participant==0].age.mean():.1f}",
                             f"{(df[df.participant==0].gender=='Female').mean()*100:.0f}%",
                             f"{df[df.participant==0].comorbidity_score.mean():.2f}"],
        "Participants": [f"{df[df.participant==1].age.mean():.1f}",
                         f"{(df[df.participant==1].gender=='Female').mean()*100:.0f}%",
                         f"{df[df.participant==1].comorbidity_score.mean():.2f}"]},
        index=["Mean age (years)", "Female (%)", "Mean comorbidity score"])
    for m, label in METRICS.items():
        means = g[f"{m}_baseline"].mean()
        out.loc[f"Baseline {label}"] = [f"{means.loc[0]:.2f}", f"{means.loc[1]:.2f}"]
    out.loc["n"] = [str(int((df.participant == 0).sum())), str(int((df.participant == 1).sum()))]
    return out


def readmit_rates(df):
    r = df.groupby("participant").readmit_90d.agg(["mean", "sum", "count"])
    tab = pd.crosstab(df.participant, df.readmit_90d)
    p = stats.fisher_exact(tab.values)[1] if tab.shape == (2, 2) else np.nan
    return dict(rate_part=r.loc[1, "mean"], rate_non=r.loc[0, "mean"], fisher_p=p)
