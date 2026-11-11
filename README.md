[README.md](https://github.com/user-attachments/files/34703823/README.md)
# Health Improvement Program (HIP) Impact Analysis

**Live dashboard:** _add your Streamlit link here_

An end-to-end analysis of whether a hospital health improvement program is associated with better clinical outcomes and fewer readmissions, built to show **why naive comparisons mislead** and how to correct for it.

> **Data note:** All data are **synthetic** (2,000 simulated patients, fixed random seed). The program effect and the selection bias are planted on purpose, so each method can be checked against the known truth. No real patient data is used.

## The question

Patients who join a program are rarely like those who don't. Healthier, more motivated patients tend to enrol, so a raw comparison flatters the program. This project quantifies that bias and shows how regression adjustment and propensity-score matching reduce it.

## What the analysis does

1. **Generates a cohort** with a planted true effect and a confounder (comorbidity score: healthier patients enrol more, sicker patients worsen on their own).
2. **Compares baseline characteristics** (Table 1) and standardised mean differences.
3. **Estimates the program effect three ways:** naive difference, covariate-adjusted regression (ANCOVA / logistic), and 1:1 propensity-score matching.
4. **Reports** 95% confidence intervals, Holm-corrected p-values across tests, and the share of the true effect each method recovers.
5. **Explores** dose-response (adherence vs improvement) and department differences in the dashboard.

## Results

Estimated program effect on change from baseline (planted true effect in the second column):

| Outcome | True | Naive | Adjusted | Matched |
|---|---|---|---|---|
| BMI (kg/m²) | -1.51 | -1.60 | -1.44 | -1.48 |
| Systolic BP (mmHg) | -8.08 | -9.41 | -8.25 | -8.16 |
| HbA1c (%) | -0.61 | -0.66 | -0.59 | -0.57 |
| LDL cholesterol (mg/dL) | -12.11 | -13.35 | -11.74 | -12.15 |
| 90-day readmission (odds ratio) | 0.40 | 0.29 | 0.39 | 0.44 |

![Naive vs adjusted](outputs/chart_naive_vs_adjusted.png)

**Reading the results:** the naive comparison overstates the benefit on every outcome, and the readmission odds ratio is the most distorted. Adjustment and matching move the estimates back towards the planted truth. Matching brings covariate balance to within ±0.1 standardised difference (see `outputs/chart_balance.png`).

## Limitations

- Synthetic data: this demonstrates method behaviour, not a real clinical effect.
- The generator contains one measured confounder. Real programs also have **unmeasured** confounders (motivation, social support) that adjustment cannot remove.
- Readmission has relatively few events among participants, so its confidence interval is wide.
- Associations here are not proof of causation. A real evaluation would need real data, a pre-specified plan and ideally a randomised or quasi-experimental design.

## Run it

```bash
pip install -r requirements.txt
python generate_data.py      # writes data/health_improvement_programs_data.csv
python analyze.py            # writes tables and charts to outputs/
streamlit run app.py         # launches the dashboard
pytest                       # runs the checks
```

## Repository structure

```
├── app.py                  # Streamlit dashboard
├── analysis.py             # statistics: naive, adjusted, matching, Holm
├── generate_data.py        # synthetic data with planted effect + confounder
├── analyze.py              # CLI: tables and charts
├── data/                   # generated CSV
├── outputs/                # summary tables and charts
├── tests/                  # pytest checks
└── requirements.txt
```

## Dashboard tabs

Overview (KPIs, baseline imbalance) · Outcomes (effects by method) · Bias Lab (change confounding strength and watch the bias move) · Adherence (dose-response) · Data (filter and download)

## Tools

Python · pandas · statsmodels · scikit-learn · SciPy · Plotly · Streamlit

## Author

**Yosra El Nagar**: Nursing Supervisor transitioning into Healthcare Data Analytics. [LinkedIn](https://www.linkedin.com/in/yosra-nagar-9a6862118/)

---

## 🇸🇦 عربي

### ملخص المشروع

تحليل بيقيس هل برنامج تحسين الصحة في المستشفى مرتبط بتحسّن المؤشرات الصحية (BMI، ضغط الدم، HbA1c، LDL) وانخفاض إعادة الدخول خلال 90 يوم.

**الفكرة الأساسية:** المرضى اللي بيشتركوا في البرنامج غالبًا أصحّ من غيرهم من البداية، فالمقارنة المباشرة بتضخّم أثر البرنامج. المشروع بيوضّح الانحياز ده وبيصحّحه بطريقتين: الانحدار المعدَّل (Adjusted regression) والمطابقة بدرجة الميل (Propensity-score matching).

> **ملاحظة:** البيانات كلها **وهمية (Synthetic)** والأثر الحقيقي متحدد مسبقًا، عشان نقدر نقيس أي طريقة بتقرّب أكتر من الحقيقة. مفيش بيانات مرضى حقيقية.

### التشغيل

```bash
pip install -r requirements.txt
python generate_data.py
python analyze.py
streamlit run app.py
```

### القيود

البيانات وهمية، وفي الواقع فيه عوامل مربكة غير مقاسة (زي الدافعية والدعم الاجتماعي) مش بتتصحّح بالتعديل الإحصائي. النتائج دي ارتباط مش إثبات سببية.
