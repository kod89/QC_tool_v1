# QC Test Result Auto Checker 🧪

A Streamlit-based tool that automatically checks test results (e.g., for raw materials or finished pharmaceutical products) against defined specifications, and generates a PDF summary report.

## 🔧 Features
- Upload test result file (CSV or Excel)
- Auto-check values against min/max specs
- Displays summary of pass/fail
- Generates downloadable PDF report
- Includes sample CSV template for testing

## 📁 Input File Format
The uploaded file must contain the following columns:

- 항목명 (Item name)
- 측정값 (Measured value)
- 기준하한 (Lower spec limit)
- 기준상한 (Upper spec limit)

## ▶️ How to Run (Locally)
```bash
pip install -r requirements.txt
streamlit run app.py
```

## 🌐 Deploy to Streamlit Cloud
1. Upload all files to a public GitHub repository
2. Go to [streamlit.io/cloud](https://streamlit.io/cloud)
3. Connect your repo and deploy!

## 📎 Sample File
A sample CSV file (`sample_test_data.csv`) is included for testing purposes.

## 📄 Output
Generates a PDF summary report showing:
- Total items
- Number passed / failed
- Table with values, specs, and results

## 💡 Author Notes
This tool was developed as a portfolio project to demonstrate practical automation in pharmaceutical QC work.
