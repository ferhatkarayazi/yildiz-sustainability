import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Yıldız Holding Sürdürülebilirlik Portali", layout="wide")

st.title("Yıldız Holding - Şirket Bazlı Sürdürülebilirlik Raporu ")
st.caption("Phase: MVP")

# 10 Şirket ve Temel KPI Verisi
data = [
    {"Şirket": "Ülker Bisküvi (Topkapı)", "Ülke": "Türkiye", "Kategori": "Atıştırmalık", "Scope1_tCO2e": 2850,
     "Scope2_tCO2e": 4120, "Veri_Durumu": "Onaylandı", "YoY_Degisim": "-%4.2"},
    {"Şirket": "pladis UK (Harlesden)", "Ülke": "İngiltere", "Kategori": "Bisküvi", "Scope1_tCO2e": 1940,
     "Scope2_tCO2e": 2850, "Veri_Durumu": "Onaylandı", "YoY_Degisim": "-%6.1"},
    {"Şirket": "Godiva Belgium (Brüksel)", "Ülke": "Belçika", "Kategori": "Premium Çikolata", "Scope1_tCO2e": 1120,
     "Scope2_tCO2e": 1680, "Veri_Durumu": "Onaylandı", "YoY_Degisim": "-%8.5"},
    {"Şirket": "Kerevitaş (Bursa Dondurulmuş)", "Ülke": "Türkiye", "Kategori": "Dondurulmuş Gıda", "Scope1_tCO2e": 3410,
     "Scope2_tCO2e": 5200, "Veri_Durumu": "Onaylandı", "YoY_Degisim": "-%2.0"},
    {"Şirket": "Besler Yağ (Gebze)", "Ülke": "Türkiye", "Kategori": "Yağ & Margarin", "Scope1_tCO2e": 2980,
     "Scope2_tCO2e": 3900, "Veri_Durumu": "Onaylandı", "YoY_Degisim": "+%1.4"},
    {"Şirket": "pladis Mena (Suudi Arabistan)", "Ülke": "Suudi Arabistan", "Kategori": "Atıştırmalık",
     "Scope1_tCO2e": 1450, "Scope2_tCO2e": 2400, "Veri_Durumu": "İnceleme Bekliyor", "YoY_Degisim": "-%3.0"},
    {"Şirket": "Ereks Dış Ticaret (Romanya)", "Ülke": "Romanya", "Kategori": "Paketleme/Ticaret", "Scope1_tCO2e": 620,
     "Scope2_tCO2e": 950, "Veri_Durumu": "Onaylandı", "YoY_Degisim": "-%5.0"},
    {"Şirket": "Polmlek / pladis CEE (Polonya)", "Ülke": "Polonya", "Kategori": "Kek & Bisküvi", "Scope1_tCO2e": 1300,
     "Scope2_tCO2e": 1950, "Veri_Durumu": "Onaylandı", "YoY_Degisim": "-%7.2"},
    {"Şirket": "Ülker Çikolata (Silivri)", "Ülke": "Türkiye", "Kategori": "Çikolata", "Scope1_tCO2e": 2150,
     "Scope2_tCO2e": 3200, "Veri_Durumu": "Onaylandı", "YoY_Degisim": "-%3.8"},
    {"Şirket": "United Biscuits (Fransa)", "Ülke": "Fransa", "Kategori": "Bisküvi Dağıtım", "Scope1_tCO2e": 480,
     "Scope2_tCO2e": 710, "Veri_Durumu": "Veri Bekleniyor", "YoY_Degisim": "0.0%"}
]

df = pd.DataFrame(data)
df["Toplam_tCO2e"] = df["Scope1_tCO2e"] + df["Scope2_tCO2e"]

# Üst Özet Kartlar
c1, c2, c3 = st.columns(3)
c1.metric("Toplam İzlenen Emisyon", f"{df['Toplam_tCO2e'].sum():,d} tCO₂e")
c2.metric("İzlenen Şirket Sayısı", f"{len(df)} Şirket")
onay_orani = (len(df[df['Veri_Durumu'] == 'Onaylandı']) / len(df)) * 100
c3.metric("Veri Tamamlanma Oranı", f"%{onay_orani:.0f}")

st.markdown("---")

# Sol Kolon: Genel Karşılaştırma Grafiği | Sağ Kolon: Şirket Detayı (Tıklama / Seçim)
col_left, col_right = st.columns([3, 2])

with col_left:
    st.subheader("📊 Şirketlerin Toplam Karbon Ayak İzi (tCO₂e)")
    fig = px.bar(
        df.sort_values(by="Toplam_tCO2e", ascending=True),
        x="Toplam_tCO2e",
        y="Şirket",
        orientation="h",
        color="Kategori",
        text_auto=",.0f",
        labels={"Toplam_tCO2e": "Toplam Emisyon (tCO₂e)", "Şirket": ""}
    )
    fig.update_layout(height=480, margin=dict(l=0, r=20, t=30, b=20))
    st.plotly_chart(fig, use_container_width=True)

with col_right:
    st.subheader("🔍 Şirket Detayına Tıkla / Seç")
    secilen_sirket = st.selectbox("İncelemek istediğiniz şirketi seçin:", df["Şirket"].tolist())

    # Seçilen şirketin verisini filtrele
    sirket_data = df[df["Şirket"] == secilen_sirket].iloc[0]

    st.markdown(f"### {secilen_sirket}")
    st.write(f"**Ülke:** {sirket_data['Ülke']} | **Kategori:** {sirket_data['Kategori']}")

    sub_c1, sub_c2 = st.columns(2)
    sub_c1.metric("Scope 1 (Doğrudan Gaz/Yakıt)", f"{sirket_data['Scope1_tCO2e']:,d} tCO₂e")
    sub_c2.metric("Scope 2 (Şebeke Elektrik)", f"{sirket_data['Scope2_tCO2e']:,d} tCO₂e")

    st.info(f"**Yıllık Değişim (YoY):** {sirket_data['YoY_Degisim']} | **Onay Durumu:** {sirket_data['Veri_Durumu']}")

    # Kapsam Dağılım Grafiği
    pie_fig = px.pie(
        values=[sirket_data['Scope1_tCO2e'], sirket_data['Scope2_tCO2e']],
        names=["Scope 1", "Scope 2"],
        hole=0.45,
        color_discrete_sequence=["#059669", "#10b981"]
    )
    pie_fig.update_layout(height=220, margin=dict(l=10, r=10, t=20, b=10))
    st.plotly_chart(pie_fig, use_container_width=True)