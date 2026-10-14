import pandas as pd
import numpy as np
from faker import Faker
import json
import random

fake = Faker('en_IN')
random.seed(42)
np.random.seed(42)

# --- CONFIGURATION & SOURCE OF TRUTH ---
official_districts = ["Mumbai", "Thane", "Palghar", "Pune", "Nashik", "Nagpur", "Aurangabad", "Ahmednagar", "Solapur", "Amravati", "Satara", "Kolhapur", "Jalgaon"]
typo_maps = {
    "Mumbai": ["Mumbay", "Mumbai City", "Mumbay HQ", "Mumbee"],
    "Thane": ["Thane Dist.", "Thane Rural", "Thane-Blk B", "Thanee"],
    "Palghar": ["Palghat", "Palghar Region", "Palgar", "Palghar Dist"],
    "Pune": ["Pune HQ", "Pune Rural", "Poona", "Punee"]
}

def get_messy_district(dist):
    if dist in typo_maps and random.random() < 0.4:
        return random.choice(typo_maps[dist])
    return dist

# ==============================================================================
# MODULE 1 & 2: LOGFRAME & FORENSIC GENERATORS
# ==============================================================================
print("⚡ Generating Module 1: 5,000 Logframe records...")
kobo_data = [{'submission_id': f"SUB-{100000+i}", 'patient_id': f"P-{200000+i}", 'district_reported': get_messy_district(random.choice(official_districts)), 'phc_visited': f"PHC-{random.randint(1,50)}", 'treatment_status': random.choice(['Completed', 'Completed', 'Pending', 'Dropped'])} for i in range(5000)]
pd.DataFrame(kobo_data).to_csv('field_survey_kobo.csv', index=False)

gov_data = [{'PHC_Code': f"PHC-{p}", 'District_Name': d if random.random() > 0.1 else get_messy_district(d), 'Infrastructure_Status': 'Functional', 'Operational_Beds': random.randint(5, 50)} for d in official_districts for p in range(1, random.randint(3, 8))]
pd.DataFrame(gov_data).to_csv('government_portal_drop.csv', index=False)

whatsapp_data = []
for i, dist in enumerate(official_districts):
    vax = random.randint(5000, 25000)
    vax_entry = -500 if dist == "Palghar" else (f"{vax // 100000:.2f} Lakhs" if dist == "Pune" else (f"Rs. {vax}" if dist == "Thane" else vax))
    whatsapp_data.append({"manager_id": f"M-{10+i}", "location": get_messy_district(dist), "vaccines_distributed": vax_entry})
with open('whatsapp_tracker_logs.json', 'w') as f:
    json.dump(whatsapp_data, f, indent=2)

logframe_data = [{'indicator_id': f"IND-{random.randint(1000,9999)}", 'indicator_name': ind, 'target_district': d} for d in official_districts for ind in ["Total Patients Treated", "Total Vaccines Distributed", "Operational Bed Capacity"]]
pd.DataFrame(logframe_data).to_csv('master_logframe_template.csv', index=False)

print("🕵️ Generating Module 2: 2,000 Forensic Auditing records...")
survey_data = []
base_lat, base_lon = 19.0760, 72.8777 

# Sample text notes for text mining module
text_samples = [
    "The clinic was closed on Tuesday because the roof leaked and broke infrastructure.",
    "Excellent distribution, doctor arrived on time and vaccines were given smoothly.",
    "Major shortage of medicines and drugs. Patients are being turned away completely.",
    "Staff behavior was very poor and unhelpful. Facility had zero clean drinking water.",
    "Successful checkup camp conducted today, high beneficiary satisfaction.",
    "Supply chain failure. The refrigerator broke down and spoiled the medical stock."
]

for i in range(2000):
    worker_id = f"FIELD-W{random.randint(10, 25)}"
    duration_mins = max(5.0, round(random.normalvariate(22, 5), 1))
    lat, lon = base_lat + random.uniform(-0.5, 0.5), base_lon + random.uniform(-0.5, 0.5)
    answers = [random.randint(1, 5) for _ in range(5)]
    narrative_note = random.choice(text_samples)
    
    fraud_trigger = random.random()
    if fraud_trigger < 0.03:
        duration_mins = random.uniform(0.2, 1.4)
    elif fraud_trigger < 0.06:
        answers = [random.randint(1, 5)] * 5
    elif fraud_trigger < 0.09:
        worker_id = "FIELD-W15"
        lat, lon = 19.12345, 72.98765 

    survey_data.append({
        'survey_id': f"SRV-{500000+i}", 'worker_id': worker_id, 'interview_duration_mins': round(duration_mins, 1),
        'latitude': round(lat, 5), 'longitude': round(lon, 5),
        'q1_score': answers, 'q2_score': answers, 'q3_score': answers, 'q4_score': answers, 'q5_score': answers,
        'field_narrative_notes': narrative_note
    })
pd.DataFrame(survey_data).to_csv('raw_field_surveys.csv', index=False)
print("🚀 Master Sandbox datasets successfully staged with text fields.")
