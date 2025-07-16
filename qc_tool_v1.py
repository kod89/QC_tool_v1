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
        st.error(f"파일을 불러오는 중 오류 발생: {e}")
        st.stop()

    expected_columns = ["항목명", "측정값", "기준하한", "기준상한"]
    if not all(col in df.columns for col in expected_columns):
        st.error("❌ 파일의 열 이름이 올바르지 않습니다. 샘플 파일 양식을 참고해주세요.")
        st.stop()

    st.success("✅ 데이터가 정상적으로 업로드되었습니다.")
    st.dataframe(df)

    # 적합/부적합 판정
    def assess_row(row):
        if row["측정값"] < row["기준하한"] or row["측정값"] > row["기준상한"]:
            return "부적합"
        return "적합"

    df["판정"] = df.apply(assess_row, axis=1)

    # 이상치 분석 (Z-score)
    df["Z-score"] = zscore(df["측정값"])
    df["이상치 여부"] = df["Z-score"].apply(lambda z: "이상치" if abs(z) > 2 else "")

    # 결과 표시
    st.markdown("### 📊 판정 결과")
    st.dataframe(df)

    # 그래프
    st.markdown("### 📈 이상치 시각화")
    fig, ax = plt.subplots()
    ax.bar(df["항목명"], df["Z-score"])
    ax.axhline(2, color="red", linestyle="--", label="Z=2")
    ax.axhline(-2, color="red", linestyle="--")
    ax.set_ylabel("Z-score")
    ax.set_title("Z-score 기반 이상치 탐지")
    ax.legend()
    st.pyplot(fig)

    # PDF 보고서 생성
    def generate_pdf(dataframe):
        buffer = io.BytesIO()
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt="시험 성적서 자동 분석 보고서", ln=True, align="C")
        pdf.ln(10)

        for i, row in dataframe.iterrows():
            text = f"{row['항목명']}: 측정값={row['측정값']} → 판정={row['판정']} {row['이상치 여부']}"
            pdf.cell(200, 10, txt=text, ln=True)

        pdf.output(buffer)
        buffer.seek(0)
        return buffer

    pdf_buffer = generate_pdf(df)
    st.download_button("📄 PDF 보고서 다운로드", data=pdf_buffer, file_name="qc_report.pdf")
