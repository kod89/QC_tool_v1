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

sample_path = "sample_qc_data.csv"
if os.path.exists(sample_path):
    with open(sample_path, "rb") as f:
        st.download_button(
            label="📥 Download Sample Data",
            data=f,
            file_name="sample_qc_data.csv",
            mime="text/csv"
        )

st.markdown("""Upload your QC test result file. The file must include the following columns:
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

    df["Result"] = df.apply(lambda r: "Pass" if r["Lower Limit"] <= r["Value"] <= r["Upper Limit"] else "Fail", axis=1)
    df["Z-score"] = zscore(df["Value"])
    df["Outlier"] = df["Z-score"].apply(lambda z: "Yes" if abs(z) > 2 else "")

    st.success("✅ File loaded and processed.")
    st.dataframe(df)

    st.markdown("### 📈 Z-score Outlier Detection")
    fig, ax = plt.subplots()
    ax.bar(df["Item"], df["Z-score"])
    ax.axhline(2, color="red", linestyle="--")
    ax.axhline(-2, color="red", linestyle="--")
    ax.set_ylabel("Z-score")
    ax.set_title("Outlier Detection")
    plt.xticks(rotation=45)
    st.pyplot(fig)

    # 요약 문장 작성
    total = len(df)
    passed = (df["Result"] == "Pass").sum()
    failed = (df["Result"] == "Fail").sum()

    summary_text = f"""
    Total test items: {total}  
    Passed: {passed}  
    Failed: {failed}  
    """

    if failed == 0:
        comment = "All test items passed the specification. No corrective action is required at this time."
    else:
        comment = f"{failed} item(s) failed to meet the specification. Please review the failed items and conduct root cause analysis if necessary."

    st.markdown("### 📝 Summary")
    st.markdown(summary_text)
    st.info(comment)

    # PDF 생성
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
        elements.append(table)
        elements.append(Spacer(1, 15))
        elements.append(Paragraph(summary_text.replace("  ", "<br/>"), styles["Normal"]))
        elements.append(Spacer(1, 8))
        elements.append(Paragraph(f"<i>{comment}</i>", styles["Normal"]))
        doc.build(elements)
        buffer.seek(0)
        return buffer

    pdf_buffer = generate_summary_pdf(df)
    st.download_button(
        label="📄 Download Summary PDF",
        data=pdf_buffer,
        file_name="qc_summary_report.pdf",
        mime="application/pdf"
    )
