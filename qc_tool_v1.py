import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from scipy.stats import zscore
import os

# PDF 생성 함수

def generate_pdf_report_with_info(df, df_summary, product_name, test_date, output_path):
    df_cleaned = df.copy()
    df_cleaned["Item"] = df_cleaned["항목명"].replace({
        "순도 (%)": "Purity (%)",
        "수분함량 (%)": "Moisture (%)",
        "잔류용매(ppm)": "Residual Solvent (ppm)",
        "pH": "pH"
    })
    df_cleaned["Result"] = df_cleaned["판정"].replace({
        "적합": "Pass",
        "부적합": "Fail"
    })
    df_cleaned["Outlier"] = df_cleaned["이상치여부"].replace({
        "정상": "Normal",
        "이상치": "Outlier"
    })

    doc = SimpleDocTemplate(output_path, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []

    title = Paragraph("Test Result Summary Report", styles['Title'])
    elements.append(title)
    elements.append(Spacer(1, 12))

    info_text = f"""
    <b>Product:</b> {product_name}<br/>
    <b>Test Date:</b> {test_date}<br/><br/>
    Total number of test items: {df_summary["총 시험 항목 수"]}<br/>
    Number of passed items: {df_summary["적합 항목 수"]}<br/>
    Number of failed items: {df_summary["부적합 항목 수"]}<br/>
    Number of outliers: {df_summary["이상치 항목 수"]}
    """
    elements.append(Paragraph(info_text, styles['Normal']))
    elements.append(Spacer(1, 12))

    table_data = [["Item", "Value", "Specification (Low ~ High)", "Result", "Outlier"]]
    for _, row in df_cleaned.iterrows():
        table_data.append([
            row["Item"],
            str(row["측정값"]),
            f"{row['기준하한']} ~ {row['기준상한']}",
            row["Result"],
            row["Outlier"]
        ])

    table = Table(table_data, colWidths=[120, 60, 160, 60, 60])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.8, colors.black),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
    ]))
    elements.append(table)
    doc.build(elements)

# 결과 시각화 함수

def plot_test_results_clean(df):
    df = df.copy()
    df["Item"] = df["항목명"].replace({
        "pH": "pH",
        "순도 (%)": "Purity (%)",
        "수분함량 (%)": "Moisture (%)",
        "잔류용매(ppm)": "Residual Solvent (ppm)"
    })
    fig, ax = plt.subplots(figsize=(10, 6))

    items = df["Item"]
    values = df["측정값"]
    lower_limits = df["기준하한"]
    upper_limits = df["기준상한"]
    outlier_flags = df["이상치여부"] == "이상치"

    colors = ["red" if flag else "skyblue" for flag in outlier_flags]

    bars = ax.bar(items, values, color=colors, edgecolor='black')

    for i, (x, low, high) in enumerate(zip(items, lower_limits, upper_limits)):
        ax.hlines([low, high], i - 0.4, i + 0.4, colors='gray', linestyles='dashed')

    ax.set_ylabel("Measured Value")
    ax.set_title("Test Results per Item (Outliers Highlighted)", fontsize=14)
    ax.grid(True, axis='y', linestyle='--', alpha=0.6)
    plt.xticks(rotation=15)
    plt.tight_layout()
    return fig

# Streamlit UI
st.set_page_config(page_title="QC Test Report Generator", layout="centered")
st.title("🧪 QC Test Result Auto Checker")

st.markdown("""
Upload your test result file (CSV or Excel) containing the following columns:
- 항목명, 측정값, 기준하한, 기준상한
""")

with st.expander("📎 Download Sample Template"):
    with open("sample_test_data.csv", "rb") as f:
        st.download_button("Download Sample CSV", f, file_name="sample_test_data.csv")

uploaded_file = st.file_uploader("Upload Test Result File", type=["csv", "xlsx"])

if uploaded_file:
    try:
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)

        st.success("✅ File successfully loaded!")
        st.dataframe(df)

        if {'항목명', '측정값', '기준하한', '기준상한'}.issubset(df.columns):
            df['판정'] = df.apply(
                lambda row: "적합" if row['기준하한'] <= row['측정값'] <= row['기준상한'] else "부적합",
                axis=1
            )

            z_scores = zscore(df["측정값"])
            df["z_score"] = z_scores
            df["이상치여부"] = df["z_score"].apply(lambda z: "이상치" if abs(z) > 2.0 else "정상")
            outliers = (df["이상치여부"] == "이상치").sum()

            passed = (df['판정'] == "적합").sum()
            failed = (df['판정'] == "부적합").sum()
            df_summary = {
                "총 시험 항목 수": len(df),
                "적합 항목 수": passed,
                "부적합 항목 수": failed,
                "이상치 항목 수": outliers
            }

            st.subheader("📋 Test Summary")
            st.markdown(f"- Total items: {len(df)}")
            st.markdown(f"- Passed: {passed}")
            st.markdown(f"- Failed: {failed}")
            st.markdown(f"- Outliers: {outliers}")

            st.dataframe(df[["항목명", "측정값", "기준하한", "기준상한", "판정", "이상치여부"]])

            st.subheader("📊 Test Result Visualization")
            st.pyplot(plot_test_results_clean(df))

            product_name = st.text_input("Enter Product Name")
            test_date = st.date_input("Select Test Date")

            if product_name and test_date:
                if st.button("📄 Generate PDF Report"):
                    output_path = f"{product_name}_{test_date}.pdf"
                    generate_pdf_report_with_info(df, df_summary, product_name, test_date, output_path)
                    with open(output_path, "rb") as f:
                        st.download_button("📥 Download PDF Report", f, file_name=output_path)
            else:
                st.info("ℹ️ Please enter both product name and test date to generate the report.")

        else:
            st.error("The file must contain: 항목명, 측정값, 기준하한, 기준상한 columns.")

    except Exception as e:
        st.error(f"❌ Error processing file: {e}")
