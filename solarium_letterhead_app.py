
import streamlit as st
import smtplib
import random
import re
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
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
import time

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
    .login-box {
        background-color: #eaf2f8;
        padding: 30px;
        border-radius: 12px;
        border: 2px solid #1a5276;
        max-width: 450px;
        margin: 0 auto;
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
    .success-msg {
        background-color: #d4edda;
        color: #155724;
        padding: 12px;
        border-radius: 8px;
        text-align: center;
        margin-bottom: 15px;
    }
    .error-msg {
        background-color: #f8d7da;
        color: #721c24;
        padding: 12px;
        border-radius: 8px;
        text-align: center;
        margin-bottom: 15px;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'otp' not in st.session_state:
    st.session_state.otp = None
if 'otp_email' not in st.session_state:
    st.session_state.otp_email = None
if 'otp_time' not in st.session_state:
    st.session_state.otp_time = None
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_email' not in st.session_state:
    st.session_state.user_email = None

# Email config from Streamlit Secrets (secure - not visible in code)
try:
    SENDER_EMAIL = st.secrets["email"]["sender_email"]
    SENDER_PASSWORD = st.secrets["email"]["sender_password"]
    SMTP_SERVER = "smtp.gmail.com"
    SMTP_PORT = 587
except:
    # Fallback for local testing - will show error if not configured
    SENDER_EMAIL = ""
    SENDER_PASSWORD = ""
    SMTP_SERVER = "smtp.gmail.com"
    SMTP_PORT = 587

def is_valid_solarium_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@solariumenergy\.in$'
    return re.match(pattern, email) is not None

def generate_otp():
    return str(random.randint(100000, 999999))

def send_otp_email(email, otp):
    try:
        if not SENDER_EMAIL or not SENDER_PASSWORD:
            st.error("Email not configured. Please set up secrets in Streamlit Cloud.")
            return False

        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = email
        msg['Subject'] = "Solarium Letterhead Generator - Login OTP"

        body = f"""
Hello,

Your OTP for Solarium Letterhead Generator is: {otp}

This OTP is valid for 10 minutes.

If you did not request this OTP, please ignore this email.

Regards,
Solarium Green Energy Limited
        """

        msg.attach(MIMEText(body, 'plain'))

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        st.error(f"Failed to send email: {str(e)}")
        return False

def show_login_page():
    st.markdown('<div class="main-header">☀️ Solarium Letterhead Generator</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Secure access for Solarium team members only</div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="login-box">
        <h3 style="text-align: center; color: #1a5276;">🔐 Login</h3>
        <p style="text-align: center; color: #666; font-size: 13px;">
            Only <b>@solariumenergy.in</b> email addresses are allowed.
        </p>
    </div>
    """, unsafe_allow_html=True)

    if st.session_state.otp is None:
        email = st.text_input("Enter your Solarium email:", placeholder="yourname@solariumenergy.in")

        if st.button("📧 Send OTP", type="primary"):
            if not email:
                st.markdown('<div class="error-msg">Please enter your email address.</div>', unsafe_allow_html=True)
            elif not is_valid_solarium_email(email):
                st.markdown('<div class="error-msg">❌ Only @solariumenergy.in emails are allowed.</div>', unsafe_allow_html=True)
            else:
                with st.spinner("Sending OTP..."):
                    otp = generate_otp()
                    if send_otp_email(email, otp):
                        st.session_state.otp = otp
                        st.session_state.otp_email = email
                        st.session_state.otp_time = datetime.now()
                        st.markdown(f'<div class="success-msg">✅ OTP sent to {email}</div>', unsafe_allow_html=True)
                        st.rerun()
                    else:
                        st.markdown('<div class="error-msg">❌ Failed to send OTP. Check email configuration.</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="success-msg">📧 OTP sent to {st.session_state.otp_email}</div>', unsafe_allow_html=True)

        if datetime.now() - st.session_state.otp_time > timedelta(minutes=10):
            st.markdown('<div class="error-msg">❌ OTP expired. Please request a new one.</div>', unsafe_allow_html=True)
            if st.button("🔄 Request New OTP"):
                st.session_state.otp = None
                st.session_state.otp_email = None
                st.session_state.otp_time = None
                st.rerun()
        else:
            otp_input = st.text_input("Enter 6-digit OTP:", max_chars=6, placeholder="123456")

            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Verify OTP", type="primary"):
                    if otp_input == st.session_state.otp:
                        st.session_state.logged_in = True
                        st.session_state.user_email = st.session_state.otp_email
                        st.markdown('<div class="success-msg">🎉 Login successful!</div>', unsafe_allow_html=True)
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.markdown('<div class="error-msg">❌ Invalid OTP. Please try again.</div>', unsafe_allow_html=True)

            with col2:
                if st.button("🔄 Resend OTP"):
                    with st.spinner("Resending OTP..."):
                        otp = generate_otp()
                        if send_otp_email(st.session_state.otp_email, otp):
                            st.session_state.otp = otp
                            st.session_state.otp_time = datetime.now()
                            st.markdown('<div class="success-msg">✅ New OTP sent!</div>', unsafe_allow_html=True)
                            st.rerun()
                        else:
                            st.markdown('<div class="error-msg">❌ Failed to resend OTP.</div>', unsafe_allow_html=True)

            if st.button("⬅️ Back to Email"):
                st.session_state.otp = None
                st.session_state.otp_email = None
                st.session_state.otp_time = None
                st.rerun()

def logout():
    st.session_state.logged_in = False
    st.session_state.user_email = None
    st.session_state.otp = None
    st.session_state.otp_email = None
    st.session_state.otp_time = None
    st.rerun()

@st.cache_resource
def register_fonts():
    try:
        pdfmetrics.registerFont(TTFont('DejaVuSans', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'))
        pdfmetrics.registerFont(TTFont('DejaVuSans-Bold', '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'))
        return 'DejaVuSans', 'DejaVuSans-Bold'
    except:
        return 'Helvetica', 'Helvetica-Bold'

normal_font, bold_font = register_fonts()

def extract_pdf_text(uploaded_file):
    reader = PdfReader(uploaded_file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n\n"
    return text.strip()

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

    title_style = ParagraphStyle('Title', fontSize=11, fontName=bold_font, spaceAfter=8, alignment=TA_CENTER, leading=14)
    heading_style = ParagraphStyle('Heading', fontSize=10, fontName=bold_font, spaceAfter=4, spaceBefore=6, leading=13)
    normal_style = ParagraphStyle('Normal', fontSize=9, fontName=normal_font, spaceAfter=3, leading=12, alignment=TA_JUSTIFY)
    body_style = ParagraphStyle('Body', fontSize=9, fontName=normal_font, spaceAfter=2, leading=12, alignment=TA_LEFT)
    small_style = ParagraphStyle('Small', fontSize=8, fontName=normal_font, spaceAfter=1, leading=10, alignment=TA_LEFT)

    story = []

    if 'rectification of defects' in content_text.lower() or 'Field Quality Inspection' in content_text:
        story.append(Paragraph("Declaration on rectification of defects Identified during Third-Party Field Quality Inspection of RTS Installations under PM Surya Ghar: Muft Bijli Yojana (PMSG-MBY)", title_style))
        story.append(Spacer(1, 4))

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

        story.append(Paragraph("1. Acknowledgement of Field Quality Inspection (FQI) Report:", heading_style))
        story.append(Paragraph("I/We, M/s <b>Solarium Green Energy Limited</b> (hereinafter referred to as &quot;the Vendor&quot;), a National Vendor, having our registered office at <b>B 1208 World Trade Tower Behind Skoda Showroom Makarba Ahmedabad 380051 Gujarat India</b>, hereby acknowledge receipt of the Field Quality Inspection (FQI) Report in our login on National Portal, issued by REC Limited under Third-Party Field Quality Inspection of PM Surya Ghar: Muft Bijli Yojana (PMSG-MBY).", normal_style))
        story.append(Spacer(1, 6))

        story.append(Paragraph("2. Statement of Identified Defects:", heading_style))
        story.append(Spacer(1, 2))

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

        defects = []
        lines = content_text.split('\n')
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if line and line[0].isdigit() and len(line) < 5:
                defect = {'sl': line, 'component': '', 'defect': '', 'category': 'Major', 'remarks': 'The issue has been resolved'}
                j = i + 1
                while j < len(lines) and not (lines[j].strip() and lines[j].strip()[0].isdigit() and len(lines[j].strip()) < 5):
                    next_line = lines[j].strip()
                    if 'PV Module' in next_line or 'Earthing' in next_line or 'Mounting' in next_line:
                        defect['component'] = next_line
                    elif 'Delaminated' in next_line or 'Loose' in next_line or 'Structure Condition' in next_line or next_line == 'No':
                        defect['defect'] = next_line
                    elif 'resolved' in next_line.lower() or 'foundation' in next_line.lower():
                        defect['remarks'] = next_line
                    j += 1
                defects.append(defect)
                i = j - 1
            i += 1

        table_rows = [header_row]
        for defect in defects:
            table_rows.append([
                p(defect['sl']), p(defect['component']), p(defect['defect']),
                p(defect['category']), p(rectified_status), p(defect['remarks'])
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

        story.append(Paragraph("3. Declaration of Rectification:", heading_style))
        story.append(Paragraph("a. Each defect listed above has been rectified in full in conformity with applicable technical specifications, safety standards, and directions issued by REC Limited / MNRE.", normal_style))
        story.append(Paragraph("b. Photographic or documentary evidence of rectification has been uploaded on the National Portal against the corresponding defect entry.", normal_style))
        story.append(Paragraph("c. To the best of my / our knowledge, no material deviation or residual non-conformity now subsists in the subject of installation.", normal_style))
        story.append(Spacer(1, 6))

        story.append(Paragraph("4. Consequences of Misrepresentation:", heading_style))
        story.append(Paragraph("I / We understand that any false statement, concealment of facts, or non-compliance with rectification requirements shall render us liable for action under the PMSG-MBY guidelines.", normal_style))
        story.append(Spacer(1, 8))

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
        paragraphs = content_text.split('\n')
        for para in paragraphs:
            if para.strip():
                story.append(Paragraph(para.strip(), normal_style))
                story.append(Spacer(1, 4))

    doc.build(story)
    content_buffer.seek(0)

    output_buffer = BytesIO()
    content_reader = PdfReader(content_buffer)

    output_writer = PdfWriter()
    for content_page in content_reader.pages:
        lh = PdfReader(BytesIO(letterhead_bytes)).pages[0]
        lh.merge_page(content_page)
        output_writer.add_page(lh)

    output_writer.write(output_buffer)
    output_buffer.seek(0)
    return output_buffer.getvalue()

# MAIN APP
if not st.session_state.logged_in:
    show_login_page()
else:
    st.markdown('<div class="main-header">☀️ Solarium Letterhead Generator</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="sub-header">Welcome, {st.session_state.user_email}</div>', unsafe_allow_html=True)

    col1, col2 = st.columns([6, 1])
    with col2:
        if st.button("🚪 Logout"):
            logout()

    st.markdown("""
    <div class="info-box">
    <b>How it works:</b><br>
    1. Upload your PDF document OR paste text content below<br>
    2. Click <b>Generate Letterhead PDF</b><br>
    3. Download your formatted PDF with Solarium letterhead<br>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    tab1, tab2 = st.tabs(["📄 Upload PDF", "📝 Paste Text"])

    with tab1:
        uploaded_pdf = st.file_uploader("Upload your PDF document", type=['pdf'])
        if uploaded_pdf:
            extracted_text = extract_pdf_text(uploaded_pdf)
            st.text_area("Extracted text (you can edit if needed):", extracted_text, height=200)

    with tab2:
        pasted_text = st.text_area("Paste your content here:", height=200, 
            placeholder="Paste any text content here...")

    st.markdown("---")

    use_default = st.checkbox("Use default Solarium letterhead", value=True)
    letterhead_file = None
    if not use_default:
        letterhead_file = st.file_uploader("Upload custom letterhead PDF", type=['pdf'])

    if st.button("🚀 Generate Letterhead PDF", type="primary"):
        with st.spinner("Generating your PDF..."):
            if uploaded_pdf:
                content = extract_pdf_text(uploaded_pdf)
            elif pasted_text:
                content = pasted_text
            else:
                st.error("Please upload a PDF or paste text content.")
                st.stop()

            if use_default:
                st.info("Please upload the Solarium letterhead PDF file.")
                st.stop()
            else:
                if letterhead_file:
                    letterhead_bytes = letterhead_file.getvalue()
                else:
                    st.error("Please upload a letterhead PDF.")
                    st.stop()

            try:
                pdf_bytes = generate_letterhead_pdf(content, letterhead_bytes)

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
    st.markdown("<center><small>☀️ Solarium Green Energy Limited | Secure Access</small></center>", unsafe_allow_html=True)
