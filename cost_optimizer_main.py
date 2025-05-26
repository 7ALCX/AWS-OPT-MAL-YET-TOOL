import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import json
import matplotlib.pyplot as plt
import seaborn as sns

# Türkçe karakter desteği ve figür kapatma ayarları
plt.rcParams['font.family'] = 'Arial'
plt.rcParams['axes.unicode_minus'] = False

# Streamlit uygulamanızın sayfa ayarları
st.set_page_config(layout="wide", page_title="AWS Maliyet Optimizasyon Aracı")

st.title("💰 AWS Maliyet Optimizasyon Aracı")
st.write("Bu uygulama, AWS maliyet verilerini analiz eder ve potansiyel optimizasyon alanlarını belirler.")
st.write("⚠️ **ÖNEMLİ:** Bu sürüm sadece 'mock_aws_costs.json' dosyasındaki simüle edilmiş veriyi kullanır, gerçek AWS verisi çekmez.")

# --- get_cost_and_usage_data fonksiyonu (Şimdi sadece mock veri döndürecek) ---
def get_mock_cost_data():
    """
    Loads mock cost data from 'mock_aws_costs.json'.
    """
    try:
        with open('mock_aws_costs.json', 'r') as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        st.error("Hata: 'mock_aws_costs.json' bulunamadı. Lütfen dosyanın uygulamanızla aynı klasörde olduğundan emin olun.")
        st.stop()
    except Exception as e:
        st.error(f"Mock veri okunurken bir hata oluştu: {e}")
        st.stop()

# --- Main Workflow ---

# Tarih aralığı seçicileri (sidebar'da) - Bu kısım sadece görsel amaçlı kalacak
st.sidebar.header("Tarih Aralığı Seçimi (Simüle Edilmiş Veri İçin)")
today = datetime.now()
default_start_date = today - timedelta(days=30)
default_end_date = today

start_date_input = st.sidebar.date_input("Başlangıç Tarihi", default_start_date)
end_date_input = st.sidebar.date_input("Bitiş Tarihi", default_end_date)


# Simüle edilmiş veriyi çek
aws_costs = get_mock_cost_data()

# Veriyi Pandas DataFrame'e dönüştür
df = pd.DataFrame(aws_costs)
df['Date'] = pd.to_datetime(df['Date'])

if not df.empty:
    st.subheader("AWS Maliyet Verisi Örneği (İlk 5 Satır)")
    st.dataframe(df.head())

    # --- Veri İşleme ve Analiz ---
    st.header("Maliyet Analizleri")

    # a) Günlük toplam maliyetler
    daily_total_cost = df.groupby('Date')['Cost'].sum().reset_index()
    st.subheader("Günlük Toplam Maliyetler")
    st.dataframe(daily_total_cost)

    # b) Servis bazında toplam maliyetler
    service_total_cost = df.groupby('Service')['Cost'].sum().reset_index()
    service_total_cost = service_total_cost.sort_values(by='Cost', ascending=False)
    st.subheader("Servis Bazında Toplam Maliyetler")
    st.dataframe(service_total_cost)

    # --- Temel Optimizasyon Önerisi Mantığı ---
    st.header("Optimizasyon Önerileri")

    df['DayServiceCost'] = df.groupby(['Date', 'Service'])['Cost'].transform('sum')
    # Öneri eşiğini düşürdük, daha fazla öneri görmek için
    high_cost_per_service_per_day = df[df['DayServiceCost'] > 1].drop_duplicates(subset=['Date', 'Service'])

    if not high_cost_per_service_per_day.empty:
        st.warning("**Optimizasyon Önerileri:**")
        for index, row in high_cost_per_service_per_day.iterrows():
            st.write(f"- **{row['Date'].strftime('%Y-%m-%d')}** tarihinde, **'{row['Service']}'** hizmetinin maliyeti **{row['Cost']:.2f} {row['Unit']}** oldu. Kullanımını gözden geçirmeyi düşünün!")
    else:
        st.info("Maliyetler kontrol altında görünüyor; şu anda belirgin bir optimizasyon önerisi yok (simüle edilmiş veri için).")

    # --- Veri Görselleştirme ---
    st.header("Maliyet Görselleştirmeleri")

    # Günlük Maliyet Trendi Plotu
    st.subheader("Günlük Toplam AWS Maliyet Eğilimi")
    plt.figure(figsize=(12, 6))
    sns.lineplot(x='Date', y='Cost', data=daily_total_cost, marker='o', color='skyblue')
    plt.title('Daily Total AWS Cost Trend', fontsize=16)
    plt.xlabel('Date', fontsize=12)
    plt.ylabel('Cost (USD)', fontsize=12)
    plt.grid(True)
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    st.pyplot(plt)
    plt.clf()

    # Servis Bazında Maliyet Dağılımı Plotu
    st.subheader("Servis Bazında AWS Maliyet Dağılımı")
    plt.figure(figsize=(12, 7))
    sns.barplot(x='Service', y='Cost', data=service_total_cost.sort_values(by='Cost', ascending=False), palette='viridis')
    plt.title('AWS Cost Distribution by Service', fontsize=16)
    plt.xlabel('AWS Service', fontsize=12)
    plt.ylabel('Total Cost (USD)', fontsize=12)
    plt.xticks(rotation=60, ha='right')
    plt.tight_layout()
    st.pyplot(plt)
    plt.clf()

else:
    st.error("Analiz edilecek veri bulunamadı. Lütfen 'mock_aws_costs.json' dosyasının doğru olduğundan emin olun.")

st.write("\nAnaliz ve görselleştirmeler tamamlandı.")
