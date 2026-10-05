import streamlit as st
import pandas as pd
import plotly.express as px
from google.cloud import bigquery
from google.oauth2 import service_account

# Sayfa Yapılandırması
st.set_page_config(
    page_title="Yıldız Holding - Sürdürülebilirlik Paneli",
    page_icon="🌱",
    layout="wide"
)

# -------------------------------------------------------------
# 1. BİGQUERY BAĞLANTISI VE VERİ ÇEKME
# -------------------------------------------------------------
@st.cache_data(ttl=600)
def load_data():
    project_id = "sustainability-510714"
    table_id = "sustainability-510714.sustainability_data.sustainability_dataset"

    # Streamlit Cloud üzerinde Secrets kontrolü
    if "gcp_service_account" in st.secrets:
        # dict() sarmalaması olası AttrDict uyuşmazlığını engeller
        key_dict = dict(st.secrets["gcp_service_account"])
        credentials = service_account.Credentials.from_service_account_info(key_dict)
        client = bigquery.Client(credentials=credentials, project=project_id)
    else:
        # Yerel geliştirme için (GOOGLE_APPLICATION_CREDENTIALS yüklüyse)
        client = bigquery.Client(project=project_id)

    query = f"""
        SELECT 
            company_name,
            year,
            total_electricity_consumed_kwh,
            offsite_electricity_percentage,
            renewable_energy_percentage,
            total_gas_consumed_m3,
            total_km_covered_km
        FROM `{table_id}`
        ORDER BY company_name, year DESC
    """
    df = client.query(query).to_dataframe()

    # Sayısal alanları güvenli bir şekilde float/int türlerine zorla
    numeric_cols = [
        "total_electricity_consumed_kwh",
        "offsite_electricity_percentage",
        "renewable_energy_percentage",
        "total_gas_consumed_m3",
        "total_km_covered_km"
    ]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)

    df["year"] = df["year"].astype(int)
    return df

try:
    df = load_data()
except Exception as e:
    st.error(f"BigQuery bağlantı hatası oluştu: {e}")
    st.stop()

# -------------------------------------------------------------
# 2. FİLTRELER
# -------------------------------------------------------------
st.title("🌱 Yıldız Holding Sürdürülebilirlik Paneli")
st.caption("BigQuery: `sustainability-510714.sustainability_data.sustainability_dataset`")

col_filter1, col_filter2 = st.columns([2, 1])

companies = sorted(df["company_name"].dropna().unique())
years = sorted(df["year"].dropna().unique(), reverse=True)

with col_filter1:
    selected_company = st.selectbox("🏢 Şirket Seçin", companies)

with col_filter2:
    selected_year = st.selectbox("📅 Yıl Seçin", years)

filtered_df = df[(df["company_name"] == selected_company) & (df["year"] == selected_year)]

if filtered_df.empty:
    st.warning("Seçilen şirket ve yıla ait kayıt bulunamadı.")
    st.stop()

data = filtered_df.iloc[0]

st.divider()

# -------------------------------------------------------------
# 3. DASHBOARD 1: ENERJİ DAĞILIMI VE ELEKTRİK
# -------------------------------------------------------------
st.subheader("1. Enerji Dağılımı ve Elektrik Tüketimi")

d1_col1, d1_col2 = st.columns([1, 2])

with d1_col1:
    st.metric(
        label="Toplam Elektrik Tüketimi",
        value=f"{float(data['total_electricity_consumed_kwh']):,.0f} kWh".replace(",", ".")
    )
    st.info(
        f"**Tesis Dışı (Offsite) Elektrik:** %{float(data['offsite_electricity_percentage']):.1f}\n\n"
        f"**Yenilenebilir Enerji Oranı:** %{float(data['renewable_energy_percentage']):.1f}"
    )

with d1_col2:
    pie_data = pd.DataFrame({
        "Kaynak": ["Offsite Elektrik", "Yenilenebilir Enerji"],
        "Yüzde": [
            float(data["offsite_electricity_percentage"]),
            float(data["renewable_energy_percentage"])
        ]
    })

    fig_pie = px.pie(
        pie_data,
        names="Kaynak",
        values="Yüzde",
        color="Kaynak",
        color_discrete_map={
            "Offsite Elektrik": "#2563EB",
            "Yenilenebilir Enerji": "#10B981"
        },
        hole=0.45,
        title=f"{selected_company} - Elektrik Kaynak Dağılımı ({selected_year})"
    )
    fig_pie.update_traces(textposition='inside', textinfo='percent+label')
    fig_pie.update_layout(margin=dict(t=40, b=10, l=10, r=10), height=300)
    st.plotly_chart(fig_pie, use_container_width=True)

st.divider()

# -------------------------------------------------------------
# 4. DASHBOARD 2: TÜKETİM, MESAFE VE CO2 SALINIMI
# -------------------------------------------------------------
st.subheader("2. Kaynak Tüketimi & Karbon Ayak İzi (t-CO₂e)")

# Ham Metrikler
m1, m2, m3 = st.columns(3)
with m1:
    st.metric(
        "Toplam Elektrik",
        f"{float(data['total_electricity_consumed_kwh']):,.0f} kWh".replace(",", ".")
    )
with m2:
    st.metric(
        "Toplam Doğalgaz",
        f"{float(data['total_gas_consumed_m3']):,.0f} m³".replace(",", ".")
    )
with m3:
    st.metric(
        "Katedilen Mesafe",
        f"{float(data['total_km_covered_km']):,.0f} km".replace(",", ".")
    )

# Emisyon Hesaplamaları:
# 1 kWh = 0.40 kg CO2 | 1 m3 doğalgaz = 2.00 kg CO2
elec_kwh = float(data["total_electricity_consumed_kwh"])
gas_m3 = float(data["total_gas_consumed_m3"])

co2_elec_kg = elec_kwh * 0.40
co2_gas_kg = gas_m3 * 2.00
total_co2_kg = co2_elec_kg + co2_gas_kg
total_co2_tons = total_co2_kg / 1000.0

st.markdown("#### 🌍 Karbon Salınım Hesaplaması")

c1, c2, c3 = st.columns(3)
with c1:
    st.metric(
        label="Elektrik Kaynaklı Salınım (0,40 kg/kWh)",
        value=f"{co2_elec_kg:,.0f} kg CO₂".replace(",", ".")
    )
with c2:
    st.metric(
        label="Doğalgaz Kaynaklı Salınım (2,00 kg/m³)",
        value=f"{co2_gas_kg:,.0f} kg CO₂".replace(",", ".")
    )
with c3:
    st.metric(
        label="Toplam Karbon Ayak İzi",
        value=f"{total_co2_tons:,.2f} Ton CO₂e".replace(",", "."),
        delta="Elektrik + Doğalgaz",
        delta_color="off"
    )