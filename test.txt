# Care360 Copilot

**Hackathon MVP** for the "Patient and Member 360 and Clinical or Regulatory Document Copilot" challenge.

A Snowflake-native Patient 360 application that combines structured patient/member data with unstructured clinical and regulatory documents to provide explainable risk stratification and evidence-grounded Q&A with cited sources.

## Architecture

```
Streamlit in Snowflake
  ├── Tab 1: Patient 360      → CURATED.PATIENT_360_SUMMARY + RAW tables
  ├── Tab 2: Risk Strat.      → CURATED.PATIENT_RISK_SCORES (rule-based, no ML)
  ├── Tab 3: Timeline         → CURATED.PATIENT_TIMELINE
  └── Tab 4: Ask Care360      → APP.ASK_CARE360 (Cortex Search + LLM)
                                    ├── Cortex Search Service (hybrid retrieval)
                                    └── CORTEX.COMPLETE (llama3.3-70b)
```

## Snowflake-Native Capabilities Used

| Capability | Purpose |
|---|---|
| Cortex Search Service | Hybrid semantic + keyword retrieval over document chunks |
| CORTEX.COMPLETE | LLM answer generation with citation enforcement |
| AI_PARSE_DOCUMENT-ready | Document text stored for parsing pipeline |
| Internal Stage | Synthetic document storage |
| Streamlit in Snowflake | Full UI with no external hosting |
| SQL Views | Patient 360 aggregation, rule-based risk scoring |
| JavaScript UDTF | Paragraph-aware document chunking |
| Semantic View + Cortex Analyst | Natural-language queries over structured data |
| CoCo Skill | Reusable patient summary skill |

## Repository Structure

```
care360-copilot/
├── README.md
├── generate_synthetic_data.py    # Creates 25 synthetic patients + CSV files
├── sql/
│   ├── care360_ddl.sql           # Database, schemas, tables, stage, file format
│   └── care360_validation.sql    # Row counts, referential integrity, scenario checks
├── data/
│   ├── csv/                      # Generated synthetic CSVs (6 files)
│   └── documents/                # 8 synthetic clinical + regulatory documents
├── streamlit/
│   ├── snowflake.yml             # Workspace Streamlit config
│   ├── pyproject.toml            # Python dependencies
│   ├── .streamlit/config.toml    # Streamlit theme config
│   └── streamlit_app.py          # Main Streamlit app (4 tabs)
└── skill/
    └── SKILL.md                  # CoCo reusable patient summary skill
```

## Setup Instructions

### 1. Create database and tables
```sql
-- Run sql/care360_ddl.sql in a Snowflake worksheet
```

### 2. Generate and load synthetic data
```bash
python generate_synthetic_data.py
# Upload CSVs to @CARE360_DB.RAW.CSV_STAGE
# COPY INTO each table using CARE360_DB.RAW.CSV_FORMAT
```

### 3. Upload documents
```bash
# Upload data/documents/*.md to @CARE360_DB.DOCUMENTS.DOC_STAGE
# INSERT metadata into CARE360_DB.DOCUMENTS.RAW_DOCUMENTS
```

### 4. Create chunking UDTF and chunk documents
```sql
-- JavaScript UDTF: CARE360_DB.DOCUMENTS.CHUNK_TEXT_FN
-- INSERT INTO DOCUMENT_CHUNKS using the UDTF
```

### 5. Create Cortex Search Service
```sql
CREATE CORTEX SEARCH SERVICE CARE360_DB.APP.DOC_SEARCH_SVC
  ON CHUNK_TEXT
  PRIMARY KEY (CHUNK_ID)
  ATTRIBUTES DOC_ID, PATIENT_ID, DOC_TYPE, FILENAME
  WAREHOUSE = COMPUTE_WH
  TARGET_LAG = '1 hour'
  AS (SELECT ... FROM DOCUMENT_CHUNKS JOIN RAW_DOCUMENTS);
```

### 6. Create curated views
```sql
-- CARE360_DB.CURATED.PATIENT_360_SUMMARY
-- CARE360_DB.CURATED.PATIENT_TIMELINE
-- CARE360_DB.CURATED.PATIENT_RISK_SCORES
```

### 7. Create Q&A procedure
```sql
-- CARE360_DB.APP.ASK_CARE360(question, patient_filter, num_chunks)
```

### 8. Deploy Streamlit app
Copy the `streamlit/` folder contents into a Snowflake Workspace project folder and click **Run**.

## Demo Scenarios

| Patient | Scenario | Risk Tier |
|---|---|---|
| P-0001 Margaret Wilson | CKD + nephrotoxic ibuprofen + rising creatinine | MODERATE |
| P-0002 Robert Garcia | Diabetes + HbA1c 10% + 6 chronic conditions + insulin non-adherence | MODERATE |
| P-0003 Denise Jackson | 3 ER visits in 90 days + 9 medications + CHF + age 78 | HIGH |

## Key Design Decisions

- **All data is synthetic** — no real PHI. All documents include synthetic disclaimers.
- **Risk stratification is rule-based** — 6 transparent boolean flags, no ML/opaque predictions.
- **Every Q&A answer cites its sources** — chunk ID + filename for every factual claim.
- **Negative queries return "Insufficient evidence"** — the LLM cannot hallucinate from general knowledge.
- **Regulatory documents are clearly labeled as synthetic** — no impersonation of FDA, CMS, or other agencies.

## Validation Results

33/33 end-to-end checks passed — structured data, documents, chunks, search, risk engine, Q&A, semantic model, skill, and Streamlit app all validated.
