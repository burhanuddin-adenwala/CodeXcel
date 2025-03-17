import streamlit as st
import pandas as pd
import time
from googletrans import Translator
from io import BytesIO
from joblib import Parallel, delayed

# Initialize translator & cache
translator = Translator()
translation_cache = {}

# Function to translate text with caching
def translate_text(text):
    if pd.notna(text):
        if text in translation_cache:
            return translation_cache[text]
        else:
            try:
                translated = translator.translate(text, dest="en").text
                translation_cache[text] = translated
                return translated
            except Exception as e:
                return "Translation Error"
    return ""

# Function to process file with live updates
def process_file(uploaded_file, status_placeholder, progress_bar):
    if uploaded_file is not None:
        df = pd.read_excel(uploaded_file, engine="openpyxl")

        required_columns = ["RCT", "BRAND_OWNER", "BRAND_1", "BRAND_EXTENSION", "PRODUCT_DESCRIPTION"]
        missing_cols = [col for col in required_columns if col not in df.columns]

        if missing_cols:
            st.error(f"Missing columns: {', '.join(missing_cols)}")
            return None

        start_time = time.time()

        # Step 1: Sorting
        df = df.sort_values(by="RCT", ascending=True)
        progress_bar.progress(10)
        status_placeholder.text("Sorting file... ✅")

        # Step 2: Concatenation
        df["Concatenated"] = df[["BRAND_OWNER", "BRAND_1", "BRAND_EXTENSION"]].fillna("").agg(";".join, axis=1).str.replace(r";+", ";", regex=True)
        progress_bar.progress(30)
        status_placeholder.text("Creating concatenated column... ✅")

        # Step 3: Batch Translation with Parallel Processing
        status_placeholder.text("Translating descriptions... 🚀 (Live updates)")
        total_rows = len(df)
        
        # Live translation updates
        translated_list = []
        for i, desc in enumerate(df["PRODUCT_DESCRIPTION"]):
            translated_list.append(translate_text(desc))
            
            # Update progress every 100 rows
            if i % 100 == 0:
                progress_percent = 30 + int((i / total_rows) * 50)
                progress_bar.progress(progress_percent)
                status_placeholder.text(f"Translating... {i}/{total_rows} rows processed ✅")

        df["Translated_Description"] = translated_list
        
        progress_bar.progress(80)
        status_placeholder.text("Translation completed! ✅")

        end_time = time.time()
        total_time = end_time - start_time
        
        progress_bar.progress(100)
        status_placeholder.text(f"Processing complete in {total_time:.2f} seconds! 🎉")

        return df, total_time
    return None, None

# Function to convert DataFrame to Excel for download
def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False)
    processed_data = output.getvalue()
    return processed_data

# --- Streamlit UI ---
st.set_page_config(page_title="CodeXcel - Automated Processing", page_icon="📊", layout="wide")

# Custom Styling
st.markdown("""
    <style>
    .css-18e3th9 {
        background-color: #F0F2F6;
    }
    .stButton>button {
        color: white;
        background-color: #FF4B4B;
        border-radius: 8px;
        border: none;
        font-size: 18px;
        padding: 10px;
    }
    .stTitle {
        color: #FF4B4B;
        font-size: 32px;
        font-weight: bold;
    }
    .footer {
        position: fixed;
        bottom: 10px;
        width: 100%;
        text-align: center;
        font-size: 14px;
        color: gray;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="stTitle"> CodeXcel - EU Omni Translater & Processor</h1>', unsafe_allow_html=True)
st.markdown("### Upload your Excel file to get started:")

uploaded_file = st.file_uploader("Upload an Excel file (.xlsx)", type=["xlsx"])

if uploaded_file:
    st.success("✅ File uploaded successfully!")

    status_placeholder = st.empty()
    progress_bar = st.progress(0)
    
    with st.spinner("Processing file...⏳"):
        processed_df, total_time = process_file(uploaded_file, status_placeholder, progress_bar)

    if processed_df is not None:
        st.write(f"### ✅ Processed Data Preview (Completed in {total_time:.2f} seconds):")
        st.dataframe(processed_df.head(10), use_container_width=True)

        # Download Processed File
        processed_file = to_excel(processed_df)
        st.download_button(
            label="📥 Download Processed File",
            data=processed_file,
            file_name="Processed_File.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

# Footer with Developer Credit
st.markdown('<p class="footer">Developed by <b>Burhanuddin Adenwala</b> 🚀</p>', unsafe_allow_html=True)
