import os
import time
from datetime import datetime
import streamlit as st
import smtplib
from email.message import EmailMessage
from persistence import delete_report_file, list_saved_reports, load_state, save_report_html, save_state

# ═════════════════ CONFIGURATION ═════════════════
APP_VERSION = "AILY OS v30000 — GREEN EMERALD CORE"
RECEIVER_EMAIL = "garryboypepito2004@gmail.com"
RECEIVER_AILYN = "ailyn_peps0678@yahoo.com"
SENDER_EMAIL = "garryboypepito71@gmail.com"
SENDER_PASSWORD = "fhyv cimp gync wjmj"

# ═════════════════ PAGE CONFIG ═════════════════
st.set_page_config(
    page_title="Ailyn Construction Management",
    page_icon="🧊",
    layout="wide",
)

# ═════════════════ SESSION STATE ═════════════════
state_data = load_state()

for key, value in state_data.items():
    if key not in st.session_state:
        st.session_state[key] = value

if "records" not in st.session_state:
    st.session_state.records = []

if "labor_records" not in st.session_state:
    st.session_state.labor_records = []

if "payroll_expenses" not in st.session_state:
    st.session_state.payroll_expenses = []

if "budget" not in st.session_state:
    st.session_state.budget = 0.0

if "remaining_money" not in st.session_state:
    st.session_state.remaining_money = 0.0

if "view" not in st.session_state:
    st.session_state.view = "home"

# ═════════════════ CORE LOGIC (MATERIAL/EXPENSE) ═════════════════
def set_view(v):
    st.session_state.view = v
    persist_state()
    st.rerun()

def total_materials():
    return sum(r["amount"] for r in st.session_state.records if r["type"] == "material")

def total_expenses():
    return sum(r["amount"] for r in st.session_state.records if r["type"] == "expense")

def total_excess():
    return sum(r["amount"] for r in st.session_state.records if r["type"] == "excess")

def get_total():
    return total_materials() + total_expenses()

def get_balance():
    return float(st.session_state.budget) + total_excess() - get_total()

def clear_all():
    st.session_state.records = []
    st.session_state.labor_records = []
    st.session_state.payroll_expenses = []
    st.session_state.budget = 0.0
    st.session_state.remaining_money = 0.0
    st.session_state.view = "home"
    save_state(st.session_state)


def persist_state():
    save_state(st.session_state)

def add_tx(name, price, qty, delivery, ttype, sender):
    if float(price) <= 0 or int(qty) <= 0:
        return False

    amount = (float(price) * int(qty)) + float(delivery) if ttype == "material" else float(price)

    st.session_state.records.append({
        "id": str(time.time()),
        "date": datetime.now().strftime("%b %d, %Y"),
        "name": name.upper(),
        "price": float(price),
        "qty": int(qty),
        "delivery": float(delivery),
        "amount": float(amount),
        "type": ttype,
        "sender": sender
    })
    persist_state()
    return True

# ═════════════════ REPORT MANAGER (MATERIAL) ═════════════════
def build_html_report(records, budget):
    material_total = total_materials()
    expense_total = total_expenses()
    excess_total = total_excess()
    remaining_balance = get_balance()
    date_now = datetime.now().strftime("%B %d, %Y")

    sobra_amount = 0.0
    kulang_amount = 0.0

    if remaining_balance > 0:
        sobra_amount = remaining_balance
    elif remaining_balance < 0:
        kulang_amount = abs(remaining_balance)

    if budget <= 0:
        balance_color = "#ffffff"
    else:
        balance_color = "#e57373" if remaining_balance < 0 else "#a5d6a7"

    html = f"""
    <html>
    <head>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
            body {{ font-family: 'Inter', sans-serif; background-color: #f0f4f0; margin: 0; padding: 20px; color: #333; }}
            .receipt-container {{ max-width: 1000px; margin: auto; background: #fff; padding: 30px; border-radius: 4px; box-shadow: 0 4px 20px rgba(0,0,0,0.08); border-top: 10px solid #1b5e20; }}
            .header {{ display: flex; flex-wrap: wrap; justify-content: space-between; align-items: flex-start; margin-bottom: 30px; border-bottom: 2px solid #f0f0f0; padding-bottom: 15px; }}
            .company-info h1 {{ color: #1b5e20; margin: 0; font-size: 24px; letter-spacing: -1px; }}
            .company-info p {{ margin: 4px 0; font-size: 12px; color: #666; }}
            .receipt-meta {{ text-align: left; margin-top: 10px; }}
            @media (min-width: 768px) {{ .receipt-meta {{ text-align: right; margin-top: 0; }} }}
            .receipt-meta h2 {{ margin: 0; font-size: 16px; text-transform: uppercase; color: #1b5e20; }}
            .receipt-meta p {{ margin: 4px 0; font-size: 12px; font-weight: bold; }}

            table {{ width: 100%; border-collapse: collapse; margin-bottom: 20px; font-size: 12px; }}
            th {{ background-color: #1b5e20; color: #ffffff; text-align: left; padding: 10px; text-transform: uppercase; letter-spacing: 1px; }}
            td {{ padding: 10px 8px; border-bottom: 1px solid #f0f0f0; }}
            .qty-col, .desccol, .pricecol, .deliverycol, .totalcol {{ text-align: left; }}
            .desccol {{ font-weight: 700; color: #1b5e20; }}

            .summary-container {{ display: flex; justify-content: flex-end; }}
            .summary-table {{ width: 100%; }}
            @media (min-width: 768px) {{ .summary-table {{ width: 420px; }} }}
            .grand-total {{ background: #1b5e20; color: white; padding: 20px; border-radius: 4px; margin-top: 15px; }}

            .balance-info {{ font-size: 13px; line-height: 1.8; }}
            .balance-row {{ display: flex; justify-content: space-between; }}
            .material-row {{ font-size: 18px; font-weight: bold; }}
            .final-balance-row {{ display: flex; justify-content: space-between; border-top: 1px dashed rgba(255,255,255,0.4); margin-top: 8px; padding-top: 8px; font-size: 18px; font-weight: bold; }}

            .footer {{ margin-top: 30px; text-align: center; font-size: 9px; color: #aaa; text-transform: uppercase; letter-spacing: 1px; }}
        </style>
    </head>
    <body>
        <div class="receipt-container">
            <div class="header">
                <div class="company-info">
                    <h1>AILYN HOUSE PROJECT</h1>
                    <p>Official Material & Expense Inventory</p>
                    <p>Management System {APP_VERSION}</p>
                    <p>Backup Receiver: <i>{RECEIVER_AILYN}</i></p>
                </div>
                <div class="receipt-meta">
                    <h2>Inventory Receipt</h2>
                    <p>Date: {date_now}</p>
                </div>
            </div>

            <table>
                <thead>
                    <tr>
                        <th>Date</th>
                        <th class="qty-col">Qty</th>
                        <th class="desccol">Description</th>
                        <th class="pricecol">Unit Price</th>
                        <th class="deliverycol">Delivery</th>
                        <th class="totalcol">Total</th>
                    </tr>
                </thead>
                <tbody>
    """

    for r in records:
        html += f"""
                    <tr>
                        <td>{r['date']}</td>
                        <td class="qty-col">{r['qty']}</td>
                        <td class="desccol">{r['name']}</td>
                        <td class="pricecol">{float(r.get('price', r['amount'])):,.2f}</td>
                        <td class="deliverycol">{float(r['delivery']):,.2f}</td>
                        <td class="totalcol">PHP {float(r['amount']):,.2f}</td>
                    </tr>
        """

    html += f"""
                </tbody>
            </table>

            <div class="summary-container">
                <div class="summary-table">
                    <div class="grand-total">
                        <div class="balance-info">
                            <div class="balance-row material-row">
                                <span>Material/Expense Total:</span>
                                <span>PHP {material_total + expense_total:,.2f}</span>
                            </div>
                            <div class="balance-row" style="font-size: 13px;">
                                <span>Excess Money Total:</span>
                                <span>PHP {excess_total:,.2f}</span>
                            </div>
                            <div class="balance-row" style="font-size: 13px;">
                                <span>Total Budget:</span>
                                <span>PHP {budget:,.2f}</span>
                            </div>
    """

    if sobra_amount > 0:
        html += f"""
                            <div class="final-balance-row">
                                <span>EXCESS</span>
                                <span style="color: #a5d6a7;">PHP {sobra_amount:,.2f}</span>
                            </div>
        """

    if kulang_amount > 0:
        html += f"""
                            <div class="final-balance-row">
                                <span>SHORTAGE</span>
                                <span style="color: #e57373;">PHP {kulang_amount:,.2f}</span>
                            </div>
        """

    html += f"""
                            <div class="final-balance-row">
                                <span>FINAL BALANCE</span>
                                <span style="color: {balance_color};">PHP {remaining_balance:,.2f}</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <div class="footer">
                This document was electronically generated and is valid without signature.
            </div>
        </div>
    </body>
    </html>
    """
    return html

# ═════════════════ REPORT MANAGER (PAYROLL) ═════════════════
def generate_payroll_html(labor_records, expense_records, remaining_money=0.0):
    date_str = datetime.now().strftime("%B %d, %Y | %I:%M %p")
    total_labor = sum(r['net'] for r in labor_records)
    total_expenses = sum(e['price'] for e in expense_records)
    
    sub_total = total_labor + total_expenses
    grand_total = sub_total - remaining_money

    html = f"""
    <html>
    <body style="font-family: 'Segoe UI', sans-serif; background-color: #f4f7f6; padding: 40px;">
    <div style="max-width: 900px; margin: auto; background: white; border-top: 10px solid #1b5e20; padding: 40px; border-radius: 8px; box-shadow: 0 4px 15px rgba(0,0,0,0.1);">

        <table style="width: 100%; border-collapse: collapse; margin-bottom: 30px;">
            <tr>
                <td>
                    <h1 style="color: #1b5e20; margin: 0; text-transform: uppercase;">Ailyn Construction</h1>
                    <p style="color: #555; margin: 5px 0 0 0;">Official Labor & Payroll Inventory</p>
                    <p style="color: #777; font-size: 14px; margin: 0;">Management System v3.6 Enterprise</p>
                </td>
                <td style="text-align: right;">
                    <h3 style="color: #1b5e20; margin: 0;">INVENTORY RECEIPT</h3>
                    <p style="color: #555; font-size: 14px; margin: 5px 0 0 0;">Date: {date_str}</p>
                    <p style="color: #777; font-size: 12px; margin: 5px 0 0 0;">Account: {RECEIVER_EMAIL}</p>
                </td>
            </tr>
        </table>

        <div style="border-bottom: 2px solid #eee; margin-bottom: 30px;"></div>

        <table style="width: 100%; border-collapse: collapse; margin-bottom: 30px;">
            <thead>
                <tr style="background-color: #1b5e20; color: white; text-transform: uppercase; font-size: 14px;">
                    <th style="padding: 12px; text-align: left;">Worker Name</th>
                    <th style="padding: 12px; text-align: center;">Days</th>
                    <th style="padding: 12px; text-align: right;">Rate</th>
                    <th style="padding: 12px; text-align: right;">C.A.</th>
                    <th style="padding: 12px; text-align: right;">Net Pay</th>
                </tr>
            </thead>
            <tbody>
    """

    for r in labor_records:
        html += f"""
                <tr>
                    <td style="padding: 12px; border-bottom: 1px solid #ddd; font-weight: bold;">{r['name']}</td>
                    <td style="padding: 12px; border-bottom: 1px solid #ddd; text-align: center;">{r['days']}</td>
                    <td style="padding: 12px; border-bottom: 1px solid #ddd; text-align: right;">{r['rate']:,.2f}</td>
                    <td style="padding: 12px; border-bottom: 1px solid #ddd; text-align: right; color: #d32f2f;">({r['ca']:,.2f})</td>
                    <td style="padding: 12px; border-bottom: 1px solid #ddd; text-align: right; font-weight: bold; color: #1b5e20;">{r['net']:,.2f}</td>
                </tr>
        """

    if expense_records:
        html += """
                <tr>
                    <td colspan="5" style="padding: 12px 0;"></td>
                </tr>
                <tr style="background-color: #388e3c; color: white; text-transform: uppercase; font-size: 14px;">
                    <th colspan="4" style="padding: 10px; text-align: left;">Expense Description</th>
                    <th style="padding: 10px; text-align: right;">Amount</th>
                </tr>
        """
        for e in expense_records:
            html += f"""
                <tr>
                    <td colspan="4" style="padding: 10px; border-bottom: 1px solid #ddd;">{e['item']}</td>
                    <td style="padding: 10px; border-bottom: 1px solid #ddd; text-align: right; font-weight: bold;">{e['price']:,.2f}</td>
                </tr>
            """

    html += f"""
            </tbody>
        </table>

        <table style="width: 100%; border-collapse: collapse; margin-top: 20px; margin-bottom: 30px;">
            <tr style="border-top: 2px solid #bbb;">
                <td style="padding: 12px; font-weight: bold; text-align: right; font-size: 15px;">Subtotal Expenses:</td>
                <td style="padding: 12px; width: 180px; text-align: right; font-weight: bold; font-size: 15px; color: #333;">PHP {sub_total:,.2f}</td>
            </tr>
    """

    if remaining_money > 0:
        html += f"""
            <tr style="border-bottom: 2px solid #bbb;">
                <td style="padding: 12px; font-weight: bold; text-align: right; color: #d32f2f; font-size: 15px;">Remaining/Leftover Money:</td>
                <td style="padding: 12px; width: 180px; text-align: right; font-weight: bold; color: #d32f2f; font-size: 15px;">-PHP {remaining_money:,.2f}</td>
            </tr>
        """

    html += f"""
        </table>

        <table style="width: 100%; border-collapse: collapse; margin-top: 20px;">
            <tr>
                <td></td>
                <td style="width: 350px; background: #1b5e20; color: white; padding: 20px; border-radius: 8px; text-align: right;">
                    <span style="font-size: 14px; text-transform: uppercase; letter-spacing: 1px;">Final Output Amount</span><br>
                    <span style="font-size: 32px; font-weight: bold; margin-top: 5px; display: inline-block;">PHP {grand_total:,.2f}</span>
                </td>
            </tr>
        </table>

        <div style="text-align: center; margin-top: 60px; border-top: 1px solid #eee; padding-top: 20px;">
            <p style="color: #999; font-size: 11px; letter-spacing: 1px; text-transform: uppercase;">
                THIS DOCUMENT WAS ELECTRONICALLY GENERATED AND IS VALID WITHOUT SIGNATURE.
            </p>
        </div>

    </div>
    </body>
    </html>
    """
    return html, grand_total

# ═════════════════ CSS & 3D GREEN INTERFACE ═════════════════
st.markdown("""
<style>
:root {
    --bg-deep: #07110b;
    --bg-panel: rgba(8, 24, 15, 0.78);
    --bg-panel-2: rgba(13, 39, 24, 0.9);
    --line: rgba(132, 255, 179, 0.16);
    --text-main: #f4fff7;
    --text-soft: #acebb3;
    --accent: #4ade80;
    --accent-strong: #22c55e;
    --accent-warm: #fbbf24;
}

@media (max-width: 768px) {
    .block-container {
        padding: 12px !important;
    }
    h1, h2, h3 {
        font-size: 18px !important;
        text-align: center;
    }
    button {
        width: 100% !important;
        margin-bottom: 8px !important;
        font-size: 15px !important;
        padding: 12px !important;
    }
    input {
        font-size: 16px !important;
    }
    .stColumns {
        flex-direction: column !important;
    }
}

.stApp {
    background: url("https://images.unsplash.com/photo-1600585154340-be6161a56a0c") no-repeat center center fixed;
    background-size: cover;
    background-position: center;
    min-height: 100vh;
}

.block-container {
    background: rgba(20, 50, 35, 0.68) !important;
    backdrop-filter: blur(18px);
    border-radius: 24px;
    border: 1px solid rgba(135, 255, 180, 0.18);
    box-shadow: 0 18px 54px rgba(0, 0, 0, 0.38);
    padding: 24px;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.block-container:hover {
    transform: translateY(-1px);
    box-shadow: 0 22px 64px rgba(72, 239, 127, 0.16);
}

section[data-testid="stSidebar"] {
    background: rgba(6, 19, 13, 0.96) !important;
    backdrop-filter: blur(20px);
    border-right: 1px solid rgba(132, 255, 179, 0.14);
}

button, .stDownloadButton > button {
    background: linear-gradient(145deg, rgba(11, 78, 47, 0.96), rgba(22, 122, 68, 0.92));
    color: #ffffff !important;
    border-radius: 16px !important;
    transition: all 0.16s ease-in-out;
    border: 1px solid rgba(135, 255, 180, 0.28);
    font-weight: 700;
    min-height: 46px;
    box-shadow:
        inset 0 1px 0 rgba(255,255,255,0.16),
        0 8px 18px rgba(0, 0, 0, 0.22),
        0 2px 8px rgba(34, 197, 94, 0.18);
    backdrop-filter: blur(10px);
}

button:hover, .stDownloadButton > button:hover {
    transform: translateY(-2px);
    box-shadow:
        inset 0 1px 0 rgba(255,255,255,0.2),
        0 12px 24px rgba(72, 239, 127, 0.24),
        0 4px 12px rgba(0, 0, 0, 0.24);
    border-color: rgba(163, 230, 53, 0.7);
    background: linear-gradient(145deg, rgba(22, 122, 68, 0.98), rgba(20, 164, 77, 0.96));
}

button:active, .stDownloadButton > button:active {
    transform: scale(0.98);
    box-shadow: inset 0 2px 8px rgba(0,0,0,0.24);
}

input, textarea, select {
    background: rgba(255, 255, 255, 0.1) !important;
    border: 1px solid rgba(135, 255, 180, 0.24) !important;
    color: #f8fff9 !important;
    border-radius: 12px !important;
    backdrop-filter: blur(10px);
    font-size: 15px !important;
    min-height: 44px;
    padding: 8px 12px;
    transition: border-color 0.15s ease, box-shadow 0.15s ease, transform 0.15s ease;
}

input:focus, textarea:focus, select:focus {
    border-color: #22c55e !important;
    box-shadow: 0 0 10px rgba(34, 197, 94, 0.28);
    transform: translateY(-1px);
}

h1, h2, h3 {
    color: #ecfff1 !important;
    text-shadow: 0 0 8px rgba(34, 197, 94, 0.22);
    letter-spacing: 0.4px;
}

[data-testid="stMetric"] {
    background: linear-gradient(145deg, rgba(14, 44, 24, 0.95), rgba(8, 32, 18, 0.9));
    border-radius: 18px;
    padding: 12px;
    border: 1px solid rgba(132, 255, 179, 0.16);
    margin-bottom: 12px;
    box-shadow: 0 10px 24px rgba(0, 0, 0, 0.24);
    transition: transform 0.2s ease, border-color 0.2s ease;
}

[data-testid="stMetric"]:hover {
    transform: translateY(-2px);
    border-color: rgba(132, 255, 179, 0.42);
}

[data-testid="stMetric"] label {
    color: #b8f5c1 !important;
    font-weight: 600;
}

[data-testid="stMetric"] div[data-testid="stMetricValue"] {
    color: #ffffff !important;
}

.stAlert, .stSuccess, .stWarning, .stInfo {
    border-radius: 12px !important;
    border: 1px solid rgba(132, 255, 179, 0.16) !important;
    box-shadow: 0 8px 20px rgba(0, 0, 0, 0.16) !important;
}

.hero-card {
    background: linear-gradient(135deg, rgba(12, 34, 21, 0.9), rgba(5, 20, 12, 0.8));
    border: 1px solid rgba(135, 255, 180, 0.18);
    border-radius: 24px;
    padding: 22px 24px;
    margin-bottom: 18px;
    box-shadow:
        inset 0 1px 0 rgba(255,255,255,0.08),
        0 16px 44px rgba(0, 0, 0, 0.28);
    backdrop-filter: blur(12px);
}

.hero-badge {
    display: inline-block;
    padding: 6px 10px;
    border-radius: 999px;
    background: rgba(74, 222, 128, 0.14);
    color: #b7f5c2;
    font-size: 12px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin-bottom: 10px;
}

.section-pill {
    display: inline-block;
    padding: 6px 10px;
    border-radius: 999px;
    background: rgba(251, 191, 36, 0.12);
    color: #fde68a;
    font-size: 12px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin-bottom: 10px;
}

.sidebar-brand {
    padding: 8px 10px 12px 10px;
    border-radius: 16px;
    background: linear-gradient(135deg, rgba(15, 41, 25, 0.96), rgba(7, 23, 14, 0.92));
    border: 1px solid rgba(132, 255, 179, 0.16);
    margin-bottom: 12px;
}

.sidebar-brand h3 {
    margin: 0 0 4px 0;
    color: #ecfff1 !important;
    font-size: 16px;
}

.sidebar-brand p {
    margin: 0;
    color: #b8f5c1;
    font-size: 12px;
}

.intro {
    text-align: center;
    color: #ffffff;
}

.intro h1 {
    font-size: 30px;
    font-weight: 800;
    color: #ecfff1;
    margin: 0;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    font-family: 'Georgia', 'Times New Roman', serif;
    text-shadow: 0 2px 10px rgba(255,255,255,0.12);
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero-card intro">
    <h1>🏗️ AILYN HOUSE PROJECT & PAYROLL</h1>
</div>
""", unsafe_allow_html=True)

# 🎛 CONTROL HUB
with st.sidebar:
    st.markdown("""
    <div class="sidebar-brand">
        <h3>📱 AILY MOBILE CONTROL</h3>
        <p>Construction • Payroll • Receipts</p>
    </div>
    """, unsafe_allow_html=True)
    
    budget_input = st.number_input("Set Project Budget", min_value=0.0, key="budget_input_sidebar", value=st.session_state.budget)
    if st.button("APPLY BUDGET", use_container_width=True):
        st.session_state.budget = float(budget_input)
        persist_state()
        st.success("Budget applied!")
        st.rerun()
        
    st.caption(f"{datetime.now().strftime('%I:%M %p | %b %d')}")
    st.divider()

    st.subheader("🏠 Navigation")
    if st.button("🏠 Project Summary / Home", use_container_width=True):
        set_view("home")
        
    st.markdown("---")
    st.subheader("🧱 Construction Ledger")
    if st.button("➕ Add Material", use_container_width=True):
        set_view("material")
    if st.button("📝 Add Construction Expense", use_container_width=True):
        set_view("expense")
    if st.button("💰 Add Excess Money", use_container_width=True):
        set_view("excess")
    if st.button("📋 View Project Ledger", use_container_width=True):
        set_view("ledger")
    if st.button("📤 Export Construction Report", use_container_width=True):
        set_view("export")
        
    st.markdown("---")
    st.subheader("👷 Payroll System")
    if st.button("➕ Add Labor", use_container_width=True):
        set_view("add_labor")
    if st.button("📝 Add Payroll Expense", use_container_width=True):
        set_view("add_payroll_expense")
    if st.button("➖ Set Remaining/Leftover", use_container_width=True):
        set_view("payroll_remaining")
    if st.button("📋 View Labor Records", use_container_width=True):
        set_view("payroll_ledger")
    if st.button("📤 Export Payroll Report", use_container_width=True):
        set_view("payroll_export")
    if st.button("📁 Receipt Archive", use_container_width=True):
        set_view("receipt_archive")
    
    st.divider()
    
    if st.button("🔄 RESET SYSTEM", use_container_width=True):
        clear_all()
        set_view("home")

# 🖥 VIEWS
view = st.session_state.view

# 🏠 HOME
if view == "home":
    st.markdown("<div class='section-pill'>Live overview</div>", unsafe_allow_html=True)
    st.subheader("📊 QUICK STATS")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("BUDGET", f"PHP {st.session_state.budget:,.2f}")
    col2.metric("USED", f"PHP {get_total():,.2f}")
    col3.metric("BALANCE", f"PHP {get_balance():,.2f}")
    
    st.markdown("---")
    
    st.subheader("📋 MATERIALS LEDGER PREVIEW")
    if not st.session_state.records:
        st.info("No materials yet.")
    else:
        materials = [r for r in st.session_state.records if r["type"] == "material"]
        for r in materials[-5:]:
            st.markdown(f"""
            ---
            🧱 **{r['name']}** 💰 PHP {float(r['amount']):,.2f}  
            👤 {r['sender']}  
            📅 {r['date']}
            """)

# ➕ MATERIAL
elif view == "material":
    st.subheader("➕ MATERIAL (LOOP MODE)")

    with st.form(key="material_form", clear_on_submit=True):
        name = st.text_input("Material Name")
        price = st.number_input("Price", min_value=0.01, value=0.01)
        qty = st.number_input("Qty", min_value=1, value=1)
        delivery = st.number_input("Delivery", min_value=0.0, value=0.0)
        sender = st.selectbox("Sender", ["Garr", "Aily"])
        
        submitted = st.form_submit_button(label="SAVE MATERIAL")

    if submitted:
        ok = add_tx(name, price, qty, delivery, "material", sender)
        if ok:
            st.success("Saved! Ready for next order.")
            st.rerun()
        else:
            st.warning("Invalid data, please check amounts.")

    st.divider()
    if st.button("🏁 FINISH LOOP", use_container_width=True):
        set_view("home")

# 📝 EXPENSE
elif view == "expense":
    st.subheader("📝 EXPENSE (LOOP MODE)")

    with st.form(key="expense_form", clear_on_submit=True):
        name = st.text_input("Expense Name")
        amount = st.number_input("Amount", min_value=0.01, value=0.01)
        sender = st.selectbox("Sender", ["Garr", "Aily"])
        
        submitted = st.form_submit_button(label="SAVE EXPENSE")

    if submitted:
        if amount > 0:
            add_tx(name, amount, 1, 0, "expense", sender)
            st.success("Expense Added → Ledger Updated")
            st.rerun()
        else:
            st.warning("Amount must be greater than zero.")

    st.divider()
    if st.button("🏁 FINISH LOOP", use_container_width=True):
        set_view("home")

# 💰 EXCESS
elif view == "excess":
    st.subheader("💰 EXCESS (LOOP MODE)")

    with st.form(key="excess_form", clear_on_submit=True):
        name = st.text_input("Reason")
        amount = st.number_input("Amount", min_value=0.01, value=0.01)
        sender = st.selectbox("Sender", ["Garr", "Aily"])
        
        submitted = st.form_submit_button(label="ADD EXCESS")

    if submitted:
        if amount > 0:
            st.session_state.records.append({
                "id": str(time.time()),
                "date": datetime.now().strftime("%b %d, %Y"),
                "name": name.upper(),
                "price": float(amount),
                "qty": 1,
                "delivery": 0.0,
                "amount": float(amount),
                "type": "excess",
                "sender": sender
            })
            persist_state()
            st.success("Excess Added")
            st.rerun()
        else:
            st.warning("Please enter a valid amount.")

    st.divider()
    if st.button("🏁 FINISH LOOP", use_container_width=True):
        set_view("home")

# 📋 LEDGER
elif view == "ledger":
    st.subheader("📋 CONSTRUCTION LEDGER (MOBILE VIEW)")

    if not st.session_state.records:
        st.info("No transaction records found in ledger.")
    else:
        for r in list(st.session_state.records):
            st.markdown(f"""
            ---
            **{r['name']}** 💰 PHP {float(r['amount']):,.2f}  
            👤 {r['sender']}  
            📦 {r['type']}  
            📅 {r['date']}
            """)

            if st.button("❌ DELETE", key=f"del_{r['id']}", use_container_width=True):
                st.session_state.records = [
                    x for x in st.session_state.records if x["id"] != r["id"]
                ]
                persist_state()
                st.rerun()

# 📤 EXPORT
elif view == "export":
    st.subheader("📤 EXPORT CONSTRUCTION REPORT")

    html = build_html_report(st.session_state.records, st.session_state.budget)
    receipt_title = st.text_input("Receipt title", value="Construction Receipt", placeholder="Enter a title for this receipt")

    if st.button("💾 Save this receipt to archive", use_container_width=True):
        if receipt_title.strip():
            archive_path = save_report_html("construction", html, title=receipt_title)
            st.success(f"Saved to archive: {archive_path}")
        else:
            st.warning("Please enter a title before saving.")

    st.download_button(
        label="⬇️ Download current construction report",
        data=html,
        file_name="aily_mobile_report.html",
        mime="text/html",
        use_container_width=True
    )

    if st.button("📁 Open receipt archive", use_container_width=True):
        set_view("receipt_archive")

    st.markdown("📧 **Receivers Enabled:**")
    st.write("Garry ✔")
    st.write("Aily ✔")
    st.write(f"{RECEIVER_AILYN} ✔")

# 👷 Payroll Views
elif view == "add_labor":
    st.subheader("👷 ADD LABOR")
    with st.form(key="labor_form", clear_on_submit=True):
        name = st.text_input("Worker Name")
        days = st.number_input("Days Worked (e.g., 1 or 0.5)", min_value=0.5, value=1.0, step=0.5)
        rate_option = st.radio("Rates", ["800", "650", "500"])
        rate = 800 if rate_option == "800" else 650 if rate_option == "650" else 500
        ca = st.number_input("Cash Advance", min_value=0.0, value=0.0)
        
        submitted = st.form_submit_button("SAVE LABOR")
        
    if submitted:
        net = (days * rate) - ca
        st.session_state.labor_records.append({
            "name": name.upper(),
            "days": days,
            "rate": rate,
            "ca": ca,
            "net": net
        })
        persist_state()
        st.success(f"Record for {name.upper()} added.")
        st.rerun()

elif view == "add_payroll_expense":
    st.subheader("📝 ADD PAYROLL EXPENSE")
    with st.form(key="payroll_expense_form", clear_on_submit=True):
        desc = st.text_input("Expense Description")
        amt = st.number_input("Amount", min_value=0.01, value=0.01)
        
        submitted = st.form_submit_button("SAVE EXPENSE")
        
    if submitted:
        st.session_state.payroll_expenses.append({
            "item": desc.upper(),
            "price": amt
        })
        persist_state()
        st.success(f"Expense {desc.upper()} added.")
        st.rerun()

elif view == "payroll_remaining":
    st.subheader("➖ SET REMAINING MONEY")
    res = st.number_input("Leftover/Remaining money to subtract from total", min_value=0.0, value=st.session_state.remaining_money)
    if st.button("Apply"):
        st.session_state.remaining_money = res
        persist_state()
        st.success("Remaining money applied.")
        st.rerun()

elif view == "payroll_ledger":
    st.subheader("📋 LABOR & PAYROLL LEDGER")
    st.markdown("### Labor Records")
    if not st.session_state.labor_records:
        st.info("No labor records.")
    for i, r in enumerate(st.session_state.labor_records):
        st.markdown(f"""
        ---
        **{r['name']}** - Days: {r['days']} | Rate: {r['rate']}  
        - C.A.: PHP {r['ca']:,.2f}  
        - **Net Pay: PHP {r['net']:,.2f}**
        """)
        if st.button("Delete Labor", key=f"del_lab_{i}"):
            st.session_state.labor_records.pop(i)
            persist_state()
            st.rerun()
            
    st.markdown("---")
    st.markdown("### Payroll Expenses")
    if not st.session_state.payroll_expenses:
        st.info("No payroll expenses.")
    for i, e in enumerate(st.session_state.payroll_expenses):
        st.markdown(f"""
        - **{e['item']}**: PHP {e['price']:,.2f}
        """)
        if st.button("Delete Payroll Expense", key=f"del_pay_exp_{i}"):
            st.session_state.payroll_expenses.pop(i)
            persist_state()
            st.rerun()

elif view == "payroll_export":
    st.subheader("📤 GENERATE PAYROLL REPORT")
    
    html, total = generate_payroll_html(
        st.session_state.labor_records, 
        st.session_state.payroll_expenses, 
        st.session_state.remaining_money
    )
    receipt_title = st.text_input("Receipt title", value="Payroll Receipt", placeholder="Enter a title for this receipt")
    
    if st.button("💾 Save this receipt to archive", use_container_width=True):
        if receipt_title.strip():
            archive_path = save_report_html("payroll", html, title=receipt_title)
            st.success(f"Saved to archive: {archive_path}")
        else:
            st.warning("Please enter a title before saving.")
    
    st.download_button(
        label="⬇️ Download current payroll report",
        data=html,
        file_name="payroll_report.html",
        mime="text/html",
        use_container_width=True
    )

    if st.button("📁 Open receipt archive", use_container_width=True):
        set_view("receipt_archive")
    
    if st.button("📧 Email Report"):
        try:
            msg = EmailMessage()
            msg['Subject'] = f"Construction Report: PHP {total:,.2f} - {datetime.now().strftime('%Y-%m-%d')}"
            msg['From'] = SENDER_EMAIL
            msg['To'] = RECEIVER_EMAIL
            msg.add_alternative(html, subtype='html')
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
                smtp.login(SENDER_EMAIL, SENDER_PASSWORD)
                smtp.send_message(msg)
            st.success("🚀 SUCCESS! Emailed report.")
        except Exception as e:
            st.error(f"❌ EMAIL FAILED: {e}")

elif view == "receipt_archive":
    st.subheader("📁 RECEIPT ARCHIVE")
    st.caption("Browse saved receipts in neat construction and payroll folders.")

    if st.button("⬅️ Back to construction export", use_container_width=True):
        set_view("export")
    if st.button("⬅️ Back to payroll export", use_container_width=True):
        set_view("payroll_export")

    for title, report_type in [("🏗️ Construction Receipts", "construction"), ("👷 Payroll Receipts", "payroll")]:
        with st.expander(title, expanded=True):
            saved_reports = list_saved_reports(report_type)
            if not saved_reports:
                st.info(f"No saved {report_type} receipts yet.")
                continue

            for report_path in saved_reports:
                st.markdown(f"- **{report_path.name}**")
                with open(report_path, "r", encoding="utf-8") as handle:
                    report_html = handle.read()
                st.download_button(
                    label="⬇️ Download this receipt",
                    data=report_html,
                    file_name=report_path.name,
                    mime="text/html",
                    use_container_width=True,
                    key=f"download_{report_type}_{report_path.name}"
                )
                if st.button("🗑️ Delete this receipt", key=f"delete_{report_type}_{report_path.name}", use_container_width=True):
                    delete_report_file(report_path)
                    st.success(f"Deleted: {report_path.name}")
                    st.rerun()
            
else:
    st.info("Welcome to AILY OS. Use the sidebar to navigate.")
