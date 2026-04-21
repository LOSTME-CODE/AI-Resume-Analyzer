import os
import io
import json
import base64
from dotenv import load_dotenv
import streamlit as st
from PIL import Image
from pdf2image import convert_from_bytes
import pytesseract
import google.generativeai as genai

# -----------------------
# Configuration / Paths
# -----------------------
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

POPPLER_PATH = r"C:\tools\poppler-25.12.0\Library\bin"
TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH

# -----------------------
# PDF -> Images + OCR
# -----------------------
def process_pdf(uploaded_file, use_ocr=True):
    uploaded_file.seek(0)
    pdf_bytes = uploaded_file.read()
    images = convert_from_bytes(pdf_bytes, poppler_path=POPPLER_PATH)

    first_page = images[0]
    img_byte_arr = io.BytesIO()
    first_page.save(img_byte_arr, format='JPEG')
    pdf_image = [{
        "mime_type": "image/jpeg",
        "data": base64.b64encode(img_byte_arr.getvalue()).decode()
    }]

    ocr_text = ""
    if use_ocr:
        full_text = ""
        for i, img in enumerate(images):
            try:
                page_text = pytesseract.image_to_string(img)
            except:
                page_text = ""
            full_text += f"--- PAGE {i+1} ---\n{page_text}\n"
        ocr_text = full_text

    return pdf_image, ocr_text, images


# -----------------------
# Gemini Helper
# -----------------------
def call_gemini(system_prompt, job_description, ocr_text, pdf_image):
    model = genai.GenerativeModel('models/gemini-2.5-flash')
    response = model.generate_content([
        {"text": system_prompt},
        {"text": f"JOB DESCRIPTION:\n{job_description}" if job_description else "No job description provided."},
        {"text": f"RESUME TEXT:\n{ocr_text}"},
        pdf_image[0]
    ])
    return response.text


# -----------------------
# PROMPTS (tight, JSON-only)
# -----------------------

PROMPT_SUMMARY = """
You are an HR expert. Analyze ONLY the uploaded resume content. Ignore job description.

Return ONLY clean JSON. No markdown. No code blocks. No extra text.

{
  "name": "Candidate name from resume",
  "title": "Current/target role",
  "overall_impression": "1 sentence HR impression",
  "strengths": ["point 1", "point 2", "point 3"],
  "weaknesses": ["point 1", "point 2", "point 3"],
  "key_skills": ["skill1", "skill2", "skill3", "skill4", "skill5"],
  "missing_keywords": ["keyword1", "keyword2", "keyword3"],
  "improvement_tips": ["tip 1", "tip 2", "tip 3"]
}

Rules:
- Each list item: max 8 words
- Max 5 items per list
- Be direct and honest
- Return ONLY JSON
"""

PROMPT_ATS = """
You are an ATS format expert. Analyze the resume for ATS compatibility.

Return ONLY clean JSON. No markdown. No code blocks. No extra text.

{
  "ats_score": 72,
  "format_issues": ["issue 1", "issue 2", "issue 3"],
  "overused_keywords": ["word1", "word2"],
  "suggestions": ["suggestion 1", "suggestion 2", "suggestion 3"],
  "general_improvements": ["tip 1", "tip 2", "tip 3"]
}

Rules:
- ats_score: integer 0-100 based on formatting, readability, ATS parsing ability
- Each list item: max 8 words
- Max 5 items per list
- Return ONLY JSON
"""

PROMPT_MATCH = """
You are an ATS job matching expert. Compare the resume against the job description.

Return ONLY clean JSON. No markdown. No code blocks. No extra text.

{
  "match_score": 65,
  "job_fit_summary": "1 sentence verdict on candidate fit",
  "matched_skills": ["skill1", "skill2", "skill3"],
  "missing_skills": ["skill1", "skill2", "skill3"],
  "important_skills_to_add": ["skill1", "skill2", "skill3"],
  "overused_keywords": ["word1", "word2"]
}

Rules:
- match_score: integer 0-100 (how well resume matches JD)
- Each list item: max 6 words
- Max 6 items per list
- Return ONLY JSON
"""


# -----------------------
# SVG Circular Chart
# -----------------------
def circular_score(score, label, color=None):
    if color is None:
        if score < 40:
            color = "#FF4B4B"
        elif score < 65:
            color = "#FFA500"
        elif score < 80:
            color = "#4BB543"
        else:
            color = "#00C853"

    circumference = 2 * 3.14159 * 54
    dash = (score / 100) * circumference
    gap = circumference - dash

    svg = f"""
    <div style="display:flex; flex-direction:column; align-items:center; margin: 10px 0;">
        <svg viewBox="0 0 120 120" width="160" height="160">
            <circle cx="60" cy="60" r="54" fill="none" stroke="#2a2a3a" stroke-width="10"/>
            <circle cx="60" cy="60" r="54" fill="none"
                stroke="{color}" stroke-width="10"
                stroke-dasharray="{dash:.1f} {gap:.1f}"
                stroke-dashoffset="{circumference/4:.1f}"
                stroke-linecap="round"/>
            <text x="60" y="55" text-anchor="middle" font-size="22" font-weight="bold" fill="{color}">{score}%</text>
            <text x="60" y="75" text-anchor="middle" font-size="9" fill="#aaaaaa">{label}</text>
        </svg>
    </div>
    """
    return svg


def render_tags(items, color="#4B8BBE"):
    if not items:
        return ""
    tags = "".join([
        f'<span style="background:{color}22; color:{color}; border:1px solid {color}44; '
        f'padding:4px 10px; border-radius:20px; font-size:13px; margin:3px; display:inline-block;">{item}</span>'
        for item in items
    ])
    return f'<div style="display:flex; flex-wrap:wrap; gap:4px; margin:8px 0;">{tags}</div>'


def card(title, content_html, card_bg, border_color, muted):
    """Render a complete card in one markdown call to avoid empty box artifacts."""
    return f"""
    <div style="background:{card_bg}; border:1px solid {border_color}; border-radius:12px;
                padding:18px 20px; margin:12px 0;">
        <div style="font-size:12px; font-weight:700; letter-spacing:0.08em; text-transform:uppercase;
                    color:{muted}; margin-bottom:10px;">{title}</div>
        {content_html}
    </div>
    """


def bullet_html(items, text_color):
    if not items:
        return f'<span style="color:{text_color}; opacity:0.4; font-size:13px;">None found</span>'
    return "".join([
        f'<div style="color:{text_color}; font-size:14px; margin:5px 0;">• {item}</div>'
        for item in items
    ])


def arrow_html(items, text_color):
    if not items:
        return f'<span style="color:{text_color}; opacity:0.4; font-size:13px;">None found</span>'
    return "".join([
        f'<div style="color:{text_color}; font-size:14px; margin:5px 0;">→ {item}</div>'
        for item in items
    ])


def safe_parse_json(raw):
    try:
        return json.loads(raw)
    except:
        start = raw.find("{")
        end = raw.rfind("}") + 1
        if start != -1:
            try:
                return json.loads(raw[start:end])
            except:
                pass
    return None


# -----------------------
# Streamlit UI
# -----------------------
st.set_page_config(page_title="AI Resume Analyzer", layout="centered")

# Hide default Streamlit sidebar and menu
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    [data-testid="stSidebar"] {display: none;}
    </style>
""", unsafe_allow_html=True)

# Right image (pic.png)
teacher_img_path = r"C:\Users\saa29\Desktop\ats\pic.png"
try:
    encoded_img = base64.b64encode(open(teacher_img_path, "rb").read()).decode()
    st.markdown(
        f"""
        <style>
        .teacher-img {{
            position: fixed;
            top: 5vh;
            right: -8vw;
            width: 28vw;
            max-width: 420px;
            min-width: 160px;
            border-radius: 10px;
            z-index: 999;
            pointer-events: none;
        }}
        </style>
        <img class="teacher-img" src="data:image/png;base64,{encoded_img}">
        """,
        unsafe_allow_html=True
    )
except:
    pass

# Left image (pic2.png)
left_img_path = r"C:\Users\saa29\Desktop\ats\pic2.png"
try:
    encoded_img2 = base64.b64encode(open(left_img_path, "rb").read()).decode()
    st.markdown(
        f"""
        <style>
        .left-img {{
            position: fixed;
            top: 5vh;
            left: -4vw;
            width: 28vw;
            max-width: 420px;
            min-width: 160px;
            border-radius: 10px;
            z-index: 999;
            pointer-events: none;
        }}
        </style>
        <img class="left-img" src="data:image/png;base64,{encoded_img2}">
        """,
        unsafe_allow_html=True
    )
except:
    pass

# Theme
if "theme" not in st.session_state:
    st.session_state.theme = "dark"

def toggle_theme():
    st.session_state.theme = "dark" if st.session_state.theme == "light" else "light"

# Colors
if st.session_state.theme == "dark":
    bg_color = "#0E1117"
    text_color = "#FAFAFA"
    card_bg = "#1A1B26"
    border_color = "#2a2a3a"
    muted = "#888"
else:
    bg_color = "#F8F9FA"
    text_color = "#111111"
    card_bg = "#FFFFFF"
    border_color = "#E0E0E0"
    muted = "#666"

BOX_COLOR = "#1e3a5f"

st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap');

    /* ── PAGE BACKGROUND & BASE TEXT ── */
    body, .stApp, .block-container,
    [data-testid="stAppViewContainer"],
    [data-testid="stMain"] {{
        background-color: {bg_color} !important;
        color: {text_color} !important;
        font-family: 'DM Sans', sans-serif !important;
    }}

    /* ── ALL TEXT ELEMENTS ── */
    h1, h2, h3, h4, h5, h6, p, label, span, div,
    [data-testid="stMarkdownContainer"] * {{
        color: {text_color} !important;
        font-family: 'DM Sans', sans-serif !important;
    }}

    /* ── TEXTAREA ── */
    textarea,
    .stTextArea textarea,
    .stTextArea > div > div > textarea {{
        background-color: {card_bg} !important;
        color: {text_color} !important;
        border: 1.5px solid {border_color} !important;
        border-radius: 8px !important;
        font-family: 'DM Sans', sans-serif !important;
        font-size: 14px !important;
    }}

    textarea::placeholder,
    .stTextArea textarea::placeholder {{
        color: {muted} !important;
        opacity: 1 !important;
    }}

    /* ── FILE UPLOADER BOX ── */
    [data-testid="stFileUploader"] section,
    [data-testid="stFileUploader"] section > div,
    [data-testid="stFileUploaderDropzone"] {{
        background-color: {card_bg} !important;
        border: 1.5px dashed #4B8BBE !important;
        border-radius: 8px !important;
    }}

    /* All text inside file uploader */
    [data-testid="stFileUploader"] *,
    [data-testid="stFileUploaderDropzone"] * {{
        color: {text_color} !important;
    }}

    /* ── LABELS above inputs ── */
    [data-testid="stTextAreaLabel"],
    [data-testid="stFileUploaderLabel"],
    .stTextArea label, .stFileUploader label {{
        color: {text_color} !important;
        font-weight: 600 !important;
        font-size: 14px !important;
    }}

    /* ── BUTTONS ── */
    .stButton > button {{
        background-color: #4B8BBE !important;
        color: white !important;
        font-weight: 600 !important;
        border-radius: 8px !important;
        border: none !important;
        padding: 8px 16px !important;
        font-family: 'DM Sans', sans-serif !important;
        transition: opacity 0.2s !important;
    }}

    .stButton > button:hover {{
        opacity: 0.85 !important;
    }}

    /* ── BROWSE FILES BUTTON inside uploader ── */
    [data-testid="stFileUploaderDropzone"] button {{
        background-color: #4B8BBE !important;
        color: white !important;
        border: none !important;
        border-radius: 6px !important;
        font-weight: 600 !important;
    }}

    .result-card {{
        background: {card_bg};
        border: 1px solid {border_color};
        border-radius: 12px;
        padding: 20px 24px;
        margin: 14px 0;
    }}

    .section-title {{
        font-size: 13px;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: {muted} !important;
        margin-bottom: 10px;
    }}

    .impression-box {{
        background: linear-gradient(135deg, #1e3a5f22, #4B8BBE11);
        border-left: 3px solid #4B8BBE;
        padding: 12px 16px;
        border-radius: 0 8px 8px 0;
        font-style: italic;
        font-size: 15px;
        margin: 10px 0;
    }}
    </style>
""", unsafe_allow_html=True)



# -----------------------
# Header
# -----------------------
col_title, col_toggle = st.columns([5, 1])
with col_title:
    st.markdown("<h1 style='margin-bottom:4px;'>AI Resume Analyzer</h1>", unsafe_allow_html=True)
    st.markdown(f"<p style='color:{muted}; margin-top:0;'>Upload your resume · Get instant AI feedback</p>", unsafe_allow_html=True)
with col_toggle:
    st.markdown("<br>", unsafe_allow_html=True)
    st.button("🌓 Theme", on_click=toggle_theme)

st.markdown("---")

# -----------------------
# Inputs
# -----------------------
job_description = st.text_area("📋 Paste Job Description (optional but recommended)", height=130,
                                placeholder="Paste the job description here to get match score and skill gaps...")
uploaded_file = st.file_uploader("📄 Upload Resume (PDF only)", type=["pdf"])

col1, col2, col3 = st.columns(3)
with col1:
    btn_summary = st.button("📝 Resume Summary")
with col2:
    btn_ats = st.button("📊 ATS Score")
with col3:
    btn_match = st.button("🎯 Match With JD")

st.markdown("---")


# -----------------------
# MAIN LOGIC
# -----------------------
if uploaded_file:
    try:
        pdf_image, ocr_text, images = process_pdf(uploaded_file)
    except Exception as e:
        st.error(f"PDF processing error: {e}")
        st.stop()

    # ---- SUMMARY ----
    if btn_summary:
        with st.spinner("Analyzing resume..."):
            try:
                raw = call_gemini(PROMPT_SUMMARY, "", ocr_text, pdf_image)
                data = safe_parse_json(raw)

                if data is None:
                    st.error("Could not parse response. Raw output:")
                    st.code(raw)
                else:
                    st.markdown(f"### 👤 {data.get('name', 'Candidate')} — {data.get('title', '')}")

                    st.markdown(
                        f'<div style="background:linear-gradient(135deg,#1e3a5f22,#4B8BBE11);'
                        f'border-left:3px solid #4B8BBE;padding:12px 16px;border-radius:0 8px 8px 0;'
                        f'font-style:italic;font-size:15px;margin:10px 0;color:{text_color};">'
                        f'💬 {data.get("overall_impression", "")}</div>',
                        unsafe_allow_html=True
                    )

                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.markdown(card("✅ Strengths", bullet_html(data.get("strengths", []), text_color), card_bg, border_color, muted), unsafe_allow_html=True)
                    with col_b:
                        st.markdown(card("⚠️ Weaknesses", bullet_html(data.get("weaknesses", []), text_color), card_bg, border_color, muted), unsafe_allow_html=True)

                    st.markdown(card("🔑 Key Skills Detected", render_tags(data.get("key_skills", []), "#4BB543"), card_bg, border_color, muted), unsafe_allow_html=True)
                    st.markdown(card("❌ Missing Keywords", render_tags(data.get("missing_keywords", []), "#FF4B4B"), card_bg, border_color, muted), unsafe_allow_html=True)
                    st.markdown(card("💡 Improvement Tips", arrow_html(data.get("improvement_tips", []), text_color), card_bg, border_color, muted), unsafe_allow_html=True)

            except Exception as e:
                st.error(f"Error: {e}")

    # ---- ATS SCORE ----
    if btn_ats:
        with st.spinner("Calculating ATS score..."):
            try:
                raw = call_gemini(PROMPT_ATS, job_description, ocr_text, pdf_image)
                data = safe_parse_json(raw)

                if data is None:
                    st.error("Could not parse response. Raw output:")
                    st.code(raw)
                else:
                    score = int(data.get("ats_score", 0))

                    st.markdown("### 📊 ATS Score")
                    st.markdown(circular_score(score, "ATS Score"), unsafe_allow_html=True)

                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.markdown(card("⚠️ Format Issues", bullet_html(data.get("format_issues", []), text_color), card_bg, border_color, muted), unsafe_allow_html=True)
                    with col_b:
                        st.markdown(card("🔁 Overused Keywords", render_tags(data.get("overused_keywords", []), "#FFA500"), card_bg, border_color, muted), unsafe_allow_html=True)

                    st.markdown(card("🛠 Suggestions to Improve ATS", arrow_html(data.get("suggestions", []), text_color), card_bg, border_color, muted), unsafe_allow_html=True)
                    st.markdown(card("📌 General Improvements", arrow_html(data.get("general_improvements", []), text_color), card_bg, border_color, muted), unsafe_allow_html=True)

            except Exception as e:
                st.error(f"Error: {e}")

    # ---- MATCH WITH JD ----
    if btn_match:
        if not job_description.strip():
            st.warning("⚠️ Please paste a Job Description above to use this feature.")
        else:
            with st.spinner("Matching resume with job description..."):
                try:
                    raw = call_gemini(PROMPT_MATCH, job_description, ocr_text, pdf_image)
                    data = safe_parse_json(raw)

                    if data is None:
                        st.error("Could not parse response. Raw output:")
                        st.code(raw)
                    else:
                        score = int(data.get("match_score", 0))

                        st.markdown("### 🎯 Job Match Analysis")
                        st.markdown(circular_score(score, "JD Match"), unsafe_allow_html=True)

                        st.markdown(
                            f'<div style="background:linear-gradient(135deg,#1e3a5f22,#4B8BBE11);'
                            f'border-left:3px solid #4B8BBE;padding:12px 16px;border-radius:0 8px 8px 0;'
                            f'font-style:italic;font-size:15px;margin:10px 0;color:{text_color};">'
                            f'🧠 {data.get("job_fit_summary", "")}</div>',
                            unsafe_allow_html=True
                        )

                        col_a, col_b = st.columns(2)
                        with col_a:
                            st.markdown(card("✅ Matched Skills", render_tags(data.get("matched_skills", []), "#4BB543"), card_bg, border_color, muted), unsafe_allow_html=True)
                        with col_b:
                            st.markdown(card("❌ Missing Skills", render_tags(data.get("missing_skills", []), "#FF4B4B"), card_bg, border_color, muted), unsafe_allow_html=True)

                        st.markdown(card("⭐ Important Skills to Add", render_tags(data.get("important_skills_to_add", []), "#4B8BBE"), card_bg, border_color, muted), unsafe_allow_html=True)

                        if data.get("overused_keywords"):
                            st.markdown(card("🔁 Overused Keywords", render_tags(data.get("overused_keywords", []), "#FFA500"), card_bg, border_color, muted), unsafe_allow_html=True)

                except Exception as e:
                    st.error(f"Error: {e}")

else:
    if btn_summary or btn_ats or btn_match:
        st.warning("⚠️ Please upload a PDF resume first!")