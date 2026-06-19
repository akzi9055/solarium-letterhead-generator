
import streamlit as st
from PyPDF2 import PdfReader
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from io import BytesIO
import base64
import re

# Page config
st.set_page_config(page_title="Solarium Letterhead Generator", page_icon="☀️", layout="centered")

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 28px;
        font-weight: bold;
        color: #1a5276;
        text-align: center;
        margin-bottom: 10px;
    }
    .sub-header {
        font-size: 14px;
        color: #666;
        text-align: center;
        margin-bottom: 30px;
    }
    .stButton>button {
        background-color: #1a5276;
        color: white;
        font-weight: bold;
        border-radius: 8px;
        padding: 12px 24px;
        width: 100%;
    }
    .stButton>button:hover {
        background-color: #2980b9;
    }
    .info-box {
        background-color: #eaf2f8;
        padding: 15px;
        border-radius: 8px;
        border-left: 4px solid #1a5276;
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">☀️ Solarium Letterhead Generator</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Upload any PDF or paste text — get it on Solarium letterhead instantly</div>', unsafe_allow_html=True)

st.markdown("""
<div class="info-box">
<b>How it works:</b><br>
1. Upload your PDF document OR paste text content below<br>
2. Click <b>Generate Letterhead PDF</b><br>
3. Download your formatted PDF with Solarium letterhead<br>
<i>No login required. No installation needed. Works on any device.</i>
</div>
""", unsafe_allow_html=True)

# Register fonts
@st.cache_resource
def register_fonts():
    try:
        pdfmetrics.registerFont(TTFont('DejaVuSans', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'))
        pdfmetrics.registerFont(TTFont('DejaVuSans-Bold', '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'))
        return 'DejaVuSans', 'DejaVuSans-Bold'
    except:
        return 'Helvetica', 'Helvetica-Bold'

normal_font, bold_font = register_fonts()

# Extract text from uploaded PDF
def extract_pdf_text(uploaded_file):
    reader = PdfReader(uploaded_file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n\n"
    return text.strip()

# Smart parser for TPI documents
def parse_tpi_content(text):
    """Parse TPI vendor undertaking content and structure it"""
    lines = text.split('\n')

    # Extract application number
    app_num = ""
    app_match = re.search(r'Application Number:\s*([A-Z0-9-]+)', text)
    if app_match:
        app_num = app_match.group(1)

    # Extract dates
    dates = {}
    date_patterns = [
        (r'Date of Installation of RTS Plant:\s*(\d{2}-\d{2}-\d{4})', 'install_date'),
        (r'Date of Inspection.*?REC:\s*(\d{2}-\d{2}-\d{4})', 'inspect_date'),
        (r'Date of Assignment.*?REC:\s*(\d{2}-\d{2}-\d{4})', 'assign_date'),
    ]
    for pattern, key in date_patterns:
        match = re.search(pattern, text)
        if match:
            dates[key] = match.group(1)

    # Extract defects table
    defects = []
    defect_pattern = r'(\d+)\s+(PV Module.*?|Earthing.*?|Mounting Structure.*?)\s+(Delaminated.*?|No|Structure Condition.*?)\s+(Major|Minor)\s+(?:☑|\u2611).*?Rectified.*?☐|\u2610.*?Not Rectified'

    # Simple line-by-line extraction for defects
    in_table = False
    for i, line in enumerate(lines):
        if 'Statement of Identified Defects' in line:
            in_table = True
            continue
        if in_table and line.strip() and line.strip()[0].isdigit():
            # Try to extract defect info
            defect_num = line.strip().split()[0] if line.strip()[0].isdigit() else ""
            if defect_num and defect_num.isdigit():
                # Look ahead for more info
                defect_info = {"no": defect_num}
                # Extract component
                if i+1 < len(lines) and 'PV Module' in lines[i+1]:
                    defect_info['component'] = lines[i+1].strip()
                if i+2 < len(lines) and ('Delaminated' in lines[i+2] or 'No' in lines[i+2]):
                    defect_info['defect'] = lines[i+2].strip()
                if 'Earthing' in line:
                    defect_info['component'] = line.strip()
                    if i+1 < len(lines):
                        defect_info['defect'] = lines[i+1].strip()
                defects.append(defect_info)

    return {
        'app_num': app_num,
        'dates': dates,
        'defects': defects,
        'raw_text': text
    }

# Generate PDF with Solarium letterhead
def generate_letterhead_pdf(content_text, letterhead_bytes):
    content_buffer = BytesIO()

    doc = SimpleDocTemplate(
        content_buffer,
        pagesize=A4,
        rightMargin=15*mm,
        leftMargin=15*mm,
        topMargin=55*mm,
        bottomMargin=15*mm
    )

    # Styles
    title_style = ParagraphStyle(
        'Title', fontSize=11, fontName=bold_font, spaceAfter=8,
        alignment=TA_CENTER, leading=14
    )
    heading_style = ParagraphStyle(
        'Heading', fontSize=10, fontName=bold_font, spaceAfter=4,
        spaceBefore=6, leading=13
    )
    normal_style = ParagraphStyle(
        'Normal', fontSize=9, fontName=normal_font, spaceAfter=3,
        leading=12, alignment=TA_JUSTIFY
    )
    body_style = ParagraphStyle(
        'Body', fontSize=9, fontName=normal_font, spaceAfter=2,
        leading=12, alignment=TA_LEFT
    )
    small_style = ParagraphStyle(
        'Small', fontSize=8, fontName=normal_font, spaceAfter=1,
        leading=10, alignment=TA_LEFT
    )

    story = []

    # Check if it's a TPI document
    if 'rectification of defects' in content_text.lower() or 'Field Quality Inspection' in content_text:
        # TPI format
        story.append(Paragraph("Declaration on rectification of defects Identified during Third-Party Field Quality Inspection of RTS Installations under PM Surya Ghar: Muft Bijli Yojana (PMSG-MBY)", title_style))
        story.append(Spacer(1, 4))

        # Extract and format reference details
        story.append(Paragraph("Reference Details:", heading_style))

        app_match = re.search(r'Application Number:\s*([A-Z0-9-]+)', content_text)
        if app_match:
            story.append(Paragraph(f"(i) Application Number: <b>{app_match.group(1)}</b>", body_style))

        for pattern, label in [
            (r'Date of Installation of RTS Plant:\s*(\d{2}-\d{2}-\d{4})', '(ii) Date of Installation of RTS Plant'),
            (r'Date of Inspection.*?REC:\s*(\d{2}-\d{2}-\d{4})', '(iii) Date of Inspection of RTS Plant by Third-Party Agency Appointed by REC'),
            (r'Date of Assignment.*?REC:\s*(\d{2}-\d{2}-\d{4})', '(iv) Date of Assignment of defect rectification by REC'),
        ]:
            match = re.search(pattern, content_text)
            if match:
                story.append(Paragraph(f"{label}: <b>{match.group(1)}</b>", body_style))

        story.append(Spacer(1, 6))

        # Section 1
        story.append(Paragraph("1. Acknowledgement of Field Quality Inspection (FQI) Report:", heading_style))
        story.append(Paragraph("I/We, M/s <b>Solarium Green Energy Limited</b> (hereinafter referred to as &quot;the Vendor&quot;), a National Vendor, having our registered office at <b>B 1208 World Trade Tower Behind Skoda Showroom Makarba Ahmedabad 380051 Gujarat India</b>, hereby acknowledge receipt of the Field Quality Inspection (FQI) Report in our login on National Portal, issued by REC Limited under Third-Party Field Quality Inspection of PM Surya Ghar: Muft Bijli Yojana (PMSG-MBY).", normal_style))
        story.append(Spacer(1, 6))

        # Section 2 - Defects table
        story.append(Paragraph("2. Statement of Identified Defects:", heading_style))
        story.append(Spacer(1, 2))

        # Extract defects from text
        defects_data = extract_defects_from_text(content_text)

        if defects_data:
            from reportlab.platypus import Paragraph as RLParagraph

            def p(text, font_size=8, bold=False):
                fn = bold_font if bold else normal_font
                return RLParagraph(f"<font name='{fn}' size={font_size}>{text}</font>", 
                    ParagraphStyle('cell', fontName=fn, fontSize=font_size, leading=10, alignment=TA_LEFT))

            checked = "\u2611"
            unchecked = "\u2610"
            rectified_status = f"{checked} Rectified<br/>{unchecked} Not Rectified"

            header_row = [
                p("Sl.<br/>No.", bold=True), p("Component No.<br/>(Aggregate)", bold=True),
                p("Identified Defect", bold=True), p("Category<br/>(Major /<br/>Minor)", bold=True),
                p("Rectification<br/>Status", bold=True), p("Remarks", bold=True)
            ]

            table_rows = [header_row]
            for defect in defects_data:
                table_rows.append([
                    p(defect.get('sl', '')),
                    p(defect.get('component', '')),
                    p(defect.get('defect', '')),
                    p(defect.get('category', 'Major')),
                    p(rectified_status),
                    p(defect.get('remarks', 'The issue has been resolved'))
                ])

            col_widths = [15*mm, 40*mm, 40*mm, 24*mm, 32*mm, 31*mm]
            table_style = TableStyle([
                ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('TOPPADDING', (0, 0), (-1, -1), 5),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                ('LEFTPADDING', (0, 0), (-1, -1), 5),
                ('RIGHTPADDING', (0, 0), (-1, -1), 5),
                ('BACKGROUND', (0, 0), (-1, 0), HexColor('#f0f0f0')),
            ])

            defect_table = Table(table_rows, colWidths=col_widths, repeatRows=1)
            defect_table.setStyle(table_style)
            story.append(defect_table)

        story.append(Spacer(1, 6))
        story.append(PageBreak())

        # Section 3
        story.append(Paragraph("3. Declaration of Rectification:", heading_style))
        story.append(Paragraph("a. Each defect listed above has been rectified in full in conformity with applicable technical specifications, safety standards, and directions issued by REC Limited / MNRE.", normal_style))
        story.append(Paragraph("b. Photographic or documentary evidence of rectification has been uploaded on the National Portal against the corresponding defect entry.", normal_style))
        story.append(Paragraph("c. To the best of my / our knowledge, no material deviation or residual non-conformity now subsists in the subject of installation.", normal_style))
        story.append(Spacer(1, 6))

        # Section 4
        story.append(Paragraph("4. Consequences of Misrepresentation:", heading_style))
        story.append(Paragraph("I / We understand that any false statement, concealment of facts, or non-compliance with rectification requirements shall render us liable for action under the PMSG-MBY guidelines.", normal_style))
        story.append(Spacer(1, 8))

        # Signature block
        story.append(Paragraph("For and on behalf of M/s <b>Solarium Green Energy Limited</b>", body_style))
        story.append(Spacer(1, 2))
        story.append(Paragraph("(Authorised Signatory)", small_style))
        story.append(Paragraph("Name: __________________________________________", body_style))
        story.append(Paragraph("Designation: ___________________________________", body_style))
        story.append(Paragraph("Mobile No.: ____________________________________", body_style))
        story.append(Spacer(1, 4))
        story.append(Paragraph("Date: ____ / ____ / 20____", body_style))
        story.append(Paragraph("Place: _________________________________________", body_style))
        story.append(Spacer(1, 8))

        # Section 5
        story.append(Paragraph("5. Consumer Acknowledgment of Defect Rectification by Vendor", heading_style))
        story.append(Paragraph("The above declaration of vendor on rectification of identified defects during Field Quality Inspection report, issued by REC Limited under Third-Party Field Quality Inspection of PM Surya Ghar: Muft Bijli Yojana (PMSG-MBY), is hereby acknowledged.", normal_style))
        story.append(Spacer(1, 4))
        story.append(Paragraph("Signature of Registered Consumer/Representative of Registered Consumer:", body_style))
        story.append(Paragraph("________________________________", body_style))
        story.append(Paragraph("Name of Registered Consumer/ Representative of Registered Consumer:", body_style))
        story.append(Paragraph("________________________________", body_style))
        story.append(Paragraph("Relation of Representative with Registered Consumer (If consumer not present):", body_style))
        story.append(Paragraph("________________________________", body_style))
        story.append(Paragraph("Mobile Number of Registered Consumer/Representative of Registered Consumer:", body_style))
        story.append(Paragraph("________________________________", body_style))
        story.append(Paragraph("Consumer Number (CA No.): _____________________", body_style))

    else:
        # Generic content - just format as-is on letterhead
        paragraphs = content_text.split('\n')
        for para in paragraphs:
            if para.strip():
                story.append(Paragraph(para.strip(), normal_style))
                story.append(Spacer(1, 4))

    doc.build(story)
    content_buffer.seek(0)

    # Merge with letterhead
    output_buffer = BytesIO()
    content_reader = PdfReader(content_buffer)
    letterhead_reader = PdfReader(BytesIO(letterhead_bytes))

    output_writer = PdfWriter()
    for content_page in content_reader.pages:
        lh = PdfReader(BytesIO(letterhead_bytes)).pages[0]
        lh.merge_page(content_page)
        output_writer.add_page(lh)

    output_writer.write(output_buffer)
    output_buffer.seek(0)
    return output_buffer.getvalue()

def extract_defects_from_text(text):
    """Extract defect entries from TPI text"""
    defects = []
    lines = text.split('\n')

    i = 0
    while i < len(lines):
        line = lines[i].strip()
        # Look for defect entries starting with numbers
        if line and line[0].isdigit() and len(line) < 5:
            defect = {'sl': line}
            # Look ahead for component, defect, category
            j = i + 1
            component_parts = []
            defect_parts = []
            category = "Major"
            remarks = "The issue has been resolved"

            while j < len(lines) and not (lines[j].strip() and lines[j].strip()[0].isdigit() and len(lines[j].strip()) < 5):
                next_line = lines[j].strip()
                if 'PV Module' in next_line or 'Earthing' in next_line or 'Mounting' in next_line:
                    component_parts.append(next_line)
                elif 'Delaminated' in next_line or 'Loose' in next_line or 'Structure Condition' in next_line or next_line == 'No':
                    defect_parts.append(next_line)
                elif 'Major' in next_line or 'Minor' in next_line:
                    category = next_line
                elif 'resolved' in next_line.lower() or 'foundation' in next_line.lower():
                    remarks = next_line
                j += 1

            defect['component'] = ' '.join(component_parts)
            defect['defect'] = ' '.join(defect_parts)
            defect['category'] = category
            defect['remarks'] = remarks
            defects.append(defect)
            i = j - 1
        i += 1

    return defects

# UI
st.markdown("---")

# Two options: Upload PDF or Paste Text
tab1, tab2 = st.tabs(["📄 Upload PDF", "📝 Paste Text"])

with tab1:
    uploaded_pdf = st.file_uploader("Upload your PDF document", type=['pdf'])
    if uploaded_pdf:
        extracted_text = extract_pdf_text(uploaded_pdf)
        st.text_area("Extracted text (you can edit if needed):", extracted_text, height=200)

with tab2:
    pasted_text = st.text_area("Paste your content here:", height=200, 
        placeholder="Paste any text content here... It will be formatted on Solarium letterhead.")

st.markdown("---")

# Letterhead upload (optional - use default if not provided)
use_default = st.checkbox("Use default Solarium letterhead", value=True)
letterhead_file = None
if not use_default:
    letterhead_file = st.file_uploader("Upload custom letterhead PDF", type=['pdf'])

# Generate button
if st.button("🚀 Generate Letterhead PDF", type="primary"):
    with st.spinner("Generating your PDF..."):
        # Get content
        if uploaded_pdf:
            content = extract_pdf_text(uploaded_pdf)
        elif pasted_text:
            content = pasted_text
        else:
            st.error("Please upload a PDF or paste text content.")
            st.stop()

        # Get letterhead
        if use_default:
            # Use a placeholder - in real deployment, include default letterhead
            st.info("Using default Solarium letterhead...")
            # For now, create a simple letterhead if no file uploaded
            if letterhead_file:
                letterhead_bytes = letterhead_file.getvalue()
            else:
                st.error("Please upload the Solarium letterhead PDF or provide one.")
                st.stop()
        else:
            if letterhead_file:
                letterhead_bytes = letterhead_file.getvalue()
            else:
                st.error("Please upload a letterhead PDF.")
                st.stop()

        # Generate PDF
        try:
            pdf_bytes = generate_letterhead_pdf(content, letterhead_bytes)

            # Download button
            st.success("✅ PDF generated successfully!")
            st.download_button(
                label="📥 Download Letterhead PDF",
                data=pdf_bytes,
                file_name="Solarium_Letterhead_Document.pdf",
                mime="application/pdf"
            )
        except Exception as e:
            st.error(f"Error generating PDF: {str(e)}")
            st.exception(e)

st.markdown("---")
st.markdown("<center><small>Made for Solarium Green Energy Limited | No login required</small></center>", unsafe_allow_html=True)
