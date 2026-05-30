"""
Preprocess UCI Household Electricity Dataset into monthly bill format
Dataset: archive.ics.uci.edu/dataset/235
"""
import pandas as pd

def load_uci_as_monthly_bills(filepath: str, discom: str = "BESCOM") -> pd.DataFrame:
    # Load raw UCI dataset
    df = pd.read_csv(
        filepath,
        sep=";",
        na_values="?",
        low_memory=False,
        usecols=["Date", "Global_active_power"]
    )
    df = df.dropna()

    # Parse date and convert power to kWh
    df["Date"] = pd.to_datetime(df["Date"], format="%d/%m/%Y")
    # Global_active_power is in kilowatts (1-minute readings)
    # kWh = kW × (1/60) for each 1-minute interval
    df["kwh"] = df["Global_active_power"].astype(float) / 60.0

    # Aggregate to monthly units consumed
    monthly = df.groupby(df["Date"].dt.to_period("M"))["kwh"].sum().reset_index()
    monthly.columns = ["period", "Units_Consumed"]
    monthly["Units_Consumed"] = monthly["Units_Consumed"].round(2)

    # Use last 12 months available in dataset
    monthly = monthly.tail(12).reset_index(drop=True)
    monthly["Month"] = monthly["period"].dt.strftime("%B %Y")

    # Compute bill using BESCOM tariff (reuse your existing function)
    from tariff_data import compute_bescom_bill
    monthly["Amount_Billed"] = monthly["Units_Consumed"].apply(
        lambda u: compute_bescom_bill(u, discom)["total_expected"]
    )
    monthly["Reading_Type"] = "Actual"
    monthly["Meter_Reading"] = monthly["Units_Consumed"].cumsum().round(2)
    monthly["Previous_Reading"] = monthly["Meter_Reading"].shift(1).fillna(0).round(2)

    return monthly[["Month", "Units_Consumed", "Amount_Billed",
                     "Reading_Type", "Meter_Reading", "Previous_Reading"]]


if __name__ == "__main__":
    df = load_uci_as_monthly_bills("household_power_consumption.txt")
    df.to_csv("sample_bills.csv", index=False)
    print(df.to_string())
    print(f"\n✅ Saved {len(df)} months from UCI dataset to sample_bills.csv")