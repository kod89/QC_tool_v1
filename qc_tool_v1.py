import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from fpdf import FPDF
from scipy.stats import zscore
import io
import os

st.set_page_config(page_title="시험 성적서 자동 검토 툴", layout="centered")
st.title("🧪 시험 성적서 자동 검토 및 요약 툴")

# 샘플 데이터 다운로드 버튼 (예외처리)
sample_path = "sample_qc_data_utf8sig.csv"
if os.path.exists(sample_path):
    with open(sample_path, "rb") as f:
        st.download_button(
            label="📥 샘플 데이터 다운로드",
            data=f,
            file_name="sample_qc_data.csv",
            mime="text/csv"
        )
else:
    st.warning("⚠️ 샘플 데이터 파일(sample_qc_data_utf8sig.csv)이 없습니다. 앱 배포 시 함께 업로드해 주세요.")

st.markdown("""
이 도구는 시험 성적서를 자동으로 검토하고 이상치를 시각화하며, 결과를 PDF 보고서로 요약해줍니다.  
샘플 데이터를 다운로드한 후 업로드하여 기능을 체험해보세요.

**💡 입력 파일은 다음과 같은 열을 포함해야 합니다:**

- 항목명
- 측정값
- 기준하한
- 기준상한
""")

# 파일 업로드
uploaded_file = st.file_uploader("📁 시험 성적서 파일 업로드 (CSV/Excel)", type=["csv", "xlsx"])

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
        st.error(f"파일을 불러
