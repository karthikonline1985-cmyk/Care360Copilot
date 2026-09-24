---
name: care360-patient-summary
description: "Return a structured Patient 360 summary from Care360 governed data. Use when: patient summary, patient 360, patient overview, show patient details, summarize patient. Triggers: patient summary, patient 360, summarize patient, show patient, patient overview."
---

# Care360 Patient Summary

Returns a concise, structured Patient 360 summary for a given patient_id using governed Care360 curated views. All data is synthetic.

## Input

- **patient_id** (required): e.g. `P-0001`. Passed by the user or extracted from context.

## Workflow

### Step 1: Query patient data

Run both queries in parallel:

```sql
SELECT * FROM CARE360_DB.CURATED.PATIENT_360_SUMMARY WHERE PATIENT_ID = '<patient_id>';
```

```sql
SELECT * FROM CARE360_DB.CURATED.PATIENT_RISK_SCORES WHERE PATIENT_ID = '<patient_id>';
```

If either returns **zero rows**, respond:

> No patient found with ID `<patient_id>`. Please verify the ID and try again. Valid IDs follow the pattern `P-NNNN` (e.g. P-0001).

Then stop.

### Step 2: Format the summary

Use the query results to produce this exact structure (replace values from query results; use "N/A" for NULL/missing values):

```
## Patient 360 Summary — <PATIENT_NAME> (<PATIENT_ID>)

> All data is synthetic. This is not a real patient record.

**Demographics:** Age <AGE>, <GENDER>, <INSURANCE_TYPE>
**Latest encounter:** <LATEST_ENCOUNTER_DATE>

| Metric | Value |
|--------|-------|
| Encounters | <ENCOUNTER_COUNT> |
| Active medications | <ACTIVE_MED_COUNT> |
| Diagnoses | <DIAGNOSIS_COUNT> |
| Latest HbA1c | <LATEST_HBA1C or N/A> |
| Latest creatinine | <LATEST_CREATININE or N/A> |
| ER visits (90 days) | <ER_VISITS_LAST_90D> |

### Risk Stratification
**Score:** <RISK_SCORE> / 6 — **<RISK_TIER>**

**Triggered rules:** <RISK_EXPLANATION or "None">

> Risk score is deterministic and rule-based. No ML predictions are used.
```

### Step 3: Return the summary

Output the formatted summary directly. Do not add commentary beyond the template.

## Data Sources

| Object | Purpose |
|--------|---------|
| `CARE360_DB.CURATED.PATIENT_360_SUMMARY` | Demographics, encounter/med/dx counts, latest labs |
| `CARE360_DB.CURATED.PATIENT_RISK_SCORES` | Risk flags, score, tier, human-readable explanation |
