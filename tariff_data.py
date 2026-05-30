"""
BESCOM/HESCOM Tariff Schedule Data (Karnataka)
Based on publicly available tariff orders from hescom.karnataka.gov.in
Tariff effective from FY 2024-25 Order
"""

BESCOM_TARIFF = {
    "name": "BESCOM (Bangalore Electricity Supply Company)",
    "category": "LT-2A Domestic",
    "fixed_charge_per_month": 50.00,  # Rs/month for single phase
    "slabs": [
        {"from": 0,   "to": 30,   "rate": 3.15,  "label": "0–30 units"},
        {"from": 31,  "to": 100,  "rate": 5.70,  "label": "31–100 units"},
        {"from": 101, "to": 200,  "rate": 7.10,  "label": "101–200 units"},
        {"from": 201, "to": 500,  "rate": 8.00,  "label": "201–500 units"},
        {"from": 501, "to": 9999, "rate": 9.00,  "label": "Above 500 units"},
    ],
    "fuel_surcharge_pct": 0.10,      # 10% of energy charges
    "electricity_duty_pct": 0.06,    # 6% of energy + fuel surcharge
    "wheeling_charge_per_unit": 0.20,
}

HESCOM_TARIFF = {
    "name": "HESCOM (Hubli Electricity Supply Company)",
    "category": "LT-2A Domestic",
    "fixed_charge_per_month": 50.00,
    "slabs": [
        {"from": 0,   "to": 30,   "rate": 3.10,  "label": "0–30 units"},
        {"from": 31,  "to": 100,  "rate": 5.60,  "label": "31–100 units"},
        {"from": 101, "to": 200,  "rate": 7.00,  "label": "101–200 units"},
        {"from": 201, "to": 500,  "rate": 7.90,  "label": "201–500 units"},
        {"from": 501, "to": 9999, "rate": 8.80,  "label": "Above 500 units"},
    ],
    "fuel_surcharge_pct": 0.10,
    "electricity_duty_pct": 0.06,
    "wheeling_charge_per_unit": 0.20,
}

TARIFF_HISTORY = {
    # Approximate revision dates for Karnataka DISCOMs
    "2022-06": {"revision": "5–8% hike across all slabs", "effective": "June 2022"},
    "2023-04": {"revision": "6–10% hike, slab thresholds unchanged", "effective": "April 2023"},
    "2024-04": {"revision": "7% average hike, fuel surcharge increased from 8% to 10%", "effective": "April 2024"},
}

SEASONAL_PATTERNS = {
    "Summer (Mar–Jun)": {
        "months": [3, 4, 5, 6],
        "expected_increase_pct": 20,
        "reason": "Air conditioning, fans, coolers usage peaks during Karnataka summer (35–42°C)"
    },
    "Monsoon (Jul–Sep)": {
        "months": [7, 8, 9],
        "expected_increase_pct": 10,
        "reason": "Slightly reduced AC usage but increased lighting due to overcast skies"
    },
    "Winter (Nov–Feb)": {
        "months": [11, 12, 1, 2],
        "expected_increase_pct": -10,
        "reason": "Reduced cooling load in Karnataka mild winter"
    },
}

def compute_bescom_bill(units: float, discom: str = "BESCOM") -> dict:
    """Compute expected bill using BESCOM/HESCOM tariff slabs."""
    tariff = BESCOM_TARIFF if discom == "BESCOM" else HESCOM_TARIFF
    energy_charge = 0.0
    remaining = units
    slab_breakdown = []

    for slab in tariff["slabs"]:
        if remaining <= 0:
            break
        slab_units = min(remaining, slab["to"] - slab["from"] + 1)
        charge = slab_units * slab["rate"]
        slab_breakdown.append({
            "label": slab["label"],
            "units": slab_units,
            "rate": slab["rate"],
            "charge": round(charge, 2)
        })
        energy_charge += charge
        remaining -= slab_units

    fuel_surcharge = energy_charge * tariff["fuel_surcharge_pct"]
    electricity_duty = (energy_charge + fuel_surcharge) * tariff["electricity_duty_pct"]
    fixed_charge = tariff["fixed_charge_per_month"]
    total = round(energy_charge + fuel_surcharge + electricity_duty + fixed_charge, 2)

    return {
        "units": units,
        "slab_breakdown": slab_breakdown,
        "energy_charge": round(energy_charge, 2),
        "fuel_surcharge": round(fuel_surcharge, 2),
        "electricity_duty": round(electricity_duty, 2),
        "fixed_charge": fixed_charge,
        "total_expected": total,
    }
