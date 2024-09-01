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
    menu = st.sidebar.radio("Menu", ["Beranda", "Keterangan Itemset", "Aturan Asosiasi", "Visualisasi Data"])

    # Menambahkan deskripsi makna support, confidence, dan lift
    st.sidebar.write("### Penjelasan Istilah")
    st.sidebar.write("**Support**: Frekuensi kemunculan aturan tertentu.")
    st.sidebar.write("**Confidence**: Kemungkinan kemunculan itemset kedua, jika itemset pertama muncul.")
    st.sidebar.write("**Lift**: Pengukuran seberapa sering itemset muncul bersama-sama dibandingkan dengan ekspektasi jika keduanya independen.")

    if menu == "Beranda":
        st.title("Selamat Datang di Aplikasi Analisis Data Diabetes (Kab. Ciamis)")
        st.write("""
        Aplikasi ini memungkinkan Anda untuk melakukan analisis data diabetes menggunakan berbagai teknik analisis data dan visualisasi. 
        Anda dapat mengakses berbagai menu melalui sidebar untuk melihat data awal, hasil analisis, dan visualisasi data.
        """)
        

    elif menu == "Keterangan Itemset":
        st.title("Keterangan Itemset")

        # Filter hanya itemset yang berisi satu item saja
        single_itemsets = frequent_itemsets[frequent_itemsets['itemsets'].apply(lambda x: len(x) == 1)].copy()
        
        # Mengubah frozenset menjadi string
        single_itemsets['itemsets'] = single_itemsets['itemsets'].apply(lambda x: ', '.join(list(x)))  # Gabungkan itemsets menjadi satu string
        single_itemsets['support'] = (single_itemsets['support'] * 100).round(2).astype(str) + '%'  # Format support dengan persentase

        # Menyusun ulang kolom agar 'itemsets' muncul sebelum 'support'
        single_itemsets = single_itemsets[['itemsets', 'support']]

        st.write("## Keterangan Itemset dengan Frekuensi Kemunculannya")
        st.dataframe(single_itemsets)

        # Tombol download
        st.download_button("Download Keterangan Itemset", single_itemsets.to_csv(index=False), "frequent_itemsets.csv", "text/csv")


    elif menu == "Aturan Asosiasi":
        st.title("Aturan Asosiasi")
        
        st.write("## Aturan Asosiasi")
        
        # Filter berdasarkan ukuran itemset
        itemset_size = st.selectbox("Pilih Ukuran Itemset untuk Aturan Asosiasi", ["1", "2", "3"])

        # Filter berdasarkan kategori (Gender, Age, Type diabetes, Komplikasi)
        categories = {
            'Gender': ['Male', 'Female'],
            'Age': ['Age_19-34','Age_35-54', 'Age_55-64', 'Age_>65'],
            'Diabetes Type': ['E10 Type 1 diabetes mellitus', 'E11 Type 2 diabetes mellitus'],
            'Komplikasi': ['No Complications', 'With Complications']
        }

        selected_gender = st.multiselect("Pilih Gender", categories['Gender'])
        selected_age = st.multiselect("Pilih Rentang Usia", categories['Age'])
        selected_diabetes_type = st.multiselect("Pilih Jenis Diabetes", categories['Diabetes Type'])
        selected_komplikasi = st.multiselect("Pilih Komplikasi", categories['Komplikasi'])

        # Membuat filter aturan
        def filter_rules(rules):
            filtered_rules = rules[rules['antecedents'].apply(lambda x: len(x) == int(itemset_size))]

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

        filtered_rules = filter_rules(rules)

        # Menampilkan aturan dalam persentase dan menambahkan kolom rekomendasi
        filtered_rules['support'] = (filtered_rules['support'] * 100).round(2).astype(str) + '%'
        filtered_rules['confidence'] = (filtered_rules['confidence'] * 100).round(2).astype(str) + '%'
        filtered_rules['Aturan'] = filtered_rules.apply(lambda row: f"Jika {', '.join(list(row['antecedents']))} maka cenderung {', '.join(list(row['consequents']))} ({row['confidence']})", axis=1)
        
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
            
            if "Female" in antecedents:
                if "Age_35-54" in consequents:
                    return "Berikan perhatian khusus pada wanita berusia 35-54 tahun untuk deteksi dini."
                elif "Age_>65" in consequents:
                    return "Prioritaskan pemantauan wanita berusia di atas 65 tahun untuk risiko kesehatan."
                elif "No Complications" in consequents:
                    return "Pertimbangkan pemantauan tambahan pada wanita untuk mencegah komplikasi."
                elif "With Complications" in consequents:
                    return "Tingkatkan pengawasan wanita yang mengalami komplikasi."
            
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
            
            if "Age_55-64" in antecedents:
                if "Female" in consequents:
                    return "Perhatikan wanita berusia 55-64 tahun dalam rencana penanganan."
                elif "Male" in consequents:
                    return "Pertimbangkan faktor risiko tambahan untuk pria berusia 55-64 tahun."
                elif "E10 Type 1 diabetes mellitus" in consequents:
                    return "Tingkatkan pengawasan terhadap pasien berusia 55-64 tahun yang mengalami diabetes tipe 1."
                elif "E11 Type 2 diabetes mellitus" in consequents:
                    return "Tingkatkan pengawasan terhadap pasien berusia 55-64 tahun yang mengalami diabetes tipe 2."
            
            if "Age_>65" in antecedents:
                if "Female" in consequents:
                    return "Perhatikan wanita berusia di atas 65 tahun untuk strategi pencegahan."
                elif "Male" in consequents:
                    return "Fokuskan penanganan pada pria berusia di atas 65 tahun."
                elif "E10 Type 1 diabetes mellitus" in consequents:
                    return "Tingkatkan pengawasan terhadap pasien berusia di atas 65 tahun yang mengalami diabetes tipe 1."
                elif "E11 Type 2 diabetes mellitus" in consequents:
                    return "Tingkatkan pengawasan terhadap pasien berusia di atas 65 tahun yang mengalami diabetes tipe 2."
            
            if "E10 Type 1 diabetes mellitus" in antecedents:
                if "Male" in consequents:
                    return "Pasien pria dengan diabetes tipe 1 memerlukan perhatian lebih pada pengelolaan diabetes."
                elif "With Complications" in consequents:
                    return "Monitor pasien dengan diabetes tipe 1 untuk kemungkinan komplikasi lebih lanjut."
            
            if "E11 Type 2 diabetes mellitus" in antecedents:
                if "Female" in consequents:
                    return "Berikan dukungan tambahan untuk wanita dengan diabetes tipe 2."
                elif "With Complications" in consequents:
                    return "Pantau secara ketat pasien dengan diabetes tipe 2 untuk mengurangi risiko komplikasi."
            
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
        filtered_rules['Rekomendasi'] = filtered_rules.apply(generate_recommendation, axis=1)
        
        st.write(f"## Aturan Asosiasi dengan Ukuran Itemset {itemset_size}")
        st.dataframe(filtered_rules[['Aturan', 'support', 'confidence', 'Rekomendasi']])
        # Mengunduh file Excel
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            filtered_rules[['Aturan', 'support', 'confidence', 'Rekomendasi']].to_excel(writer, index=False, sheet_name='Aturan Asosiasi')
        
        st.download_button(
            label="Unduh Aturan Asosiasi (Excel)",
            data=output.getvalue(),
            file_name='aturan_asosiasi.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )



    elif menu == "Visualisasi Data":
        st.title("Visualisasi Data")
        
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
