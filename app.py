import streamlit as st
import math
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

st.set_page_config(page_title="Ontario Mortgage App", page_icon="🏠", layout="wide")

st.title("🏠 Ontario Mortgage Qualification App")
st.caption("Annual Underwriting Engine (OSFI Guideline B-20 & CMHC Rules)")
st.divider()

class IncomeExtraction(BaseModel):
    gross_annual_income: float = Field(description="Gross annual income from T4, NOA, or paystub.")
    document_type: str = Field(description="T4, NOA, or Paystub")

def extract_income(image_bytes, api_key: str) -> IncomeExtraction:
    client = genai.Client(api_key=api_key)
    prompt = "Extract gross annual income (Line 15000 / Box 14) from this document. Respond strictly with JSON."
    
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=[
            types.Part.from_bytes(data=image_bytes, mime_type='image/jpeg'),
            prompt
        ],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=IncomeExtraction,
            temperature=0.0
        )
    )
    return IncomeExtraction.parse_raw(response.text)

def calc_annual_p_and_i(loan: float, rate_pct: float, years: int) -> float:
    rate = rate_pct / 100.0
    eff_monthly_rate = (1.0 + rate / 2.0)**(2.0 / 12.0) - 1.0
    n = years * 12
    monthly = loan * (eff_monthly_rate * (1 + eff_monthly_rate)**n) / ((1 + eff_monthly_rate)**n - 1)
    return monthly * 12.0

st.sidebar.header("📂 1. Document Extraction")
gemini_key = st.sidebar.text_input("Gemini API Key (Optional)", type="password")
uploaded_file = st.sidebar.file_uploader("Upload T4, NOA, or Paystub", type=["jpg", "jpeg", "png"])

extracted_income = None
if uploaded_file and gemini_key:
    if st.sidebar.button("Scan Document"):
        try:
            res = extract_income(uploaded_file.getvalue(), gemini_key)
            extracted_income = res.gross_annual_income
            st.sidebar.success(f"Found: ${extracted_income:,.2f}")
        except Exception as e:
            st.sidebar.error(f"Error: {e}")

st.sidebar.divider()
st.sidebar.header("📊 2. Underwriting Inputs")

default_inc = float(extracted_income) if extracted_income else 140000.0
gross_annual_income = st.sidebar.number_input("Annual Gross Income ($)", min_value=1.0, value=default_inc, step=5000.0)
loan_amount = st.sidebar.number_input("Mortgage Loan Amount ($)", min_value=1.0, value=650000.0, step=10000.0)
contract_rate = st.sidebar.number_input("Contract Rate (%)", min_value=0.1, max_value=15.0, value=4.25, step=0.05)
amortization_years = st.sidebar.slider("Amortization (Years)", min_value=5, max_value=30, value=25)

st.sidebar.subheader("Annual Expenses")
annual_tax = st.sidebar.number_input("Property Tax ($)", min_value=0.0, value=4800.0)
annual_heat = st.sidebar.number_input("Heating Cost ($)", min_value=0.0, value=1800.0)
annual_condo = st.sidebar.number_input("Condo Fees ($)", min_value=0.0, value=2400.0)
annual_debts = st.sidebar.number_input("Non-Housing Debts ($)", min_value=0.0, value=7200.0)

non_mortgage_housing = annual_tax + annual_heat + (0.50 * annual_condo)

actual_p_i = calc_annual_p_and_i(loan_amount, contract_rate, amortization_years)
actual_housing = actual_p_i + non_mortgage_housing
actual_gds = (actual_housing / gross_annual_income) * 100.0
actual_tds = ((actual_housing + annual_debts) / gross_annual_income) * 100.0

qual_rate = max(5.25, contract_rate + 2.0)
qual_p_i = calc_annual_p_and_i(loan_amount, qual_rate, amortization_years)
qual_housing = qual_p_i + non_mortgage_housing
qual_gds = (qual_housing / gross_annual_income) * 100.0
qual_tds = ((qual_housing + annual_debts) / gross_annual_income) * 100.0

gds_pass = qual_gds <= 39.0
tds_pass = qual_tds <= 44.0
approved = gds_pass and tds_pass

col1, col2 = st.columns(2)

with col1:
    st.subheader("💵 Actual Out-of-Pocket Cash Flow")
    st.caption(f"Evaluated at Contract Rate: **{contract_rate:.2f}%**")
    m1, m2 = st.columns(2)
    m1.metric("Actual GDS", f"{actual_gds:.2f}%")
    m2.metric("Actual TDS", f"{actual_tds:.2f}%")
    st.markdown(f"* **Annual Housing Cost:** `${actual_housing:,.2f}`")

with col2:
    st.subheader("🏛️ OSFI B-20 Qualifying Test")
    st.caption(f"Evaluated at Stress Rate: **{qual_rate:.2f}%**")
    m3, m4 = st.columns(2)
    m3.metric("Qualifying GDS", f"{qual_gds:.2f}%", delta="Pass (≤39%)" if gds_pass else "Exceeds 39%", delta_color="normal" if gds_pass else "inverse")
    m4.metric("Qualifying TDS", f"{qual_tds:.2f}%", delta="Pass (≤44%)" if tds_pass else "Exceeds 44%", delta_color="normal" if tds_pass else "inverse")
    st.markdown(f"* **Qualifying Housing Cost:** `${qual_housing:,.2f}`")

st.divider()

if approved:
    st.success("✅ **LENDER DECISION: APPROVED** — Both GDS and TDS pass OSFI stress test guidelines.")
else:
    st.error("❌ **LENDER DECISION: DECLINED** — Exceeds regulatory GDS/TDS limits under stress testing.")
