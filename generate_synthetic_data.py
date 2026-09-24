"""
Care360 Copilot — Synthetic Data Generator
Generates CSV files for 25 patients with 3 curated demo scenarios.
All data is fully synthetic — no real PHI.
"""

import csv
import os
import random
from datetime import date, timedelta

random.seed(42)
OUT_DIR = "/workspace/care360_csv"
os.makedirs(OUT_DIR, exist_ok=True)

# ── Reference lists ──────────────────────────────────────────────

FIRST_NAMES_F = ["Maria", "Linda", "Susan", "Patricia", "Barbara", "Jennifer", "Lisa", "Nancy", "Karen", "Sarah", "Emily", "Jessica", "Anna"]
FIRST_NAMES_M = ["James", "Robert", "Michael", "William", "David", "Richard", "Joseph", "Thomas", "Daniel", "Mark", "Charles", "Steven"]
LAST_NAMES = ["Garcia", "Smith", "Johnson", "Williams", "Brown", "Jones", "Davis", "Martinez", "Wilson", "Anderson",
              "Taylor", "Thomas", "Moore", "Jackson", "Martin", "Lee", "Harris", "Clark", "Lewis", "Robinson",
              "Walker", "Young", "Allen", "King", "Wright"]
STATES = ["CA", "TX", "NY", "FL", "IL", "PA", "OH", "MI", "GA", "NC"]
RACES = ["White", "Black", "Asian", "Hispanic", "Native American", "Pacific Islander", "Two or More"]
INSURANCE_TYPES = ["Medicare", "Medicaid", "Commercial", "Commercial", "Medicare"]  # weighted
FACILITIES = ["Mercy General Hospital", "St. Luke's Medical Center", "Valley Health Clinic", "Metro Community Hospital"]
PROVIDERS = ["Dr. Chen", "Dr. Patel", "Dr. Okonkwo", "Dr. Rivera", "Dr. Thompson", "Dr. Kim", "NP Simmons", "NP Blake"]

DIAGNOSIS_CATALOG = [
    ("E11.9",  "Type 2 diabetes mellitus without complications", "Chronic"),
    ("E11.65", "Type 2 diabetes mellitus with hyperglycemia", "Chronic"),
    ("I50.9",  "Heart failure, unspecified", "Chronic"),
    ("I10",    "Essential hypertension", "Chronic"),
    ("J44.1",  "COPD with acute exacerbation", "Active"),
    ("N18.3",  "Chronic kidney disease, stage 3", "Chronic"),
    ("N18.4",  "Chronic kidney disease, stage 4", "Chronic"),
    ("F32.1",  "Major depressive disorder, moderate", "Active"),
    ("M17.11", "Primary osteoarthritis, right knee", "Chronic"),
    ("E78.5",  "Dyslipidemia, unspecified", "Chronic"),
    ("J18.9",  "Pneumonia, unspecified organism", "Active"),
    ("I25.10", "Coronary artery disease", "Chronic"),
    ("E03.9",  "Hypothyroidism, unspecified", "Chronic"),
    ("G47.33", "Obstructive sleep apnea", "Chronic"),
    ("K21.0",  "GERD with esophagitis", "Active"),
    ("M54.5",  "Low back pain", "Active"),
    ("J45.20", "Mild intermittent asthma, uncomplicated", "Chronic"),
    ("I48.91", "Atrial fibrillation, unspecified", "Chronic"),
    ("D64.9",  "Anemia, unspecified", "Active"),
    ("R51.9",  "Headache, unspecified", "Active"),
]

MEDICATION_CATALOG = [
    ("Metformin",       "00378-7252-01", "1000mg", "Twice daily",  "Oral"),
    ("Lisinopril",      "00378-2115-01", "20mg",   "Once daily",   "Oral"),
    ("Atorvastatin",    "00378-3953-01", "40mg",   "Once daily",   "Oral"),
    ("Amlodipine",      "00378-0097-01", "10mg",   "Once daily",   "Oral"),
    ("Omeprazole",      "00378-6150-01", "20mg",   "Once daily",   "Oral"),
    ("Levothyroxine",   "00378-1800-01", "75mcg",  "Once daily",   "Oral"),
    ("Furosemide",      "00378-0206-01", "40mg",   "Twice daily",  "Oral"),
    ("Insulin Glargine","00088-5020-01", "30 units","Once daily",   "Subcutaneous"),
    ("Carvedilol",      "00378-3635-01", "25mg",   "Twice daily",  "Oral"),
    ("Sertraline",      "00378-4187-01", "100mg",  "Once daily",   "Oral"),
    ("Gabapentin",      "00378-4011-01", "300mg",  "Three times daily","Oral"),
    ("Ibuprofen",       "00904-5852-60", "400mg",  "Three times daily","Oral"),
    ("Prednisone",      "00378-0542-01", "10mg",   "Once daily",   "Oral"),
    ("Albuterol",       "00173-0682-20", "2 puffs","As needed",    "Inhalation"),
    ("Warfarin",        "00378-2074-01", "5mg",    "Once daily",   "Oral"),
    ("Hydrochlorothiazide","00378-0241-01","25mg", "Once daily",   "Oral"),
    ("Clopidogrel",     "00378-5200-01", "75mg",   "Once daily",   "Oral"),
    ("Apixaban",        "00003-0894-21", "5mg",    "Twice daily",  "Oral"),
    ("Duloxetine",      "00002-3237-60", "60mg",   "Once daily",   "Oral"),
    ("Acetaminophen",   "00904-1982-60", "500mg",  "Every 6 hours","Oral"),
]

LAB_CATALOG = [
    # (test_name, loinc, unit, ref_low, ref_high)
    ("HbA1c",          "4548-4",  "%",       4.0,   5.6),
    ("Creatinine",     "2160-0",  "mg/dL",   0.6,   1.2),
    ("eGFR",           "33914-3", "mL/min",  60.0, 120.0),
    ("BNP",            "42637-9", "pg/mL",    0.0, 100.0),
    ("Total Cholesterol","2093-3","mg/dL",  125.0, 200.0),
    ("LDL",            "2089-1",  "mg/dL",    0.0, 100.0),
    ("HDL",            "2085-9",  "mg/dL",   40.0,  60.0),
    ("Triglycerides",  "2571-8",  "mg/dL",    0.0, 150.0),
    ("WBC",            "6690-2",  "K/uL",     4.5,  11.0),
    ("Hemoglobin",     "718-7",   "g/dL",    12.0,  17.5),
    ("Platelet Count", "777-3",   "K/uL",   150.0, 400.0),
    ("Sodium",         "2951-2",  "mEq/L",  136.0, 145.0),
    ("Potassium",      "2823-3",  "mEq/L",    3.5,   5.0),
    ("Glucose (Fasting)","1558-6","mg/dL",   70.0, 100.0),
    ("TSH",            "3016-3",  "mIU/L",    0.4,   4.0),
    ("ALT",            "1742-6",  "U/L",      7.0,  56.0),
]

PROCEDURE_CATALOG = [
    ("99213", "Office visit, established, low complexity",        85.0,  150.0),
    ("99214", "Office visit, established, moderate complexity",  120.0,  250.0),
    ("99283", "ED visit, moderate severity",                     250.0,  600.0),
    ("99285", "ED visit, high severity",                         500.0, 1200.0),
    ("99222", "Initial hospital care, moderate complexity",      400.0,  900.0),
    ("99232", "Subsequent hospital care, moderate complexity",   200.0,  500.0),
    ("99024", "Postoperative follow-up",                          0.0,    0.0),
    ("85025", "CBC with differential",                           15.0,   45.0),
    ("80053", "Comprehensive metabolic panel",                   20.0,   60.0),
    ("71046", "Chest X-ray, 2 views",                            50.0,  150.0),
    ("93000", "Electrocardiogram (ECG)",                         30.0,  100.0),
    ("99441", "Telephone E/M, 5-10 min",                         40.0,   80.0),
]

ENCOUNTER_TYPES = ["Outpatient", "Inpatient", "ER", "Telehealth"]
COMPLAINTS = {
    "Outpatient": ["Routine follow-up", "Medication refill", "Lab review", "Chronic disease management", "Annual wellness visit"],
    "Inpatient":  ["Chest pain", "Shortness of breath", "Pneumonia", "CHF exacerbation", "Acute kidney injury"],
    "ER":         ["Chest pain", "Fall injury", "Severe headache", "Abdominal pain", "Shortness of breath", "Laceration"],
    "Telehealth": ["Medication review", "Follow-up", "Mental health check-in", "Lab result review"],
}


# ── Helper functions ─────────────────────────────────────────────

def rand_date(start: date, end: date) -> date:
    delta = (end - start).days
    return start + timedelta(days=random.randint(0, max(delta, 1)))

def fmt(d: date) -> str:
    return d.strftime("%Y-%m-%d")

TODAY = date(2026, 9, 24)
ID_COUNTERS = {"enc": 0, "dx": 0, "med": 0, "lab": 0, "clm": 0}

def next_id(prefix: str) -> str:
    ID_COUNTERS[prefix] += 1
    return f"{prefix.upper()}-{ID_COUNTERS[prefix]:05d}"


# ── Build patients ───────────────────────────────────────────────

patients = []
encounters_all = []
diagnoses_all = []
medications_all = []
labs_all = []
claims_all = []


def make_patient(pid: str, first: str, last: str, dob: date, gender: str, insurance: str, state: str = None):
    return {
        "PATIENT_ID": pid,
        "FIRST_NAME": first,
        "LAST_NAME": last,
        "DATE_OF_BIRTH": fmt(dob),
        "GENDER": gender,
        "RACE": random.choice(RACES),
        "ETHNICITY": random.choice(["Hispanic or Latino", "Not Hispanic or Latino", "Not Hispanic or Latino"]),
        "ZIP_CODE": f"{random.randint(10000, 99999)}",
        "STATE": state or random.choice(STATES),
        "INSURANCE_TYPE": insurance,
        "PRIMARY_LANGUAGE": random.choice(["English", "English", "English", "Spanish", "Mandarin"]),
    }


def add_encounter(patient_id: str, enc_date: date, enc_type: str, complaint: str = None):
    eid = next_id("enc")
    discharge = enc_date + timedelta(days=random.randint(1, 5)) if enc_type == "Inpatient" else enc_date
    enc = {
        "ENCOUNTER_ID": eid,
        "PATIENT_ID": patient_id,
        "ENCOUNTER_DATE": fmt(enc_date),
        "ENCOUNTER_TYPE": enc_type,
        "PROVIDER_NAME": random.choice(PROVIDERS),
        "FACILITY_NAME": random.choice(FACILITIES),
        "DISCHARGE_DATE": fmt(discharge) if enc_type in ("Inpatient", "ER") else "",
        "CHIEF_COMPLAINT": complaint or random.choice(COMPLAINTS[enc_type]),
    }
    encounters_all.append(enc)
    return eid


def add_diagnosis(patient_id: str, encounter_id: str, dx_tuple: tuple, is_primary: bool, dx_date: date, status: str = None):
    did = next_id("dx")
    diagnoses_all.append({
        "DIAGNOSIS_ID": did,
        "ENCOUNTER_ID": encounter_id,
        "PATIENT_ID": patient_id,
        "ICD10_CODE": dx_tuple[0],
        "DESCRIPTION": dx_tuple[1],
        "IS_PRIMARY": str(is_primary),
        "DIAGNOSED_DATE": fmt(dx_date),
        "STATUS": status or dx_tuple[2],
    })
    return did


def add_medication(patient_id: str, med_tuple: tuple, start: date, end: date = None, prescriber: str = None):
    mid = next_id("med")
    medications_all.append({
        "MEDICATION_ID": mid,
        "PATIENT_ID": patient_id,
        "DRUG_NAME": med_tuple[0],
        "NDC_CODE": med_tuple[1],
        "DOSAGE": med_tuple[2],
        "FREQUENCY": med_tuple[3],
        "ROUTE": med_tuple[4],
        "PRESCRIBER": prescriber or random.choice(PROVIDERS),
        "START_DATE": fmt(start),
        "END_DATE": fmt(end) if end else "",
        "IS_ACTIVE": str(end is None),
    })
    return mid


def add_lab(patient_id: str, encounter_id: str, lab_tuple: tuple, collected: date, value: float = None):
    lid = next_id("lab")
    test_name, loinc, unit, ref_low, ref_high = lab_tuple
    if value is None:
        value = round(random.uniform(ref_low * 0.7, ref_high * 1.3), 1)
    abnormal = ""
    if value > ref_high:
        abnormal = "HH" if value > ref_high * 1.5 else "H"
    elif value < ref_low:
        abnormal = "LL" if value < ref_low * 0.5 else "L"
    labs_all.append({
        "LAB_ID": lid,
        "PATIENT_ID": patient_id,
        "ENCOUNTER_ID": encounter_id,
        "TEST_NAME": test_name,
        "LOINC_CODE": loinc,
        "RESULT_VALUE": str(round(value, 1)),
        "RESULT_UNIT": unit,
        "REFERENCE_LOW": str(ref_low),
        "REFERENCE_HIGH": str(ref_high),
        "ABNORMAL_FLAG": abnormal,
        "COLLECTED_DATE": fmt(collected),
    })
    return lid


def add_claim(patient_id: str, encounter_id: str, service_date: date, proc_tuple: tuple = None, payer: str = None):
    cid = next_id("clm")
    if proc_tuple is None:
        proc_tuple = random.choice(PROCEDURE_CATALOG)
    code, desc, low, high = proc_tuple
    billed = round(random.uniform(max(low, 10), max(high, 50)), 2)
    allowed = round(billed * random.uniform(0.6, 0.9), 2)
    paid = round(allowed * random.uniform(0.7, 1.0), 2)
    claims_all.append({
        "CLAIM_ID": cid,
        "PATIENT_ID": patient_id,
        "ENCOUNTER_ID": encounter_id,
        "SERVICE_DATE": fmt(service_date),
        "PROCEDURE_CODE": code,
        "PROCEDURE_DESC": desc,
        "BILLED_AMOUNT": str(billed),
        "ALLOWED_AMOUNT": str(allowed),
        "PAID_AMOUNT": str(paid),
        "PAYER": payer or random.choice(["Aetna", "UnitedHealthcare", "Blue Cross", "Medicare", "Medicaid"]),
        "CLAIM_STATUS": random.choice(["Paid", "Paid", "Paid", "Pending", "Denied"]),
    })
    return cid


# ── SCENARIO 1: CKD + Nephrotoxic med + High Creatinine ─────────
p1 = make_patient("P-0001", "Margaret", "Wilson", date(1954, 3, 12), "Female", "Medicare", "OH")
patients.append(p1)

# Encounters
dates_p1 = [date(2026, 3, 5), date(2026, 5, 14), date(2026, 7, 20), date(2026, 9, 2)]
eids_p1 = []
for i, d in enumerate(dates_p1):
    etype = "Outpatient" if i < 3 else "Inpatient"
    eid = add_encounter("P-0001", d, etype, "Chronic disease management" if etype == "Outpatient" else "Acute kidney injury")
    eids_p1.append(eid)

# Diagnoses: CKD stage 3, hypertension, osteoarthritis
add_diagnosis("P-0001", eids_p1[0], DIAGNOSIS_CATALOG[5], True, dates_p1[0])   # CKD stage 3
add_diagnosis("P-0001", eids_p1[0], DIAGNOSIS_CATALOG[3], False, dates_p1[0])  # Hypertension
add_diagnosis("P-0001", eids_p1[1], DIAGNOSIS_CATALOG[8], False, dates_p1[1])  # Osteoarthritis

# Medications: lisinopril, atorvastatin, and IBUPROFEN (nephrotoxic!)
add_medication("P-0001", MEDICATION_CATALOG[1], date(2025, 1, 10))   # Lisinopril
add_medication("P-0001", MEDICATION_CATALOG[2], date(2025, 3, 20))   # Atorvastatin
add_medication("P-0001", MEDICATION_CATALOG[11], date(2026, 5, 14))  # Ibuprofen — nephrotoxic in CKD

# Labs: creatinine trending up, low eGFR
for i, d in enumerate(dates_p1):
    eid = eids_p1[i]
    add_lab("P-0001", eid, LAB_CATALOG[1], d, value=1.4 + i * 0.3)   # Creatinine: 1.4 → 2.3
    add_lab("P-0001", eid, LAB_CATALOG[2], d, value=52 - i * 5)       # eGFR: 52 → 37
    add_lab("P-0001", eid, LAB_CATALOG[4], d)  # Total Cholesterol
    add_lab("P-0001", eid, LAB_CATALOG[12], d) # Potassium
    if i % 2 == 0:
        add_lab("P-0001", eid, LAB_CATALOG[9], d)  # Hemoglobin
        add_lab("P-0001", eid, LAB_CATALOG[11], d)  # Sodium

# Claims
for i, d in enumerate(dates_p1):
    add_claim("P-0001", eids_p1[i], d)
    add_claim("P-0001", eids_p1[i], d, PROCEDURE_CATALOG[8])  # CMP


# ── SCENARIO 2: Diabetes + High A1c + Multi-morbidity ────────────
p2 = make_patient("P-0002", "Robert", "Garcia", date(1959, 8, 25), "Male", "Medicare", "TX")
patients.append(p2)

dates_p2 = [date(2026, 2, 10), date(2026, 4, 18), date(2026, 6, 22), date(2026, 8, 15), date(2026, 9, 10)]
eids_p2 = []
for d in dates_p2:
    eid = add_encounter("P-0002", d, random.choice(["Outpatient", "Outpatient", "Telehealth"]))
    eids_p2.append(eid)

# Diagnoses: diabetes, hypertension, CHF, dyslipidemia, depression, sleep apnea
add_diagnosis("P-0002", eids_p2[0], DIAGNOSIS_CATALOG[1], True, dates_p2[0])   # Diabetes w/ hyperglycemia
add_diagnosis("P-0002", eids_p2[0], DIAGNOSIS_CATALOG[3], False, dates_p2[0])  # Hypertension
add_diagnosis("P-0002", eids_p2[0], DIAGNOSIS_CATALOG[2], False, dates_p2[0])  # CHF
add_diagnosis("P-0002", eids_p2[1], DIAGNOSIS_CATALOG[9], False, dates_p2[1])  # Dyslipidemia
add_diagnosis("P-0002", eids_p2[1], DIAGNOSIS_CATALOG[7], False, dates_p2[1])  # Depression
add_diagnosis("P-0002", eids_p2[2], DIAGNOSIS_CATALOG[13], False, dates_p2[2]) # Sleep apnea

# Medications: 6 active — metformin, insulin, lisinopril, atorvastatin, carvedilol, sertraline
add_medication("P-0002", MEDICATION_CATALOG[0], date(2024, 6, 1))   # Metformin
add_medication("P-0002", MEDICATION_CATALOG[7], date(2025, 2, 15))  # Insulin Glargine
add_medication("P-0002", MEDICATION_CATALOG[1], date(2024, 6, 1))   # Lisinopril
add_medication("P-0002", MEDICATION_CATALOG[2], date(2024, 8, 10))  # Atorvastatin
add_medication("P-0002", MEDICATION_CATALOG[8], date(2025, 5, 1))   # Carvedilol
add_medication("P-0002", MEDICATION_CATALOG[9], date(2025, 9, 20))  # Sertraline

# Labs: A1c trending high
for i, d in enumerate(dates_p2):
    eid = eids_p2[i]
    add_lab("P-0002", eid, LAB_CATALOG[0], d, value=9.2 + i * 0.2)  # A1c: 9.2 → 10.0
    add_lab("P-0002", eid, LAB_CATALOG[3], d, value=180 + i * 30)    # BNP elevated
    add_lab("P-0002", eid, LAB_CATALOG[13], d, value=140 + i * 15)   # Fasting glucose high
    add_lab("P-0002", eid, LAB_CATALOG[1], d, value=1.1)             # Creatinine normal
    add_lab("P-0002", eid, LAB_CATALOG[5], d)                         # LDL
    add_lab("P-0002", eid, LAB_CATALOG[6], d)                         # HDL

for i, d in enumerate(dates_p2):
    add_claim("P-0002", eids_p2[i], d)


# ── SCENARIO 3: Frequent ER + Polypharmacy ───────────────────────
p3 = make_patient("P-0003", "Denise", "Jackson", date(1948, 11, 7), "Female", "Medicare", "FL")
patients.append(p3)

# 5 encounters: 3 ER visits in last 90 days
dates_p3 = [date(2026, 4, 10), date(2026, 7, 5), date(2026, 7, 28), date(2026, 8, 19), date(2026, 9, 8)]
types_p3 = ["Outpatient", "ER", "ER", "ER", "Inpatient"]
complaints_p3 = ["Routine follow-up", "Fall injury", "Chest pain", "Shortness of breath", "CHF exacerbation"]
eids_p3 = []
for d, t, c in zip(dates_p3, types_p3, complaints_p3):
    eid = add_encounter("P-0003", d, t, c)
    eids_p3.append(eid)

# Diagnoses: CHF, afib, COPD, hypertension, hypothyroid, anemia, GERD, back pain
add_diagnosis("P-0003", eids_p3[0], DIAGNOSIS_CATALOG[2], True, dates_p3[0])   # CHF
add_diagnosis("P-0003", eids_p3[0], DIAGNOSIS_CATALOG[17], False, dates_p3[0]) # Afib
add_diagnosis("P-0003", eids_p3[0], DIAGNOSIS_CATALOG[4], False, dates_p3[0])  # COPD
add_diagnosis("P-0003", eids_p3[0], DIAGNOSIS_CATALOG[3], False, dates_p3[0])  # Hypertension
add_diagnosis("P-0003", eids_p3[1], DIAGNOSIS_CATALOG[12], False, dates_p3[1]) # Hypothyroid
add_diagnosis("P-0003", eids_p3[1], DIAGNOSIS_CATALOG[18], False, dates_p3[1]) # Anemia
add_diagnosis("P-0003", eids_p3[2], DIAGNOSIS_CATALOG[14], False, dates_p3[2]) # GERD
add_diagnosis("P-0003", eids_p3[3], DIAGNOSIS_CATALOG[15], False, dates_p3[3]) # Back pain

# Polypharmacy: 9 active medications
add_medication("P-0003", MEDICATION_CATALOG[6], date(2024, 3, 1))   # Furosemide
add_medication("P-0003", MEDICATION_CATALOG[8], date(2024, 3, 1))   # Carvedilol
add_medication("P-0003", MEDICATION_CATALOG[17], date(2024, 6, 10)) # Apixaban
add_medication("P-0003", MEDICATION_CATALOG[1], date(2024, 3, 1))   # Lisinopril
add_medication("P-0003", MEDICATION_CATALOG[3], date(2024, 9, 15))  # Amlodipine
add_medication("P-0003", MEDICATION_CATALOG[5], date(2025, 1, 5))   # Levothyroxine
add_medication("P-0003", MEDICATION_CATALOG[4], date(2025, 3, 20))  # Omeprazole
add_medication("P-0003", MEDICATION_CATALOG[10], date(2025, 7, 10)) # Gabapentin
add_medication("P-0003", MEDICATION_CATALOG[13], date(2025, 8, 1))  # Albuterol

# Labs
for i, d in enumerate(dates_p3):
    eid = eids_p3[i]
    add_lab("P-0003", eid, LAB_CATALOG[3], d, value=350 + i * 40)  # BNP very high
    add_lab("P-0003", eid, LAB_CATALOG[9], d, value=10.5 - i * 0.3) # Hemoglobin low
    add_lab("P-0003", eid, LAB_CATALOG[8], d)   # WBC
    add_lab("P-0003", eid, LAB_CATALOG[11], d)   # Sodium
    add_lab("P-0003", eid, LAB_CATALOG[12], d)   # Potassium
    if i % 2 == 0:
        add_lab("P-0003", eid, LAB_CATALOG[14], d) # TSH
        add_lab("P-0003", eid, LAB_CATALOG[10], d) # Platelet

# Claims — ER claims are expensive
for i, d in enumerate(dates_p3):
    proc = PROCEDURE_CATALOG[3] if types_p3[i] == "ER" else PROCEDURE_CATALOG[0]
    add_claim("P-0003", eids_p3[i], d, proc)
    add_claim("P-0003", eids_p3[i], d, PROCEDURE_CATALOG[8])  # CMP
    if types_p3[i] == "ER":
        add_claim("P-0003", eids_p3[i], d, PROCEDURE_CATALOG[9])  # Chest X-ray


# ── GENERIC PATIENTS (P-0004 through P-0025) ─────────────────────

for idx in range(4, 26):
    pid = f"P-{idx:04d}"
    gender = random.choice(["Male", "Female"])
    first = random.choice(FIRST_NAMES_M if gender == "Male" else FIRST_NAMES_F)
    last = random.choice(LAST_NAMES)
    dob = rand_date(date(1945, 1, 1), date(2000, 12, 31))
    insurance = random.choice(INSURANCE_TYPES)
    p = make_patient(pid, first, last, dob, gender, insurance)
    patients.append(p)

    # 3-5 encounters
    n_enc = random.randint(3, 5)
    enc_dates = sorted([rand_date(date(2026, 1, 1), date(2026, 9, 20)) for _ in range(n_enc)])
    eids = []
    for d in enc_dates:
        etype = random.choice(ENCOUNTER_TYPES)
        eid = add_encounter(pid, d, etype)
        eids.append(eid)

    # 2-4 diagnoses
    n_dx = random.randint(2, 4)
    chosen_dx = random.sample(DIAGNOSIS_CATALOG, n_dx)
    for j, dx in enumerate(chosen_dx):
        enc_idx = min(j, len(eids) - 1)
        add_diagnosis(pid, eids[enc_idx], dx, j == 0, enc_dates[enc_idx])

    # 2-4 medications
    n_med = random.randint(2, 4)
    chosen_meds = random.sample(MEDICATION_CATALOG, n_med)
    for med in chosen_meds:
        start = rand_date(date(2024, 1, 1), date(2026, 6, 1))
        ended = None
        if random.random() < 0.2:  # 20% chance discontinued
            ended = start + timedelta(days=random.randint(30, 180))
        add_medication(pid, med, start, ended)

    # 6-8 labs spread across encounters
    n_lab = random.randint(6, 8)
    chosen_labs = random.sample(LAB_CATALOG, min(n_lab, len(LAB_CATALOG)))
    for k, lab in enumerate(chosen_labs):
        enc_idx = k % len(eids)
        add_lab(pid, eids[enc_idx], lab, enc_dates[enc_idx])

    # 5-6 claims
    n_claims = random.randint(5, 6)
    for k in range(n_claims):
        enc_idx = k % len(eids)
        add_claim(pid, eids[enc_idx], enc_dates[enc_idx])


# ── Write CSV files ──────────────────────────────────────────────

def write_csv(filename: str, rows: list, fieldnames: list):
    path = os.path.join(OUT_DIR, filename)
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_MINIMAL)
        writer.writeheader()
        writer.writerows(rows)
    print(f"  {filename}: {len(rows)} rows")
    return path

print(f"Writing CSVs to {OUT_DIR}/\n")

write_csv("patients.csv", patients,
          ["PATIENT_ID","FIRST_NAME","LAST_NAME","DATE_OF_BIRTH","GENDER","RACE","ETHNICITY","ZIP_CODE","STATE","INSURANCE_TYPE","PRIMARY_LANGUAGE"])

write_csv("encounters.csv", encounters_all,
          ["ENCOUNTER_ID","PATIENT_ID","ENCOUNTER_DATE","ENCOUNTER_TYPE","PROVIDER_NAME","FACILITY_NAME","DISCHARGE_DATE","CHIEF_COMPLAINT"])

write_csv("diagnoses.csv", diagnoses_all,
          ["DIAGNOSIS_ID","ENCOUNTER_ID","PATIENT_ID","ICD10_CODE","DESCRIPTION","IS_PRIMARY","DIAGNOSED_DATE","STATUS"])

write_csv("medications.csv", medications_all,
          ["MEDICATION_ID","PATIENT_ID","DRUG_NAME","NDC_CODE","DOSAGE","FREQUENCY","ROUTE","PRESCRIBER","START_DATE","END_DATE","IS_ACTIVE"])

write_csv("lab_results.csv", labs_all,
          ["LAB_ID","PATIENT_ID","ENCOUNTER_ID","TEST_NAME","LOINC_CODE","RESULT_VALUE","RESULT_UNIT","REFERENCE_LOW","REFERENCE_HIGH","ABNORMAL_FLAG","COLLECTED_DATE"])

write_csv("claims.csv", claims_all,
          ["CLAIM_ID","PATIENT_ID","ENCOUNTER_ID","SERVICE_DATE","PROCEDURE_CODE","PROCEDURE_DESC","BILLED_AMOUNT","ALLOWED_AMOUNT","PAID_AMOUNT","PAYER","CLAIM_STATUS"])

print(f"\nTotals:")
print(f"  Patients:    {len(patients)}")
print(f"  Encounters:  {len(encounters_all)}")
print(f"  Diagnoses:   {len(diagnoses_all)}")
print(f"  Medications: {len(medications_all)}")
print(f"  Labs:        {len(labs_all)}")
print(f"  Claims:      {len(claims_all)}")
print(f"\nDone.")
