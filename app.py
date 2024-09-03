import streamlit as st
import pandas as pd
import io
import matplotlib.pyplot as plt
import seaborn as sns
from mlxtend.frequent_patterns import apriori, association_rules

# Fungsi untuk membuat rentang umur
def create_age_bins(age):
    if age <= 18:
        return 'Umur_0-18'
    elif age <= 34:
        return 'Umur_19-34'
    elif age <= 54:
        return 'Umur_35-54'
    elif age <= 64:
        return 'Umur_55-64'
    else:
        return 'Umur_>65'

# Streamlit UI untuk upload file
uploaded_file = st.sidebar.file_uploader("Upload File Data Excel", type=["xlsx"])
if uploaded_file:
    data = pd.read_excel(uploaded_file)
    df = pd.DataFrame(data)
    df['Rentang Umur'] = df['Umur'].apply(create_age_bins)
    
    # One-Hot Encoding
    one_hot_encoded = pd.get_dummies(df[['Gender', 'Rentang Umur', 'Nama diagnosis ICD 10', 'Komplikasi']])
    
    # Rename Columns
    rename_dict = {
    'Gender_LAKI-LAKI': 'Male',
    'Gender_PEREMPUAN': 'Female',
    'Rentang Umur_Umur_0-18': 'Age_0-18',
    'Rentang Umur_Umur_19-34': 'Age_19-34',
    'Rentang Umur_Umur_35-54': 'Age_35-54',
    'Rentang Umur_Umur_55-64': 'Age_55-64',
    'Rentang Umur_Umur_>65': 'Age_>65',
    'Nama diagnosis ICD 10_E10 Type 1 diabetes mellitus': 'E10 Type 1 diabetes mellitus',
    'Nama diagnosis ICD 10_E11 Type 2 diabetes mellitus': 'E11 Type 2 diabetes mellitus',
    'Nama diagnosis ICD 10_O24 Diabetes mellitus in pregnancy': 'O24 Diabetes mellitus in pregnancy',
    'Komplikasi_No': 'No Complications',
    'Komplikasi_Yes': 'With Complications'
}
    one_hot_encoded.rename(columns=rename_dict, inplace=True)

    # Menggunakan apriori untuk mendapatkan frequent itemsets
    min_support = 0.02  # Nilai support minimum, bisa diubah dari Streamlit slider
    frequent_itemsets = apriori(one_hot_encoded, min_support=min_support, use_colnames=True)

    # Menghitung aturan asosiasi menggunakan mlxtend
    rules = association_rules(frequent_itemsets, metric="confidence", min_threshold=0.05)

    # Streamlit UI
    st.sidebar.title("Navigasi")
    menu = st.sidebar.radio("Menu", ["Dashboard", "Keterangan Pasien Diabetes Melitus", "Analisis Pola Diabetes"])

    # Menambahkan deskripsi makna support, confidence, dan lift
    st.sidebar.write("### Penjelasan Istilah")
    st.sidebar.write("**Support**: Frekuensi kemunculan aturan tertentu.")
    st.sidebar.write("**Confidence**: Kemungkinan kemunculan itemset kedua, jika itemset pertama muncul.")
    st.sidebar.write("**Lift**: Pengukuran seberapa sering itemset muncul bersama-sama dibandingkan dengan ekspektasi jika keduanya independen.")

    if menu == "Dashboard":
        st.title("Selamat Datang di Platform Analisis Data Diabetes (Kab. Ciamis)")
        st.write("""
        Aplikasi ini memungkinkan Anda untuk melakukan analisis data diabetes menggunakan berbagai teknik analisis data dan visualisasi. 
        Anda dapat mengakses berbagai menu melalui sidebar untuk melihat cakupan DM di Kabupaten Ciamis. Berikut adalah distribusi data terkait DM di Kabupaten Ciamis: 
        """)

        st.write("## Data DM Kab. Ciamis")
        
        plot_type = st.selectbox("Pilih Jenis Visualisasi", ["Rentang Umur", "Gender", "Tipe Diabetes", "Komplikasi"])
        
        if plot_type == "Rentang Umur":
            plt.figure(figsize=(10, 5))
            sns.countplot(data=df, x='Rentang Umur', palette='viridis')
            plt.title('Rentang Umur Pasien Diabetes')
            st.pyplot(plt)
            
        elif plot_type == "Gender":
            plt.figure(figsize=(10, 5))
            sns.countplot(data=df, x='Gender', palette='viridis')
            plt.title('Gender')
            st.pyplot(plt)
        
        elif plot_type == "Tipe Diabetes":
            plt.figure(figsize=(10, 5))
            sns.countplot(data=df, x='Nama diagnosis ICD 10', palette='viridis')
            plt.title('Tipe Diabetes')
            st.pyplot(plt)
        
        elif plot_type == "Komplikasi":
            plt.figure(figsize=(10, 5))
            sns.countplot(data=df, x='Komplikasi', palette='viridis')
            plt.title('Komplikasi Pasien Diabetes')
            st.pyplot(plt)

    elif menu == "Keterangan Pasien Diabetes Melitus":
        st.title("Keterangan Pasien Diabetes Melitus")

        # Filter hanya data yang berisi satu item saja
        single_items = frequent_itemsets[frequent_itemsets['itemsets'].apply(lambda x: len(x) == 1)].copy()
        
        # Mengubah frozenset menjadi string
        total_data_count = len(data)
        single_items['item'] = single_items['itemsets'].apply(lambda x: ', '.join(list(x)))  # Gabungkan itemsets menjadi satu string
        single_items['persentase'] = (single_items['support'] * 100).round(2).astype(str) + '%'  # Format support sebagai persentase
        single_items['jumlah'] = (single_items['support'] * total_data_count).astype(int)  # Menghitung jumlah kemunculan

        # Menyusun ulang kolom agar 'item' muncul sebelum 'percentage' dan 'count'
        single_items = single_items[['item', 'jumlah', 'persentase']]

        st.dataframe(single_items)

        # Tombol download
        st.download_button("Download Keterangan Frekuensi", single_items.to_csv(index=False), "frekuensi_kemunculan.csv", "text/csv")


    elif menu == "Analisis Pola Diabetes":
        st.title("Analisis Pola Diabetes")
        
        # Filter berdasarkan ukuran kelompok
        kelompok_ukuran = st.selectbox("Jumlah Kondisi Pertama", ["1", "2", "3"])

        # Filter berdasarkan kategori (Gender, Age, Type diabetes, Komplikasi)
        categories = {
            'Gender': ['Male', 'Female'],
            'Usia': ['Age_19-34', 'Age_35-54', 'Age_55-64', 'Age_>65'],
            'Jenis Diabetes': ['E10 Type 1 diabetes mellitus', 'E11 Type 2 diabetes mellitus'],
            'Komplikasi': ['No Complications', 'With Complications']
        }

        selected_gender = st.multiselect("Pilih Jenis Kelamin", categories['Gender'])
        selected_age = st.multiselect("Pilih Rentang Usia", categories['Usia'])
        selected_diabetes_type = st.multiselect("Pilih Jenis Diabetes", categories['Jenis Diabetes'])
        selected_komplikasi = st.multiselect("Pilih Komplikasi", categories['Komplikasi'])

        # Membuat filter untuk pola yang ditemukan
        def filter_pola(rules):
            filtered_rules = rules[rules['antecedents'].apply(lambda x: len(x) == int(kelompok_ukuran))]

            if selected_gender:
                filtered_rules = filtered_rules[filtered_rules['antecedents'].apply(lambda x: any(cat in x for cat in selected_gender)) | 
                                                filtered_rules['consequents'].apply(lambda x: any(cat in x for cat in selected_gender))]
            if selected_age:
                filtered_rules = filtered_rules[filtered_rules['antecedents'].apply(lambda x: any(cat in x for cat in selected_age)) | 
                                                filtered_rules['consequents'].apply(lambda x: any(cat in x for cat in selected_age))]
            if selected_diabetes_type:
                filtered_rules = filtered_rules[filtered_rules['antecedents'].apply(lambda x: any(cat in x for cat in selected_diabetes_type)) | 
                                                filtered_rules['consequents'].apply(lambda x: any(cat in x for cat in selected_diabetes_type))]
            if selected_komplikasi:
                filtered_rules = filtered_rules[filtered_rules['antecedents'].apply(lambda x: any(cat in x for cat in selected_komplikasi)) | 
                                                filtered_rules['consequents'].apply(lambda x: any(cat in x for cat in selected_komplikasi))]

            return filtered_rules

        filtered_pola = filter_pola(rules)
        total_data_count = len(data)

        # Menampilkan hasil dalam persentase dan menambahkan kolom rekomendasi
        filtered_pola['Persentase Kemunculan'] = (filtered_pola['support'] * 100).round(2).astype(str) + '%'
        filtered_pola['Tingkat Kebenaran'] = (filtered_pola['confidence'] * 100).round(2).astype(str) + '%'
        filtered_pola['Pola'] = filtered_pola.apply(lambda row: f"Jika {', '.join(list(row['antecedents']))}, maka kemungkinan {', '.join(list(row['consequents']))} ({row['Tingkat Kebenaran']})", axis=1)
        filtered_pola['Jumlah Pasien'] = (filtered_pola['support'] * total_data_count).round().astype(int)
        
        # Menghasilkan rekomendasi berdasarkan aturan yang ditemukan
        def generate_recommendation(row):
            antecedents = ', '.join(list(row['antecedents']))
            consequents = ', '.join(list(row['consequents']))
            
            # Contoh rekomendasi berdasarkan kombinasi aturan
            if "Male" in antecedents:
                if "Age_55-64" in consequents:
                    return "Perhatikan pasien pria dengan rentang usia 55-64 tahun untuk evaluasi risiko kesehatan."
                elif "Age_>65" in consequents:
                    return "Pertimbangkan tindakan pencegahan tambahan untuk pria berusia di atas 65 tahun."
                elif "No Complications" in consequents:
                    return "Lakukan pemantauan berkala pada pria untuk memastikan tidak mengalami komplikasi."
                elif "With Complications" in consequents:
                    return "Monitor secara intensif pria yang menunjukkan gejala komplikasi."
                elif "Age_19-34" in consequents:
                    return "Pantau usia dewasa muda untuk melakukan pencegahan dini"
                elif "E10 Type 1 diabetes mellitus" in consequents:
                    return "Lakukan pemantauan lebih lanjut terhadap pasien pria yang mengalami diabetes tipe 1"
                elif "E11 Type 2 diabetes mellitus" in consequents:
                    return "Pertimbangkan tindakan yang lebih tepat terhadap pasien pria yang mengalami diabetes tipe 2"
                elif "Age_35-54" in consequents:
                    return "Berikan perhatian khusus pada pria berusia 35-54 tahun untuk deteksi dini."
            
            if "Female" in antecedents:
                if "Age_19-34" in consequents:
                    return "Pantau usia dewasa muda untuk melakukan pencegahan dini"
                elif "Age_35-54" in consequents:
                    return "Berikan perhatian khusus pada wanita berusia 35-54 tahun untuk deteksi dini."
                elif "Age_55-64" in consequents:
                    return "Tingkatkan pengawasan terhadap pasien wanita di usia produktif"
                elif "Age_>65" in consequents:
                    return "Prioritaskan pemantauan wanita berusia di atas 65 tahun untuk risiko kesehatan."
                elif "No Complications" in consequents:
                    return "Pertimbangkan pemantauan tambahan pada wanita untuk mencegah komplikasi."
                elif "With Complications" in consequents:
                    return "Tingkatkan pengawasan wanita yang mengalami komplikasi."
                elif "E10 Type 1 diabetes mellitus" in consequents:
                    return "Lakukan pemantauan lebih lanjut terhadap pasien wanita yang mengalami diabetes tipe 1"
                elif "E11 Type 2 diabetes mellitus" in consequents:
                    return "Pertimbangkan tindakan yang lebih tepat terhadap pasien wanita yang mengalami diabetes tipe 2"
                
            
            # Rekomendasi berdasarkan Age
            if "Age_35-54" in antecedents:
                if "Female" in consequents:
                    return "Fokuskan strategi penanganan pada wanita berusia 35-54 tahun."
                elif "Male" in consequents:
                    return "Fokuskan strategi penanganan pada pria berusia 35-54 tahun."
                elif "E10 Type 1 diabetes mellitus" in consequents:
                    return "Tingkatkan pengawasan terhadap pasien berusia 35-54 tahun yang mengalami diabetes tipe 1."
                elif "E11 Type 2 diabetes mellitus" in consequents:
                    return "Tingkatkan pengawasan terhadap pasien berusia 35-54 tahun yang mengalami diabetes tipe 2."
                elif "No Complications" in consequents:
                    return "Pertimbangkan pemantauan tambahan pada pasien usia 35-54 tahun untuk mencegah komplikasi."
                elif "With Complications" in consequents:
                    return "Tingkatkan pengawasan pada pasien usia 35-54 tahun yang mengalami komplikasi."
            
            if "Age_55-64" in antecedents:
                if "Female" in consequents:
                    return "Perhatikan wanita berusia 55-64 tahun dalam rencana penanganan."
                elif "Male" in consequents:
                    return "Pertimbangkan faktor risiko tambahan untuk pria berusia 55-64 tahun."
                elif "E10 Type 1 diabetes mellitus" in consequents:
                    return "Tingkatkan pengawasan terhadap pasien berusia 55-64 tahun yang mengalami diabetes tipe 1."
                elif "E11 Type 2 diabetes mellitus" in consequents:
                    return "Tingkatkan pengawasan terhadap pasien berusia 55-64 tahun yang mengalami diabetes tipe 2."
                elif "No Complications" in consequents:
                    return "Pertimbangkan pemantauan tambahan pada pasien usia 55-64 tahun untuk mencegah komplikasi."
                elif "With Complications" in consequents:
                    return "Tingkatkan pengawasan pada pasien usia 55-64 tahun yang mengalami komplikasi."
            
            if "Age_>65" in antecedents:
                if "Female" in consequents:
                    return "Perhatikan wanita berusia di atas 65 tahun untuk strategi pencegahan."
                elif "Male" in consequents:
                    return "Fokuskan penanganan pada pria berusia di atas 65 tahun."
                elif "E10 Type 1 diabetes mellitus" in consequents:
                    return "Tingkatkan pengawasan terhadap pasien berusia di atas 65 tahun yang mengalami diabetes tipe 1."
                elif "E11 Type 2 diabetes mellitus" in consequents:
                    return "Tingkatkan pengawasan terhadap pasien berusia di atas 65 tahun yang mengalami diabetes tipe 2."
                elif "No Complications" in consequents:
                    return "Pertimbangkan pemantauan tambahan pada pasien di atas 65 tahun untuk mencegah komplikasi."
                elif "With Complications" in consequents:
                    return "Tingkatkan pengawasan pada pasien usia di atas 65 tahun yang mengalami komplikasi."
            
            if "E10 Type 1 diabetes mellitus" in antecedents:
                if "Male" in consequents:
                    return "Pasien pria dengan diabetes tipe 1 memerlukan perhatian lebih pada pengelolaan diabetes."
                elif "With Complications" in consequents:
                    return "Monitor pasien dengan diabetes tipe 1 untuk kemungkinan komplikasi lebih lanjut."
                elif "Age_19-34" in consequents:
                    return "Pantau usia dewasa muda yang mengalami diabetes tipe 1"
                elif "Age_35-54" in consequents:
                    return "Berikan perhatian khusus pada pasien diabetes tipe 1 untuk deteksi dini."
                elif "Age_55-64" in consequents:
                    return "Tingkatkan pengawasan terhadap pasien diabetes tipe 1 di usia produktif"
                elif "Age_>65" in consequents:
                    return "Prioritaskan pemantauan pasien diabetes tipe 1 berusia di atas 65 tahun untuk risiko kesehatan."
            
            if "E11 Type 2 diabetes mellitus" in antecedents:
                if "Female" in consequents:
                    return "Berikan dukungan tambahan untuk wanita dengan diabetes tipe 2."
                elif "With Complications" in consequents:
                    return "Pantau secara ketat pasien dengan diabetes tipe 2 untuk mengurangi risiko komplikasi."
                elif "Age_19-34" in consequents:
                    return "Pantau usia dewasa muda yang mengalami diabetes tipe 2"
                elif "Age_35-54" in consequents:
                    return "Berikan perhatian khusus pada pasien diabetes tipe 2 untuk deteksi dini."
                elif "Age_55-64" in consequents:
                    return "Tingkatkan pengawasan terhadap pasien diabetes tipe 2 di usia produktif"
                elif "Age_>65" in consequents:
                    return "Prioritaskan pemantauan pasien diabetes tipe 2 berusia di atas 65 tahun untuk risiko kesehatan."
            
            if "E10 Type 1 diabetes mellitus" in antecedents and "Komplikasi_Yes" in consequents:
                return "Pantau pasien dengan diabetes tipe 1 secara ketat untuk mencegah komplikasi."
            elif "E11 Type 2 diabetes mellitus" in antecedents and "Komplikasi_Yes" in consequents:
                return "Lakukan pemeriksaan rutin pada pasien dengan diabetes tipe 2 untuk mengurangi risiko komplikasi."
            elif "Age_>65" in antecedents and "Komplikasi_Yes" in consequents:
                return "Prioritaskan penanganan komplikasi untuk pasien di atas 65 tahun."
            elif "Male" in antecedents and "Komplikasi_Yes" in consequents:
                return "Perhatikan faktor risiko komplikasi pada pasien pria."
            elif "No Complications" in consequents:
                return "Berikan perhatian lebih pada pasien yang menunjukkan gejala komplikasi."
            else:
                return "Pertimbangkan untuk menyesuaikan strategi penanganan berdasarkan aturan yang dihasilkan."

        # Tambahkan kolom Rekomendasi ke dataframe
        filtered_pola['Rekomendasi'] = filtered_pola.apply(generate_recommendation, axis=1)
        
        st.write(f"## Pola yang Ditemukan")
        st.dataframe(filtered_pola[['Pola', 'Tingkat Kebenaran','Jumlah Pasien', 'Rekomendasi']])
        
        # Mengunduh file Excel
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            filtered_pola[['Pola', 'Tingkat Kebenaran','Jumlah Pasien', 'Rekomendasi']].to_excel(writer, index=False, sheet_name='Pola Diabetes')
        
        st.download_button(
            label="Unduh Hasil Analisis Pola (Excel)",
            data=output.getvalue(),
            file_name='analisis_pola_diabetes.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )


    elif menu == "Dashboard":
        st.title("Dashboard")
        
        st.write("## Distribusi Data")
        
        plot_type = st.selectbox("Pilih Jenis Visualisasi", ["Distribusi Rentang Umur", "Distribusi Gender", "Distribusi Nama Diagnosis ICD 10", "Distribusi Komplikasi"])
        
        if plot_type == "Distribusi Rentang Umur":
            plt.figure(figsize=(10, 5))
            sns.countplot(data=df, x='Rentang Umur', palette='viridis')
            plt.title('Distribusi Rentang Umur')
            st.pyplot(plt)
            
        elif plot_type == "Distribusi Gender":
            plt.figure(figsize=(10, 5))
            sns.countplot(data=df, x='Gender', palette='viridis')
            plt.title('Distribusi Gender')
            st.pyplot(plt)
        
        elif plot_type == "Distribusi Nama Diagnosis ICD 10":
            plt.figure(figsize=(10, 5))
            sns.countplot(data=df, x='Nama diagnosis ICD 10', palette='viridis')
            plt.title('Distribusi Nama Diagnosis ICD 10')
            st.pyplot(plt)
        
        elif plot_type == "Distribusi Komplikasi":
            plt.figure(figsize=(10, 5))
            sns.countplot(data=df, x='Komplikasi', palette='viridis')
            plt.title('Distribusi Komplikasi')
            st.pyplot(plt)

else:
    st.warning("Silakan upload file data untuk memulai.")
    st.stop()