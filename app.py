import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

st.set_page_config(page_title="Penentuan Kuota Kinerja", layout="wide")

st.title("📊 Penentuan Kuota Kinerja berdasarkan Gap KPI dan Distribusi Skor")

uploaded_file = st.file_uploader("Unggah file Penilaian_Kinerja.csv", type="csv")

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)

    st.subheader("📂 Data Awal")
    st.dataframe(df.head())

    # 1. Hitung GAP KPI terhadap atasan
    skor_kpi_dict = df.set_index("NIPP_Pekerja")["Skor_KPI_Final"].to_dict()

    def hitung_gap(row):
        skor_unit = row["Skor_KPI_Final"]
        skor_atasan = skor_kpi_dict.get(row["NIPP_Atasan"])
        if pd.notna(skor_unit) and pd.notna(skor_atasan) and skor_atasan != 0:
            return (skor_unit - skor_atasan) / skor_atasan * 100
        else:
            return None

    df["Gap_KPI_vs_Atasan_%"] = df.apply(hitung_gap, axis=1)

    # 2. Adjustment distribusi
    def assign_adjustment(gap):
        if pd.isna(gap):
            return None
        elif gap < -5:
            return -1
        elif gap > 5:
            return 1
        else:
            return 0

    df["Adjustment"] = df["Gap_KPI_vs_Atasan_%"].apply(assign_adjustment)

    # 3. Kuota berdasarkan adjustment
    def assign_kuota(adjustment, skor):
        if pd.isna(adjustment) or pd.isna(skor):
            return "Tidak Ditetapkan"
        if adjustment == -1:
            return "C (Low Performer)"
        elif adjustment == 0:
            return "B (Middle Performer)"
        elif adjustment == 1:
            return "A (Top Performer)"
        else:
            return "Tidak Dikenal"

    df["Kategori_Kuota_Manual"] = df.apply(lambda row: assign_kuota(row["Adjustment"], row["Skor_KPI_Final"]), axis=1)

    # 4. Visualisasi Gap
    st.subheader("📈 Visualisasi Distribusi Gap (%)")
    fig, ax = plt.subplots()
    sns.histplot(df["Gap_KPI_vs_Atasan_%"].dropna(), bins=30, kde=True, ax=ax)
    ax.axvline(-5, color='red', linestyle='--', label='-5% Threshold')
    ax.axvline(5, color='green', linestyle='--', label='+5% Threshold')
    ax.set_title("Distribusi Gap (%) antara KPI Unit dan Atasan")
    ax.set_xlabel("Gap (%)")
    ax.legend()
    st.pyplot(fig)

    # 5. Tabel hasil kuota manual
    st.subheader("📊 Hasil Kuota Berdasarkan Gap dan Adjustment")
    st.dataframe(df[[
        "NIPP_Pekerja", "Nama_Posisi", "Skor_KPI_Final",
        "NIPP_Atasan", "Gap_KPI_vs_Atasan_%", "Adjustment", "Kategori_Kuota_Manual"
    ]])

    # 6. Kuota otomatis berdasarkan distribusi skor
    st.subheader("🎯 Penentuan Kuota Otomatis Berdasarkan Distribusi Skor")

    skor_pilihan = st.selectbox("Pilih skor yang digunakan untuk distribusi kuota:", 
                                options=["Skor_KPI_Final", "Skor_Kinerja_Individu"])

    q80 = df[skor_pilihan].quantile(0.80)
    q20 = df[skor_pilihan].quantile(0.20)

    def assign_auto_kuota(skor):
        if pd.isna(skor):
            return "Tidak Ditetapkan"
        elif skor >= q80:
            return "A (Top Performer)"
        elif skor <= q20:
            return "C (Low Performer)"
        else:
            return "B (Middle Performer)"

    df["Kategori_Kuota_Otomatis"] = df[skor_pilihan].apply(assign_auto_kuota)

    st.markdown(f"""
    **Distribusi Kuota berdasarkan {skor_pilihan}:**  
    - **A (Top 20%)**: Skor ≥ {q80:.2f}  
    - **B (Middle 60%)**: {q20:.2f} < Skor < {q80:.2f}  
    - **C (Bottom 20%)**: Skor ≤ {q20:.2f}
    """)

    st.dataframe(df[[
        "NIPP_Pekerja", "Nama_Posisi", skor_pilihan, 
        "Kategori_Kuota_Otomatis"
    ]])

    # 7. Unduh hasil
    hasil_csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("📥 Unduh Hasil Lengkap", hasil_csv, file_name="Kuota_Kinerja_Hasil.csv")
