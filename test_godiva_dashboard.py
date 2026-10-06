import time
from playwright.sync_api import sync_playwright

APP_URL = "https://yildiz-sustainability.streamlit.app/"
HEDEF_SIRKET = "Godiva"
HEDEF_YIL = "2026"  # BigQuery'deki yıl (2025 veya 2026)

def test_godiva():
    with sync_playwright() as p:
        print("[1/5] Tarayıcı açılıyor...")
        browser = p.chromium.launch(headless=False, slow_mo=300)
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()

        try:
            print(f"[2/5] Sayfaya gidiliyor: {APP_URL}")
            page.goto(APP_URL, timeout=90000)
            time.sleep(5)

            # Streamlit Cloud Iframe tespiti
            has_iframe = page.locator("iframe[title='streamlitApp']").count() > 0
            app = page.frame_locator("iframe[title='streamlitApp']") if has_iframe else page

            # Dashboard gövdesinin gelmesini bekle
            print("Dashboard bileşenleri bekleniyor...")
            app.locator("[data-testid='stAppViewContainer']").wait_for(state="visible", timeout=60000)
            time.sleep(3)

            # -------------------------------------------------------------
            # 1. FİLTRE: ŞİRKET SEÇİMİ (GODIVA)
            # -------------------------------------------------------------
            print(f"[3/5] 1. Filtre: Şirket olarak '{HEDEF_SIRKET}' seçiliyor...")
            sirket_kutusu = app.locator("[data-testid='stSelectbox']").nth(0)
            sirket_kutusu.scroll_into_view_if_needed()
            sirket_kutusu.click()
            time.sleep(0.5)

            page.keyboard.type(HEDEF_SIRKET, delay=100)
            time.sleep(0.5)
            page.keyboard.press("Enter")
            print(f" -> '{HEDEF_SIRKET}' seçildi.")
            time.sleep(2)

            # -------------------------------------------------------------
            # 2. FİLTRE: YIL SEÇİMİ (2026)
            # -------------------------------------------------------------
            print(f"[3.1/5] 2. Filtre: Yıl olarak '{HEDEF_YIL}' seçiliyor...")
            # İkinci selectbox kutusunu seç (Yıl filtresi)
            yil_kutusu = app.locator("[data-testid='stSelectbox']").nth(1)
            yil_kutusu.scroll_into_view_if_needed()
            yil_kutusu.click()
            time.sleep(0.5)

            page.keyboard.type(HEDEF_YIL, delay=100)
            time.sleep(0.5)
            page.keyboard.press("Enter")
            print(f" -> '{HEDEF_YIL}' seçildi.")

            # Hesaplamanın tamamlanması için bekleme
            print("[4/5] Dashboard'un verileri hesaplaması bekleniyor...")
            time.sleep(5)

            # -------------------------------------------------------------
            # DOĞRULAMA (ASSERTION)
            # -------------------------------------------------------------
            print("[5/5] Ekrandaki metrikler taranıyor...")
            ekran_metni = app.locator("[data-testid='stAppViewContainer']").inner_text()

            print("\n--- Ekranda Okunan Bazı Satırlar ---")
            for satir in ekran_metni.split("\n"):
                s = satir.strip()
                if s and any(ch.isdigit() for ch in s) and len(s) < 80:
                    print(f"  > {s}")

            # BigQuery sonuçlarındaki 2026 Godiva değerleri:
            # Elektrik: 17900000, Yenilenebilir: %55, Doğalgaz: 1950000
            aranan_degerler = [
                
                "17900000", 
                "55", 
                "1950000"
            ]

            bulunanlar = [val for val in aranan_degerler if val in ekran_metni]

            print(f"\nEkranda Eşleşen BigQuery Değerleri: {bulunanlar}")
            assert len(bulunanlar) > 0, (
                f"HATA: 2026 yılı Godiva değerleri ekranda bulunamadı!\n"
                f"Aranan değerler: {aranan_degerler}"
            )

            print("\n✅ TEST BAŞARILI: Godiva ve 2026 yılı seçildi, BigQuery verileri doğrulandı!")
            print("Sayfa 10 saniye açık tutuluyor...")
            time.sleep(10)

        except Exception as e:
            page.screenshot(path="godiva_yil_hata.png", full_page=True)
            print(f"\n❌ TEST BAŞARISIZ! Ekran görüntüsü alındı: godiva_yil_hata.png")
            raise e

        finally:
            browser.close()

if __name__ == "__main__":
    test_godiva()