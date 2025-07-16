
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from fpdf import FPDF
from scipy.stats import zscore
import io
import os

st.set_page_config(page_title="QC Report Analyzer", layout="centered")
st.title("🧪 QC Test Report Analyzer")

sample_path = "sample_qc_data_utf8sig.csv"
if os.path.exists(sample_path):
    with open(sample_path, "rb") as f:
        st.download_button(
            label="📥 Download Sample Data",
            data=f,
            file_name="sample_qc_data.csv",
            mime="text/csv"
        )
else:
    st.warning("⚠️ Sample file not found. Please include sample_qc_data_utf8sig.csv when deploying.")

st.markdown("""
This tool automatically evaluates QC test results, detects outliers using Z-score, and generates a PDF summary report.

**💡 Input file must contain the following columns:**

- 항목명 (Test Item)
- 측정값 (Measured Value)
- 기준하한 (Lower Limit)
- 기준상한 (Upper Limit)
""")

uploaded_file = st.file_uploader("📁 Upload QC Test File (CSV or Excel)", type=["csv", "xlsx"])

if uploaded_file is not None:
    try:
        if uploaded_file.name.endswith("csv"):
            try:
                df = pd.read_csv(uploaded_file, encoding="utf-8-sig")
            except UnicodeDecodeError:
                df = pd.read_csv(uploaded_file, encoding="utf-8")
        else:
            df = pd.read_excel(uploaded_file)
    except Exception as e:
        st.error(f"Error loading file: {e}")
        st.stop()

    expected_columns = ["항목명", "측정값", "기준하한", "기준상한"]
    if not all(col in df.columns for col in expected_columns):
        st.error("❌ Column names are incorrect. Please refer to the sample file.")
        st.stop()

    st.success("✅ File loaded successfully.")
    st.dataframe(df)

    def assess_row(row):
        if row["측정값"] < row["기준하한"] or row["측정값"] > row["기준상한"]:
            return "Fail"
        return "Pass"

    df["Result"] = df.apply(assess_row, axis=1)
    df["Z-score"] = zscore(df["측정값"])
    df["Outlier"] = df["Z-score"].apply(lambda z: "Yes" if abs(z) > 2 else "")

    st.markdown("### 📊 Judgment Result")
    st.dataframe(df)

    st.markdown("### 📈 Z-score Outlier Detection")
    fig, ax = plt.subplots()
    ax.bar(df["항목명"], df["Z-score"])
    ax.axhline(2, color="red", linestyle="--", label="Z=2")
    ax.axhline(-2, color="red", linestyle="--")
    ax.set_ylabel("Z-score")
    ax.set_title("Outlier Detection by Z-score")
    ax.legend()
    plt.xticks(rotation=45)
    st.pyplot(fig)

    # 항목명 매핑 (한글 → 영어)
    rename_map = {
        "온도": "Temperature",
        "색상": "Color",
        "탁도": "Turbidity",
        "pH": "pH",
        "수분함량": "Moisture",
        "점도": "Viscosity",
        "비중": "Specific Gravity",
        "항목1": "Item 1",
        "항목2": "Item 2",
        "항목3": "Item 3",
        "항목4": "Item 4",
        "항목5": "Item 5",
    }

    def generate_pdf(dataframe):
        buffer = io.BytesIO()
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt="QC Test Summary Report", ln=True, align="C")
        pdf.ln(10)

        for i, row in dataframe.iterrows():
            item_name = rename_map.get(row["항목명"], row["항목명"])
            text = f"{item_name}: Value={row['측정값']}, Spec=({row['기준하한']}–{row['기준상한']}), Result={row['Result']}, Outlier={row['Outlier']}"
            text = text.encode('latin-1', 'replace').decode('latin-1')
            pdf.cell(200, 10, txt=text, ln=True)

        pdf_output = pdf.output(dest='S').encode('latin-1')
        buffer.write(pdf_output)
        buffer.seek(0)
        return buffer

    pdf_buffer = generate_pdf(df)
    st.download_button("📄 Download PDF Report", data=pdf_buffer, file_name="qc_report.pdf")
