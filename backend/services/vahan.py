"""Indian RTO Vahan Registry & E-Challan Generator.

Provides verified vehicle registration lookup (simulated Vahan 4.0 database)
and generates official Motor Vehicles Act (MVA) compliant E-Challan data.
"""
import hashlib
from datetime import datetime, timedelta

# Official Indian MVA Offense & Fine Schedule
MVA_OFFENSES = {
    "Red Light Violation": {
        "section": "Section 119 / 177 MVA 1988/2019",
        "description": "Disobedience of Traffic Signal (Jumping Red Light)",
        "fine": 1000,
        "points": 3,
    },
    "No Helmet": {
        "section": "Section 129 / 194D MVA 1988/2019",
        "description": "Riding Two-Wheeler without Protective Headgear (Helmet)",
        "fine": 500,
        "points": 2,
    },
    "Triple Riding": {
        "section": "Section 128 / 194C MVA 1988/2019",
        "description": "Riding with more than one pillion passenger (Triple Riding)",
        "fine": 1000,
        "points": 3,
    },
    "Over Speeding": {
        "section": "Section 112 / 183 MVA 1988/2019",
        "description": "Exceeding Prescribed Speed Limit in Junction Zone",
        "fine": 2000,
        "points": 4,
    },
    "Wrong Way Driving": {
        "section": "Section 184 MVA 1988/2019",
        "description": "Driving dangerously against designated traffic flow",
        "fine": 1000,
        "points": 3,
    },
    "Other": {
        "section": "Section 177 MVA 1988/2019",
        "description": "General Traffic Rule Infraction",
        "fine": 500,
        "points": 1,
    },
}

# Pre-seeded authentic vehicle registry records
SEED_REGISTRY = {
    "MH15AB1234": {
        "owner_name": "Rajesh Kumar Sharma",
        "father_name": "Ramakant Sharma",
        "vehicle_class": "Two Wheeler (MCWG)",
        "model": "Royal Enfield Classic 350",
        "color": "Stealth Black",
        "fuel_type": "Petrol",
        "rto_office": "MH-15 RTO Nashik, Maharashtra",
        "reg_date": "2021-03-14",
        "insurance_valid_till": "2027-04-10",
        "puc_valid_till": "2026-11-20",
        "chassis_last4": "8492",
        "engine_last4": "3104",
        "mobile_masked": "+91 98****1234",
    },
    "MH12DE1432": {
        "owner_name": "Sunil D. Patil",
        "father_name": "Dinkar Patil",
        "vehicle_class": "Light Motor Vehicle (LMV-Car)",
        "model": "Hyundai Creta 1.5 SX",
        "color": "Polar White",
        "fuel_type": "Diesel",
        "rto_office": "MH-12 RTO Pune Central, Maharashtra",
        "reg_date": "2022-08-19",
        "insurance_valid_till": "2027-08-15",
        "puc_valid_till": "2027-02-28",
        "chassis_last4": "5512",
        "engine_last4": "9931",
        "mobile_masked": "+91 97****5678",
    },
    "MH14AB9821": {
        "owner_name": "Amit Deshmukh",
        "father_name": "Vilasrao Deshmukh",
        "vehicle_class": "Two Wheeler (MCWG)",
        "model": "Yamaha FZ-S FI V3",
        "color": "Racing Blue",
        "fuel_type": "Petrol",
        "rto_office": "MH-14 RTO Pimpri-Chinchwad, Maharashtra",
        "reg_date": "2023-01-10",
        "insurance_valid_till": "2028-01-05",
        "puc_valid_till": "2026-12-30",
        "chassis_last4": "2249",
        "engine_last4": "4490",
        "mobile_masked": "+91 94****3321",
    },
    "MH15BT4554": {
        "owner_name": "Ramesh K. Jadhav",
        "father_name": "Kashinath Jadhav",
        "vehicle_class": "Two Wheeler (MCWG)",
        "model": "Hero Splendor Plus BS6",
        "color": "Black with Purple",
        "fuel_type": "Petrol",
        "rto_office": "MH-15 RTO Nashik, Maharashtra",
        "reg_date": "2020-11-05",
        "insurance_valid_till": "2026-11-01",
        "puc_valid_till": "2026-10-15",
        "chassis_last4": "7718",
        "engine_last4": "1209",
        "mobile_masked": "+91 99****8844",
    },
    "DL08CA7721": {
        "owner_name": "Vikramjeet Singh",
        "father_name": "Harbhajan Singh",
        "vehicle_class": "Light Motor Vehicle (LMV-Car)",
        "model": "Maruti Suzuki Swift ZXi",
        "color": "Fire Red",
        "fuel_type": "Petrol",
        "rto_office": "DL-08 RTO Wazirpur, Delhi",
        "reg_date": "2021-07-22",
        "insurance_valid_till": "2027-07-20",
        "puc_valid_till": "2027-01-15",
        "chassis_last4": "6034",
        "engine_last4": "8821",
        "mobile_masked": "+91 98****7721",
    },
}


def lookup_vahan(vehicle_number):
    """Returns Vahan vehicle registration record for a given plate number."""
    clean = vehicle_number.strip().upper().replace(" ", "").replace("-", "")
    if clean in SEED_REGISTRY:
        data = SEED_REGISTRY[clean].copy()
        data["vehicle_number"] = clean
        return data

    # Procedural generator for any newly encountered plate number
    h = int(hashlib.md5(clean.encode()).hexdigest(), 16)
    first_names = ["Rahul", "Sanjay", "Anil", "Pooja", "Gaurav", "Nitin", "Sachin", "Vijay"]
    last_names = ["Shinde", "Kulkarni", "Chavan", "More", "Pawar", "Bhosale", "Gaikwad"]
    models_bike = ["Honda Activa 6G", "TVS Jupiter", "Bajaj Pulsar 150", "Honda Shine"]
    models_car = ["Maruti Baleno", "Tata Nexon", "Hyundai i20", "Honda Amaze"]

    is_bike = (h % 2 == 0)
    owner = f"{first_names[h % len(first_names)]} {last_names[(h // 10) % len(last_names)]}"
    model = (models_bike if is_bike else models_car)[h % 4]
    v_class = "Two Wheeler (MCWG)" if is_bike else "Light Motor Vehicle (LMV-Car)"
    state_code = clean[:2] if len(clean) >= 2 else "MH"
    rto_code = clean[:4] if len(clean) >= 4 else "MH15"

    return {
        "vehicle_number": clean,
        "owner_name": owner,
        "father_name": f"Senior {owner.split()[-1]}",
        "vehicle_class": v_class,
        "model": model,
        "color": ["Grey", "White", "Silver", "Black"][h % 4],
        "fuel_type": "Petrol" if is_bike else ("Diesel" if h % 3 == 0 else "Petrol"),
        "rto_office": f"{rto_code} District Transport Office ({state_code})",
        "reg_date": f"202{h % 4 + 1}-0{(h % 8) + 1}-15",
        "insurance_valid_till": "2027-12-31",
        "puc_valid_till": "2026-12-15",
        "chassis_last4": str(1000 + (h % 8999)),
        "engine_last4": str(1000 + ((h // 7) % 8999)),
        "mobile_masked": f"+91 98****{(h % 8999) + 1000}",
    }


def get_challan_data(violation):
    """Formats full official E-Challan payload for any violation dictionary."""
    vid = violation.get("id", 1)
    vtype = violation.get("violation_type", "Red Light Violation")
    vnum = violation.get("vehicle_number", "MH15AB1234")
    vahan = lookup_vahan(vnum)
    offense = MVA_OFFENSES.get(vtype, MVA_OFFENSES["Other"])

    ts_raw = violation.get("timestamp", datetime.now().isoformat())
    try:
        dt = datetime.fromisoformat(ts_raw)
    except Exception:
        dt = datetime.now()

    challan_number = f"MH-CHAL-2026-{vid:06d}"
    due_date = (dt + timedelta(days=15)).strftime("%d-%b-%Y")

    status = violation.get("status", "")
    is_paid = "paid" in status.lower()

    return {
        "challan_number": challan_number,
        "violation_id": vid,
        "vehicle_number": vnum,
        "owner_name": vahan["owner_name"],
        "vehicle_class": vahan["vehicle_class"],
        "model": vahan["model"],
        "rto_office": vahan["rto_office"],
        "mobile_masked": vahan["mobile_masked"],
        "violation_type": vtype,
        "mva_section": offense["section"],
        "offense_description": offense["description"],
        "fine_amount": offense["fine"],
        "demerit_points": offense["points"],
        "location": violation.get("location", "College Demo Junction - Signal #2"),
        "timestamp": dt.strftime("%d-%b-%Y %I:%M:%S %p"),
        "due_date": due_date,
        "evidence_image": violation.get("evidence_image", ""),
        "confidence": violation.get("confidence", 0.95),
        "payment_status": "PAID" if is_paid else "PENDING",
        "issuing_authority": "Traffic Control Branch, Maharashtra Motor Vehicles Dept.",
    }
