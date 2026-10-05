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
# 1. BİGQUERY BAĞLANTISI VE VERİ ÇEKME
# -------------------------------------------------------------
@st.cache_data(ttl=600)
@st.cache_data(ttl=600)
def load_data():
    project_id = "sustainability-510714"
    table_id = "sustainability-510714.sustainability_data.sustainability_dataset"

    if "gcp_service_account" in st.secrets:
        # st.secrets AttrDict nesnesini standart dict yapısına dönüştürün
        key_dict = dict(st.secrets["gcp_service_account"])
        
        # Kaçış karakterlerini ve satır sonu boşluklarını temizleyin
        raw_key = key_dict["private_key"]
        raw_key = raw_key.replace("\\n", "\n").replace("\r", "").strip()
        key_dict["private_key"] = raw_key

        credentials = service_account.Credentials.from_service_account_info(key_dict)
        client = bigquery.Client(credentials=credentials, project=project_id)
    else:
        st.error("Streamlit Secrets içinde 'gcp_service_account' bulunamadı!")
        st.stop()

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

# -------------------------------------------------------------
# BİGQUERY BAĞLANTISI VE GLOBAL CLIENT
# -------------------------------------------------------------
try:
    key_dict = dict(st.secrets["gcp_service_account"])
    raw_key = key_dict["private_key"].replace("\\n", "\n").replace("\r", "").strip()
    key_dict["private_key"] = raw_key
    credentials = service_account.Credentials.from_service_account_info(key_dict)
    
    # Global client: Hem okumada hem de Excel yüklemede burası kullanılacak
    client = bigquery.Client(credentials=credentials, project="sustainability-510714")
    
    df = load_data()
except Exception as e:
    st.error(f"BigQuery bağlantı hatası oluştu: {e}")
    st.stop()

# -------------------------------------------------------------
# 2. FİLTRELER
# -------------------------------------------------------------
st.title("Sustainability Data Platform")
st.caption("BigQuery Dataproduct: `sustainability-510714.sustainability_data.sustainability_dataset`")

col_filter1, col_filter2 = st.columns([2, 1])

companies = sorted(df["company_name"].dropna().unique())
years = sorted(df["year"].dropna().unique(), reverse=True)

with col_filter1:
    selected_company = st.selectbox("Select Company", companies)

with col_filter2:
    selected_year = st.selectbox("Select Year", years)

filtered_df = df[(df["company_name"] == selected_company) & (df["year"] == selected_year)]

if filtered_df.empty:
    st.warning("Seçilen şirket ve yıla ait kayıt bulunamadı.")
    st.stop()

data = filtered_df.iloc[0]

st.divider()

# -------------------------------------------------------------
# 3. DASHBOARD 1: ENERJİ DAĞILIMI VE ELEKTRİK
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
# 4. DASHBOARD 2: TÜKETİM VE CO2 SALINIMI
# -------------------------------------------------------------
st.subheader("Resource Consumption & Carbon Footprint")

# Ham Metrikler
m1, m2, m3 = st.columns(3)
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


import io
import streamlit as st
import pandas as pd
from google.cloud import bigquery

# -------------------------------------------------------------
# EXCEL İNDİRME VE BİGQUERY GÜNCELLEME MODÜLÜ
# -------------------------------------------------------------
st.sidebar.header("📥 Veri Yönetimi")

# 1. Mevcut BigQuery Verisini Excel Olarak İndirme
buffer = io.BytesIO()
with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
    df.to_excel(writer, index=False, sheet_name="SustainabilityData")

st.sidebar.download_button(
    label="📊 Güncel Veriyi Excel Olarak İndir",
    data=buffer.getvalue(),
    file_name="sustainability_data.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

st.sidebar.divider()

# 2. Güncellenmiş Excel Dosyasını Yükleme
st.sidebar.subheader("📤 Veri Güncelle / Ekle")
uploaded_file = st.sidebar.file_uploader(
    "Düzenlenmiş Excel dosyasını yükleyin", 
    type=["xlsx"]
)

if uploaded_file is not None:
    try:
        new_df = pd.read_excel(uploaded_file)
        
        # Beklenen zorunlu kolonların kontrolü
        required_cols = [
            "company_name", "year", "total_electricity_consumed_kwh",
            "offsite_electricity_percentage", "renewable_energy_percentage",
            "total_gas_consumed_m3"
        ]
        
        if not all(col in new_df.columns for col in required_cols):
            st.sidebar.error("Hata: Excel dosyasındaki kolon isimleri BigQuery şemasıyla uyuşmuyor.")
        else:
            if st.sidebar.button("🚀 BigQuery'ye Aktar ve Güncelle"):
                with st.spinner("Veriler BigQuery'ye işleniyor..."):
                    # Veri tiplerini güvenli hale getir
                    for col in required_cols[2:]:
                        new_df[col] = pd.to_numeric(new_df[col], errors="coerce").fillna(0.0)
                    new_df["year"] = new_df["year"].astype(int)
                    new_df["company_name"] = new_df["company_name"].astype(str)

                    # BigQuery Client (Daha önce tanımlanan client nesnesi)
                    project_id = "sustainability-510714"
                    dataset_id = "sustainability_data"
                    target_table = f"{project_id}.{dataset_id}.sustainability_dataset"
                    temp_table = f"{project_id}.{dataset_id}.temp_sustainability_upload"

                    # 1. Adım: Geçici (Staging) tabloya yükle
                    job_config = bigquery.LoadJobConfig(
                        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE
                    )
                    load_job = client.load_table_from_dataframe(new_df, temp_table, job_config=job_config)
                    load_job.result()  # Yüklemenin bitmesini bekle

                    # 2. Adım: MERGE sorgusuyla varsa güncelle, yoksa ekle (Upsert)
                    merge_query = f"""
                        MERGE `{target_table}` T
                        USING `{temp_table}` S
                        ON T.company_name = S.company_name AND T.year = S.year
                        WHEN MATCHED THEN
                          UPDATE SET
                            total_electricity_consumed_kwh = S.total_electricity_consumed_kwh,
                            offsite_electricity_percentage = S.offsite_electricity_percentage,
                            renewable_energy_percentage = S.renewable_energy_percentage,
                            total_gas_consumed_m3 = S.total_gas_consumed_m3,
                            total_km_covered_km = S.total_km_covered_km
                        WHEN NOT MATCHED THEN
                          INSERT (
                            company_name, year, total_electricity_consumed_kwh,
                            offsite_electricity_percentage, renewable_energy_percentage,
                            total_gas_consumed_m3, total_km_covered_km
                          )
                          VALUES (
                            S.company_name, S.year, S.total_electricity_consumed_kwh,
                            S.offsite_electricity_percentage, S.renewable_energy_percentage,
                            S.total_gas_consumed_m3, S.total_km_covered_km
                          );
                    """
                    client.query(merge_query).result()

                    # 3. Adım: Geçici tabloyu temizle
                    client.delete_table(temp_table, not_found_ok=True)

                    # Streamlit önbelleğini sıfırla ve sayfayı yenile
                    st.cache_data.clear()
                    st.sidebar.success("Veriler başarıyla güncellendi!")
                    st.rerun()

    except Exception as e:
        st.sidebar.error(f"İşlem sırasında hata oluştu: {e}")