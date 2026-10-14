import streamlit as st
import pandas as pd
import json
import os
from rapidfuzz import process, utils

st.set_page_config(page_title="ImpactGuard Enterprise Platform", page_icon="🛡️", layout="wide")

# ==============================================================================
# UPGRADED BACKEND AUTO-INITIALIZATION HANDLER (Cache & Schema Reset)
# ==============================================================================
required_files = ['field_survey_kobo.csv', 'government_portal_drop.csv', 'whatsapp_tracker_logs.json', 'master_logframe_template.csv', 'raw_field_surveys.csv']

# Check if ANY file is missing, OR if the forensic file exists but is outdated (missing text column)
force_regeneration = False
if os.path.exists('raw_field_surveys.csv'):
    try:
        test_df = pd.read_csv('raw_field_surveys.csv', nrows=5)
        if 'field_narrative_notes' not in test_df.columns:
            force_regeneration = True # Old file detected, trigger overwrite!
    except Exception:
        force_regeneration = True

missing_files = [f for f in required_files if not os.path.exists(f)]

if missing_files or force_regeneration:
    with st.spinner("⚡ System Update: Overwriting legacy schemas & generating 7,000+ modern records..."):
        # Explicitly delete old files to prevent cache retention errors
        for f in required_files:
            if os.path.exists(f):
                os.remove(f)
                
        import generate_big_data
        st.rerun()

# --- SIDEBAR PANEL ---
st.sidebar.title("🛡️ ImpactGuard Engine")
st.sidebar.markdown("`Firmware v3.0 (Enterprise Track)`")
st.sidebar.markdown("---")

app_mode = st.sidebar.radio(
    "Select Operational Suite:",
    ["📊 Logframe Orchestration (ETL)", "🕵️ Forensic Fraud Surveillance (QA)", "📝 Qualitative Text Mining (NLP)"]
)

st.sidebar.markdown("---")
master_districts = ["Mumbai", "Thane", "Palghar", "Pune", "Nashik", "Nagpur", "Aurangabad", "Ahmednagar", "Solapur", "Amravati", "Satara", "Kolhapur", "Jalgaon"]

# ==============================================================================
# MODULE 1 & 2 CODE IMPLEMENTATIONS (Kept identical for stability)
# ==============================================================================
if app_mode == "📊 Logframe Orchestration (ETL)":
    st.title("📊 Module 1: Automated Multi-Source Logframe Ingestion")
    with open('field_survey_kobo.csv', 'r') as f: st.sidebar.download_button("📥 Download Messy Logframe Data", f.read(), file_name="messy_logframe_input.csv", mime="text/csv")
    uploaded_file = st.file_uploader("Upload 'messy_logframe_input.csv'", type=["csv"])
    if uploaded_file is not None:
        df_kobo = pd.read_csv(uploaded_file)
        df_gov = pd.read_csv('government_portal_drop.csv')
        with open('whatsapp_tracker_logs.json', 'r') as f: df_whatsapp = pd.DataFrame(json.load(f))
        df_logframe = pd.read_csv('master_logframe_template.csv')
        def normalize_geo(text, master_list):
            cleaned = utils.default_process(str(text)).replace('dist', '').replace('rural', '').strip()
            match = process.extractOne(cleaned, master_list, score_cutoff=65)
            return match if match else "UNRESOLVED_GEOGRAPHY"
        def clean_scale(entry):
            val_str = str(entry).upper().replace('RS.', '').replace(',', '').strip()
            if 'LAKH' in val_str: return float(''.join(c for c in val_str if c.isdigit() or c=='.')) * 100000
            n = float(''.join(c for c in val_str if c.isdigit() or c=='.' or c=='-'))
            return 0.0 if n < 0 else n
        df_kobo['clean_district'] = df_kobo['district_reported'].apply(lambda x: normalize_geo(x, master_districts))
        df_gov['clean_district'] = df_gov['District_Name'].apply(lambda x: normalize_geo(x, master_districts))
        df_whatsapp['clean_district'] = df_whatsapp['location'].apply(lambda x: normalize_geo(x, master_districts))
        df_whatsapp['clean_vaccines'] = df_whatsapp['vaccines_distributed'].apply(clean_scale)
        patients_treated = df_kobo[df_kobo['treatment_status'] == 'Completed'].groupby('clean_district').size().to_dict()
        vaccines_distributed = df_whatsapp.groupby('clean_district')['clean_vaccines'].sum().to_dict()
        beds_capacity = df_gov.groupby('clean_district')['Operational_Beds'].sum().to_dict()
        def map_metrics(row):
            dist = row['target_district']
            ind = row['indicator_name']
            if ind == "Total Patients Treated": return patients_treated.get(dist, 0)
            elif ind == "Total Vaccines Distributed": return vaccines_distributed.get(dist, 0)
            elif ind == "Operational Bed Capacity": return beds_capacity.get(dist, 0)
            return 0
        df_logframe['actual_metric_value'] = df_logframe.apply(map_metrics, axis=1)
        st.dataframe(df_logframe, use_container_width=True)

elif app_mode == "🕵️ Forensic Fraud Surveillance (QA)":
    st.title("🕵️ Module 2: Algorithmic Field-Data Fraud Identification")
    with open('raw_field_surveys.csv', 'r') as f: st.sidebar.download_button("📥 Download Messy Forensic Data", f.read(), file_name="messy_forensic_input.csv", mime="text/csv")
    uploaded_file = st.file_uploader("Upload 'messy_forensic_input.csv'", type=["csv"])
    if uploaded_file is not None:
        df_forensic = pd.read_csv(uploaded_file)
        df_forensic['response_variance'] = df_forensic[['q1_score', 'q2_score', 'q3_score', 'q4_score', 'q5_score']].var(axis=1)
        df_forensic['gps_coordinate_string'] = df_forensic['latitude'].astype(str) + "_" + df_forensic['longitude'].astype(str)
        gps_counts = df_forensic.groupby(['worker_id', 'gps_coordinate_string']).size().to_dict()
        def evaluate_fraud_risk(row):
            risk_flags = []
            if row['interview_duration_mins'] < 2.0: risk_flags.append("CRITICAL: Improbable Duration (<2 Mins)")
            if row['response_variance'] == 0.0: risk_flags.append("WARNING: Zero-Variance Responses")
            k = (row['worker_id'], row['gps_coordinate_string'])
            if gps_counts.get(k, 0) > 3: risk_flags.append(f"CRITICAL: High GPS Duplication ({gps_counts[k]} records)")
            return " | ".join(risk_flags) if risk_flags else "VERIFIED_CLEAN"
        df_forensic['forensic_audit_status'] = df_forensic.apply(evaluate_fraud_risk, axis=1)
        flagged = df_forensic[df_forensic['forensic_audit_status'] != "VERIFIED_CLEAN"]
        st.dataframe(flagged[['survey_id', 'worker_id', 'interview_duration_mins', 'forensic_audit_status']], use_container_width=True)

# ==============================================================================
# NEW MODULE 3: NLP QUALITATIVE TEXT MINING ENGINE
# ==============================================================================
elif app_mode == "📝 Qualitative Text Mining (NLP)":
    st.title("📝 Module 3: Algorithmic NLP Feedback & Anomaly Classifier")
    st.markdown("Automates text parsing across unstructured narrative feedback fields to classify issues and score sentiment trends.")
    
    with open('raw_field_surveys.csv', 'r') as f:
        st.sidebar.download_button("📥 Download Qualitative Data", f.read(), file_name="qualitative_input.csv", mime="text/csv")
        
    uploaded_file = st.file_uploader("Upload 'qualitative_input.csv' to execute text categorization rules", type=["csv"])
    
    if uploaded_file is not None:
        df_nlp = pd.read_csv(uploaded_file)
        
        # Verify the target column exists safely before execution
        if 'field_narrative_notes' not in df_nlp.columns:
            st.error("❌ Schema Validation Failure: Uploaded file missing the 'field_narrative_notes' text field.")
            st.stop()
        
        # Corrected Classification Matrix returning a precise list structure
        def classify_text_feedback(text):
            text_upper = str(text).upper()
            
            # 1. Automated Classification Rules
            if "SHORTAGE" in text_upper or "DRUGS" in text_upper or "MEDICINE" in text_upper: 
                category = "Supply Shortage"
            elif "LEAK" in text_upper or "INFRASTRUCTURE" in text_upper or "WATER" in text_upper: 
                category = "Infrastructure Failure"
            elif "BEHAVIOR" in text_upper or "POOR" in text_upper or "UNHELPFUL" in text_upper: 
                category = "Staff Conduct Issue"
            else: 
                category = "Positive Program Delivery"
            
            # 2. Sentiment Scoring Metrics
            negative_words = ["SHORTAGE", "POOR", "UNHELPFUL", "FAILED", "BROKE", "LEAKED", "ANOMALY"]
            positive_words = ["EXCELLENT", "SMOOTH", "SUCCESSFUL", "SATISFACTION", "GOOD"]
            
            score = 0
            for w in negative_words:
                if w in text_upper: score -= 1
            for w in positive_words:
                if w in text_upper: score += 1
                
            sentiment = "Positive" if score > 0 else ("Negative" if score < 0 else "Neutral")
            
            # CRITICAL FIX: Return as a zip-ready tuple/list structure rather than a raw indexed Series
            return [category, sentiment]

        with st.spinner("Executing NLP text transformations across narrative rows..."):
            # Deploys standard result expansion to safely map parameters without KeyError loops
            res = df_nlp['field_narrative_notes'].apply(classify_text_feedback)
            df_nlp['Inferred_Category'] = [r[0] for r in res]
            df_nlp['Sentiment_Analysis'] = [r[1] for r in res]

        # Output UI Visualizations
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("#### 🚨 Distribution of Field Issues & Operational Failures")
            st.bar_chart(df_nlp['Inferred_Category'].value_counts())
        with col2:
            st.markdown("#### 📈 Calculated Community Sentiment Trend Matrix")
            st.bar_chart(df_nlp['Sentiment_Analysis'].value_counts())
            
        st.markdown("### 📋 Audited Qualitative Narrative Data Mart")
        st.dataframe(df_nlp[['survey_id', 'field_narrative_notes', 'Inferred_Category', 'Sentiment_Analysis']], use_container_width=True)
        st.success("✓ Narrative classifications computed successfully. Qualitative anomalies mapped.")
            
        st.markdown("### 📋 Audited Qualitative Narrative Data Mart")
        st.dataframe(df_nlp[['survey_id', 'field_narrative_notes', 'Inferred_Category', 'Sentiment_Analysis']], use_container_width=True)
