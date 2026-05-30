"""
Anomaly Detection Engine for Electricity Bills
Uses Z-Score and IQR methods as required by PS-SC7
"""

import pandas as pd
import numpy as np
from scipy import stats
from typing import Tuple

# ─── Column normalization ───────────────────────────────────────────────────

REQUIRED_COLS = {
    "month":            ["month", "bill_month", "billing_month", "date", "period"],
    "units":            ["units_consumed", "units", "kwh", "consumption", "energy_kwh"],
    "amount":           ["amount_billed", "amount", "bill_amount", "total", "charge", "rs"],
    "reading_type":     ["reading_type", "type", "meter_reading_type"],
    "meter_reading":    ["meter_reading", "current_reading", "reading"],
    "previous_reading": ["previous_reading", "prev_reading", "last_reading"],
}

def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Map whatever column names the CSV has to our canonical names."""
    rename = {}
    lower_cols = {c.lower().strip().replace(" ", "_"): c for c in df.columns}
    for canonical, aliases in REQUIRED_COLS.items():
        for alias in aliases:
            if alias in lower_cols:
                rename[lower_cols[alias]] = canonical
                break
    return df.rename(columns=rename)


# ─── Loader ────────────────────────────────────────────────────────────────

def load_bill_data(filepath_or_buffer) -> pd.DataFrame:
    """Load and validate the 12-month bill CSV."""
    df = pd.read_csv(filepath_or_buffer)
    df = _normalize_columns(df)

    missing = [c for c in ["month", "units", "amount"] if c not in df.columns]
    if missing:
        raise ValueError(
            f"CSV is missing required columns: {missing}. "
            f"Found: {list(df.columns)}"
        )

    df["units"]  = pd.to_numeric(df["units"],  errors="coerce")
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
    df = df.dropna(subset=["units", "amount"])

    # Try to parse month as datetime for proper ordering
    try:
        df["month_dt"] = pd.to_datetime(df["month"], infer_datetime_format=True)
        df = df.sort_values("month_dt").reset_index(drop=True)
    except Exception:
        df["month_dt"] = pd.Series(range(len(df)))

    return df


# ─── Z-Score Detection ─────────────────────────────────────────────────────

def detect_anomalies_zscore(df: pd.DataFrame, threshold: float = 2.0) -> pd.DataFrame:
    """Flag months where z-score of units > threshold."""
    df = df.copy()
    mean = df["units"].mean()
    std  = df["units"].std()

    if std == 0:
        df["zscore_units"]       = 0.0
        df["anomaly_zscore"]     = False
        df["anomaly_direction"]  = "normal"
        return df

    df["zscore_units"] = (df["units"] - mean) / std
    df["anomaly_zscore"] = df["zscore_units"].abs() > threshold
    df["anomaly_direction"] = df["zscore_units"].apply(
        lambda z: "high" if z > threshold else ("low" if z < -threshold else "normal")
    )
    return df


# ─── IQR Detection ─────────────────────────────────────────────────────────

def detect_anomalies_iqr(df: pd.DataFrame, multiplier: float = 1.5) -> pd.DataFrame:
    """Flag months outside [Q1 - k*IQR, Q3 + k*IQR]."""
    df = df.copy()
    Q1  = df["units"].quantile(0.25)
    Q3  = df["units"].quantile(0.75)
    IQR = Q3 - Q1

    lower = Q1 - multiplier * IQR
    upper = Q3 + multiplier * IQR

    df["iqr_lower"] = lower
    df["iqr_upper"] = upper
    df["anomaly_iqr"] = (df["units"] < lower) | (df["units"] > upper)
    return df


# ─── Combined Analysis ─────────────────────────────────────────────────────

def full_anomaly_analysis(
    df: pd.DataFrame,
    zscore_threshold: float = 2.0,
    iqr_multiplier: float  = 1.5,
) -> Tuple[pd.DataFrame, dict]:
    """Run both methods and produce summary statistics."""
    df = detect_anomalies_zscore(df, zscore_threshold)
    df = detect_anomalies_iqr(df, iqr_multiplier)

    # Consensus: flagged by EITHER method
    df["anomaly"] = df["anomaly_zscore"] | df["anomaly_iqr"]

    stats_summary = {
        "mean_units":    round(df["units"].mean(), 1),
        "median_units":  round(df["units"].median(), 1),
        "std_units":     round(df["units"].std(), 1),
        "min_units":     round(df["units"].min(), 1),
        "max_units":     round(df["units"].max(), 1),
        "mean_amount":   round(df["amount"].mean(), 2),
        "Q1":            round(df["units"].quantile(0.25), 1),
        "Q3":            round(df["units"].quantile(0.75), 1),
        "IQR":           round(df["units"].quantile(0.75) - df["units"].quantile(0.25), 1),
        "iqr_lower":     round(df["iqr_lower"].iloc[0], 1),
        "iqr_upper":     round(df["iqr_upper"].iloc[0], 1),
        "anomaly_count": int(df["anomaly"].sum()),
        "anomaly_months": df[df["anomaly"]]["month"].tolist(),
    }

    return df, stats_summary


# ─── Cause Classification ──────────────────────────────────────────────────

MONTH_TO_NUM = {
    "january": 1, "february": 2, "march": 3, "april": 4,
    "may": 5, "june": 6, "july": 7, "august": 8,
    "september": 9, "october": 10, "november": 11, "december": 12,
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "jun": 6, "jul": 7,
    "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}

def classify_anomaly_cause(row: pd.Series, df: pd.DataFrame) -> dict:
    """
    Heuristically classify the likely cause of a billing anomaly.
    Returns a dict with 'primary_cause', 'confidence', 'explanation'.
    """
    causes = []
    month_str = str(row["month"]).lower()
    month_num = None
    for k, v in MONTH_TO_NUM.items():
        if k in month_str:
            month_num = v
            break

    # 1. Estimated reading check
    if "reading_type" in row and str(row.get("reading_type", "")).lower() in ["estimated", "est"]:
        causes.append({
            "cause": "Estimated Meter Reading",
            "confidence": "High",
            "explanation": (
                f"The meter was not physically read in {row['month']}. An estimated bill was raised "
                "based on past averages. When actual reading resumes the next month, accumulated "
                "units get billed together, inflating that month's bill significantly."
            ),
            "action": "Request actual meter reading and bill correction / rebate for over-estimated month.",
        })

    # 2. Meter reading jump check
    if "meter_reading" in row and "previous_reading" in row:
        try:
            gap = float(row["meter_reading"]) - float(row["previous_reading"])
            if abs(gap - row["units"]) > 5:
                causes.append({
                    "cause": "Meter Reading Discrepancy / Possible Meter Fault",
                    "confidence": "High",
                    "explanation": (
                        f"The difference between meter readings ({gap:.0f} units) does not match "
                        f"the billed units ({row['units']:.0f}). This indicates a possible meter "
                        "malfunction, tampering, or a billing system error."
                    ),
                    "action": "Request meter testing under Electricity Act Section 26. DISCOM must test within 30 days.",
                })
        except (TypeError, ValueError):
            pass

    # 3. Seasonal spike — summer months
    if month_num in [3, 4, 5, 6]:
        mean_non_summer = df[~df["month"].str.lower().str.contains(
            "march|april|may|june|mar|apr|jun", na=False
        )]["units"].mean()
        if row["units"] > mean_non_summer * 1.15:
            causes.append({
                "cause": "Seasonal Demand — Summer Peak",
                "confidence": "Medium",
                "explanation": (
                    f"Karnataka summer months (March–June) typically see 15–30% higher consumption "
                    "due to air conditioning, coolers, and fans running longer hours. "
                    f"Your non-summer average is ~{mean_non_summer:.0f} units."
                ),
                "action": "Cross-check with appliance usage logs. No dispute warranted if usage is genuine.",
            })

    # 4. Tariff revision
    tariff_revision_months = ["april", "apr"]  # Karnataka tariff revisions typically in April
    if any(m in month_str for m in tariff_revision_months):
        causes.append({
            "cause": "Tariff Revision (April Rate Hike)",
            "confidence": "Medium",
            "explanation": (
                "Karnataka electricity tariffs are revised annually, usually effective April. "
                "Even with the same consumption, bills increase 6–10% due to higher per-unit rates "
                "and revised fuel surcharges."
            ),
            "action": "Verify BESCOM/HESCOM tariff order. Calculate expected bill using new slabs.",
        })

    # 5. Sudden spike with no seasonal explanation
    zscore = row.get("zscore_units", 0)
    if abs(zscore) > 2.5 and not causes:
        causes.append({
            "cause": "Unexplained Consumption Spike — Possible Meter Fault",
            "confidence": "High",
            "explanation": (
                f"Consumption of {row['units']:.0f} units is {abs(zscore):.1f} standard deviations "
                "from your 12-month average. No seasonal or tariff explanation fits. "
                "This strongly suggests a meter fault, internal wiring issue, or billing error."
            ),
            "action": "File formal complaint with DISCOM. Request meter replacement under Electricity Act.",
        })

    if not causes:
        causes.append({
            "cause": "Moderate Variation — Within Normal Range",
            "confidence": "Low",
            "explanation": "Consumption is slightly above average but within expected variance.",
            "action": "Monitor next month. No immediate action required.",
        })

    return causes[0]  # Return primary (highest confidence) cause
