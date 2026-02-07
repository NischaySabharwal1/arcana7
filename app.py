import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from fpdf import FPDF
import io
import datetime

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="Arcana7 Cost Calculator",
    page_icon="🔮",
    layout="wide",
)

# --- CUSTOM CSS FOR PREMIUM LOOK ---
st.markdown("""
<style>
    .main {
        background-color: #0e1117;
    }
    .stNumberInput, .stSlider, .stSelectbox {
        background-color: #1e2130;
        border-radius: 10px;
    }
    .stMetric {
        background-color: #1e2130;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
    }
    .css-1offfwp { 
        background-image: linear-gradient(180deg, #1e2130, #0e1117);
    }
    h1, h2, h3 {
        color: #00d2ff;
        font-family: 'Outfit', sans-serif;
    }
    .export-button {
        background-color: #00d2ff;
        color: white;
        border-radius: 5px;
        padding: 10px;
    }
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR: CONSTANTS & RATES ---
st.sidebar.title("⚙️ Arcana7 Configuration")
st.sidebar.subheader("Resource Rates (₹)")

material_rate = st.sidebar.number_input("Material Rate (₹/g)", value=1.0, step=0.1, help="Cost of Numakers PLA+ per gram")
machine_rate = st.sidebar.number_input("Machine Rate (₹/hr)", value=25.0, step=1.0, help="Bambu Lab A1 electricity + maintenance")
designer_pro_rate = st.sidebar.number_input("Proper Design Rate (₹/hr)", value=1200.0, step=50.0)
designer_basic_rate = st.sidebar.number_input("Basic Design Rate (₹/hr)", value=400.0, step=50.0)
finishing_labor_rate = st.sidebar.number_input("Finishing Labor Rate (₹/hr)", value=350.0, step=10.0)
overhead_flat = st.sidebar.number_input("Finishing Material Flat Fee (₹)", value=150.0, step=10.0, help="Sandpaper, paint, etc.")

# --- MAIN UI ---
st.title("🔮 Arcana7 Cost Calculator")
st.markdown("---")

col1, col2 = st.columns([1, 1.2])

with col1:
    st.subheader("📦 Product Details")
    
    product_name = st.text_input("Product Name", value="Custom 3D Print")
    quantity = st.number_input("Quantity", min_value=1, value=1, step=1)
    
    st.markdown("### 🛠️ Production Inputs")
    design_type = st.selectbox("Design Quality", ["Proper (Advanced)", "Basic (Structural)"])
    design_hours = st.number_input("Design Time (Hours)", value=1.0, min_value=0.0, step=0.5)
    
    print_time = st.number_input("Total Printing Time (Hours)", value=5.0, min_value=0.1, step=0.5)
    material_weight = st.number_input("Material Weight (Grams)", value=100.0, min_value=1.0, step=1.0)
    
    finishing_hours = st.number_input("Finishing/Labor Time (Hours)", value=1.0, min_value=0.0, step=0.5)
    
    st.markdown("### 📈 Business Logic")
    profit_margin_pct = st.slider("Target Profit Margin (%)", 0, 500, 40)

# --- CALCULATIONS ---
design_rate = designer_pro_rate if design_type == "Proper (Advanced)" else designer_basic_rate
design_cost = design_hours * design_rate
material_cost = material_weight * material_rate
printing_cost = print_time * machine_rate
finishing_labor_cost = finishing_hours * finishing_labor_rate
finishing_materials = overhead_flat if finishing_hours > 0 else 0

total_base_cost_per_unit = (design_cost + material_cost + printing_cost + finishing_labor_cost + finishing_materials)
total_manufacturing_cost = total_base_cost_per_unit * quantity

markup_multiplier = 1 + (profit_margin_pct / 100)
selling_price_per_unit = total_base_cost_per_unit * markup_multiplier
total_revenue = selling_price_per_unit * quantity
total_profit = total_revenue - total_manufacturing_cost

# --- RESULTS DISPLAY ---
with col2:
    st.subheader("💰 Price Summary")
    
    m1, m2 = st.columns(2)
    m1.metric("Selling Price / Unit", f"₹{selling_price_per_unit:,.2f}")
    m2.metric("Total Revenue", f"₹{total_revenue:,.2f}")
    
    m3, m4 = st.columns(2)
    m3.metric("Base Cost / Unit", f"₹{total_base_cost_per_unit:,.2f}")
    m4.metric("Total Profit", f"₹{total_profit:,.2f}", delta=f"{profit_margin_pct}% Margin")
    
    st.markdown("### 📊 Cost Breakdown")
    
    # Pie chart for breakdown
    labels = ['Design', 'Material', 'Printing (Machine)', 'Labor', 'Finishing Mats']
    values = [design_cost, material_cost, printing_cost, finishing_labor_cost, finishing_materials]
    
    fig = go.Figure(data=[go.Pie(labels=labels, values=values, hole=.4, marker_colors=['#00d2ff', '#3a7bd5', '#0072ff', '#00c6ff', '#0078ff'])])
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color="white"),
        margin=dict(t=0, b=0, l=0, r=0),
        showlegend=True
    )
    st.plotly_chart(fig, use_container_width=True)

# --- DETAILED BREAKDOWN TABLE ---
st.write("---")
st.subheader("📝 Detailed Element Breakdown (Per Unit)")
breakdown_data = {
    "Element": ["Design Cost", "Material Cost", "Machine/Printing Cost", "Finishing Labor", "Static Overheads/Mats", "TOTAL BASE COST"],
    "Calculation": [
        f"{design_hours} hrs @ ₹{design_rate}/hr",
        f"{material_weight}g @ ₹{material_rate}/g",
        f"{print_time} hrs @ ₹{machine_rate}/hr",
        f"{finishing_hours} hrs @ ₹{finishing_labor_rate}/hr",
        "Flat Fee",
        ""
    ],
    "Cost (₹)": [design_cost, material_cost, printing_cost, finishing_labor_cost, finishing_materials, total_base_cost_per_unit]
}
df_breakdown = pd.DataFrame(breakdown_data)
st.table(df_breakdown)

# --- EXPORT SECTION ---
st.write("---")
st.subheader("📥 Export Invoice")

def create_pdf():
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 20)
    pdf.cell(0, 10, "ARCANA7 COST INVOICE", ln=True, align="C")
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 10, f"Date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=True, align="R")
    pdf.ln(10)
    
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 10, f"Product: {product_name}", ln=True)
    pdf.cell(0, 10, f"Quantity: {quantity}", ln=True)
    pdf.ln(5)
    
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(100, 10, "Cost Element", border=1)
    pdf.cell(60, 10, "Details", border=1)
    pdf.cell(30, 10, "Total (INR)", border=1, ln=True)
    
    pdf.set_font("Helvetica", "", 10)
    for i in range(len(breakdown_data["Element"]) - 1):
        pdf.cell(100, 10, breakdown_data["Element"][i], border=1)
        # Replace Rupee symbol with 'INR' for PDF compatibility
        calc_text = str(breakdown_data["Calculation"][i]).replace("₹", "INR ")
        pdf.cell(60, 10, calc_text, border=1)
        pdf.cell(30, 10, f"{breakdown_data['Cost (₹)'][i]:.2f}", border=1, ln=True)
        
    pdf.ln(5)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(160, 10, "Total Cost Per Unit:", border=0)
    pdf.cell(30, 10, f"INR {total_base_cost_per_unit:.2f}", border=0, ln=True)
    pdf.cell(160, 10, f"Selling Price Per Unit ({profit_margin_pct}% Margin):", border=0)
    pdf.cell(30, 10, f"INR {selling_price_per_unit:.2f}", border=0, ln=True)
    pdf.ln(5)
    pdf.set_fill_color(0, 210, 255)
    pdf.cell(160, 12, "GRAND TOTAL REVENUE:", border=1, fill=True)
    pdf.cell(30, 12, f"INR {total_revenue:.2f}", border=1, fill=True, ln=True)
    
    return bytes(pdf.output())

def create_excel():
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df_breakdown.to_excel(writer, index=False, sheet_name="Cost Breakdown")
        summary_df = pd.DataFrame({
            "Field": ["Product Name", "Quantity", "Profit Margin (%)", "Base Cost Unit", "Selling Price Unit", "Total Revenue", "Total Profit"],
            "Value": [product_name, quantity, f"{profit_margin_pct}%", total_base_cost_per_unit, selling_price_per_unit, total_revenue, total_profit]
        })
        summary_df.to_excel(writer, index=False, sheet_name="Invoice Summary")
    return output.getvalue()

c_exp1, c_exp2 = st.columns(2)

with c_exp1:
    pdf_bytes = create_pdf()
    st.download_button(
        label="📄 Download PDF Invoice",
        data=pdf_bytes,
        file_name=f"Arcana7_Invoice_{product_name.replace(' ', '_')}.pdf",
        mime="application/pdf",
    )

with c_exp2:
    excel_bytes = create_excel()
    st.download_button(
        label="📊 Download Excel Breakdown",
        data=excel_bytes,
        file_name=f"Arcana7_Invoice_{product_name.replace(' ', '_')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

st.markdown("---")
st.caption("Arcana7 Cost Calculator - Precision Pricing for 3D Printing Excellence.")
