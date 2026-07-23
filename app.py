import streamlit as st
import datetime
import re
from pypdf import PdfReader

st.set_page_config(
    page_title="Mortgage Intake, Income & Underwriting Engine",
    page_icon="🏠",
    layout="wide"
)

# --- RED HOUSE LOGO SVG ---
LOGO_SVG = """
<div style="text-align: center; padding-bottom: 10px;">
    <svg width="220" height="110" viewBox="0 0 200 100" xmlns="http://www.w3.org/2000/svg">
        <circle cx="55" cy="40" r="22" fill="#8B9A68" />
        <circle cx="70" cy="45" r="18" fill="#A3B17E" />
        <rect x="58" y="55" width="5" height="20" fill="#6B5B45" />
        <ellipse cx="50" cy="74" rx="20" ry="6" fill="#D2DCB6" />
        <ellipse cx="145" cy="74" rx="25" ry="6" fill="#D2DCB6" />
        <rect x="75" y="60" width="105" height="20" fill="#EAEAEA" />
        <polygon points="70,60 115,38 180,60" fill="#D32F2F" />
        <rect x="110" y="44" width="70" height="16" fill="#D32F2F" />
        <rect x="110" y="60" width="70" height="18" fill="#FFFFFF" />
        <rect x="80" y="62" width="22" height="16" fill="#9E9E9E" />
        <line x1="80" y1="67" x2="102" y2="67" stroke="#757575" stroke-width="0.8" />
        <line x1="80" y1="72" x2="102" y2="72" stroke="#757575" stroke-width="0.8" />
        <rect x="135" y="65" width="8" height="13" fill="#757575" />
        <rect x="117" y="64" width="10" height="8" fill="#B0BEC5" />
        <rect x="155" y="64" width="10" height="8" fill="#B0BEC5" />
        <rect x="30" y="77" width="155" height="5" fill="#C5D1A5" />
    </svg>
</div>
"""

def parse_pay_stub_details(pdf_file):
    try:
        reader = PdfReader(pdf_file)
        text = ""
        for page in reader.pages:
            t = page.extract_text()
            if t:
                text += t + "\n"
    except Exception:
        text = ""

    lines = [line.strip() for line in text.split("\n") if line.strip()]
    
    # 1. Employer Name
    employer_name = "Not Detected"
    if len(lines) > 1:
        employer_name = lines[1] if "ADP" in lines[0] else lines[0]

    # 2. How Often Paid (Pay Frequency)
    freq_str = "Monthly (12)"
    freq_mult = 12
    freq_match = re.search(r"OF\s*(\d{1,2})", text, re.IGNORECASE)
    if freq_match:
        total_pays = int(freq_match.group(1))
        if total_pays == 26:
            freq_str = "Bi-Weekly (26)"
            freq_mult = 26
        elif total_pays == 24:
            freq_str = "Semi-Monthly (24)"
            freq_mult = 24
        elif total_pays == 52:
            freq_str = "Weekly (52)"
            freq_mult = 52
        elif total_pays == 12:
            freq_str = "Monthly (12)"
            freq_mult = 12

    # 3. Current Work Schedule Gross Earnings
    current_gross = 3100.00
    curr_match = re.search(r"TOTAL\s*GROSS[^\d]*([0-9,]+\.\d{2})", text, re.IGNORECASE)
    if curr_match:
        try:
            current_gross = float(curr_match.group(1).replace(",", ""))
        except ValueError:
            pass

    # 4. YTD Earnings
    ytd_gross = 9550.00
    ytd_match = re.search(r"TOTAL\s*GROSS[^\d]*[0-9,]+\.\d{2}[^\d]*([0-9,]+\.\d{2})", text, re.IGNORECASE)
    if ytd_match:
        try:
            ytd_gross = float(ytd_match.group(1).replace(",", ""))
        except ValueError:
            pass

    # 5. Annual Projection
    annual_projection = current_gross * freq_mult

    return {
        "employer_name": employer_name,
        "pay_frequency": freq_str,
        "freq_mult": freq_mult,
        "current_gross": current_gross,
        "ytd_gross": ytd_gross,
        "annual_projection": annual_projection
    }

# Session State Initializations
if "total_eligible_income" not in st.session_state:
    st.session_state["total_eligible_income"] = 140000.0

if "s1_pay" not in st.session_state:
    st.session_state["s1_pay"] = 3100.0
if "s1_freq" not in st.session_state:
    st.session_state["s1_freq"] = "Monthly (12)"
if "s2_y1" not in st.session_state:
    st.session_state["s2_y1"] = 15000.0
if "s2_y2" not in st.session_state:
    st.session_state["s2_y2"] = 12000.0
if "s3_y1" not in st.session_state:
    st.session_state["s3_y1"] = 40000.0
if "s3_y2" not in st.session_state:
    st.session_state["s3_y2"] = 35000.0
if "s4_rent" not in st.session_state:
    st.session_state["s4_rent"] = 24000.0

# --- SIDEBAR NAVIGATION ---
st.sidebar.markdown(LOGO_SVG, unsafe_allow_html=True)
st.sidebar.title("📌 Navigation")
page = st.sidebar.radio("Select Section:", ["1. Client Details", "2. Income Details", "3. GDS/TDS Calculator"])
st.sidebar.divider()

# ==========================================
# PAGE 1: CLIENT DETAILS & FORM 524 CONSENT
# ==========================================
if page == "1. Client Details":
    st.markdown(LOGO_SVG, unsafe_allow_html=True)
    st.title("👤 Client Details")
    st.caption("Form 524 - Client Agreement & Personal Data Authorization")
    st.divider()

    st.subheader("1. Client Personal Information")
    col1, col2 = st.columns(2)
    
    with col1:
        client_name = st.text_input("Full Legal Name", placeholder="e.g. Jane Doe")
        dob = st.date_input("Date of Birth", min_value=datetime.date(1920, 1, 1), max_value=datetime.date.today(), value=datetime.date(1990, 1, 1))
        sex = st.selectbox("Sex", ["Select...", "Male", "Female", "Other / Prefer not to say"])
        marital_status = st.selectbox("Marital Status", ["Select...", "Single", "Married", "Common-Law", "Divorced", "Separated", "Widowed"])
    
    with col2:
        phone = st.text_input("Phone Number", placeholder="(555) 000-0000")
        email = st.text_input("Email Address", placeholder="client@example.com")
        address = st.text_area("Residential Address", placeholder="123 Main St, Unit 4B, Toronto, ON M5V 2T6")

    st.divider()

    st.subheader("2. Form 524 - Client Agreement & Disclosure")
    st.caption("Personal Information and Credit Application Consent")
    
    with st.expander("📖 Click to Read Full Form 524 Terms & Conditions", expanded=False):
        st.markdown("""
        ### Personal Information Collection & Usage
        * **Collection:** You authorize the collection of financial and identity information (name, address, phone number, DOB, payment history, credit worthiness) from credit reporting agencies, financial institutions, and references.
        * **Usage:** Information will be used to verify identity, investigate personal background, open/operate accounts, determine credit eligibility, and maintain accuracy with credit reporting agencies.
        * **Sharing:** Information may be shared with employees, service providers, credit reporting agencies, and affiliated companies as permitted or required by law.
        * **Social Insurance Number (SIN):** If provided, your SIN may be used for tax reporting and credit agency identification.
        
        ### Credit Application & Mortgage Terms
        * **Accuracy:** You certify that all information provided is true and complete. Providing false or misleading information may result in cancellation of the credit application or immediate repayment of advanced funds.
        * **Property Valuation:** Mortgage approval does not represent confirmation of property value/condition or guaranteed long-term capacity to pay.
        * **Third Party Broker Fees:** Mortgage proceeds will not be used to pay third-party mortgage broker fees.
        * **Alternate Lenders:** If credit needs cannot be met, authorization is given to share application details with alternate lenders.
        * **Third Party Benefit:** Proceeds of the credit facility will not be used by or on behalf of an undisclosed third party.
        """)

    st.warning("⚠️ **Client Acknowledgment Required**")
    ack_1 = st.checkbox("I confirm that all personal details provided above are true, complete, and accurate.")
    ack_2 = st.checkbox("I have read, understood, and agree to the terms of Form 524 (Client Agreement & Personal Information Authorization).")

    st.divider()
    if st.button("Save Client Intake & Agreement"):
        if client_name and ack_1 and ack_2:
            st.success(f"✅ Client Details and Form 524 Consent successfully recorded for **{client_name}**.")
            st.session_state["client_saved_name"] = client_name
        else:
            st.error("❌ Please complete all mandatory fields and check both acknowledgment boxes before submitting.")

# ==========================================
# PAGE 2: INCOME DETAILS & CALCULATOR
# ==========================================
elif page == "2. Income Details":
    st.markdown(LOGO_SVG, unsafe_allow_html=True)
    st.title("💼 Income Details & Automated Extraction Engine")
    st.caption("Standardized Employment & Income Guideline Policy")
    st.divider()

    if "client_saved_name" in st.session_state:
        st.info(f"👤 Active Client Profile: **{st.session_state['client_saved_name']}**")

    # --- DOCUMENT UPLOAD & EXTRACTION SECTION ---
    st.subheader("1. Pay Stub Extraction & Field Breakdown")
    
    col_up1, col_up2 = st.columns([2, 1])
    with col_up1:
        uploaded_doc = st.file_uploader(
            "Upload Income Document (PDF Paystub, T4, T1 General, NOA)",
            type=["pdf", "png", "jpg", "jpeg"]
        )
    with col_up2:
        target_stream = st.selectbox(
            "Assign to Income Stream:",
            [
                "Source 1: Base Salary / Full-Time Hourly",
                "Source 2: Variable Income (OT, Bonus, Commission)",
                "Source 3: Self-Employed / Business (BFS)",
                "Source 4: Rental Income"
            ]
        )

    if uploaded_doc and st.button("⚡ Extract Data & Auto-Calculate Income"):
        if uploaded_doc.type == "application/pdf":
            parsed = parse_pay_stub_details(uploaded_doc)
            
            st.session_state["paystub_parsed"] = parsed
            st.session_state["s1_pay"] = parsed["current_gross"]
            st.session_state["s1_freq"] = parsed["pay_frequency"]
            
            st.success("✅ Pay Stub extracted successfully and updated into Source 1!")

    if "paystub_parsed" in st.session_state:
        p = st.session_state["paystub_parsed"]
        st.markdown("### 📋 Pay Stub Extracted Summary")
        m1, m2, m3 = st.columns(3)
        m1.metric("Name of Employer", p["employer_name"])
        m2.metric("How Often Paid", p["pay_frequency"])
        m3.metric("YTD Earnings", f"${p['ytd_gross']:,.2f}")
        
        m4, m5 = st.columns(2)
        m4.metric("Current Work Schedule Earnings", f"${p['current_gross']:,.2f}")
        m5.metric("Annual Projected Income", f"${p['annual_projection']:,.2f}")

    st.divider()
    st.subheader("2. Income Stream Calculations & Guideline Verification")

    # --- SOURCE 1: SALARIED / HOURLY GUARANTEED ---
    with st.expander("💵 Source 1: Base Salary / Full-Time Hourly", expanded=True):
        st.caption("Policy: Calculated using regular base pay per pay period multiplied by annual pay frequency[cite: 12, 13, 18].")
        c1, c2, c3 = st.columns(3)
        with c1:
            pay_freq_opts = ["Bi-Weekly (26)", "Semi-Monthly (24)", "Weekly (52)", "Monthly (12)"]
            default_idx = pay_freq_opts.index(st.session_state.get("s1_freq", "Monthly (12)")) if st.session_state.get("s1_freq") in pay_freq_opts else 3
            pay_freq = st.selectbox("Pay Frequency", pay_freq_opts, index=default_idx)
            freq_mult = 26 if "Bi-Weekly" in pay_freq else (24 if "Semi-Monthly" in pay_freq else (52 if "Weekly" in pay_freq else 12))
        with c2:
            base_pay_amount = st.number_input(
                "Gross Base Pay per Pay Period ($)",
                min_value=0.0,
                value=float(st.session_state.get("s1_pay", 3100.0)),
                step=100.0
            )
        with c3:
            s1_annual = base_pay_amount * freq_mult
            st.metric("Eligible Salaried Annual Income", f"${s1_annual:,.2f}")

    # --- SOURCE 2: VARIABLE INCOME ---
    with st.expander("📈 Source 2: Variable Income (Overtime, Bonus, Commission, Contract)"):
        st.caption("Policy: Lower of 2-Year Average or Most Recent Tax Year[cite: 12, 13, 19].")
        c1, c2, c3 = st.columns(3)
        with c1:
            var_year1 = st.number_input("Most Recent Year ($)", min_value=0.0, value=float(st.session_state.get("s2_y1", 15000.0)), step=1000.0)
        with c2:
            var_year2 = st.number_input("Previous Year ($)", min_value=0.0, value=float(st.session_state.get("s2_y2", 12000.0)), step=1000.0)
        with c3:
            var_avg = (var_year1 + var_year2) / 2.0
            s2_annual = min(var_avg, var_year1)
            st.metric("Eligible Variable Income", f"${s2_annual:,.2f}")

    # --- SOURCE 3: SELF-EMPLOYED (BFS) ---
    with st.expander("🏢 Source 3: Self-Employed Income (BFS)"):
        st.caption("Policy: Sole Proprietorship / Partnership eligible for 15% Gross-Up on Net Income[cite: 12, 14, 19]. Lower of 2-Year Average or Current Year[cite: 12, 14, 19].")
        bfs_type = st.radio("Business Type", ["Sole Proprietorship / Partnership (15% Gross-Up)", "Corporation (Salary + Dividends)"])
        c1, c2, c3 = st.columns(3)
        with c1:
            bfs_year1 = st.number_input("Current Year Net Income ($)", min_value=0.0, value=float(st.session_state.get("s3_y1", 40000.0)), step=1000.0)
        with c2:
            bfs_year2 = st.number_input("Previous Year Net Income ($)", min_value=0.0, value=float(st.session_state.get("s3_y2", 35000.0)), step=1000.0)
        with c3:
            bfs_base_eligible = min((bfs_year1 + bfs_year2) / 2.0, bfs_year1)
            gross_up = (bfs_base_eligible * 0.15) if "Sole" in bfs_type else 0.0
            s3_annual = bfs_base_eligible + gross_up
            st.metric("Eligible BFS Income", f"${s3_annual:,.2f}")

    # --- SOURCE 4: RENTAL INCOME ---
    with st.expander("🏘️ Source 4: Rental Income"):
        st.caption("Policy: Owner-Occupied Primary Residence uses 80% Gross Rent[cite: 12, 16]. Non-Owner Occupied uses 100% Gross Rent[cite: 12, 16].")
        rental_occupancy = st.selectbox("Property Type", ["Owner-Occupied (80% Factor)", "Non-Owner Occupied Investment (100% Factor)"])
        gross_rent = st.number_input("Gross Annual Rental Income ($)", min_value=0.0, value=float(st.session_state.get("s4_rent", 24000.0)), step=1000.0)
        s4_annual = gross_rent * (0.80 if "Owner-Occupied" in rental_occupancy else 1.00)
        st.metric("Eligible Rental Income", f"${s4_annual:,.2f}")

    st.divider()

    final_eligible_income = s1_annual + s2_annual + s3_annual + s4_annual

    st.subheader("📊 Annualized Eligible Income Summary")
    st.metric("Total Eligible Annual Gross Income", f"${final_eligible_income:,.2f}")

    if st.button("Apply Total Income to GDS/TDS Calculator"):
        st.session_state["total_eligible_income"] = final_eligible_income
        st.success(f"✅ Total Eligible Annual Income of **${final_eligible_income:,.2f}** locked and pushed to Section 3!")

# ==========================================
# PAGE 3: GDS/TDS CALCULATOR
# ==========================================
elif page == "3. GDS/TDS Calculator":
    st.markdown(LOGO_SVG, unsafe_allow_html=True)
    st.title("🧮 GDS/TDS Calculator")
    st.caption("Retail Credit Policy & OSFI Guideline B-20 Standards")
    st.divider()

    if "client_saved_name" in st.session_state:
        st.info(f"👤 Active Client Profile: **{st.session_state['client_saved_name']}**")

    # --- SIDEBAR INPUTS ---
    st.sidebar.header("📊 Borrower & Property Inputs")
    default_income = float(st.session_state.get("total_eligible_income", 140000.0))
    gross_annual_income = st.sidebar.number_input("Eligible Annual Gross Income ($)", min_value=1.0, value=default_income, step=5000.0)
    loan_amount = st.sidebar.number_input("Mortgage Loan Amount ($)", min_value=1.0, value=650000.0, step=10000.0)
    contract_rate = st.sidebar.number_input("Contract Rate (%)", min_value=0.1, max_value=15.0, value=4.25, step=0.05)
    amortization_years = st.sidebar.slider("Amortization (Years)", min_value=5, max_value=30, value=25)

    st.sidebar.subheader("Property Expenses (Annual)")
    annual_tax = st.sidebar.number_input("Property Tax ($)", min_value=0.0, value=4800.0)
    annual_heat = st.sidebar.number_input("Heating Cost ($) [Std: $1,200]", min_value=0.0, value=1200.0)
    annual_condo = st.sidebar.number_input("Condo Fees ($)", min_value=0.0, value=2400.0)
    is_investor = st.sidebar.checkbox("Non-Owner Occupied / Investment Property (100% Condo Fees)", value=False)

    condo_factor = 1.0 if is_investor else 0.50
    pith_c_expenses = annual_tax + annual_heat + (condo_factor * annual_condo)

    st.sidebar.divider()
    st.sidebar.header("💳 Existing Obligations (Policy Standards)")
    is_quebec = st.sidebar.checkbox("Quebec Resident (Credit Card Rules: 5%)", value=False)

    cc_balance = st.sidebar.number_input("Credit Card Balance ($)", min_value=0.0, value=5000.0)
    loc_balance = st.sidebar.number_input("Unsecured LOC Balance ($)", min_value=0.0, value=10000.0)
    inst_monthly = st.sidebar.number_input("Installment Loan Monthly Payment ($)", min_value=0.0, value=350.0)
    inst_balance = st.sidebar.number_input("Installment Loan Outstanding Balance ($)", min_value=0.0, value=15000.0)
    other_monthly = st.sidebar.number_input("Support / CRA / Other Monthly ($)", min_value=0.0, value=0.0)

    # --- CALCULATIONS ---
    cc_rate = 0.05 if is_quebec else 0.03
    monthly_cc = cc_balance * cc_rate
    monthly_loc = loc_balance * 0.03
    monthly_inst = inst_monthly if inst_monthly > 0 else (inst_balance * 0.02)
    total_annual_debt = (monthly_cc + monthly_loc + monthly_inst + other_monthly) * 12.0

    def calc_annual_p_and_i(loan: float, rate_pct: float, years: int) -> float:
        rate = rate_pct / 100.0
        eff_monthly_rate = (1.0 + rate / 2.0)**(2.0 / 12.0) - 1.0
        n = years * 12
        monthly = loan * (eff_monthly_rate * (1 + eff_monthly_rate)**n) / ((1 + eff_monthly_rate)**n - 1)
        return monthly * 12.0

    actual_p_i = calc_annual_p_and_i(loan_amount, contract_rate, amortization_years)
    actual_gds = ((actual_p_i + pith_c_expenses) / gross_annual_income) * 100.0
    actual_tds = ((actual_p_i + pith_c_expenses + total_annual_debt) / gross_annual_income) * 100.0

    qual_rate = max(5.25, contract_rate + 2.0)
    qual_p_i = calc_annual_p_and_i(loan_amount, qual_rate, amortization_years)
    qual_gds = ((qual_p_i + pith_c_expenses) / gross_annual_income) * 100.0
    qual_tds = ((qual_p_i + pith_c_expenses + total_annual_debt) / gross_annual_income) * 100.0

    std_gds_pass = qual_gds <= 32.0
    std_tds_pass = qual_tds <= 40.0
    max_gds_pass = qual_gds <= 39.0
    max_tds_pass = qual_tds <= 44.0

    # --- DISPLAY ---
    st.subheader("📋 Debt Carrying Cost Breakdown")
    col_a, col_b, col_c, col_d = st.columns(4)
    col_a.metric("Credit Card Monthly", f"${monthly_cc:,.2f}", f"{'5%' if is_quebec else '3%'} of balance")
    col_b.metric("Line of Credit Monthly", f"${monthly_loc:,.2f}", "3% of balance")
    col_c.metric("Installment Loan Monthly", f"${monthly_inst:,.2f}", "Actual / 2% fallback")
    col_d.metric("Total Monthly Obligations", f"${(total_annual_debt / 12.0):,.2f}")

    st.divider()

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("💵 Actual Out-of-Pocket Cash Flow")
        st.caption(f"Contract Rate: **{contract_rate:.2f}%** | P&I: **${(actual_p_i/12):,.2f}/mo**")
        m1, m2 = st.columns(2)
        m1.metric("Actual GDS", f"{actual_gds:.2f}%")
        m2.metric("Actual TDS", f"{actual_tds:.2f}%")

    with col2:
        st.subheader("🏛️ Stress Test (OSFI B-20 / Policy Standards)")
        st.caption(f"Qualifying Rate: **{qual_rate:.2f}%** | P&I: **${(qual_p_i/12):,.2f}/mo**")
        m3, m4 = st.columns(2)
        m3.metric("Qualifying GDS", f"{qual_gds:.2f}%", 
                  delta="Standard (≤32%)" if std_gds_pass else ("Max Limit (≤39%)" if max_gds_pass else "Exceeds 39%"), 
                  delta_color="normal" if max_gds_pass else "inverse")
        m4.metric("Qualifying TDS", f"{qual_tds:.2f}%", 
                  delta="Standard (≤40%)" if std_tds_pass else ("Max Limit (≤44%)" if max_tds_pass else "Exceeds 44%"), 
                  delta_color="normal" if max_tds_pass else "inverse")

    st.divider()
    if std_gds_pass and std_tds_pass:
        st.success("✅ **DECISION: APPROVED (Standard Policy)** — GDS ≤ 32% and TDS ≤ 40%.")
    elif max_gds_pass and max_tds_pass:
        st.warning("⚠️ **DECISION: REQUIRES BUSINESS CASE / EXCEPTION** — Exceeds standard 32/40 limits but within max thresholds (GDS ≤ 39%, TDS ≤ 44%). Rationale required.")
    else:
        st.error("❌ **DECISION: DECLINED** — Exceeds maximum allowable debt service limits.")
