# Team3_CDiv
# ⚡ BillSense AI — Electricity Bill Anomaly Detector

> **Hackathon Project · PS-SC7 · Karnataka 2026**  
> Detect anomalous electricity bills, explain causes in plain language, and generate formal DISCOM dispute letters.

---

## 📌 Problem Statement

Urban consumers in Karnataka frequently receive unexpectedly high electricity bills from BESCOM/HESCOM without clear explanation. This system:

- Ingests 12-month bill history (CSV)
- Detects anomalous months using **Z-Score** and **IQR** statistical methods
- Generates **plain-language explanations** of probable causes
- Drafts a **formal dispute letter** (DOCX) to the electricity DISCOM
- Powered by **Claude AI** (Anthropic) — no paid OpenAI API used

---

## 🗂️ Project Structure

```
electricity_app/
├── app.py                          # Main Streamlit application
├── anomaly_detection.py            # Z-Score + IQR detection engine
├── dispute_letter.py               # python-docx letter generator
├── tariff_data.py                  # BESCOM/HESCOM tariff slabs & calculator
├── preprocess_uci.py               # UCI dataset → monthly bill CSV converter
├── sample_bills.csv                # 12-month bill data (generated from UCI dataset)
├── household_power_consumption.txt # UCI dataset (place here after download)
├── Sample_Dispute_Letter_BESCOM.docx
└── requirements.txt
```

---

## 📦 Dataset Used

### UCI Individual Household Electric Power Consumption
- **Source:** https://archive.ics.uci.edu/dataset/235/individual+household+electric+power+consumption
- **Size:** 19.7 MB (2,075,259 instances)
- **Sampling rate:** 1-minute intervals over ~4 years (Dec 2006 – Nov 2010)
- **License:** CC BY 4.0
- **Citation:** Hebrail, G. & Berard, A. (2012). UCI Machine Learning Repository.

> We preprocess minute-level readings into monthly kWh totals using `preprocess_uci.py`, then apply BESCOM/HESCOM Karnataka tariff slabs to compute expected bill amounts.

---

## ⚙️ Tech Stack

| Component | Technology |
|-----------|-----------|
| UI | Streamlit |
| Data processing | pandas, numpy |
| Anomaly detection | scipy (Z-Score + IQR) |
| Visualisation | Plotly |
| AI explanation | Claude AI (Anthropic API) |
| Document export | python-docx |
| Language | Python 3.10+ |

---

## 🚀 Setup & Run

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Download the UCI dataset
Go to: https://archive.ics.uci.edu/dataset/235  
Click **DOWNLOAD (19.7 MB)** and extract `household_power_consumption.txt`  
Place it inside the `electricity_app/` folder.

### 3. Preprocess UCI data into monthly bills
```bash
python preprocess_uci.py
```
This generates a real `sample_bills.csv` from the UCI dataset.

### 4. Run the app
```bash
streamlit run app.py
```
Open your browser at `http://localhost:8501`

---

## 📊 How It Works

```
UCI Dataset (2M real readings)
        ↓
preprocess_uci.py  →  monthly kWh CSV
        ↓
anomaly_detection.py
    ├── Z-Score  (flags if |z| > 2.0σ)
    └── IQR      (flags if outside Q1−1.5×IQR to Q3+1.5×IQR)
        ↓
tariff_data.py  (BESCOM / HESCOM Karnataka slabs)
    └── Computes expected bill vs actual billed amount
        ↓
Claude AI API  →  plain-language explanation + dispute letter text
        ↓
Streamlit UI  +  python-docx  →  downloadable DOCX letter
```

---

## 🔍 Anomaly Detection Methods

### Z-Score
Measures how many standard deviations a month's consumption is from the 12-month mean.

```
z = (x − μ) / σ
```
- Flag if `|z| > 2.0` (adjustable via sidebar slider)

### IQR (Interquartile Range)
Flags consumption outside the normal spread.

```
Lower bound = Q1 − 1.5 × IQR
Upper bound = Q3 + 1.5 × IQR
```
- Flag if units < lower bound or > upper bound

> A month is marked **anomalous** if flagged by **either** method.

---

## 🧾 Cause Classification

The system automatically identifies probable causes:

| Cause | Detection Logic |
|-------|----------------|
| Estimated Meter Reading | `Reading_Type == "Estimated"` |
| Meter Reading Discrepancy | Gap between readings ≠ billed units |
| Seasonal Demand (Summer) | March–June + consumption > 115% of non-summer avg |
| Tariff Revision | April months (Karnataka annual revision) |
| Meter Fault | Z-Score > 2.5 with no other explanation |

---

## 💡 BESCOM / HESCOM Tariff Reference (FY 2024-25)

### BESCOM — LT-2A Domestic
| Slab | Rate |
|------|------|
| 0–30 units | ₹3.15/unit |
| 31–100 units | ₹5.70/unit |
| 101–200 units | ₹7.10/unit |
| 201–500 units | ₹8.00/unit |
| Above 500 units | ₹9.00/unit |

- Fixed charge: ₹50/month
- Fuel surcharge: 10% of energy charges
- Electricity duty: 6% of (energy + fuel surcharge)

---

## 📄 Dispute Letter

The generated DOCX letter includes:
- Consumer details and account number
- Statistical evidence (Z-Score and IQR analysis)
- Disputed bill breakdown table
- AI root-cause analysis
- 6 specific relief requests
- Legal provisions — **Electricity Act 2003, Section 26** and **KERC Consumer Grievance Redressal Regulations**
- Enclosures list

---

## 🗣️ CSV Format

Upload your own bill history in this format:

```csv
Month,Units_Consumed,Amount_Billed,Reading_Type,Meter_Reading,Previous_Reading
April 2024,210,1450.50,Actual,12350,12140
May 2024,245,1720.00,Actual,12595,12350
...
March 2025,678,5820.00,Actual,15455,14777
```

---

## 📋 Attribution & Credits

| Resource | Source |
|----------|--------|
| UCI Electricity Dataset | Hebrail & Berard, UCI ML Repository (CC BY 4.0) |
| BESCOM Tariff Schedule | bescom.org / KERC Tariff Order FY 2024-25 |
| HESCOM Tariff Schedule | hescom.karnataka.gov.in / KERC Tariff Order FY 2024-25 |
| AI Engine | Claude (Anthropic) — claude-sonnet-4-20250514 |
| Streamlit | streamlit.io (Apache 2.0) |
| python-docx | python-docx (MIT License) |
| Plotly | plotly.com (MIT License) |
| pandas | pandas.pydata.org (BSD License) |
| scipy | scipy.org (BSD License) |

---

## 👥 Team

> Karnataka Hackathon 2026 — PS-SC7 Submission  
> Domain: Smart Energy / Consumer Technology  
> DISCOM Coverage: BESCOM (Bangalore) · HESCOM (Hubli-Dharwad)

---

## ⚖️ Legal Disclaimer

This tool provides statistical analysis and AI-generated content to assist consumers in understanding their electricity bills. The dispute letter is a template — consumers should verify all facts before submission. This is not legal advice.
