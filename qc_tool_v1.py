import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import zscore
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle, Paragraph, SimpleDocTemplate, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from io import BytesIO
from datetime import datetime
import os

st.set_page_config(page_title="QC Report Analyzer", layout="centered")
st.title("🧪 QC Test Report Analyzer")

# 샘플 파일 다운로드
sample_path = "sample_qc_data_utf8sig.csv"
if os.path.exists(sample_path):
    with open(sample_path, "rb") as f:
        st.download_button(
            label="📥 Download Sample Data",
            data=f,
            file_name="sample_qc_data.csv",
            mime="text/csv"
        )

st.markdown("""
Upload your QC test result file. The file must include the following columns:
- Item
- Value
- Lower Limit
- Upper Limit
""")

uploaded_file = st.file_uploader("📁 Upload QC Test File (CSV or Excel)", type=["csv", "xlsx"])

if uploaded_file:
    try:
        if uploaded_file.name.endswith("csv"):
            df = pd.read_csv(uploaded_file, encoding="utf-8-sig")
        else:
            df = pd.read_excel(uploaded_file)
    except Exception as e:
        st.error(f"Failed to load file: {e}")
        st.stop()

    # 한글 컬럼명 자동 변환
    rename_dict = {
        "항목명": "Item",
        "측정값": "Value",
        "기준하한": "Lower Limit",
        "기준상한": "Upper Limit"
    }
    df = df.rename(columns=rename_dict)

    required_cols = ["Item", "Value", "Lower Limit", "Upper Limit"]
    if not all(col in df.columns for col in required_cols):
        st.error("❌ Required columns are missing.")
        st.write("Columns found:", df.columns.tolist())
        st.stop()

    # 결과 처리
    df["Result"] = df.apply(lambda r: "Pass" if r["Lower Limit"] <= r["Value"] <= r["Upper Limit"] else "Fail", axis=1)
    df["Z-score"] = zscore(df["Value"])
    df["Outlier"] = df["Z-score"].apply(lambda z: "Yes" if abs(z) > 2 else "")

    st.success("✅ File loaded and processed.")
    st.dataframe(df)

    # Z-score 그래프
    st.markdown("### 📈 Z-score Outlier Detection")
    fig, ax = plt.subplots()
    ax.bar(df["Item"], df["Z-score"])
    ax.axhline(2, color="red", linestyle="--")
    ax.axhline(-2, color="red", linestyle="--")
    ax.set_ylabel("Z-score")
    ax.set_title("Outlier Detection")
    plt.xticks(rotation=45)
    st.pyplot(fig)

    # 분석 결과에 따른 요약 문장 생성 함수
    def generate_summary_sentence(df):
        total = len(df)
        failed_items = df[df["Result"] == "Fail"]
        outliers = df[df["Outlier"] == "Yes"]

        sentences = [f"A total of {total} items were tested."]
        if not failed_items.empty:
            items = ", ".join(failed_items["Item"].tolist())
            sentences.append(f"The following items failed to meet specifications: {items}.")
        else:
            sentences.append("All items passed the specification criteria.")

        if not outliers.empty:
            outlier_list = ", ".join(outliers["Item"].tolist())
            sentences.append(f"Statistical anomalies (outliers) were detected in: {outlier_list}.")
        else:
            sentences.append("No significant statistical outliers were detected.")

        return " ".join(sentences)

    # PDF 생성 함수
    def generate_summary_pdf(df):
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=20, leftMargin=20, topMargin=20, bottomMargin=20)
        styles = getSampleStyleSheet()
        elements = []

        elements.append(Paragraph("<b>Test Result Summary Report</b>", styles["Title"]))
        elements.append(Spacer(1, 10))
        elements.append(Paragraph("Product: Acetaminophen", styles["Normal"]))
        elements.append(Paragraph(f"Test Date: {datetime.today().strftime('%Y-%m-%d')}", styles["Normal"]))
        elements.append(Spacer(1, 10))

        total = len(df)
        passed = (df["Result"] == "Pass").sum()
        failed = (df["Result"] == "Fail").sum()

        elements.append(Paragraph(f"Total test items: {total}", styles["Normal"]))
        elements.append(Paragraph(f"Passed: {passed}", styles["Normal"]))
        elements.append(Paragraph(f"Failed: {failed}", styles["Normal"]))
        elements.append(Spacer(1, 10))

        summary_sentence = generate_summary_sentence(df)
        elements.append(Paragraph(f"<b>Summary:</b> {summary_sentence}", styles["Normal"]))
        elements.append(Spacer(1, 15))

        table_data = [["Item", "Value", "Spec (Low ~ High)", "Result"]]
        for _, row in df.iterrows():
            table_data.append([
                str(row["Item"]),
                str(row["Value"]),
                f"{row['Lower Limit']} ~ {row['Upper Limit']}",
                row["Result"]
            ])

        table = Table(table_data, colWidths=[100, 60, 120, 60])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
            ("ALIGN", (1, 1), (-1, -1), "CENTER"),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        elem
