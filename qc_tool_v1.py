import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from scipy.stats import zscore
from reportlab.lib.pagesizes import A4
from reportlab.platypus import Table, TableStyle, Paragraph, SimpleDocTemplate, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from io import BytesIO
from datetime import datetime
import os

# Streamlit 설정
st.set_page_config(page_title="QC Report Analyzer", layout="centered")
st.title("🧪 QC Test Report Analyzer")

# 샘플 파일 다운로드 버튼
sample_path = "sample_qc_data.csv"
if os.path.exists(sample_path):
    with open(sample_path, "rb") as f:
        st.download_button("📥 Download Sample Data", f, file_name="sample_qc_data.csv", mime="text/csv")

# 사용자 안내
st.markdown("""
Upload your QC test result file. Required columns:
- Item
- Value
- Lower Limit
- Upper Limit
""")

# 파일 업로드
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

    required_cols = ["Item", "Value", "Lower Limit", "Upper Limit"]
    if not all(col in df.columns for col in required_cols):
        st.error("❌ Required columns are missing.")
        st.stop()

    # 결과 및 이상치 계산
    df["Result"] = df.apply(lambda r: "Pass" if r["Lower Limit"] <= r["Value"] <= r["Upper Limit"] else "Fail", axis=1)
    df["Z-score"] = zscore(df["Value"])
    df["Outlier"] = df["Z-score"].apply(lambda z: "Yes" if abs(z) > 2 else "")

    st.success("✅ File loaded and processed.")
    st.dataframe(df)

    # Z-score 시각화
    st.markdown("### 📈 Z-score Outlier Detection")
    fig, ax = plt.subplots()
    ax.bar(df["Item"], df["Z-score"])
    ax.axhline(2, color="red", linestyle="--")
    ax.axhline(-2, color="red", linestyle="--")
    ax.set_ylabel("Z-score")
    ax.set_title("Outlier Detection")
    plt.xticks(rotation=45)
    st.pyplot(fig)

    # 요약 서술문 생성 함수
    def generate_summary_text(df):
        total = len(df)
        passed = (df["Result"] == "Pass").sum()
        failed = (df["Result"] == "Fail").sum()
        outliers = df["Outlier"].eq("Yes").sum()
        outlier_names = df[df["Outlier"] == "Yes"]["Item"].tolist()
        failed_names = df[df["Result"] == "Fail"]["Item"].tolist()

        summary = f"A total of {total} items were tested. {passed} items passed and {failed} failed. "
        if failed:
            summary += f"The following item(s) did not meet the specification limits: {', '.join(failed_names)}. "
        if outliers:
            summary += f"{outliers} item(s) showed statistically significant deviations (|Z-score| > 2): {', '.join(outlier_names)}. "

        if failed == 0 and outliers == 0:
            summary += "All items met quality standards with no significant deviations, indicating stable and consistent quality."
        elif failed == 0 and outliers:
            summary += "Although all items passed the specification range, a few showed notable variability that may require attention."
        elif failed and outliers == 0:
            summary += "Some items failed to meet specification limits, but no statistical outliers were observed."
        else:
            summary += "Both failed results and statistical outliers were detected, suggesting the need for further investigation or corrective actions."

        return summary

    # 보고서 요약 출력
    st.markdown("### 📝 Summary Interpretation")
    st.info(generate_summary_text(df))
