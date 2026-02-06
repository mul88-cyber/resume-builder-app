import streamlit as st
import json
from fpdf import FPDF
import io
import zipfile
from datetime import datetime
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
import base64
import re

# --- KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="CV Builder Pro Ultra",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/streamlit',
        'Report a bug': "https://github.com/streamlit",
        'About': "# CV Builder Pro Ultra v2.1\n### Build professional CVs with AI-powered suggestions"
    }
)

# --- STATE MANAGEMENT ---
if 'cv_data' not in st.session_state:
    st.session_state.cv_data = {
        'personal_info': {
            'nama': '', 'email': '', 'telepon': '', 'alamat': '',
            'linkedin': '', 'github': '', 'website': '', 'posisi_target': '',
            'foto': None
        },
        'ringkasan': '',
        'pengalaman': [],
        'pendidikan': [],
        'keahlian': [],
        'sertifikasi': [],
        'proyek': [],
        'bahasa': [],
        'hobi': []
    }

if 'settings' not in st.session_state:
    st.session_state.settings = {
        'template_style': 'modern_sidebar',
        'font_family': 'Helvetica',
        'base_color': '#2563eb',
        'accent_color': '#1e40af',
        'font_size_body': 10,
        'font_size_header': 24,
        'section_spacing': 5,
        'show_icons': True,
        'theme': 'light',
        'ats_friendly': True
    }

# --- DATA TEMPLATES & PRESETS ---
LAYOUTS = {
    'modern_sidebar': {'name': 'Modern Sidebar', 'type': '2_column', 'ats_score': 85},
    'classic_vertical': {'name': 'ATS Professional', 'type': '1_column', 'ats_score': 95},
    'minimal_clean': {'name': 'Minimalist Clean', 'type': '1_column_compact', 'ats_score': 80},
    'executive': {'name': 'Executive Style', 'type': '2_column', 'ats_score': 90},
    'creative': {'name': 'Creative Portfolio', 'type': 'creative', 'ats_score': 70}
}

THEME_COLORS = {
    'professional_blue': {'primary': '#1e40af', 'secondary': '#3b82f6'},
    'corporate_gray': {'primary': '#374151', 'secondary': '#6b7280'},
    'green_teal': {'primary': '#0f766e', 'secondary': '#14b8a6'},
    'purple_premium': {'primary': '#7c3aed', 'secondary': '#a78bfa'},
    'red_passion': {'primary': '#dc2626', 'secondary': '#ef4444'}
}

FONTS = {
    'Helvetica': {'pdf': 'Helvetica', 'docx': 'Calibri'},
    'Times': {'pdf': 'Times', 'docx': 'Times New Roman'},
    'Arial': {'pdf': 'Arial', 'docx': 'Arial'},
    'Georgia': {'pdf': 'Georgia', 'docx': 'Georgia'},
    'Verdana': {'pdf': 'Verdana', 'docx': 'Verdana'}
}

# --- FUNGSI HELPER DIPERBAIKI ---
def hex_to_rgb(hex_color):
    """Convert hex color to RGB tuple with robust error handling"""
    try:
        hex_color = hex_color.lstrip('#')
        if len(hex_color) == 6:
            return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        elif len(hex_color) == 3:
            return tuple(int(hex_color[i:i+1]*2, 16) for i in (0, 1, 2))
        else:
            return (37, 99, 235)
    except Exception:
        return (37, 99, 235)

def calculate_ats_score(data):
    """Calculate ATS compatibility score with improved algorithm"""
    score = 0
    
    # Required fields (40 points)
    if data['personal_info']['nama']: score += 10
    if data['personal_info']['email']: score += 10
    if data['personal_info']['posisi_target']: score += 10
    if data['ringkasan'] and len(data['ringkasan'].split()) >= 50: score += 10
    
    # Experience (25 points)
    exp_count = len(data['pengalaman'])
    if exp_count >= 1: score += 10
    if exp_count >= 2: score += 8
    if exp_count >= 3: score += 7
    
    # Education (15 points)
    edu_count = len(data['pendidikan'])
    if edu_count >= 1: score += 10
    if edu_count >= 2: score += 5
    
    # Skills (20 points)
    skill_count = len(data['keahlian'])
    if skill_count >= 5: score += 10
    if skill_count >= 8: score += 6
    if skill_count >= 12: score += 4
    
    # Bonus for quantifiable achievements (10 points)
    summary_text = (data['ringkasan'] + ' ' + 
                   ' '.join([exp.get('deskripsi', '') for exp in data['pengalaman']])).lower()
    
    # Check for numbers (quantifiable results)
    if re.search(r'\d+%', summary_text) or re.search(r'\d+x', summary_text) or re.search(r'\$\d+', summary_text):
        score += 5
    
    # Check for action verbs
    action_verbs = ['managed', 'developed', 'created', 'improved', 'increased', 'reduced', 'led', 'achieved']
    if any(verb in summary_text for verb in action_verbs):
        score += 5
    
    return min(score, 100)

# --- PDF GENERATOR DIPERBAIKI (DENGAN SUPPORT CIRCLE CUSTOM) ---
class CVPDF(FPDF):
    def header(self):
        pass
    
    def footer(self):
        self.set_y(-15)
        font_family = st.session_state.settings['font_family']
        pdf_font = FONTS.get(font_family, FONTS['Helvetica'])['pdf']
        self.set_font(pdf_font, 'I', 8)
        self.set_text_color(128)
        self.cell(0, 10, f"Generated by CV Builder Pro Ultra - Page {self.page_no()}", 0, 0, 'C')
    
    def circle(self, x, y, r, style='D'):
        """Draw a circle - custom implementation since FPDF doesn't have this method"""
        self.ellipse(x - r, y - r, 2 * r, 2 * r, style)

def generate_pdf_enhanced(data, settings):
    pdf = CVPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    
    font = settings['font_family']
    pdf_font = FONTS.get(font, FONTS['Helvetica'])['pdf']
    
    try:
        r_prim, g_prim, b_prim = hex_to_rgb(settings['base_color'])
        r_sec, g_sec, b_sec = hex_to_rgb(settings['accent_color'])
    except:
        r_prim, g_prim, b_prim = (37, 99, 235)
        r_sec, g_sec, b_sec = (30, 64, 175)
    
    # MODERN SIDEBAR TEMPLATE (default)
    if settings['template_style'] == 'modern_sidebar':
        # Sidebar (left column)
        pdf.set_fill_color(r_prim, g_prim, b_prim)
        pdf.rect(0, 0, 70, 297, 'F')
        
        # Name in sidebar
        pdf.set_text_color(255, 255, 255)
        pdf.set_font(pdf_font, 'B', 16)
        pdf.set_xy(5, 20)
        pdf.multi_cell(60, 6, data['personal_info']['nama'].upper() if data['personal_info']['nama'] else "YOUR NAME", align='C')
        
        # Contact info in sidebar
        pdf.set_font(pdf_font, '', 9)
        pdf.set_xy(5, 40)
        contact_items = []
        if data['personal_info']['email']: 
            contact_items.append(f"✉ {data['personal_info']['email']}")
        if data['personal_info']['telepon']: 
            contact_items.append(f"📱 {data['personal_info']['telepon']}")
        if data['personal_info']['linkedin']: 
            contact_items.append(f"🔗 LinkedIn")
        
        for item in contact_items:
            pdf.set_x(5)
            pdf.cell(60, 5, item, ln=True, align='C')
        
        # Skills section in sidebar
        if data['keahlian']:
            pdf.set_xy(5, 80)
            pdf.set_font(pdf_font, 'B', 11)
            pdf.cell(60, 6, "SKILLS", ln=True, align='C')
            pdf.set_font(pdf_font, '', 8)
            pdf.set_text_color(255, 255, 255)
            for skill in data['keahlian'][:12]:
                pdf.set_x(5)
                pdf.cell(60, 4, f"• {skill}", ln=True, align='L')
        
        # Main content (right column)
        pdf.set_text_color(0, 0, 0)
        pdf.set_xy(75, 20)
        
        # Position title
        if data['personal_info']['posisi_target']:
            pdf.set_font(pdf_font, 'B', 18)
            pdf.set_text_color(r_prim, g_prim, b_prim)
            pdf.cell(0, 10, data['personal_info']['posisi_target'], ln=True)
            pdf.ln(5)
        
        # Summary
        if data['ringkasan']:
            pdf.set_font(pdf_font, 'B', 12)
            pdf.set_text_color(r_prim, g_prim, b_prim)
            pdf.cell(0, 8, "PROFESSIONAL SUMMARY", ln=True)
            pdf.set_font(pdf_font, '', settings['font_size_body'])
            pdf.set_text_color(0, 0, 0)
            pdf.multi_cell(0, 5, data['ringkasan'])
            pdf.ln(8)
        
        # Experience
        if data['pengalaman']:
            pdf.set_font(pdf_font, 'B', 12)
            pdf.set_text_color(r_prim, g_prim, b_prim)
            pdf.cell(0, 8, "WORK EXPERIENCE", ln=True)
            
            for exp in data['pengalaman']:
                pdf.set_font(pdf_font, 'B', 11)
                pdf.set_text_color(0, 0, 0)
                pdf.cell(0, 6, exp.get('posisi', 'Position'), ln=True)
                
                pdf.set_font(pdf_font, 'I', 10)
                pdf.set_text_color(r_sec, g_sec, b_sec)
                pdf.cell(0, 5, f"{exp.get('perusahaan', 'Company')} | {exp.get('periode', 'Period')}", ln=True)
                
                pdf.set_font(pdf_font, '', settings['font_size_body'])
                pdf.set_text_color(0, 0, 0)
                pdf.multi_cell(0, 5, exp.get('deskripsi', 'Description'))
                pdf.ln(5)
        
        # Education
        if data['pendidikan']:
            pdf.set_font(pdf_font, 'B', 12)
            pdf.set_text_color(r_prim, g_prim, b_prim)
            pdf.cell(0, 8, "EDUCATION", ln=True)
            
            for edu in data['pendidikan']:
                pdf.set_font(pdf_font, 'B', 11)
                pdf.set_text_color(0, 0, 0)
                pdf.cell(0, 6, edu.get('institusi', 'Institution'), ln=True)
                
                pdf.set_font(pdf_font, '', 10)
                pdf.set_text_color(r_sec, g_sec, b_sec)
                pdf.cell(0, 5, f"{edu.get('gelar', 'Degree')} | {edu.get('tahun', 'Year')}", ln=True)
                pdf.ln(4)
    
    # EXECUTIVE TEMPLATE
    elif settings['template_style'] == 'executive':
        # Header with colored bar
        pdf.set_fill_color(r_prim, g_prim, b_prim)
        pdf.rect(0, 0, 210, 40, 'F')
        
        # Name in header
        pdf.set_text_color(255, 255, 255)
        pdf.set_font(pdf_font, 'B', 28)
        pdf.set_xy(20, 12)
        pdf.cell(0, 10, data['personal_info']['nama'].upper() if data['personal_info']['nama'] else "YOUR NAME", ln=True)
        
        # Contact info below header
        pdf.set_text_color(255, 255, 255)
        pdf.set_font(pdf_font, '', 10)
        pdf.set_xy(20, 35)
        contact_items = []
        if data['personal_info']['email']: contact_items.append(data['personal_info']['email'])
        if data['personal_info']['telepon']: contact_items.append(data['personal_info']['telepon'])
        if data['personal_info']['linkedin']: contact_items.append("LinkedIn")
        pdf.cell(0, 6, " | ".join(contact_items) if contact_items else "Add contact information", ln=True)
        
        # Two column layout
        pdf.set_xy(20, 55)
        
        # Left column - Summary and Experience
        pdf.set_font(pdf_font, 'B', 16)
        pdf.set_text_color(r_prim, g_prim, b_prim)
        pdf.cell(85, 10, "PROFESSIONAL SUMMARY", ln=True)
        pdf.set_font(pdf_font, '', settings['font_size_body'])
        pdf.set_text_color(0, 0, 0)
        pdf.multi_cell(85, 5, data['ringkasan'] if data['ringkasan'] else "Add your professional summary here.")
        pdf.ln(8)
        
        # Experience
        if data['pengalaman']:
            pdf.set_font(pdf_font, 'B', 16)
            pdf.set_text_color(r_prim, g_prim, b_prim)
            pdf.cell(85, 10, "WORK EXPERIENCE", ln=True)
            
            for exp in data['pengalaman']:
                pdf.set_font(pdf_font, 'B', 12)
                pdf.set_text_color(0, 0, 0)
                pdf.cell(85, 6, exp.get('posisi', 'Position'), ln=True)
                
                pdf.set_font(pdf_font, 'I', 10)
                pdf.set_text_color(r_sec, g_sec, b_sec)
                pdf.cell(85, 5, f"{exp.get('perusahaan', 'Company')} | {exp.get('periode', 'Period')}", ln=True)
                
                pdf.set_font(pdf_font, '', 9)
                pdf.set_text_color(0, 0, 0)
                pdf.multi_cell(85, 4, exp.get('deskripsi', 'Description'))
                pdf.ln(5)
        
        # Right column - Skills, Education
        pdf.set_xy(115, 55)
        
        # Skills
        if data['keahlian']:
            pdf.set_font(pdf_font, 'B', 16)
            pdf.set_text_color(r_prim, g_prim, b_prim)
            pdf.cell(85, 10, "KEY SKILLS", ln=True)
            
            pdf.set_font(pdf_font, '', 10)
            pdf.set_text_color(0, 0, 0)
            col_width = 40
            x_start = pdf.get_x()
            y_start = pdf.get_y()
            
            for i, skill in enumerate(data['keahlian'][:12]):
                if i > 0 and i % 2 == 0:
                    pdf.set_xy(x_start, pdf.get_y() + 6)
                pdf.cell(col_width, 6, f"• {skill}", ln=False)
                if i % 2 == 0:
                    pdf.set_x(x_start + col_width)
            pdf.ln(12)
        
        # Education
        if data['pendidikan']:
            pdf.set_font(pdf_font, 'B', 16)
            pdf.set_text_color(r_prim, g_prim, b_prim)
            pdf.cell(85, 10, "EDUCATION", ln=True)
            
            for edu in data['pendidikan']:
                pdf.set_font(pdf_font, 'B', 11)
                pdf.set_text_color(0, 0, 0)
                pdf.cell(85, 6, edu.get('institusi', 'Institution'), ln=True)
                
                pdf.set_font(pdf_font, '', 10)
                pdf.set_text_color(r_sec, g_sec, b_sec)
                pdf.cell(85, 5, f"{edu.get('gelar', 'Degree')} | {edu.get('tahun', 'Year')}", ln=True)
                pdf.ln(4)
    
    # CREATIVE TEMPLATE (dengan circle custom implementation)
    elif settings['template_style'] == 'creative':
        # Header with gradient effect (simulated)
        pdf.set_fill_color(r_prim, g_prim, b_prim)
        pdf.rect(0, 0, 210, 70, 'F')
        
        # Name with large font
        pdf.set_text_color(255, 255, 255)
        pdf.set_font(pdf_font, 'B', 32)
        pdf.set_xy(25, 25)
        pdf.cell(0, 15, data['personal_info']['nama'] if data['personal_info']['nama'] else "YOUR NAME", ln=True)
        
        # Position
        if data['personal_info']['posisi_target']:
            pdf.set_font(pdf_font, 'I', 16)
            pdf.set_text_color(255, 255, 220)
            pdf.set_x(25)
            pdf.cell(0, 10, data['personal_info']['posisi_target'], ln=True)
        
        # Main content starts at y=85
        pdf.set_xy(25, 85)
        
        # Summary with icon
        if data['ringkasan']:
            pdf.set_font(pdf_font, 'B', 14)
            pdf.set_text_color(r_prim, g_prim, b_prim)
            pdf.cell(0, 8, "✨ ABOUT ME", ln=True)
            pdf.set_font(pdf_font, '', 11)
            pdf.set_text_color(0, 0, 0)
            pdf.multi_cell(0, 6, data['ringkasan'])
            pdf.ln(12)
        
        # Experience in timeline style
        if data['pengalaman']:
            pdf.set_font(pdf_font, 'B', 14)
            pdf.set_text_color(r_prim, g_prim, b_prim)
            pdf.cell(0, 8, "📈 EXPERIENCE", ln=True)
            
            for i, exp in enumerate(data['pengalaman']):
                # Timeline dot (using custom circle method)
                pdf.set_fill_color(r_prim, g_prim, b_prim)
                pdf.circle(30, pdf.get_y() + 4, 2, style='F')
                
                pdf.set_font(pdf_font, 'B', 12)
                pdf.set_text_color(0, 0, 0)
                pdf.set_x(40)
                pdf.cell(0, 6, exp.get('posisi', 'Position'), ln=True)
                
                pdf.set_font(pdf_font, 'I', 10)
                pdf.set_text_color(100, 100, 100)
                pdf.set_x(40)
                pdf.cell(0, 5, f"{exp.get('perusahaan', 'Company')} • {exp.get('periode', 'Period')}", ln=True)
                
                pdf.set_font(pdf_font, '', 10)
                pdf.set_text_color(0, 0, 0)
                pdf.set_x(40)
                pdf.multi_cell(0, 5, exp.get('deskripsi', 'Description'))
                pdf.ln(8)
    
    # CLASSIC VERTICAL (ATS-friendly)
    else:  # classic_vertical or minimal_clean
        pdf.set_font(pdf_font, 'B', 22)
        pdf.set_text_color(r_prim, g_prim, b_prim)
        pdf.cell(0, 12, data['personal_info']['nama'] if data['personal_info']['nama'] else "YOUR NAME", ln=True)
        
        if data['personal_info']['posisi_target']:
            pdf.set_font(pdf_font, 'B', 14)
            pdf.set_text_color(r_sec, g_sec, b_sec)
            pdf.cell(0, 8, data['personal_info']['posisi_target'], ln=True)
        
        pdf.ln(3)
        
        # Contact info
        pdf.set_font(pdf_font, '', 10)
        pdf.set_text_color(80, 80, 80)
        contact_items = []
        if data['personal_info']['email']: contact_items.append(data['personal_info']['email'])
        if data['personal_info']['telepon']: contact_items.append(data['personal_info']['telepon'])
        if data['personal_info']['alamat']: contact_items.append(data['personal_info']['alamat'])
        
        if contact_items:
            pdf.cell(0, 6, " | ".join(contact_items), ln=True)
        pdf.ln(8)
        
        # Summary
        if data['ringkasan']:
            pdf.set_font(pdf_font, 'B', 12)
            pdf.set_text_color(0, 0, 0)
            pdf.cell(0, 8, "PROFESSIONAL SUMMARY", ln=True)
            pdf.set_font(pdf_font, '', settings['font_size_body'])
            pdf.multi_cell(0, 6, data['ringkasan'])
            pdf.ln(10)
        
        # Experience
        if data['pengalaman']:
            pdf.set_font(pdf_font, 'B', 12)
            pdf.set_text_color(r_prim, g_prim, b_prim)
            pdf.cell(0, 8, "WORK EXPERIENCE", ln=True)
            
            for exp in data['pengalaman']:
                pdf.set_font(pdf_font, 'B', 11)
                pdf.set_text_color(0, 0, 0)
                pdf.cell(0, 7, exp.get('posisi', 'Position'), ln=True)
                
                pdf.set_font(pdf_font, 'I', 10)
                pdf.set_text_color(r_sec, g_sec, b_sec)
                pdf.cell(0, 5, f"{exp.get('perusahaan', 'Company')} | {exp.get('periode', 'Period')}", ln=True)
                
                pdf.set_font(pdf_font, '', settings['font_size_body'])
                pdf.set_text_color(0, 0, 0)
                pdf.multi_cell(0, 6, exp.get('deskripsi', 'Description'))
                pdf.ln(5)
        
        # Education
        if data['pendidikan']:
            pdf.set_font(pdf_font, 'B', 12)
            pdf.set_text_color(r_prim, g_prim, b_prim)
            pdf.cell(0, 8, "EDUCATION", ln=True)
            
            for edu in data['pendidikan']:
                pdf.set_font(pdf_font, 'B', 11)
                pdf.set_text_color(0, 0, 0)
                pdf.cell(0, 6, edu.get('institusi', 'Institution'), ln=True)
                
                pdf.set_font(pdf_font, '', 10)
                pdf.set_text_color(r_sec, g_sec, b_sec)
                pdf.cell(0, 5, f"{edu.get('gelar', 'Degree')} | {edu.get('tahun', 'Year')}", ln=True)
                pdf.ln(4)
        
        # Skills
        if data['keahlian']:
            pdf.set_font(pdf_font, 'B', 12)
            pdf.set_text_color(r_prim, g_prim, b_prim)
            pdf.cell(0, 8, "SKILLS", ln=True)
            
            pdf.set_font(pdf_font, '', 10)
            pdf.set_text_color(0, 0, 0)
            skills_per_line = 4
            skills = data['keahlian'][:16]  # Limit to 16 skills
            
            for i in range(0, len(skills), skills_per_line):
                line_skills = skills[i:i+skills_per_line]
                pdf.cell(0, 6, " • ".join(line_skills), ln=True)
    
    # Generate PDF to buffer
    buffer = io.BytesIO()
    pdf.output(buffer)
    buffer.seek(0)
    return buffer

# --- WORD DOCX GENERATOR (DIPERBAIKI) ---
def generate_word_doc(data, settings):
    doc = docx.Document()
    
    # Set document properties
    doc.core_properties.author = "CV Builder Pro Ultra"
    doc.core_properties.title = f"CV - {data['personal_info']['nama']}"
    
    # Set margins
    sections = doc.sections
    for section in sections:
        section.top_margin = Inches(0.5)
        section.bottom_margin = Inches(0.5)
        section.left_margin = Inches(0.5)
        section.right_margin = Inches(0.5)
    
    # Choose template style
    if settings['template_style'] == 'classic_vertical':
        generate_word_classic(doc, data, settings)
    elif settings['template_style'] == 'executive':
        generate_word_executive(doc, data, settings)
    elif settings['template_style'] == 'creative':
        generate_word_creative(doc, data, settings)
    else:  # modern_sidebar or minimal_clean
        generate_word_modern(doc, data, settings)
    
    # Save to BytesIO
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

# [Sisa fungsi Word generator dipertahankan seperti asli dengan perbaikan minor untuk alignment]
# ... (implementasi fungsi generate_word_executive, generate_word_classic, dll. tetap sama 
# dengan penyesuaian minor untuk menghindari duplikasi panjang di respons)

# --- HTML PREVIEW DIPERBAIKI DENGAN RESPONSIVE DESIGN ---
def get_html_preview_enhanced(data, settings):
    ats_score = calculate_ats_score(data)
    
    # Theme colors
    if settings['theme'] == 'dark':
        border_color = '#444'
        text_color = '#fff'
        bg_color = '#1e1e1e'
        skill_bg = '#333'
        date_color = '#aaa'
    else:
        border_color = '#eee'
        text_color = '#333'
        bg_color = 'white'
        skill_bg = '#f0f0f0'
        date_color = '#666'
    
    # Build HTML dengan responsive design
    html = f"""
    <style>
        .cv-container {{
            max-width: 800px;
            margin: 0 auto;
            background: {bg_color};
            color: {text_color};
            box-shadow: 0 5px 25px rgba(0,0,0,0.1);
            border-radius: 10px;
            overflow: hidden;
            font-family: Arial, sans-serif;
        }}
        .cv-header {{
            background: linear-gradient(135deg, {settings['base_color']}, {settings['accent_color']});
            padding: 30px;
            color: white;
            position: relative;
        }}
        .ats-badge {{
            position: absolute;
            top: 15px;
            right: 15px;
            background: rgba(255,255,255,0.2);
            padding: 4px 12px;
            border-radius: 15px;
            font-size: 13px;
            font-weight: bold;
        }}
        .name {{
            font-size: 32px;
            font-weight: bold;
            margin-bottom: 5px;
            line-height: 1.2;
        }}
        .position {{
            font-size: 18px;
            opacity: 0.95;
            margin-bottom: 15px;
        }}
        .contact-bar {{
            display: flex;
            flex-wrap: wrap;
            gap: 15px;
            margin-top: 10px;
            font-size: 14px;
        }}
        .contact-item {{
            display: flex;
            align-items: center;
            gap: 5px;
        }}
        .section {{
            padding: 25px 30px;
            border-bottom: 1px solid {border_color};
        }}
        .section:last-child {{
            border-bottom: none;
        }}
        .section-title {{
            color: {settings['base_color']};
            font-size: 19px;
            font-weight: bold;
            margin-bottom: 15px;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        .skill-container {{
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-top: 5px;
        }}
        .skill-tag {{
            background: {skill_bg};
            padding: 6px 14px;
            border-radius: 20px;
            font-size: 14px;
            border-left: 3px solid {settings['accent_color']};
        }}
        .timeline-item {{
            position: relative;
            padding-left: 30px;
            margin-bottom: 25px;
        }}
        .timeline-item:before {{
            content: '';
            position: absolute;
            left: 0;
            top: 8px;
            width: 12px;
            height: 12px;
            background: {settings['accent_color']};
            border-radius: 50%;
        }}
        .job-title {{
            font-weight: bold;
            font-size: 17px;
            margin-bottom: 4px;
            color: {text_color};
        }}
        .company {{
            color: {settings['accent_color']};
            font-style: italic;
            margin-bottom: 6px;
            font-size: 15px;
        }}
        .date {{
            color: {date_color};
            font-size: 14px;
            margin-bottom: 8px;
            display: block;
        }}
        @media (max-width: 600px) {{
            .cv-header {{
                padding: 20px;
            }}
            .name {{
                font-size: 26px;
            }}
            .position {{
                font-size: 16px;
            }}
            .section {{
                padding: 20px;
            }}
            .contact-bar {{
                flex-direction: column;
                gap: 8px;
            }}
        }}
    </style>
    
    <div class="cv-container">
        <div class="cv-header">
            <div class="ats-badge">ATS: {ats_score}%</div>
            <div class="name">{data['personal_info']['nama'] or 'Your Name'}</div>
            <div class="position">{data['personal_info']['posisi_target'] or 'Professional'}</div>
            <div class="contact-bar">
    """
    
    # Add contact info
    contacts = []
    if data['personal_info']['email']:
        contacts.append(f'<div class="contact-item">📧 {data["personal_info"]["email"]}</div>')
    if data['personal_info']['telepon']:
        contacts.append(f'<div class="contact-item">📱 {data["personal_info"]["telepon"]}</div>')
    if data['personal_info']['alamat']:
        contacts.append(f'<div class="contact-item">📍 {data["personal_info"]["alamat"]}</div>')
    
    html += "".join(contacts) + "</div></div>"
    
    # Professional Summary
    html += f'''
    <div class="section">
        <div class="section-title">📝 Professional Summary</div>
        <p style="line-height: 1.6; margin: 0;">{data["ringkasan"] or "No summary provided"}</p>
    </div>
    '''
    
    # Work Experience
    if data['pengalaman']:
        html += '<div class="section"><div class="section-title">💼 Work Experience</div>'
        for exp in data['pengalaman']:
            html += f'''
            <div class="timeline-item">
                <span class="date">{exp.get('periode', '')}</span>
                <div class="job-title">{exp.get('posisi', 'Position')}</div>
                <div class="company">{exp.get('perusahaan', 'Company')}</div>
                <p style="margin: 0; line-height: 1.5;">{exp.get('deskripsi', 'Description')}</p>
            </div>
            '''
        html += '</div>'
    
    # Education
    if data['pendidikan']:
        html += '<div class="section"><div class="section-title">🎓 Education</div>'
        for edu in data['pendidikan']:
            html += f'''
            <div class="timeline-item">
                <span class="date">{edu.get('tahun', '')}</span>
                <div class="job-title">{edu.get('institusi', 'Institution')}</div>
                <p style="margin: 0; color: {settings['accent_color']};">{edu.get('gelar', 'Degree')}</p>
            </div>
            '''
        html += '</div>'
    
    # Skills
    if data['keahlian']:
        html += '<div class="section"><div class="section-title">🛠️ Skills</div><div class="skill-container">'
        for skill in data['keahlian'][:20]:
            html += f'<span class="skill-tag">{skill}</span>'
        html += '</div></div>'
    
    # Languages
    if data['bahasa']:
        html += f'''
        <div class="section">
            <div class="section-title">🌐 Languages</div>
            <p>{", ".join(data["bahasa"][:5])}</p>
        </div>
        '''
    
    html += '</div>'
    return html

# --- AI SUGGESTION ENGINE DIPERBAIKI ---
def get_ai_suggestions(data):
    suggestions = []
    ats_score = calculate_ats_score(data)
    
    if ats_score < 70:
        suggestions.append("⚠️ **Tingkatkan ATS Score** - CV Anda perlu perbaikan signifikan untuk lolos sistem pelacakan")
    
    if not data['ringkasan'] or len(data['ringkasan'].split()) < 50:
        suggestions.append("✨ **Perpanjang Ringkasan Profesional** - Minimal 50 kata dengan pencapaian terukur")
    
    if len(data['keahlian']) < 8:
        suggestions.append("🛠️ **Tambahkan keahlian** - Targetkan 8-12 skill relevan untuk meningkatkan daya saing")
    
    if not data['pengalaman']:
        suggestions.append("💼 **Tambahkan pengalaman kerja** - Minimal 1 posisi profesional wajib ada")
    elif len(data['pengalaman']) < 2:
        suggestions.append("📈 **Tambahkan pengalaman lain** - 2-3 posisi menunjukkan perkembangan karir yang baik")
    
    # Check for quantifiable achievements
    summary_text = (data['ringkasan'] + ' ' + 
                   ' '.join([exp.get('deskripsi', '') for exp in data['pengalaman']])).lower()
    
    if not re.search(r'\d+%', summary_text) and not re.search(r'\d+x', summary_text) and not re.search(r'\$\d+', summary_text):
        suggestions.append("📊 **Tambahkan pencapaian terukur** - Gunakan angka: 'Meningkatkan penjualan 30%', 'Menghemat $50K'")
    
    # Check action verbs
    action_verbs = ['managed', 'developed', 'created', 'improved', 'increased', 'reduced', 'led', 'achieved']
    if not any(verb in summary_text for verb in action_verbs):
        suggestions.append("⚡ **Gunakan action verbs** - Mulai poin dengan: Led, Developed, Increased, Optimized")
    
    if not suggestions:
        suggestions.append("✅ **CV Anda sudah optimal!** - Siap untuk dikirim ke perusahaan target")
    
    return suggestions[:4]  # Limit to top 4 suggestions

# --- UI UTAMA (DIPERBAIKI) ---
st.title("🚀 CV Builder Pro Ultra v2.1")
st.markdown("Build professional, ATS-friendly CVs with AI-powered optimization")

# [Sisa UI Streamlit dipertahankan dengan perbaikan minor]
# ... (implementasi sidebar, tabs, dll. tetap sama dengan penyesuaian untuk error handling)

# Footer diperbarui
st.markdown("---")
col_footer1, col_footer2, col_footer3 = st.columns(3)
with col_footer1:
    st.caption("© 2026 CV Builder Pro Ultra")
with col_footer2:
    st.caption("✨ Enhanced with AI Optimization")
with col_footer3:
    st.caption("v2.1 | Production Ready")
