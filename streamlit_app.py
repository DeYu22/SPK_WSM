# -*- coding: utf-8 -*-
"""app2

Sistem Pendukung Keputusan untuk Rekomendasi Tempat Wisata Terbaik Deli Serdang Menggunakan Metode Weighted Sum Model (WSM)
"""

import numpy as np
import pandas as pd
import streamlit as st
from PIL import Image
import plotly.express as px
import io

# Konfigurasi halaman
st.set_page_config(
    page_title="SPK Rekomendasi Destinasi Wisata",
    page_icon="🌴",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS kustom untuk mempercantik tampilan
def local_css(file_name):
    try:
        with open(file_name) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except:
        st.markdown("""
        <style>
        .stButton>button {
            background-color: #4CAF50;
            color: white;
            border-radius: 5px;
        }
        .stDownloadButton>button {
            background-color: #2196F3;
            color: white;
        }
        </style>
        """, unsafe_allow_html=True)

local_css("style.css")

# Fungsi untuk memuat gambar
def load_image(image_path):
    try:
        return Image.open(image_path)
    except:
        return None

header_img = load_image("assets/header.jpg")
logo_img = load_image("assets/logo.png")

# Fungsi untuk membuat template
@st.cache_data
def create_template():
    template_df = pd.DataFrame(columns=[
        'Destinasi', 'Jarak (km)', 'Biaya (ribu Rp)', 
        'Fasilitas (1-5)', 'Rating (1-5)'
    ])
    return template_df.to_csv(index=False).encode('utf-8')

def input_data_destinasi():
    st.subheader("📍 Tambah Data Destinasi Wisata")
    st.markdown("---")
    
    # Section untuk upload file
    st.subheader("📤 Upload Data dari Spreadsheet")
    
    # Template download
    csv = create_template()
    st.download_button(
        label="Download Template CSV",
        data=csv,
        file_name="template_destinasi.csv",
        mime="text/csv",
        help="Unduh template untuk mengisi data destinasi"
    )
    
    uploaded_file = st.file_uploader(
        "Upload file Excel atau CSV", 
        type=["xlsx", "xls", "csv"],
        help="Format kolom wajib: Destinasi, Jarak (km), Biaya (ribu Rp), Fasilitas (1-5), Rating (1-5)"
    )
    
    if uploaded_file is not None:
        try:
            # Baca file excel atau csv
            if uploaded_file.name.endswith('.csv'):
                df_upload = pd.read_csv(uploaded_file)
            else:
                df_upload = pd.read_excel(uploaded_file)
            
            # Validasi kolom
            required_columns = ['Destinasi', 'Jarak (km)', 'Biaya (ribu Rp)', 'Fasilitas (1-5)', 'Rating (1-5)']
            if not all(col in df_upload.columns for col in required_columns):
                st.error("Format kolom tidak sesuai. Pastikan ada kolom: Destinasi, Jarak (km), Biaya (ribu Rp), Fasilitas (1-5), Rating (1-5)")
            else:
                # Konversi ke list dan simpan ke session state
                st.session_state.destinasi = df_upload[required_columns].values.tolist()
                st.success("✅ Data berhasil diupload!")
                
                # Tampilkan preview
                st.subheader("Preview Data")
                st.dataframe(
                    df_upload.head().style.format({
                        'Jarak (km)': '{:.1f} km',
                        'Biaya (ribu Rp)': 'Rp {:,.0f}',
                        'Rating (1-5)': '{:.1f}'
                    }),
                    use_container_width=True
                )
                
        except Exception as e:
            st.error(f"Error membaca file: {str(e)}")
    
    st.markdown("---")
    st.subheader("Atau Tambah Data Manual")
    
    # Contoh data sesuai tabel normalisasi
    if st.button("Gunakan Contoh Data"):
        contoh_data = [
            ["Air Terjun Dua Warna", 66, 25000, 4, 4],
            ["Air Terjun Sempurga Putih", 66, 20000, 3, 4],
            ["Air Terjun Pelangi Indah", 71, 25000, 3, 4],
            ["Pulau Siba", 50, 30000, 4, 4],
            ["Danau Linting", 70, 20000, 4, 4],
            ["Pemandian Alam Loknya", 61, 15000, 3, 4],
            ["Pemandian Alam Sembabe", 41, 15000, 4, 4],
            ["Pemandian Alam Lau Siegmbura", 54, 20000, 4, 5],
            ["Pantai Salju", 66, 25000, 4, 4],
            ["Hillpark Sibolangi", 59, 110000, 4, 5]
        ]
        st.session_state.destinasi = contoh_data
        st.success("Contoh data berhasil dimuat!")
    
    with st.expander("➕ Tambah Destinasi Baru", expanded=True):
        col1, col2 = st.columns(2)

        with col1:
            nama = st.text_input("Nama Destinasi", key="nama")
            jarak = st.number_input("Jarak (km)", min_value=0.0, format="%.1f", key="jarak", help="Semakin kecil jarak semakin baik")

        with col2:
            biaya = st.number_input(
                "Biaya (ribu Rp)", 
                min_value=0.0, 
                step=1000.0,
                key="biaya", 
                help="Semakin murah biaya semakin baik"
            )
            fasilitas = st.slider("Fasilitas (1-5)", 1, 5, 3, key="fasilitas", help="1 = Buruk, 5 = Sangat Baik")
            rating = st.slider("Rating Pengunjung (1-5)", 1.0, 5.0, 4.0, step=0.1, format="%.1f", key="rating", help="1 = Terburuk, 5 = Terbaik")

        if st.button("Tambahkan Destinasi", key="add_button"):
            destinasi_baru = [nama, float(jarak), float(biaya), int(fasilitas), float(rating)]
            st.session_state.destinasi.append(destinasi_baru)
            st.success(f"✅ Destinasi '{nama}' berhasil ditambahkan!")
            st.balloons()

    # Tampilkan destinasi yang sudah ditambahkan
    if st.session_state.destinasi:
        st.markdown("---")
        st.subheader("📋 Daftar Destinasi")

        df = pd.DataFrame(
            st.session_state.destinasi,
            columns=['Destinasi', 'Jarak (km)', 'Biaya (ribu Rp)', 'Fasilitas (1-5)', 'Rating (1-5)']
        )

        # Tampilkan dataframe dengan format yang lebih rapi
        st.dataframe(
            df.style.format({
                'Jarak (km)': '{:.1f} km',
                'Biaya (ribu Rp)': 'Rp {:,.0f}',
                'Rating (1-5)': '{:.1f}'
            })
            .background_gradient(cmap='Blues', subset=['Rating (1-5)'])
            .bar(color='#ff6961', subset=['Biaya (ribu Rp)'])
            .bar(color='#77dd77', subset=['Fasilitas (1-5)']),
            use_container_width=True
        )

        if st.button("Lanjut ke Bobot Kriteria ➡", key="continue_button"):
            st.session_state.step = 2
            st.rerun()

def input_bobot_kriteria():
    st.subheader("⚖️ Penentuan Bobot Kriteria")
    st.markdown("""
    <div style='background-color:#e6f3ff; padding:15px; border-radius:10px; margin-bottom:20px;'>
    <p style='font-size:16px;'>Silakan tentukan bobot untuk setiap kriteria (total harus 100%). Bobot yang lebih besar berarti kriteria tersebut lebih penting.</p>
    </div>
    """, unsafe_allow_html=True)

    cols = st.columns(4)
    kriteria = {
        "Jarak (km)": {"min": 0, "max": 100, "value": 30, "icon": "📍", "help": "Bobot untuk jarak (semakin kecil semakin baik)"},
        "Biaya (ribu Rp)": {"min": 0, "max": 100, "value": 25, "icon": "💰", "help": "Bobot untuk biaya (semakin murah semakin baik)"},
        "Fasilitas": {"min": 0, "max": 100, "value": 20, "icon": "🏨", "help": "Bobot untuk fasilitas (semakin baik semakin tinggi)"},
        "Rating": {"min": 0, "max": 100, "value": 25, "icon": "⭐", "help": "Bobot untuk rating pengunjung (semakin tinggi semakin baik)"}
    }

    bobot = []
    for i, (nama, params) in enumerate(kriteria.items()):
        with cols[i]:
            st.markdown(f"**{params['icon']} {nama}**")
            weight = st.number_input(
                f"Bobot (%)",
                min_value=params["min"],
                max_value=params["max"],
                value=params["value"],
                key=f"bobot_{i}",
                help=params["help"]
            )
            bobot.append(weight)

    total = sum(bobot)
    st.markdown(f"**Total Bobot: {total}%**")

    if total != 100:
        st.error(f"🚨 Total bobot harus tepat 100%. Saat ini: {total}%")
    else:
        if st.button("Hitung Skor 🧮", key="calculate_button"):
            st.session_state.bobot = np.array([w/100 for w in bobot])
            st.session_state.step = 3
            st.rerun()

    if st.button("⬅ Kembali ke Destinasi", key="back_button"):
        st.session_state.step = 1
        st.rerun()

def normalisasi_data(df):
    # Normalisasi kriteria benefit (Fasilitas, Rating)
    df[['Fasilitas (1-5)', 'Rating (1-5)']] = df[['Fasilitas (1-5)', 'Rating (1-5)']].div(
        df[['Fasilitas (1-5)', 'Rating (1-5)']].max()
    )

    # Normalisasi kriteria cost (Jarak, Biaya)
    df[['Jarak (km)', 'Biaya (ribu Rp)']] = df[['Jarak (km)', 'Biaya (ribu Rp)']].min() / df[['Jarak (km)', 'Biaya (ribu Rp)']]

    return df

def hitung_skor(df_normalized, bobot):
    return (
        df_normalized['Jarak (km)'] * bobot[0] +
        df_normalized['Biaya (ribu Rp)'] * bobot[1] +
        df_normalized['Fasilitas (1-5)'] * bobot[2] +
        df_normalized['Rating (1-5)'] * bobot[3]
    )

def tampilkan_hasil():
    st.subheader("📊 Hasil Analisis")
    st.markdown("---")

    # Buat DataFrame
    df = pd.DataFrame(
        st.session_state.destinasi,
        columns=['Destinasi', 'Jarak (km)', 'Biaya (ribu Rp)', 'Fasilitas (1-5)', 'Rating (1-5)']
    )

    # Normalisasi data
    df_normalized = normalisasi_data(df.copy())

    # Hitung skor akhir
    df['Skor Akhir'] = hitung_skor(df_normalized, st.session_state.bobot)

    # Ranking
    df_ranking = df.sort_values('Skor Akhir', ascending=False)
    df_ranking['Peringkat'] = range(1, len(df_ranking)+1)  # Perbaikan di sini

    # Tampilkan hasil dalam tab
    tab1, tab2, tab3, tab4 = st.tabs(["🏆 Peringkat", "📈 Data Normalisasi", "📊 Visualisasi", "🔍 Analisis Detail"])

    with tab1:
        st.subheader("Peringkat Destinasi")
        cols = st.columns([1,3,1])
        with cols[1]:
            st.dataframe(
                df_ranking[['Peringkat', 'Destinasi', 'Skor Akhir']].style
                .format({
                    'Skor Akhir': '{:.3f}',
                    'Peringkat': '{:.0f}'
                })
                .background_gradient(cmap='YlOrBr', subset=['Skor Akhir']),
                use_container_width=True
            )

        # Tampilkan pemenang
        pemenang = df_ranking.iloc[0]
        st.success(f"""
        🎉 **Destinasi Terbaik:** {pemenang['Destinasi']}
        **Skor Akhir:** {pemenang['Skor Akhir']:.3f}
        **Rating:** {pemenang['Rating (1-5)']:.1f} ⭐
        **Biaya:** Rp {pemenang['Biaya (ribu Rp)']:,.0f}
        **Jarak:** {pemenang['Jarak (km)']:.1f} km
        """)

    with tab2:
        st.subheader("Data Normalisasi")
        st.write("""
        - Jarak dan Biaya adalah **kriteria cost** (semakin kecil semakin baik)
        - Fasilitas dan Rating adalah **kriteria benefit** (semakin besar semakin baik)
        """)
        st.dataframe(
            df_normalized.style.format({
                'Jarak (km)': '{:.3f}',
                'Biaya (ribu Rp)': '{:.3f}',
                'Fasilitas (1-5)': '{:.3f}',
                'Rating (1-5)': '{:.3f}'
            }),
            use_container_width=True
        )

    with tab3:
        st.subheader("Visualisasi Interaktif")

        col1, col2 = st.columns(2)
        with col1:
            fig1 = px.bar(
                df_ranking,
                x='Skor Akhir',
                y='Destinasi',
                orientation='h',
                color='Skor Akhir',
                title='Peringkat Skor Destinasi'
            )
            st.plotly_chart(fig1, use_container_width=True)

        with col2:
            fig2 = px.scatter(
                df,
                x='Biaya (ribu Rp)',
                y='Rating (1-5)',
                size='Fasilitas (1-5)',
                color='Skor Akhir',
                hover_name='Destinasi',
                title='Biaya vs Rating (Ukuran = Fasilitas)'
            )
            st.plotly_chart(fig2, use_container_width=True)

    with tab4:
        st.subheader("Analisis Kriteria Detail")
        st.dataframe(
            df_ranking.set_index('Peringkat').style
            .format({
                'Jarak (km)': '{:.1f} km',
                'Biaya (ribu Rp)': 'Rp {:,.0f}',
                'Rating (1-5)': '{:.1f}'
            })
            .background_gradient(cmap='Greens', subset=['Rating (1-5)'])
            .background_gradient(cmap='Reds', subset=['Biaya (ribu Rp)'])
            .background_gradient(cmap='Blues', subset=['Jarak (km)']),
            use_container_width=True
        )

    if st.button("🔄 Analisis Baru", key="new_analysis"):
        st.session_state.clear()
        st.session_state.step = 1
        st.rerun()

def main():
    # Header aplikasi
    col1, col2 = st.columns([1, 3])
    with col1:
        if logo_img:
            st.image(logo_img, width=150)
    with col2:
        st.title("🌴 Sistem Pendukung Keputusan untuk Rekomendasi Tempat Wisata Terbaik Deli Serdang Menggunakan Metode Weighted Sum Model (WSM)")
        st.markdown("""
<div style='text-align: justify; font-size:16px; line-height:1.6;'>
    <p>Kabupaten Deli Serdang, yang berada di Provinsi Sumatera Utara, memiliki berbagai destinasi wisata yang menarik, baik itu wisata alam maupun budaya. Dengan banyaknya pilihan yang ada, wisatawan seringkali merasa kesulitan dalam memilih tempat wisata yang paling sesuai dengan keinginan mereka. Untuk itu, dibutuhkan sebuah sistem yang dapat memudahkan pengunjung dalam memilih destinasi wisata berdasarkan kriteria yang mereka anggap penting.
    Untuk mempermudah calon wisatawan dalam mengetahui lebih banyak mengenai tempat wisata dengan informasi yang akurat dan rekomendasi pemilihan objek wisata yang sesuai dengan kriteria-kriteria yang dipilih, maka dibutuhkan sebuah sistem komputerisasi yang memuat seluruh informasi daerah wisata secara online yang diharapkan dapat digunakan untuk mendapatkan informasi dan pendukung keputusan pemilihan objek wisata secara efektif.
    Salah satu sistem komputerisasi yang cukup berkembang saat ini adalah sistem pendukung keputusan (Decisions Support System). Sistem pendukung keputusan adalah bagian dari sistem informasi berbasis komputer yang dipakai untuk mendukung pengambilan Keputusan.</p>
</div>
""", unsafe_allow_html=True)

    if header_img:
        st.image(header_img, use_container_width=True, caption="Temukan Destinasi Wisata Terbaik")

    # Inisialisasi session state
    if 'step' not in st.session_state:
        st.session_state.step = 1
    if 'destinasi' not in st.session_state:
        st.session_state.destinasi = []
    if 'bobot' not in st.session_state:
        st.session_state.bobot = None

    # Langkah 1: Input data destinasi
    if st.session_state.step == 1:
        input_data_destinasi()

    # Langkah 2: Input bobot kriteria
    elif st.session_state.step == 2:
        input_bobot_kriteria()

    # Langkah 3: Hasil dan visualisasi
    elif st.session_state.step == 3:
        tampilkan_hasil()

if __name__ == '__main__':
    main()
