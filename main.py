import io
import streamlit as st
import pandas as pd
import plotly.express as px
from google.cloud import bigquery
from google.oauth2 import service_account

# Sayfa Yapılandırması
st.set_page_config(
    page_title="Sustainability Data Platform",
    page_icon="🌱",
    layout="wide"
)

# -------------------------------------------------------------
# 1. BİGQUERY CLIENT VE VERİ ÇEKME
# -------------------------------------------------------------
def get_bigquery_client():
    project_id = "sustainability-510714"
    if "gcp_service_account" in st.secrets:
        key_dict = dict(st.secrets["gcp_service_account"])
        raw_key = key_dict["private_key"].replace("\\n", "\n").replace("\r", "").strip()
        key_dict["private_key"] = raw_key
        credentials = service_account.Credentials.from_service_account_info(key_dict)
        return bigquery.Client(credentials=credentials, project=project_id)
    else:
        st.error("Streamlit Secrets içinde 'gcp_service_account' bulunamadı!")
        st.stop()

@st.cache_data(ttl=600)
def load_data():
    client = get_bigquery_client()
    table_id = "sustainability-510714.sustainability_data.sustainability_dataset"

    query = f"""
        SELECT 
            company_name,
            year,
            total_electricity_consumed_kwh,
            offsite_electricity_percentage,
            renewable_energy_percentage,
            total_gas_consumed_m3
        FROM `{table_id}`
        ORDER BY company_name, year DESC
    """
    df = client.query(query).to_dataframe()

    numeric_cols = [
        "total_electricity_consumed_kwh",
        "offsite_electricity_percentage",
        "renewable_energy_percentage",
        "total_gas_consumed_m3"
    ]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)

    df["year"] = df["year"].astype(int)
    return df

try:
    df = load_data()
except Exception as e:
    st.error(f"BigQuery connection error: {e}")
    st.stop()

# -------------------------------------------------------------
# 2. ÜST BAŞLIK VE SAĞ ÜST EXCEL YÖNETİMİ (POPOVER)
# -------------------------------------------------------------
col_head1, col_head2 = st.columns([3, 1])

with col_head1:
    st.title("Sustainability Data Platform")
    st.caption("BigQuery Dataproduct: `sustainability-510714.sustainability_data.sustainability_dataset`")

with col_head2:
    st.write("")  # Dikey hizalama
    with st.popover("📥 Data Management (Excel)", use_container_width=True):
        st.markdown("#### 📊 Excel Operations")
        
        # 1. Excel İndirme
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="SustainabilityData")

        st.download_button(
            label="⬇️ Download Current Data",
            data=buffer.getvalue(),
            file_name="sustainability_data.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

        st.divider()

        # 2. Excel Yükleme (Session State Korumalı)
        st.markdown("#### 📤 Update / Add Data")
        uploaded_file = st.file_uploader(
            "Select Excel File", 
            type=["xlsx"],
            key="excel_file_input"
        )

        if uploaded_file is not None:
            st.session_state["cached_excel_file"] = uploaded_file

        if "cached_excel_file" in st.session_state and st.session_state["cached_excel_file"] is not None:
            active_file = st.session_state["cached_excel_file"]
            try:
                active_file.seek(0)
                new_df = pd.read_excel(active_file)
                new_df.columns = [str(col).strip().lower() for col in new_df.columns]
                
                required_cols = [
                    "company_name", 
                    "year", 
                    "total_electricity_consumed_kwh",
                    "offsite_electricity_percentage", 
                    "renewable_energy_percentage", 
                    "total_gas_consumed_m3"
                ]
                
                missing_cols = [col for col in required_cols if col not in new_df.columns]
                
                if missing_cols:
                    st.error(f"❌ Missing required columns: {', '.join(missing_cols)}")
                else:
                    st.info(f"📄 Loaded {len(new_df)} rows from `{active_file.name}`")
                    
                    if st.button("🚀 Upload & Update BigQuery", type="primary", use_container_width=True):
                        with st.spinner("Processing data into BigQuery..."):
                            for col in required_cols[2:]:
                                new_df[col] = pd.to_numeric(new_df[col], errors="coerce").fillna(0.0)
                            new_df["year"] = new_df["year"].astype(int)
                            new_df["company_name"] = new_df["company_name"].astype(str)

                            client = get_bigquery_client()

                            # Upsert: Aynı şirket ve yıl varsa yenisi geçerli olur
                            combined_df = pd.concat([df[required_cols], new_df[required_cols]]).drop_duplicates(
                                subset=["company_name", "year"], 
                                keep="last"
                            ).reset_index(drop=True)

                            target_table = "sustainability-510714.sustainability_data.sustainability_dataset"

                            # Ücretsiz Load Job ile yazma (Billing / DML hatası vermez)
                            job_config = bigquery.LoadJobConfig(
                                write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE
                            )
                            load_job = client.load_table_from_dataframe(combined_df, target_table, job_config=job_config)
                            load_job.result()

                            del st.session_state["cached_excel_file"]
                            st.session_state["upload_success"] = True
                            st.cache_data.clear()
                            st.rerun()

            except Exception as e:
                st.error(f"Error reading file: {e}")

# Başarı bildirimi (Yenileme sonrasında sayfanın üstünde kalıcı görünür)
if st.session_state.get("upload_success"):
    st.success("✅ Data successfully updated in BigQuery and platform refreshed!")
    st.balloons()
    del st.session_state["upload_success"]

# -------------------------------------------------------------
# 3. FİLTRELER
# -------------------------------------------------------------
col_filter1, col_filter2 = st.columns([2, 1])

companies = sorted(df["company_name"].dropna().unique())
years = sorted(df["year"].dropna().unique(), reverse=True)

with col_filter1:
    selected_company = st.selectbox("Select Company", companies)

with col_filter2:
    selected_year = st.selectbox("Select Year", years)

filtered_df = df[(df["company_name"] == selected_company) & (df["year"] == selected_year)]

if filtered_df.empty:
    st.warning("No records found for the selected company and year.")
    st.stop()

data = filtered_df.iloc[0]

st.divider()

# -------------------------------------------------------------
# 4. DASHBOARD 1: ENERJİ DAĞILIMI VE ELEKTRİK
# -------------------------------------------------------------
st.subheader("Electricity & Renewable Energy Share")

d1_col1, d1_col2 = st.columns([1, 2])

with d1_col1:
    st.metric(
        label="Total Electricity Consumption",
        value=f"{float(data['total_electricity_consumed_kwh']):,.0f} kWh".replace(",", ".")
    )
    st.info(
        f"**Off-Site Electricity Percentage:** %{float(data['offsite_electricity_percentage']):.1f}\n\n"
        f"**Renewable Energy Percentage:** %{float(data['renewable_energy_percentage']):.1f}"
    )

with d1_col2:
    pie_data = pd.DataFrame({
        "Source": ["Off-Site Electricity", "Renewable Energy"],
        "Percentage": [
            float(data["offsite_electricity_percentage"]),
            float(data["renewable_energy_percentage"])
        ]
    })

    fig_pie = px.pie(
        pie_data,
        names="Source",
        values="Percentage",
        color="Source",
        color_discrete_map={
            "Off-Site Electricity": "#2563EB",
            "Renewable Energy": "#10B981"
        },
        hole=0.45,
        title=f"{selected_company} - Electricity Source Distribution ({selected_year})"
    )
    fig_pie.update_traces(textposition='inside', textinfo='percent+label')
    fig_pie.update_layout(margin=dict(t=40, b=10, l=10, r=10), height=300)
    st.plotly_chart(fig_pie, use_container_width=True)

st.divider()

# -------------------------------------------------------------
# 5. DASHBOARD 2: TÜKETİM VE CO2 SALINIMI
# -------------------------------------------------------------
st.subheader("Resource Consumption & Carbon Footprint")

m1, m2 = st.columns(2)
with m1:
    st.metric(
        "Total Electricity Consumption",
        f"{float(data['total_electricity_consumed_kwh']):,.0f} kWh".replace(",", ".")
    )
with m2:
    st.metric(
        "Total Natural Gas Consumption",
        f"{float(data['total_gas_consumed_m3']):,.0f} m³".replace(",", ".")
    )

# Emisyon Hesaplamaları:
# 1 kWh = 0.40 kg CO2 | 1 m3 doğalgaz = 2.00 kg CO2
elec_kwh = float(data["total_electricity_consumed_kwh"])
gas_m3 = float(data["total_gas_consumed_m3"])

co2_elec_kg = elec_kwh * 0.40
co2_gas_kg = gas_m3 * 2.00
total_co2_kg = co2_elec_kg + co2_gas_kg
total_co2_tons = total_co2_kg / 1000.0

st.markdown("#### Carbon Footprint Calculation")

c1, c2, c3 = st.columns(3)
with c1:
    st.metric(
        label="Electricity-Related Emissions (0.40 kg/kWh)",
        value=f"{co2_elec_kg:,.0f} kg CO₂".replace(",", ".")
    )
with c2:
    st.metric(
        label="Natural Gas-Related Emissions (2.00 kg/m³)",
        value=f"{co2_gas_kg:,.0f} kg CO₂".replace(",", ".")
    )
with c3:
    st.metric(
        label="Total Carbon Footprint",
        value=f"{total_co2_tons:,.2f} Ton CO₂e".replace(",", "."),
        help="Electricity + Natural Gas",
        delta_color="off"
    )