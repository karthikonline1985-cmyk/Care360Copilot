import os
import json
import math
import streamlit as st

st.set_page_config(page_title="Care360 Copilot", page_icon="🏥", layout="wide")


def fmt_num(val, decimals=1):
    """Format a numeric value, returning 'N/A' for None/NaN."""
    if val is None or (isinstance(val, float) and math.isnan(val)):
        return "N/A"
    return f"{val:.{decimals}f}"

conn = st.connection("snowflake", ttl=os.getenv("SNOWFLAKE_CONNECTION_TTL"))


# ── Data loaders ─────────────────────────────────────────────────

@st.cache_data(ttl=300)
def load_patients():
    return conn.query("SELECT * FROM CARE360_DB.CURATED.PATIENT_360_SUMMARY ORDER BY PATIENT_ID")


@st.cache_data(ttl=300)
def load_risk_scores():
    return conn.query("SELECT * FROM CARE360_DB.CURATED.PATIENT_RISK_SCORES ORDER BY RISK_SCORE DESC, PATIENT_ID")


@st.cache_data(ttl=300)
def load_timeline(patient_id):
    return conn.query(
        "SELECT EVENT_DATE, EVENT_TYPE, EVENT_SUMMARY, SOURCE_ID "
        "FROM CARE360_DB.CURATED.PATIENT_TIMELINE WHERE PATIENT_ID = ? "
        "ORDER BY EVENT_DATE DESC, EVENT_TYPE",
        params=[patient_id],
    )


# ── Sidebar ──────────────────────────────────────────────────────

patients_df = load_patients()
risk_df = load_risk_scores()

with st.sidebar:
    st.title("Care360 Copilot")
    st.caption("Hackathon MVP — Patient & Member 360")

    patient_options = {
        f"{row['PATIENT_NAME']} ({row['PATIENT_ID']})": row["PATIENT_ID"]
        for _, row in patients_df.iterrows()
    }
    selected_label = st.selectbox("Select patient", list(patient_options.keys()))
    selected_pid = patient_options[selected_label]

    st.markdown(f"**Patient ID:** `{selected_pid}`")

    st.divider()
    st.warning(
        "**Synthetic data only.** All patient names, IDs, providers, "
        "facilities, and clinical details are entirely fictional.",
        icon="⚠️",
    )
    st.info(
        "**Not medical advice.** This tool is for informational and demo "
        "purposes only. It is not a substitute for professional medical judgment.",
        icon="ℹ️",
    )

# ── Patient data ─────────────────────────────────────────────────

pat = patients_df[patients_df["PATIENT_ID"] == selected_pid].iloc[0]
risk = risk_df[risk_df["PATIENT_ID"] == selected_pid].iloc[0]

tier_color = {"HIGH": "red", "MODERATE": "orange", "LOW": "green"}.get(risk["RISK_TIER"], "gray")

st.markdown(
    f"### {pat['PATIENT_NAME']}  \n"
    f"**Age:** {pat['AGE']} · **Gender:** {pat['GENDER']} · "
    f"**Insurance:** {pat['INSURANCE_TYPE']} · "
    f"**Latest encounter:** {pat['LATEST_ENCOUNTER_DATE']} · "
    f"**Risk:** :{tier_color}[{risk['RISK_TIER']}]"
)

# ── Tabs ─────────────────────────────────────────────────────────

tab1, tab2, tab3, tab4 = st.tabs(
    ["Patient 360", "Risk Stratification", "Timeline", "Ask Care360"]
)

# ── Tab 1: Patient 360 ──────────────────────────────────────────

with tab1:
    cols = st.columns(6, gap="medium")
    cols[0].metric("Encounters", int(pat["ENCOUNTER_COUNT"]))
    cols[1].metric("Active Meds", int(pat["ACTIVE_MED_COUNT"]))
    cols[2].metric("Diagnoses", int(pat["DIAGNOSIS_COUNT"]))
    cols[3].metric("HbA1c (%)", fmt_num(pat["LATEST_HBA1C"]))
    cols[4].metric("Creatinine", fmt_num(pat["LATEST_CREATININE"]))
    cols[5].metric("ER (90 days)", int(pat["ER_VISITS_LAST_90D"]))

    st.divider()

    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Active Diagnoses")
        dx_df = conn.query(
            "SELECT ICD10_CODE, DESCRIPTION, STATUS, DIAGNOSED_DATE "
            "FROM CARE360_DB.RAW.DIAGNOSES WHERE PATIENT_ID = ? ORDER BY DIAGNOSED_DATE DESC",
            params=[selected_pid],
        )
        st.dataframe(dx_df, use_container_width=True, hide_index=True)

    with c2:
        st.subheader("Active Medications")
        med_df = conn.query(
            "SELECT DRUG_NAME, DOSAGE, FREQUENCY, ROUTE, PRESCRIBER "
            "FROM CARE360_DB.RAW.MEDICATIONS WHERE PATIENT_ID = ? AND IS_ACTIVE = TRUE "
            "ORDER BY DRUG_NAME",
            params=[selected_pid],
        )
        st.dataframe(med_df, use_container_width=True, hide_index=True)

# ── Tab 2: Risk Stratification ──────────────────────────────────

with tab2:
    st.subheader(f"Risk Score: {int(risk['RISK_SCORE'])} / 6 — :{tier_color}[{risk['RISK_TIER']}]")

    st.markdown(
        "> This score is calculated using **transparent, deterministic rules only**. "
        "No machine learning, no opaque predictions. Every point maps to a named, "
        "inspectable condition."
    )

    flag_defs = [
        ("FLAG_MULTIMORBIDITY", "Multimorbidity", f"Diagnosis count >= 3 (actual: {int(risk['DIAGNOSIS_COUNT'])})"),
        ("FLAG_UNCONTROLLED_DIABETES", "Uncontrolled Diabetes", f"Diabetes diagnosis + HbA1c > 9.0 (actual: {fmt_num(risk['LATEST_HBA1C'])})"),
        ("FLAG_POLYPHARMACY", "Polypharmacy", f"Active medications >= 8 (actual: {int(risk['ACTIVE_MED_COUNT'])})"),
        ("FLAG_FREQUENT_ER", "Frequent ER Visits", f"ER visits in 90 days >= 2 (actual: {int(risk['ER_VISITS_LAST_90D'])})"),
        ("FLAG_RENAL_RISK", "Renal Risk", f"CKD diagnosis + creatinine > 2.0 (actual: {fmt_num(risk['LATEST_CREATININE'])})"),
        ("FLAG_ELDERLY", "Elderly", f"Age >= 75 (actual: {int(risk['AGE'])})"),
    ]

    for flag_col, label, detail in flag_defs:
        fired = int(risk[flag_col]) == 1
        icon = "✅" if fired else "—"
        st.markdown(f"**{icon} {label}** — {detail}")

    st.divider()
    st.subheader("Explanation")
    explanation = risk["RISK_EXPLANATION"]
    if explanation:
        st.info(explanation)
    else:
        st.success("No risk flags triggered for this patient.")

# ── Tab 3: Timeline ─────────────────────────────────────────────

with tab3:
    timeline_df = load_timeline(selected_pid)

    event_types = sorted(timeline_df["EVENT_TYPE"].unique().tolist())
    selected_types = st.multiselect(
        "Filter by event type", event_types, default=event_types
    )

    filtered = timeline_df[timeline_df["EVENT_TYPE"].isin(selected_types)]
    st.dataframe(
        filtered,
        use_container_width=True,
        hide_index=True,
        column_config={
            "EVENT_DATE": st.column_config.DateColumn("Date"),
            "EVENT_TYPE": "Type",
            "EVENT_SUMMARY": "Summary",
            "SOURCE_ID": "Source ID",
        },
    )
    st.caption(f"Showing {len(filtered)} of {len(timeline_df)} events")

# ── Tab 4: Ask Care360 ──────────────────────────────────────────

with tab4:
    st.markdown(
        "Ask a clinical, safety, or regulatory question. Answers are grounded "
        "in retrieved document evidence with cited sources."
    )

    question = st.text_area(
        "Your question",
        placeholder=f"e.g., What evidence suggests {pat['PATIENT_NAME']} has medication safety risks?",
        height=80,
    )

    if st.button("Ask Care360", type="primary", disabled=not question.strip()):
        with st.spinner("Searching evidence and generating answer..."):
            session = conn.session()
            result_raw = session.sql(
                "CALL CARE360_DB.APP.ASK_CARE360(?, ?, 5)",
                params=[question.strip(), selected_pid],
            ).collect()

            result = json.loads(result_raw[0][0])

        answer = result.get("answer", "")
        sources = result.get("sources", [])
        chunks_retrieved = result.get("chunks_retrieved", 0)

        st.subheader("Answer")
        if "Insufficient evidence" in answer:
            st.warning(answer)
        else:
            st.markdown(answer)

        st.divider()
        st.subheader(f"Sources ({chunks_retrieved} chunks retrieved)")

        for i, src in enumerate(sources):
            with st.expander(
                f"[{i+1}] {src.get('FILENAME', 'Unknown')} — Chunk {src.get('CHUNK_ID', '?')}"
            ):
                st.markdown(f"**Document Type:** {src.get('DOC_TYPE', 'N/A')}")
                st.markdown(f"**Patient ID:** {src.get('PATIENT_ID') or 'N/A (regulatory)'}")
                st.markdown(f"**Chunk ID:** `{src.get('CHUNK_ID', '?')}`")
                st.text(src.get("CHUNK_TEXT", "")[:1500])
