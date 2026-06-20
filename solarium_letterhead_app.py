import streamlit as st
from PyPDF2 import PdfReader, PdfWriter
from io import BytesIO
import base64
import re

st.set_page_config(page_title="Solarium Letterhead Generator", page_icon="☀️", layout="centered")

st.markdown("""
<style>
    .main-header { font-size: 28px; font-weight: bold; color: #1a5276; text-align: center; margin-bottom: 10px; }
    .sub-header { font-size: 14px; color: #666; text-align: center; margin-bottom: 30px; }
    .stButton>button { background-color: #1a5276; color: white; font-weight: bold; border-radius: 8px; padding: 12px 24px; width: 100%; }
    .stButton>button:hover { background-color: #2980b9; }
    .info-box { background-color: #eaf2f8; padding: 15px; border-radius: 8px; border-left: 4px solid #1a5276; margin-bottom: 20px; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">☀️ Solarium Letterhead Generator</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Upload any PDF — get it on Solarium letterhead instantly</div>', unsafe_allow_html=True)

st.markdown("""
<div class="info-box">
<b>How it works:</b><br>
1. Upload your PDF document<br>
2. Upload the Solarium letterhead PDF<br>
3. Click <b>Generate Letterhead PDF</b><br>
4. Download your formatted PDF<br>
</div>
""", unsafe_allow_html=True)

def extract_pdf_text(uploaded_file):
    reader = PdfReader(uploaded_file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n\n"
    return text.strip()

def merge_pdfs(content_pdf_bytes, letterhead_pdf_bytes):
    """Overlay content PDF on top of letterhead PDF"""
    content_reader = PdfReader(BytesIO(content_pdf_bytes))
    letterhead_reader = PdfReader(BytesIO(letterhead_pdf_bytes))

    output_writer = PdfWriter()

    for i, content_page in enumerate(content_reader.pages):
        # Use letterhead page for each content page
        if i < len(letterhead_reader.pages):
            lh_page = letterhead_reader.pages[i]
        else:
            lh_page = letterhead_reader.pages[0]

        # Merge content on top of letterhead
        lh_page.merge_page(content_page)
        output_writer.add_page(lh_page)

    output_buffer = BytesIO()
    output_writer.write(output_buffer)
    output_buffer.seek(0)
    return output_buffer.getvalue()

# File uploaders
uploaded_pdf = st.file_uploader("📄 Upload your content PDF", type=['pdf'])
letterhead_pdf = st.file_uploader("☀️ Upload Solarium letterhead PDF", type=['pdf'])

if st.button("🚀 Generate Letterhead PDF", type="primary"):
    if not uploaded_pdf:
        st.error("Please upload a content PDF.")
    elif not letterhead_pdf:
        st.error("Please upload the Solarium letterhead PDF.")
    else:
        with st.spinner("Generating your PDF..."):
            try:
                content_bytes = uploaded_pdf.getvalue()
                letterhead_bytes = letterhead_pdf.getvalue()

                pdf_bytes = merge_pdfs(content_bytes, letterhead_bytes)

                st.success("✅ PDF generated successfully!")
                st.download_button(
                    label="📥 Download Letterhead PDF",
                    data=pdf_bytes,
                    file_name="Solarium_Letterhead_Document.pdf",
                    mime="application/pdf"
                )
            except Exception as e:
                st.error(f"Error: {str(e)}")

st.markdown("---")
st.markdown("<center><small>☀️ Solarium Green Energy Limited</small></center>", unsafe_allow_html=True)
