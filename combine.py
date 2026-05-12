import os
import time
from datetime import datetime
import streamlit as st
import smtplib
from email.message import EmailMessage

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
if "records" not in st.session_state:
    st.session_state.records = []  # Material/Expense records

if "labor_records" not in st.session_state:
    st.session_state.labor_records = []  # Labor records

if "payroll_expenses" not in st.session_state:
    st.session_state.payroll_expenses = []  # Payroll expense records

if "tools_records" not in st.session_state:
    st.session_state.tools_records = []  # Tools inventory records

if "material_inventory" not in st.session_state:
    st.session_state.material_inventory = []  # Stock monitoring records

if "budget" not in st.session_state:
    st.session_state.budget = 0.0

if "remaining_money" not in st.session_state:
    st.session_state.remaining_money = 0.0

if "view" not in st.session_state:
    st.session_state.view = "home"

# ═════════════════ CORE LOGIC (MATERIAL/EXPENSE) ═════════════════
def set_view(v):
    st.session_state.view = v
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
    st.session_state.tools_records = []
    st.session_state.material_inventory = []
    st.session_state.budget = 0.0
    st.session_state.remaining_money = 0.0

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
    return True


def total_tools():
    return sum(r["amount"] for r in st.session_state.tools_records)


def get_material_stock(item_name):
    stock_in = sum(r["stock_in"] for r in st.session_state.material_inventory if r["name"] == item_name)
    stock_out = sum(r["stock_out"] for r in st.session_state.material_inventory if r["name"] == item_name)
    return stock_in - stock_out

def material_names():
    return sorted(set(r["name"] for r in st.session_state.material_inventory))



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


def generate_tools_html(tools_records):
    date_str = datetime.now().strftime("%B %d, %Y")
    html = f'''
    <html>
    <body style="font-family: Arial; padding: 20px;">
        <h2 style="color: #1b5e20;">🛠️ TOOL INVENTORY REPORT</h2>
        <p>Date: {date_str}</p>
        <table border="1" style="width: 100%; border-collapse: collapse;">
            <tr style="background: #1b5e20; color: white;">
                <th>Tool Name</th><th>Qty</th><th>Price</th><th>Total</th><th>Status</th><th>Sender</th>
            </tr>
    '''
    for r in tools_records:
        status = "✅ AVAILABLE" if r.get('available', True) else "❌ OUT"
        html += f"<tr><td>{r['name']}</td><td>{r['qty']}</td><td>{r['price']:,.2f}</td><td>{r['amount']:,.2f}</td><td>{status}</td><td>{r['sender']}</td></tr>"
    
    html += "</table></body></html>"
    return html

def generate_inventory_html(inventory):
    date_str = datetime.now().strftime("%B %d, %Y")
    html = f'''
    <html>
    <body style="font-family: Arial; padding: 20px;">
        <h2 style="color: #1b5e20;">📦 MATERIAL STOCK REPORT</h2>
        <p>Date: {date_str}</p>
        <table border="1" style="width: 100%; border-collapse: collapse;">
            <tr style="background: #1b5e20; color: white;">
                <th>Material</th><th>Unit</th><th>Stock In</th><th>Stock Out</th><th>Date</th>
            </tr>
    '''
    for r in inventory:
        html += f"<tr><td>{r['name']}</td><td>{r['unit']}</td><td>{r['stock_in']}</td><td>{r['stock_out']}</td><td>{r['date']}</td></tr>"
    
    html += "</table></body></html>"
    return html

def generate_inventory_receipt_html(inventory):
    date_str = datetime.now().strftime("%B %d, %Y")
    # Usually a receipt is for the latest transaction
    latest = inventory[-1] if inventory else {}
    html = f'''
    <html>
    <body style="font-family: 'Courier New'; padding: 40px; border: 2px solid #333; max-width: 500px; margin: auto;">
        <div style="text-align: center;">
            <h2>INVENTORY MATERIALS RECEIPT</h2>
            <p>AILYN CONSTRUCTION</p>
            <hr>
        </div>
        <p><b>Date:</b> {date_str}</p>
        <p><b>Material:</b> {latest.get('name', 'N/A')}</p>
        <p><b>Movement:</b> +{latest.get('stock_in', 0)} / -{latest.get('stock_out', 0)} {latest.get('unit', '')}</p>
        <p><b>Notes:</b> {latest.get('notes', 'None')}</p>
        <hr>
        <p style="text-align: center; font-size: 10px;">Thank you for your update!</p>
    </body>
    </html>
    '''
    return html
# ═════════════════ CSS & 3D GREEN INTERFACE ═════════════════
st.markdown("""
<style>
@media (max-width: 768px) {
    .block-container {
        padding: 10px !important;
    }
    h1, h2, h3 {
        font-size: 18px !important;
        text-align: center;
    }
    button {
        width: 100% !important;
        margin-bottom: 8px !important;
        font-size: 16px !important;
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
}

.block-container {
    background: rgba(20, 50, 35, 0.65) !important;
    backdrop-filter: blur(16px);
    border-radius: 20px;
    border: 1px solid rgba(135, 255, 180, 0.2);
    box-shadow: 0 12px 48px rgba(0, 0, 0, 0.6);
    padding: 24px;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.block-container:hover {
    transform: scale(1.01);
    box-shadow: 0 16px 64px rgba(72, 239, 127, 0.15);
}

section[data-testid="stSidebar"] {
    background: rgba(10, 30, 20, 0.85) !important;
    backdrop-filter: blur(20px);
    border-right: 1px solid rgba(135, 255, 180, 0.1);
}

button {
    background: linear-gradient(145deg, #0b4e2f, #167a44);
    color: #ffffff !important;
    border-radius: 14px !important;
    transition: all 0.15s ease-in-out;
    border: 1px solid rgba(135, 255, 180, 0.4);
    font-weight: bold;
    min-height: 45px;
}

button:hover {
    transform: scale(1.02);
    box-shadow: 0 6px 18px rgba(72, 239, 127, 0.3);
    border-color: #a3e635;
    background: linear-gradient(145deg, #167a44, #14a44d);
}

button:active {
    transform: scale(0.98);
}

input, textarea, select {
    background: rgba(255, 255, 255, 0.08) !important;
    border: 1px solid rgba(135, 255, 180, 0.3) !important;
    color: #4ade80 !important;
    border-radius: 10px !important;
    backdrop-filter: blur(8px);
    font-size: 16px !important;
    min-height: 40px;
    padding: 6px 12px;
    transition: border-color 0.15s ease, box-shadow 0.15s ease;
}

input:focus, textarea:focus, select:focus {
    border-color: #22c55e !important;
    box-shadow: 0 0 10px rgba(34, 197, 94, 0.4);
}

h1, h2, h3 {
    color: #4ade80 !important;
    text-shadow: 0 0 6px rgba(34, 197, 94, 0.3);
    letter-spacing: 0.5px;
}

[data-testid="stMetric"] {
    background: rgba(15, 45, 30, 0.7);
    border-radius: 16px;
    padding: 12px;
    border: 1px solid rgba(135, 255, 180, 0.2);
    margin-bottom: 12px;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
    transition: transform 0.2s ease;
}

[data-testid="stMetric"]:hover {
    transform: translateY(-2px);
    border-color: #4ade80;
}

[data-testid="stMetric"] label {
    color: #a3e635 !important;
    font-weight: 600;
}

[data-testid="stMetric"] div[data-testid="stMetricValue"] {
    color: #ffffff !important;
}

.intro {
    text-align: center;
    padding: 16px;
    color: #ffffff;
}

.intro h1 {
    font-size: 28px;
    font-weight: 800;
    color: #4ade80;
}

.intro p {
    font-size: 13px;
    color: #a3e635;
    opacity: 0.9;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="intro">
    <h1>🏗️ AILYN HOUSE PROJECT & PAYROLL</h1>
    <p>Combined System | Mobile Operating Engine v30000</p>
</div>
""", unsafe_allow_html=True)

# 🎛 CONTROL HUB
with st.sidebar:
    st.markdown("## 📱 AILY MOBILE CONTROL")
    
    budget_input = st.number_input("Set Project Budget", min_value=0.0, key="budget_input_sidebar", value=st.session_state.budget)
    if st.button("APPLY BUDGET", use_container_width=True):
        st.session_state.budget = float(budget_input)
        st.success("Budget applied!")
        st.rerun()
        
    st.caption(f"{datetime.now().strftime('%I:%M %p | %b %d')}")
    st.divider()

    st.subheader("🏠 Navigation")
    if st.button("🏠 Project Summary / Home", use_container_width=True):
        set_view("home")
        
    low_stock = sum(1 for n in material_names() if get_material_stock(n) <= 5)
    st.caption(f"📦 Material Types: {len(material_names())} | ⚠️ Low Stock Items: {low_stock}")

    st.markdown("---")
    st.subheader("🧱 Construction Ledger")
    if st.button("➕ Add Material", use_container_width=True):
        set_view("material")
    if st.button("📦 Material Inventory", use_container_width=True):
        set_view("material_inventory")
    if st.button("📊 Material Stock Monitor", use_container_width=True):
        set_view("material_stock")
    if st.button("📝 Add Construction Expense", use_container_width=True):
        set_view("expense")
    if st.button("💰 Add Excess Money", use_container_width=True):
        set_view("excess")
    if st.button("📋 View Project Ledger", use_container_width=True):
        set_view("ledger")
    if st.button("🛠️ Add Tool", use_container_width=True):
        set_view("tool")
    if st.button("🧰 View Tools Inventory", use_container_width=True):
        set_view("tools_ledger")
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
    
    st.divider()
    
    if st.button("🔄 RESET SYSTEM", use_container_width=True):
        clear_all()
        set_view("home")

# 🖥 VIEWS
view = st.session_state.view

# 🏠 HOME
if view == "home":
    st.subheader("📊 QUICK STATS")
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("BUDGET", f"PHP {st.session_state.budget:,.2f}")
    col2.metric("USED", f"PHP {get_total():,.2f}")
    col3.metric("TOOLS", f"PHP {total_tools():,.2f}")
    col4.metric("BALANCE", f"PHP {get_balance():,.2f}")
    
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
            st.success("Excess Added")
            st.rerun()
        else:
            st.warning("Please enter a valid amount.")

    st.divider()
    if st.button("🏁 FINISH LOOP", use_container_width=True):
        set_view("home")

# 🛠️ TOOL
elif view == "tool":
    st.subheader("🛠️ ADD TOOL (LOOP MODE)")

    with st.form(key="tool_form", clear_on_submit=True):
        name = st.text_input("Tool Name")
        price = st.number_input("Tool Price", min_value=0.01, value=0.01)
        qty = st.number_input("Quantity", min_value=1, value=1)
        sender = st.selectbox("Sender", ["Garr", "Aily"], key="tool_sender")
        available = st.toggle("Is Tool Available? (Check/X)", value=True)
        submitted = st.form_submit_button("SAVE TOOL")

    if submitted:
        if name.strip() and price > 0 and qty > 0:
            st.session_state.tools_records.append({
                "id": str(time.time()),
                "date": datetime.now().strftime("%b %d, %Y"),
                "name": name.upper(),
                "price": float(price),
                "qty": int(qty),
                "amount": float(price) * int(qty),
                "sender": sender,
                "type": "tool",
                "available": available
            })
            st.success("Tool saved successfully.")
            st.rerun()
        else:
            st.warning("Please enter valid tool data.")

    if st.button("🏁 FINISH LOOP", use_container_width=True):
        set_view("home")

# 🧰 TOOLS LEDGER
elif view == "tools_ledger":
    st.subheader("🧰 TOOLS INVENTORY")

    if not st.session_state.tools_records:
        st.info("No tools recorded.")
    else:
        # Download Section
        t_html = generate_tools_html(st.session_state.tools_records)
        st.download_button("📥 DOWNLOAD TOOLS LEDGER", data=t_html, file_name="tools_report.html", mime="text/html", use_container_width=True)
        
        for i, r in enumerate(list(st.session_state.tools_records)):
            status_icon = "✅ AVAILABLE" if r.get('available', True) else "❌ OUT/UNAVAILABLE"
            st.markdown(f"""
            ---
            ### {r['name']} {status_icon}
            🔧 Qty: {r['qty']} | 💰 PHP {r['amount']:,.2f}  
            👤 {r['sender']} | 📅 {r['date']}
            """)
            
            col_a, col_b = st.columns(2)
            if col_a.button(f"🔄 TOGGLE STATUS", key=f"tog_{r['id']}"):
                st.session_state.tools_records[i]['available'] = not r.get('available', True)
                st.rerun()
                
            if col_b.button("❌ DELETE", key=f"del_tool_{r['id']}"):
                st.session_state.tools_records = [
                    x for x in st.session_state.tools_records if x["id"] != r["id"]
                ]
                st.rerun()


# 📦 MATERIAL INVENTORY
elif view == "material_inventory":
    st.subheader("📦 MATERIAL INVENTORY")

    with st.form("material_inventory_form", clear_on_submit=True):
        name = st.text_input("Material Name")
        unit = st.text_input("Unit (bags, pcs, kg, meters)", value="pcs")
        stock_in = st.number_input("Stock In", min_value=0.0, value=0.0)
        stock_out = st.number_input("Stock Out", min_value=0.0, value=0.0)
        minimum = st.number_input("Minimum Stock Alert", min_value=0.0, value=5.0)
        notes = st.text_input("Notes")
        submitted = st.form_submit_button("SAVE INVENTORY MOVEMENT")

    if submitted:
        if name.strip() and (stock_in > 0 or stock_out > 0):
            st.session_state.material_inventory.append({
                "id": str(time.time()),
                "date": datetime.now().strftime("%b %d, %Y"),
                "name": name.upper(),
                "unit": unit,
                "stock_in": float(stock_in),
                "stock_out": float(stock_out),
                "minimum": float(minimum),
                "notes": notes
            })
            st.success("Inventory movement saved.")
            st.rerun()
        else:
            st.warning("Enter a material name and stock in or stock out value.")

# 📊 MATERIAL STOCK MONITOR
elif view == "material_stock":
    st.subheader("📊 MATERIAL STOCK MONITOR")

    names = material_names()
    if not names:
        st.info("No material inventory records yet.")
    else:
        # CHART SECTION
        st.subheader("📈 STOCK COMPARISON (OLD vs LATEST)")
        chart_data = []
        for name in names:
            movements = [r for r in st.session_state.material_inventory if r["name"] == name]
            latest_val = movements[-1]["stock_in"] if movements else 0
            old_val = sum(m["stock_in"] for m in movements[:-1]) if len(movements) > 1 else 0
            chart_data.append({"Material": name, "Old Stock In": old_val, "Latest Stock In": latest_val})
        
        if chart_data:
            import pandas as pd
            df = pd.DataFrame(chart_data).set_index("Material")
            st.bar_chart(df)

        # DOWNLOAD SECTION
        c1, c2 = st.columns(2)
        inv_html = generate_inventory_html(st.session_state.material_inventory)
        c1.download_button("📥 DOWNLOAD FULL INVENTORY", data=inv_html, file_name="material_inventory.html", mime="text/html", use_container_width=True)
        
        rec_html = generate_inventory_receipt_html(st.session_state.material_inventory)
        c2.download_button("🧾 DOWNLOAD LATEST RECEIPT", data=rec_html, file_name="inventory_receipt.html", mime="text/html", use_container_width=True)

        for name in names:
            rows = [r for r in st.session_state.material_inventory if r["name"] == name]
            current = get_material_stock(name)
            unit = rows[-1]["unit"]
            minimum = rows[-1]["minimum"]
            status = "⚠️ LOW STOCK" if current <= minimum else "✅ OK"

            st.markdown(f"""
            ---
            **{name}**  
            📦 Current Stock: **{current:,.2f} {unit}**  
            🔔 Minimum Level: {minimum:,.2f} {unit}  
            {status}
            """)

            with st.expander("View Movements"):
                for r in reversed(rows[-10:]):
                    st.write(f"{r['date']} | +{r['stock_in']} / -{r['stock_out']} {unit} | {r['notes']}")

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
                st.rerun()

# 📤 EXPORT
elif view == "export":
    st.subheader("📤 EXPORT CONSTRUCTION REPORT")

    html = build_html_report(st.session_state.records, st.session_state.budget)

    st.download_button(
        label="DOWNLOAD CONSTRUCTION REPORT",
        data=html,
        file_name="aily_mobile_report.html",
        mime="text/html",
        use_container_width=True
    )

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
        st.success(f"Expense {desc.upper()} added.")
        st.rerun()

elif view == "payroll_remaining":
    st.subheader("➖ SET REMAINING MONEY")
    res = st.number_input("Leftover/Remaining money to subtract from total", min_value=0.0, value=st.session_state.remaining_money)
    if st.button("Apply"):
        st.session_state.remaining_money = res
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
            st.rerun()

elif view == "payroll_export":
    st.subheader("📤 GENERATE PAYROLL REPORT")
    
    html, total = generate_payroll_html(
        st.session_state.labor_records, 
        st.session_state.payroll_expenses, 
        st.session_state.remaining_money
    )
    
    st.download_button(
        label="DOWNLOAD PAYROLL REPORT",
        data=html,
        file_name="payroll_report.html",
        mime="text/html",
        use_container_width=True
    )
    
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
            
else:
    st.info("Welcome to AILY OS. Use the sidebar to navigate.")