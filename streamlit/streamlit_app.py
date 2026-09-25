import json
import math
import pandas as pd
import streamlit as st
import snowflake.connector
from cryptography.hazmat.primitives import serialization

# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(
    page_title="Care360 Copilot",
    page_icon="\U0001f3e5",
    layout="wide",
)

# ============================================================
# SNOWFLAKE CONNECTION
# ============================================================
@st.cache_resource
def get_connection():
    """
    Create a Snowflake connection using RSA key-pair authentication.
    Credentials are read from Streamlit Community Cloud Secrets.
    Nothing sensitive is stored in GitHub.
    """
    private_key_pem = st.secrets["snowflake"]["private_key"]
    private_key = serialization.load_pem_private_key(
        private_key_pem.encode("utf-8"),
        password=None,
    )
    private_key_der = private_key.private_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    return snowflake.connector.connect(
        account=st.secrets["snowflake"]["account"],
        user=st.secrets["snowflake"]["user"],
        authenticator="SNOWFLAKE_JWT",
        private_key=private_key_der,
        role=st.secrets["snowflake"]["role"],
        warehouse=st.secrets["snowflake"]["warehouse"],
        database=st.secrets["snowflake"]["database"],
        schema=st.secrets["snowflake"]["schema"],
    )

conn = get_connection()

# ============================================================
# DATABASE HELPERS
# ============================================================
def query_dataframe(sql, params=None):
    """
    Execute a parameterized Snowflake query and return a pandas DataFrame.
    """
    cursor = conn.cursor()
    try:
        cursor.execute(sql, params or ())
        rows = cursor.fetchall()
        columns = [column[0] for column in cursor.description]
        return pd.DataFrame(rows, columns=columns)
    finally:
        cursor.close()

def execute_scalar(sql, params=None):
    """
    Execute a query expected to return one value.
    """
    cursor = conn.cursor()
    try:
        cursor.execute(sql, params or ())
        row = cursor.fetchone()
        if row:
            return row[0]
        return None
    finally:
        cursor.close()

# ============================================================
# DATA LOADERS
# ============================================================
@st.cache_data(ttl=300)
def load_patients():
    return query_dataframe(
        """
        SELECT *
        FROM CARE360_DB.CURATED.PATIENT_360_SUMMARY
        ORDER BY PATIENT_NAME
        """
    )

@st.cache_data(ttl=300)
def load_risk_scores():
    return query_dataframe(
        """
        SELECT *
        FROM CARE360_DB.CURATED.PATIENT_RISK_SCORES
        ORDER BY PATIENT_ID
        """
    )

@st.cache_data(ttl=300)
def load_diagnoses(patient_id):
    return query_dataframe(
        """
        SELECT DIAGNOSIS_ID, ICD10_CODE, DESCRIPTION, IS_PRIMARY
        FROM CARE360_DB.RAW.DIAGNOSES
        WHERE PATIENT_ID = %s
        ORDER BY IS_PRIMARY DESC, DESCRIPTION
        """,
        (patient_id,),
    )

@st.cache_data(ttl=300)
def load_medications(patient_id):
    return query_dataframe(
        """
        SELECT MEDICATION_ID, DRUG_NAME, NDC_CODE, START_DATE, END_DATE, PRESCRIBER
        FROM CARE360_DB.RAW.MEDICATIONS
        WHERE PATIENT_ID = %s
        ORDER BY START_DATE DESC
        """,
        (patient_id,),
    )

@st.cache_data(ttl=300)
def load_timeline(patient_id):
    return query_dataframe(
        """
        SELECT EVENT_DATE, EVENT_TYPE, EVENT_SUMMARY, SOURCE_ID
        FROM CARE360_DB.CURATED.PATIENT_TIMELINE
        WHERE PATIENT_ID = %s
        ORDER BY EVENT_DATE DESC
        """,
        (patient_id,),
    )

# ============================================================
# HELPERS
# ============================================================
def display_value(value, decimals=None):
    """
    Convert null / NaN values to N/A for clean UI display.
    """
    if value is None:
        return "N/A"
    try:
        if pd.isna(value):
            return "N/A"
    except Exception:
        pass
    if isinstance(value, float):
        if math.isnan(value):
            return "N/A"
        if decimals is not None:
            return round(value, decimals)
    # Convert dates / timestamps / other unsupported objects to string
    if not isinstance(value, (str, int, float)):
        return str(value)
    return value

def risk_badge(tier):
    tier = str(tier).upper()
    if tier == "HIGH":
        return "\U0001f534 HIGH"
    if tier == "MODERATE":
        return "\U0001f7e0 MODERATE"
    return "\U0001f7e2 LOW"

def flag_display(value):
    return "\u2705 Triggered" if int(value or 0) == 1 else "\u2796 Not triggered"

# ============================================================
# LOAD BASE DATA
# ============================================================
try:
    patients_df = load_patients()
    risk_df = load_risk_scores()
except Exception as exc:
    st.error(
        "Unable to connect to the Care360 Snowflake data."
    )
    st.exception(exc)
    st.stop()

if patients_df.empty:
    st.error("No synthetic patients were found.")
    st.stop()

# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.title("\U0001f3e5 Care360 Copilot")
    st.caption(
        "Evidence-based Patient 360 and Clinical Document Copilot"
    )
    st.divider()

    patient_options = {
        f"{row['PATIENT_NAME']} ({row['PATIENT_ID']})": row["PATIENT_ID"]
        for _, row in patients_df.iterrows()
    }
    selected_label = st.selectbox(
        "Select patient",
        list(patient_options.keys()),
    )
    selected_pid = patient_options[selected_label]
    st.caption(f"Patient ID: `{selected_pid}`")

    st.divider()
    st.warning(
        "\u26a0\ufe0f **Synthetic Demo Data**\n\n"
        "All patient identities, providers, facilities and "
        "clinical information in this application are fictional."
    )
    st.info(
        "\u2139\ufe0f **Not medical advice.** "
        "This prototype is for informational and demonstration "
        "purposes only and is not a substitute for professional "
        "medical judgment."
    )

# ============================================================
# SELECT PATIENT
# ============================================================
patient_match = patients_df[
    patients_df["PATIENT_ID"] == selected_pid
]
risk_match = risk_df[
    risk_df["PATIENT_ID"] == selected_pid
]

if patient_match.empty or risk_match.empty:
    st.error("Unable to locate the selected patient.")
    st.stop()

patient = patient_match.iloc[0]
risk = risk_match.iloc[0]

# ============================================================
# HEADER
# ============================================================
st.title(patient["PATIENT_NAME"])

header_cols = st.columns(6)
header_cols[0].metric(
    "Age",
    display_value(patient["AGE"]),
)
header_cols[1].metric(
    "Gender",
    display_value(patient["GENDER"]),
)
header_cols[2].metric(
    "Insurance",
    display_value(patient["INSURANCE_TYPE"]),
)
header_cols[3].metric(
    "Latest Encounter",
    display_value(patient["LATEST_ENCOUNTER_DATE"]),
)
header_cols[4].metric(
    "Risk Score",
    f"{display_value(risk['RISK_SCORE'])}/6",
)
header_cols[5].metric(
    "Risk Tier",
    risk_badge(risk["RISK_TIER"]),
)

st.divider()

# ============================================================
# TABS
# ============================================================
tab_patient, tab_risk, tab_timeline, tab_ask = st.tabs(
    [
        "Patient 360",
        "Risk Stratification",
        "Timeline",
        "Ask Care360",
    ]
)

# ============================================================
# TAB 1 - PATIENT 360
# ============================================================
with tab_patient:
    st.subheader("Patient 360")

    metric_cols = st.columns(6)
    metric_cols[0].metric(
        "Encounters",
        display_value(patient["ENCOUNTER_COUNT"]),
    )
    metric_cols[1].metric(
        "Active Medications",
        display_value(patient["ACTIVE_MED_COUNT"]),
    )
    metric_cols[2].metric(
        "Diagnoses",
        display_value(patient["DIAGNOSIS_COUNT"]),
    )
    metric_cols[3].metric(
        "Latest HbA1c (%)",
        display_value(
            patient["LATEST_HBA1C"],
            1,
        ),
    )
    metric_cols[4].metric(
        "Latest Creatinine (mg/dL)",
        display_value(
            patient["LATEST_CREATININE"],
            2,
        ),
    )
    metric_cols[5].metric(
        "ER Visits (90 days)",
        display_value(
            patient["ER_VISITS_LAST_90D"]
        ),
    )

    st.divider()
    left, right = st.columns(2)

    with left:
        st.markdown("### Diagnoses")
        try:
            diagnoses_df = load_diagnoses(selected_pid)
            if diagnoses_df.empty:
                st.info(
                    "No diagnoses available for this patient."
                )
            else:
                st.dataframe(
                    diagnoses_df,
                    use_container_width=True,
                    hide_index=True,
                )
        except Exception as exc:
            st.error("Unable to load diagnoses.")
            st.exception(exc)

    with right:
        st.markdown("### Medications")
        try:
            medications_df = load_medications(selected_pid)
            if medications_df.empty:
                st.info(
                    "No medications available for this patient."
                )
            else:
                st.dataframe(
                    medications_df,
                    use_container_width=True,
                    hide_index=True,
                )
        except Exception as exc:
            st.error("Unable to load medications.")
            st.exception(exc)

# ============================================================
# TAB 2 - RISK STRATIFICATION
# ============================================================
with tab_risk:
    st.subheader("Explainable Risk Stratification")
    st.caption(
        "Care360 uses deterministic, transparent rules. "
        "No machine-learning model is used to predict patient risk."
    )

    score_col, tier_col = st.columns(2)
    score_col.metric(
        "Risk Score",
        f"{risk['RISK_SCORE']} / 6",
    )
    tier_col.metric(
        "Risk Tier",
        risk_badge(risk["RISK_TIER"]),
    )

    st.divider()
    st.markdown("### Rule Evaluation")

    rules = [
        (
            "Multimorbidity",
            "3 or more diagnoses",
            risk["FLAG_MULTIMORBIDITY"],
        ),
        (
            "Uncontrolled Diabetes",
            "Diabetes + latest HbA1c > 9%",
            risk["FLAG_UNCONTROLLED_DIABETES"],
        ),
        (
            "Polypharmacy",
            "8 or more active medications",
            risk["FLAG_POLYPHARMACY"],
        ),
        (
            "Frequent ER",
            "2 or more ER visits in 90 days",
            risk["FLAG_FREQUENT_ER"],
        ),
        (
            "Renal Risk",
            "CKD + latest creatinine > 2 mg/dL",
            risk["FLAG_RENAL_RISK"],
        ),
        (
            "Elderly",
            "Age 75 or older",
            risk["FLAG_ELDERLY"],
        ),
    ]

    rule_df = pd.DataFrame(
        [
            {
                "Risk Rule": rule_name,
                "Definition": definition,
                "Result": flag_display(value),
            }
            for rule_name, definition, value in rules
        ]
    )

    st.dataframe(
        rule_df,
        hide_index=True,
        use_container_width=True,
    )

    st.markdown("### Why this score?")
    explanation = risk.get(
        "RISK_EXPLANATION",
        "No risk explanation available.",
    )
    if pd.isna(explanation):
        explanation = "No risk rules triggered."
    st.info(explanation)

# ============================================================
# TAB 3 - TIMELINE
# ============================================================
with tab_timeline:
    st.subheader("Patient Timeline")
    try:
        timeline_df = load_timeline(selected_pid)
        if timeline_df.empty:
            st.info(
                "No timeline events available for this patient."
            )
        else:
            event_types = sorted(
                timeline_df["EVENT_TYPE"]
                .dropna()
                .unique()
                .tolist()
            )
            selected_events = st.multiselect(
                "Filter event types",
                event_types,
                default=event_types,
            )
            filtered_timeline = timeline_df[
                timeline_df["EVENT_TYPE"]
                .isin(selected_events)
            ]
            st.dataframe(
                filtered_timeline,
                hide_index=True,
                use_container_width=True,
            )
    except Exception as exc:
        st.error("Unable to load patient timeline.")
        st.exception(exc)

# ============================================================
# TAB 4 - ASK CARE360
# ============================================================
with tab_ask:
    st.subheader("Ask Care360")
    st.caption(
        "Answers are generated only from retrieved Care360 "
        "evidence and include source citations."
    )

    question = st.text_area(
        "Ask a clinical or safety question",
        placeholder=(
            "Example: What evidence suggests "
            "NSAID-related kidney risk?"
        ),
        height=100,
    )
    ask_button = st.button(
        "Ask Care360",
        type="primary",
    )

    if ask_button:
        if not question.strip():
            st.warning("Please enter a question.")
        else:
            with st.spinner(
                "Searching Care360 evidence and generating answer..."
            ):
                try:
                    result_raw = execute_scalar(
                        """
                        CALL CARE360_DB.APP.ASK_CARE360(
                            %s, %s, %s
                        )
                        """,
                        (
                            question.strip(),
                            selected_pid,
                            5,
                        ),
                    )
                    if result_raw is None:
                        st.error(
                            "No response was returned by Care360."
                        )
                    else:
                        if isinstance(result_raw, str):
                            try:
                                result = json.loads(result_raw)
                            except json.JSONDecodeError:
                                result = {
                                    "answer": result_raw
                                }
                        else:
                            result = result_raw

                        answer = result.get(
                            "answer",
                            "No answer returned.",
                        )

                        st.markdown("### Answer")
                        if (
                            "insufficient evidence"
                            in answer.lower()
                        ):
                            st.warning(answer)
                        else:
                            st.success(answer)

                        # ------------------------------------
                        # SOURCES
                        # ------------------------------------
                        sources = result.get(
                            "sources",
                            [],
                        )
                        if sources:
                            st.markdown("### Sources")
                            for index, source in enumerate(
                                sources,
                                start=1,
                            ):
                                if isinstance(source, dict):
                                    filename = source.get(
                                        "filename",
                                        source.get(
                                            "FILENAME",
                                            "Source",
                                        ),
                                    )
                                    chunk_id = source.get(
                                        "chunk_id",
                                        source.get(
                                            "CHUNK_ID",
                                            "",
                                        ),
                                    )
                                    patient_id = source.get(
                                        "patient_id",
                                        source.get(
                                            "PATIENT_ID",
                                            "",
                                        ),
                                    )
                                    chunk_text = source.get(
                                        "chunk_text",
                                        source.get(
                                            "CHUNK_TEXT",
                                            "",
                                        ),
                                    )
                                    label = (
                                        f"{index}. {filename}"
                                    )
                                    if chunk_id:
                                        label += (
                                            f" - {chunk_id}"
                                        )
                                    with st.expander(label):
                                        if patient_id:
                                            st.caption(
                                                "Patient ID: "
                                                f"{patient_id}"
                                            )
                                        if chunk_text:
                                            st.write(
                                                chunk_text
                                            )
                                else:
                                    st.write(
                                        f"{index}. {source}"
                                    )

                        chunks_retrieved = result.get(
                            "chunks_retrieved"
                        )
                        if chunks_retrieved is not None:
                            st.caption(
                                "Evidence chunks retrieved: "
                                f"{chunks_retrieved}"
                            )

                        st.caption(
                            "All data shown in this prototype "
                            "is synthetic demo data."
                        )
                except Exception as exc:
                    st.error(
                        "Care360 was unable to process "
                        "the question."
                    )
                    st.exception(exc)

# ============================================================
# FOOTER
# ============================================================
st.divider()
st.caption(
    "Care360 Copilot - Snowflake CoCo CLI Hackathon - "
    "Synthetic data only"
)
