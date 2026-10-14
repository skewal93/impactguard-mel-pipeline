import pandas as pd
import numpy as np
from faker import Faker
import json
import random

fake = Faker('en_IN')
random.seed(42)
np.random.seed(42)

# Source of Truth: Real Districts of Maharashtra
official_districts = [
    "Mumbai", "Thane", "Palghar", "Pune", "Nashik", "Nagpur", "Aurangabad", 
    "Ahmednagar", "Solapur", "Amravati", "Satara", "Kolhapur", "Jalgaon"
]

# Variations used to simulate data-entry typos
typo_maps = {
    "Mumbai": ["Mumbay", "Mumbai City", "Mumbay HQ", "Mumbee"],
    "Thane": ["Thane Dist.", "Thane Rural", "Thane-Blk B", "Thanee"],
    "Palghar": ["Palghat", "Palghar Region", "Palgar", "Palghar Dist"],
    "Pune": ["Pune HQ", "Pune Rural", "Poona", "Punee"],
    "Nashik": ["Nasik", "Nashik Core", "Nasik Dist"],
    "Nagpur": ["Nagpur region", "Nagpur Urban", "Nagpure"]
}

def get_messy_district(dist):
    if dist in typo_maps and random.random() < 0.4:
        return random.choice(typo_maps[dist])
    return dist

num_records = 5000
print(f"Generating {num_records} hyper-realistic messy records...")

# --- 1. KOBO FIELD SURVEYS (5,000 Rows) ---
kobo_data = []
for i in range(num_records):
    dist = random.choice(official_districts)
    kobo_data.append({
        'submission_id': f"SUB-{100000 + i}",
        'patient_id': f"P-{200000 + i}",
        'district_reported': get_messy_district(dist),
        'phc_visited': f"PHC-{random.randint(1, 50)}",
        'treatment_status': random.choice(['Completed', 'Completed', 'Pending', 'Dropped'])
    })
df_kobo = pd.DataFrame(kobo_data)
df_kobo.to_csv('field_survey_kobo.csv', index=False)

# --- 2. GOVERNMENT PORTAL DROP (Real District Schema) ---
gov_data = []
for dist in official_districts:
    for phc_num in range(1, random.randint(3, 8)):
        gov_data.append({
            'PHC_Code': f"PHC-{phc_num}",
            'District_Name': dist if random.random() > 0.1 else get_messy_district(dist),
            'Infrastructure_Status': 'Functional',
            'Operational_Beds': random.randint(5, 50)
        })
df_gov = pd.DataFrame(gov_data)
df_gov.to_csv('government_portal_drop.csv', index=False)

# --- 3. WHATSAPP TRACKER LOGS (JSON Scale Mixup) ---
whatsapp_data = []
for i, dist in enumerate(official_districts):
    # Inject typical scale/corruption issues
    vax_clean = random.randint(5000, 25000)
    
    # Intentionally corrupt some entries
    if dist == "Palghar": vax_entry = -500 # Negative entry
    elif dist == "Pune": vax_entry = f"{vax_clean // 100000:.2f} Lakhs" # String format scale mixup
    elif dist == "Thane": vax_entry = f"Rs. {vax_clean}" # Prefixed format
    else: vax_entry = vax_clean

    whatsapp_data.append({
        "manager_id": f"M-{10 + i}",
        "location": get_messy_district(dist),
        "vaccines_distributed": vax_entry
    })
with open('whatsapp_tracker_logs.json', 'w') as f:
    json.dump(whatsapp_data, f, indent=2)

# --- 4. MASTER LOGFRAME TEMPLATE ---
logframe_data = []
indicators = ["Total Patients Treated", "Total Vaccines Distributed", "Operational Bed Capacity"]
for dist in official_districts:
    for ind in indicators:
        logframe_data.append({
            'indicator_id': f"IND-{random.randint(1000, 9999)}",
            'indicator_name': ind,
            'target_district': dist
        })
df_logframe = pd.DataFrame(logframe_data)
df_logframe.to_csv('master_logframe_template.csv', index=False)

print("🚀 Successfully generated big datasets: 'field_survey_kobo.csv' now contains 5,000 messy rows!")
