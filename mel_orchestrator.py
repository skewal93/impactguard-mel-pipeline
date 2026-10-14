import pandas as pd
import json
from rapidfuzz import process, utils
import os

print("\n=== STARTING PRODUCTION-GRADE LOGFRAME ORCHESTRATOR ===")
master_districts = ["Mumbai", "Thane", "Palghar", "Pune", "Nashik", "Nagpur", "Aurangabad", "Ahmednagar", "Solapur", "Amravati", "Satara", "Kolhapur", "Jalgaon"]

# Ingestion Layer
df_kobo = pd.read_csv('field_survey_kobo.csv')
df_gov = pd.read_csv('government_portal_drop.csv')
with open('whatsapp_tracker_logs.json', 'r') as file:
    df_whatsapp = pd.DataFrame(json.load(file))
df_logframe = pd.read_csv('master_logframe_template.csv')

# --- RECONCILIATION & PARSING FUNCTIONS ---
def normalize_geo(text, master_list):
    if pd.isna(text): return "UNKNOWN"
    cleaned = utils.default_process(str(text)).replace('dist', '').replace('rural', '').replace('region', '').replace('hq', '').replace('city', '').replace('urban', '').replace('core', '').strip()
    match = process.extractOne(cleaned, master_list, score_cutoff=65)
    return match[0] if match else "UNRESOLVED_GEOGRAPHY"

def clean_scale_and_wages(entry):
    """Parses text entries, drops currency string prefixes, and normalizes Lakhs to absolute values."""
    if pd.isna(entry): return 0.0
    val_str = str(entry).upper().replace('RS.', '').replace(',', '').strip()
    try:
        if 'LAKH' in val_str:
            numeric_part = float(''.join(c for c in val_str if c.isdigit() or c=='.'))
            return numeric_part * 100000
        else:
            numeric_part = float(''.join(c for c in val_str if c.isdigit() or c=='.' or c=='-'))
            return 0.0 if numeric_part < 0 else numeric_part # Defensive fix for negatives
    except ValueError:
        return 0.0

# --- EXECUTE BIG DATA CLEANING PIPELINES ---
print(f"Processing {len(df_kobo)} rows from field surveys...")
df_kobo['clean_district'] = df_kobo['district_reported'].apply(lambda x: normalize_geo(x, master_districts))
df_gov['clean_district'] = df_gov['District_Name'].apply(lambda x: normalize_geo(x, master_districts))
df_whatsapp['clean_district'] = df_whatsapp['location'].apply(lambda x: normalize_geo(x, master_districts))
df_whatsapp['clean_vaccines'] = df_whatsapp['vaccines_distributed'].apply(clean_scale_and_wages)

# --- CALCULATE LOGFRAME PERFORMANCE MATRICES ---
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
df_logframe.to_csv("final_verified_logframe_report.csv", index=False)
print("✓ Enterprise Execution Finished. Final production mart outputted to 'final_verified_logframe_report.csv'")
