import streamlit as st
import json
from fpdf import FPDF
import io
import zipfile

# --- KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="CV Builder Pro Ultra",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- STATE MANAGEMENT ---
if 'cv_data' not in st.session_state:
    st.session_state.cv_data = {
        'personal_info': {
            'nama': '', 'email': '', 'telepon': '', 'alamat': '',
            'linkedin': '', 'github': '', 'website': '', 'posisi_target': ''
        },
        'ringkasan': '',
        'pengalaman': [],
        'pendidikan': [],
        'keahlian': [],
        'sertifikasi': [], # New
        'proyek': [],      # New
        'bahasa': []       # New
    }

if 'settings' not in st.session_state:
    st.session_state.settings = {
        'template_style': 'modern_sidebar', # modern_sidebar, classic_vertical, minimal
        'font_family': 'Helvetica',
        'base_color': '#2563eb',
        'accent_color': '#1e40af',
        'font_size_body': 10,
        'font_size_header': 24,
        'section_spacing': 5,
        'show_icons': True
    }

# --- DATA TEMPLATES & PRESETS ---
LAYOUTS = {
    'modern_sidebar': {'name': 'Modern Sidebar', 'type': '2_column'},
    'classic_vertical': {'name': 'Classic Professional', 'type': '1_column'},
    'minimal_clean': {'name': 'Minimalist Clean', 'type': '1_column_compact'}
}

FONTS = ['Helvetica', 'Times', 'Courier', 'Arial']

# --- FUNGSI HELPER PDF ---
class PDF(FPDF):
    def header(self):
        pass # Header manual di dalam fungsi generate

    def footer(self):
        self.set_y(-15)
        self.set_font(st.session_state.settings['font_family'], 'I', 8)
        self.set_text_color(128)
        self.cell(0, 10, f"Dibuat dengan CV Builder Pro - Halaman {self.page_no()}", 0, 0, 'C')

def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

# --- GENERATOR PDF UTAMA ---
def generate_pdf_v2(data, settings):
    pdf = PDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    
    font = settings['font_family']
    # Konversi warna
    try:
        r_prim, g_prim, b_prim = hex_to_rgb(settings['base_color'])
        r_sec, g_sec, b_sec = hex_to_rgb(settings['accent_color'])
    except:
        r_prim, g_prim, b_prim = (0, 0, 0)
        r_sec, g_sec, b_sec = (50, 50, 50)

    # --- LAYOUT: MODERN SIDEBAR (2 KOLOM) ---
    if settings['template_style'] == 'modern_sidebar':
        # Sidebar Background
        pdf.set_fill_color(r_prim, g_prim, b_prim)
        pdf.rect(0, 0, 65, 297, 'F')
        
        # --- SIDEBAR CONTENT (KIRI) ---
        pdf.set_text_color(255, 255, 255)
        pdf.set_xy(5, 20)
        
        # Nama & Judul di Sidebar? Opsional, tapi biasanya di atas.
        # Kita taruh Kontak & Skill di Sidebar
        
        # Kontak
        pdf.set_font(font, 'B', 14)
        pdf.cell(55, 10, "KONTAK", ln=True)
        pdf.set_font(font, '', 9)
        
        kontak_list = [
            data['personal_info']['email'],
            data['personal_info']['telepon'],
            data['personal_info']['alamat'],
            data['personal_info']['linkedin'],
            data['personal_info']['website']
        ]
        for k in kontak_list:
            if k:
                pdf.multi_cell(55, 5, k)
                pdf.ln(2)
        
        pdf.ln(10)
        
        # Keahlian (Sidebar)
        if data['keahlian']:
            pdf.set_font(font, 'B', 14)
            pdf.cell(55, 10, "KEAHLIAN", ln=True)
            pdf.set_font(font, '', 9)
            for skill in data['keahlian']:
                pdf.cell(55, 6, f"- {skill}", ln=True)
        
        pdf.ln(10)
        
        # Bahasa (Sidebar)
        if data['bahasa']:
            pdf.set_font(font, 'B', 14)
            pdf.cell(55, 10, "BAHASA", ln=True)
            pdf.set_font(font, '', 9)
            for lang in data['bahasa']:
                pdf.cell(55, 6, f"- {lang}", ln=True)

        # --- MAIN CONTENT (KANAN) ---
        pdf.set_xy(70, 20)
        pdf.set_text_color(r_prim, g_prim, b_prim)
        
        # Header Nama
        pdf.set_font(font, 'B', settings['font_size_header'])
        pdf.multi_cell(0, 10, data['personal_info']['nama'].upper())
        
        if data['personal_info']['posisi_target']:
            pdf.set_font(font, 'B', 14)
            pdf.set_text_color(r_sec, g_sec, b_sec)
            pdf.cell(0, 10, data['personal_info']['posisi_target'], ln=True)
            
        pdf.ln(5)
        
        # Ringkasan
        if data['ringkasan']:
            pdf.set_text_color(0, 0, 0)
            pdf.set_font(font, '', settings['font_size_body'])
            pdf.multi_cell(0, 5, data['ringkasan'])
            pdf.ln(10)

        # Helper function untuk Judul Section Kanan
        def section_title(title):
            pdf.set_font(font, 'B', 14)
            pdf.set_text_color(r_prim, g_prim, b_prim)
            pdf.cell(0, 8, title.upper(), border='B', ln=True)
            pdf.ln(4)

        # Pengalaman
        if data['pengalaman']:
            section_title("Pengalaman Kerja")
            for exp in data['pengalaman']:
                pdf.set_x(70) # Reset margin kiri
                pdf.set_text_color(0, 0, 0)
                pdf.set_font(font, 'B', 11)
                pdf.cell(0, 6, exp['posisi'], ln=True)
                
                pdf.set_x(70)
                pdf.set_font(font, 'I', 10)
                pdf.set_text_color(100)
                pdf.cell(0, 5, f"{exp['perusahaan']} | {exp['periode']}", ln=True)
                
                pdf.set_x(70)
                pdf.set_font(font, '', settings['font_size_body'])
                pdf.set_text_color(0)
                pdf.multi_cell(0, 5, exp['deskripsi'])
                pdf.ln(3)
            pdf.ln(5)

        # Pendidikan
        if data['pendidikan']:
            pdf.set_x(70)
            section_title("Pendidikan")
            for edu in data['pendidikan']:
                pdf.set_x(70)
                pdf.set_font(font, 'B', 11)
                pdf.set_text_color(0)
                pdf.cell(0, 6, edu['gelar'], ln=True)
                
                pdf.set_x(70)
                pdf.set_font(font, 'I', 10)
                pdf.set_text_color(100)
                pdf.cell(0, 5, f"{edu['institusi']} | {edu['tahun']}", ln=True)
                pdf.ln(2)

    # --- LAYOUT: CLASSIC / MINIMAL (1 KOLOM) ---
    else: 
        is_minimal = settings['template_style'] == 'minimal_clean'
        
        # Header Center
        align = 'C' if is_minimal else 'L'
        pdf.set_font(font, 'B', settings['font_size_header'])
        pdf.set_text_color(r_prim, g_prim, b_prim)
        pdf.cell(0, 10, data['personal_info']['nama'].upper(), ln=True, align=align)
        
        if data['personal_info']['posisi_target']:
            pdf.set_font(font, 'B', 14)
            pdf.set_text_color(r_sec, g_sec, b_sec)
            pdf.cell(0, 8, data['personal_info']['posisi_target'], ln=True, align=align)

        # Kontak Bar
        pdf.set_font(font, '', 9)
        pdf.set_text_color(50)
        contacts = []
        if data['personal_info']['email']: contacts.append(data['personal_info']['email'])
        if data['personal_info']['telepon']: contacts.append(data['personal_info']['telepon'])
        if data['personal_info']['linkedin']: contacts.append("LinkedIn")
        if data['personal_info']['alamat']: contacts.append(data['personal_info']['alamat'])
        
        pdf.cell(0, 6, " | ".join(contacts), ln=True, align=align, border='B' if is_minimal else 0)
        pdf.ln(5)

        # Ringkasan
        if data['ringkasan']:
            if not is_minimal:
                pdf.set_font(font, 'B', 12)
                pdf.set_fill_color(r_prim, g_prim, b_prim)
                pdf.set_text_color(255)
                pdf.cell(0, 7, "  RINGKASAN", ln=True, fill=True)
            
            pdf.set_text_color(0)
            pdf.set_font(font, '', settings['font_size_body'])
            pdf.multi_cell(0, 5, data['ringkasan'])
            pdf.ln(5)

        # Helper Section 1 Kolom
        def section_1col(title):
            pdf.ln(3)
            if is_minimal:
                pdf.set_font(font, 'B', 14)
                pdf.set_text_color(r_prim, g_prim, b_prim)
                pdf.cell(0, 8, title.upper(), border='B', ln=True)
            else:
                pdf.set_font(font, 'B', 12)
                pdf.set_fill_color(r_prim, g_prim, b_prim)
                pdf.set_text_color(255)
                pdf.cell(0, 7, f"  {title.upper()}", ln=True, fill=True)
            pdf.ln(2)

        # Pengalaman
        if data['pengalaman']:
            section_1col("Pengalaman Kerja")
            for exp in data['pengalaman']:
                pdf.set_text_color(0)
                pdf.set_font(font, 'B', 11)
                # Layout baris judul: Posisi (Kiri) --- Tanggal (Kanan)
                pdf.cell(130, 6, exp['posisi'])
                pdf.set_font(font, 'B', 10)
                pdf.cell(0, 6, exp['periode'], align='R', ln=True)
                
                pdf.set_font(font, 'I', 10)
                pdf.set_text_color(r_sec, g_sec, b_sec)
                pdf.cell(0, 5, exp['perusahaan'], ln=True)
                
                pdf.set_font(font, '', settings['font_size_body'])
                pdf.set_text_color(0)
                pdf.multi_cell(0, 5, exp['deskripsi'])
                pdf.ln(3)

        # Pendidikan
        if data['pendidikan']:
            section_1col("Pendidikan")
            for edu in data['pendidikan']:
                pdf.set_font(font, 'B', 11)
                pdf.cell(130, 6, edu['institusi'])
                pdf.set_font(font, 'B', 10)
                pdf.cell(0, 6, edu['tahun'], align='R', ln=True)
                
                pdf.set_font(font, '', 10)
                pdf.cell(0, 5, edu['gelar'], ln=True)
                pdf.ln(2)

        # Keahlian (2 kolom grid untuk minimalis)
        if data['keahlian']:
            section_1col("Keahlian")
            pdf.set_font(font, '', 10)
            skills_str = ", ".join(data['keahlian'])
            pdf.multi_cell(0, 5, skills_str)

    # Output
    buffer = io.BytesIO()
    pdf.output(buffer)
    buffer.seek(0)
    return buffer

# --- HTML PREVIEW GENERATOR ---
def get_html_preview(data, settings):
    # CSS dinamis berdasarkan settings
    font_fam = settings['font_family'] if settings['font_family'] != 'Times' else 'Times New Roman'
    bg_color = "#f4f4f9"
    
    # Mapping style ke CSS sederhana
    if settings['template_style'] == 'modern_sidebar':
        layout_css = f"""
            .main-container {{ display: flex; min-height: 1000px; background: white; box-shadow: 0 0 10px rgba(0,0,0,0.1); }}
            .sidebar {{ width: 30%; background-color: {settings['base_color']}; color: white; padding: 20px; }}
            .content {{ width: 70%; padding: 30px; }}
            .sidebar h3 {{ border-bottom: 1px solid rgba(255,255,255,0.3); padding-bottom: 5px; margin-top: 20px; }}
            .name-title {{ color: {settings['base_color']}; font-size: 32px; font-weight: bold; line-height: 1.2; }}
            .job-title {{ color: {settings['accent_color']}; font-size: 18px; margin-bottom: 20px; font-weight: bold; }}
            .section-title {{ color: {settings['base_color']}; border-bottom: 2px solid {settings['base_color']}; margin-top: 25px; margin-bottom: 10px; font-weight: bold; font-size: 18px; }}
        """
    else: # Classic / Minimal
        layout_css = f"""
            .main-container {{ background: white; padding: 40px; max-width: 800px; margin: 0 auto; box-shadow: 0 0 10px rgba(0,0,0,0.1); }}
            .sidebar {{ display: none; }}
            .content {{ width: 100%; }}
            .name-title {{ color: {settings['base_color']}; font-size: 28px; font-weight: bold; text-align: {'center' if settings['template_style'] == 'minimal_clean' else 'left'}; }}
            .contact-line {{ text-align: {'center' if settings['template_style'] == 'minimal_clean' else 'left'}; border-bottom: 1px solid #ddd; padding-bottom: 10px; margin-bottom: 20px; color: #666; font-size: 14px; }}
            .section-title {{ background-color: {settings['base_color'] if settings['template_style'] == 'classic_vertical' else 'white'}; color: {'white' if settings['template_style'] == 'classic_vertical' else settings['base_color']}; padding: 5px 10px; font-weight: bold; margin-top: 20px; border-bottom: {'none' if settings['template_style'] == 'classic_vertical' else '2px solid '+settings['base_color']}; }}
        """

    html = f"""
    <style>
        body {{ font-family: {font_fam}, sans-serif; }}
        {layout_css}
        .exp-item {{ margin-bottom: 15px; }}
        .exp-role {{ font-weight: bold; font-size: 110%; }}
        .exp-company {{ font-style: italic; color: {settings['accent_color']}; }}
        .exp-date {{ float: right; font-size: 0.9em; color: #666; }}
        .skill-tag {{ display: inline-block; background: #eee; padding: 2px 8px; border-radius: 4px; margin: 2px; font-size: 12px; color: #333; }}
        ul {{ padding-left: 20px; }}
    </style>
    <div class="main-container">
        <div class="sidebar">
            <div style="margin-bottom: 20px;">
                {'<div style="font-weight:bold;">KONTAK</div>' if settings['template_style'] == 'modern_sidebar' else ''}
                <div style="font-size: 0.9em; margin-top: 10px;">
                    <div>{data['personal_info']['email']}</div>
                    <div>{data['personal_info']['telepon']}</div>
                    <div>{data['personal_info']['alamat']}</div>
                </div>
            </div>
            
            {'<h3>KEAHLIAN</h3>' if settings['template_style'] == 'modern_sidebar' and data['keahlian'] else ''}
            {''.join([f'<div>• {s}</div>' for s in data['keahlian']]) if settings['template_style'] == 'modern_sidebar' else ''}
            
             {'<h3>BAHASA</h3>' if settings['template_style'] == 'modern_sidebar' and data['bahasa'] else ''}
            {''.join([f'<div>• {s}</div>' for s in data['bahasa']]) if settings['template_style'] == 'modern_sidebar' else ''}
        </div>

        <div class="content">
            <div class="name-title">{data['personal_info']['nama']}</div>
            <div class="job-title" style="text-align: {'center' if settings['template_style'] == 'minimal_clean' else 'left'}">{data['personal_info']['posisi_target']}</div>
            
            {f'<div class="contact-line">{data["personal_info"]["email"]} | {data["personal_info"]["telepon"]} | {data["personal_info"]["alamat"]}</div>' if settings['template_style'] != 'modern_sidebar' else ''}
            
            {f'<div class="section-title">RINGKASAN</div><p>{data["ringkasan"]}</p>' if data['ringkasan'] else ''}
            
            {f'<div class="section-title">PENGALAMAN KERJA</div>' if data['pengalaman'] else ''}
            {''.join([f'<div class="exp-item"><span class="exp-date">{e["periode"]}</span><div class="exp-role">{e["posisi"]}</div><div class="exp-company">{e["perusahaan"]}</div><p>{e["deskripsi"]}</p></div>' for e in data['pengalaman']])}
            
            {f'<div class="section-title">PENDIDIKAN</div>' if data['pendidikan'] else ''}
             {''.join([f'<div class="exp-item"><span class="exp-date">{e["tahun"]}</span><div class="exp-role">{e["institusi"]}</div><div>{e["gelar"]}</div></div>' for e in data['pendidikan']])}
            
            {f'<div class="section-title">KEAHLIAN</div>' if settings['template_style'] != 'modern_sidebar' and data['keahlian'] else ''}
             {''.join([f'<span class="skill-tag">{s}</span>' for s in data['keahlian']]) if settings['template_style'] != 'modern_sidebar' else ''}
        </div>
    </div>
    """
    return html

# --- UI UTAMA ---
st.title("🚀 CV Builder Pro Ultra")
st.markdown("Buat CV standar ATS atau Kreatif dalam hitungan menit.")

# Tab Navigasi Utama
tab_data, tab_design, tab_preview = st.tabs(["📝 Input Data", "🎨 Desain & Template", "👁️ Preview & Download"])

# --- TAB 1: INPUT DATA ---
with tab_data:
    col_info_1, col_info_2 = st.columns(2)
    with col_info_1:
        st.subheader("Informasi Pribadi")
        st.session_state.cv_data['personal_info']['nama'] = st.text_input("Nama Lengkap", st.session_state.cv_data['personal_info']['nama'])
        st.session_state.cv_data['personal_info']['posisi_target'] = st.text_input("Posisi yang Dilamar / Gelar", st.session_state.cv_data['personal_info']['posisi_target'], placeholder="Contoh: Senior Data Scientist")
        st.session_state.cv_data['personal_info']['email'] = st.text_input("Email", st.session_state.cv_data['personal_info']['email'])
    
    with col_info_2:
        st.subheader("Kontak & Sosmed")
        st.session_state.cv_data['personal_info']['telepon'] = st.text_input("No. Telepon", st.session_state.cv_data['personal_info']['telepon'])
        st.session_state.cv_data['personal_info']['linkedin'] = st.text_input("LinkedIn URL", st.session_state.cv_data['personal_info']['linkedin'])
        st.session_state.cv_data['personal_info']['alamat'] = st.text_input("Domisili (Kota, Negara)", st.session_state.cv_data['personal_info']['alamat'])

    st.subheader("Ringkasan Profesional")
    st.session_state.cv_data['ringkasan'] = st.text_area("Deskripsi Diri", st.session_state.cv_data['ringkasan'], height=100)

    with st.expander("💼 Pengalaman Kerja", expanded=False):
        if st.button("➕ Tambah Pengalaman"):
            st.session_state.cv_data['pengalaman'].append({'posisi': '', 'perusahaan': '', 'periode': '', 'deskripsi': ''})
        
        for i, exp in enumerate(st.session_state.cv_data['pengalaman']):
            st.markdown(f"**Pekerjaan #{i+1}**")
            c1, c2, c3 = st.columns([3,3,2])
            exp['posisi'] = c1.text_input(f"Posisi #{i+1}", exp['posisi'])
            exp['perusahaan'] = c2.text_input(f"Perusahaan #{i+1}", exp['perusahaan'])
            exp['periode'] = c3.text_input(f"Periode #{i+1}", exp['periode'])
            exp['deskripsi'] = st.text_area(f"Deskripsi #{i+1}", exp['deskripsi'], height=70)
            if st.button(f"Hapus Pekerjaan #{i+1}", key=f"del_exp_{i}"):
                st.session_state.cv_data['pengalaman'].pop(i)
                st.rerun()
            st.divider()

    with st.expander("🎓 Pendidikan", expanded=False):
        if st.button("➕ Tambah Pendidikan"):
            st.session_state.cv_data['pendidikan'].append({'institusi': '', 'gelar': '', 'tahun': ''})
        
        for i, edu in enumerate(st.session_state.cv_data['pendidikan']):
            c1, c2, c3 = st.columns([3,3,2])
            edu['institusi'] = c1.text_input(f"Institusi #{i+1}", edu['institusi'])
            edu['gelar'] = c2.text_input(f"Gelar/Jurusan #{i+1}", edu['gelar'])
            edu['tahun'] = c3.text_input(f"Tahun Lulus #{i+1}", edu['tahun'])

    with st.expander("🛠️ Keahlian & Bahasa", expanded=False):
        skill_input = st.text_area("Keahlian (Pisahkan dengan koma)", ", ".join(st.session_state.cv_data['keahlian']))
        st.session_state.cv_data['keahlian'] = [s.strip() for s in skill_input.split(',')] if skill_input else []
        
        lang_input = st.text_input("Bahasa (Pisahkan dengan koma)", ", ".join(st.session_state.cv_data['bahasa']))
        st.session_state.cv_data['bahasa'] = [l.strip() for l in lang_input.split(',')] if lang_input else []

# --- TAB 2: DESAIN ---
with tab_design:
    col_d1, col_d2 = st.columns([1, 2])
    
    with col_d1:
        st.subheader("Pilih Layout")
        selected_layout_key = st.radio(
            "Gaya Layout", 
            list(LAYOUTS.keys()),
            format_func=lambda x: LAYOUTS[x]['name']
        )
        st.session_state.settings['template_style'] = selected_layout_key
        
        st.divider()
        st.subheader("Tipografi")
        st.session_state.settings['font_family'] = st.selectbox("Jenis Font", FONTS, index=0)
        st.session_state.settings['font_size_body'] = st.slider("Ukuran Font Body", 8, 12, 10)
    
    with col_d2:
        st.subheader("Palet Warna")
        c1, c2 = st.columns(2)
        with c1:
            st.session_state.settings['base_color'] = st.color_picker("Warna Utama (Header/Sidebar)", st.session_state.settings['base_color'])
        with c2:
            st.session_state.settings['accent_color'] = st.color_picker("Warna Aksen (Subjudul/Detail)", st.session_state.settings['accent_color'])
            
        st.info("💡 **Tips:** Untuk CV formal, gunakan Biru Navy (#1e40af) atau Abu Gelap (#374151). Untuk Kreatif, bebas bereksperimen!")
        
        # Preview Miniatur (Mockup text)
        st.markdown("### Konfigurasi Saat Ini")
        st.write(f"Layout: **{LAYOUTS[selected_layout_key]['name']}**")
        st.write(f"Font: **{st.session_state.settings['font_family']}**")

# --- TAB 3: PREVIEW & DOWNLOAD ---
with tab_preview:
    st.header("Preview Hasil")
    
    if not st.session_state.cv_data['personal_info']['nama']:
        st.warning("⚠️ Silakan isi Nama Lengkap di tab 'Input Data' untuk melihat preview.")
    else:
        # Generate HTML Preview
        html_content = get_html_preview(st.session_state.cv_data, st.session_state.settings)
        st.components.v1.html(html_content, height=800, scrolling=True)
        
        st.divider()
        col_act1, col_act2 = st.columns(2)
        
        with col_act1:
            st.subheader("Siap Mengunduh?")
            # Generate PDF
            pdf_file = generate_pdf_v2(st.session_state.cv_data, st.session_state.settings)
            
            st.download_button(
                label="📥 DOWNLOAD PDF (High Quality)",
                data=pdf_file,
                file_name=f"CV_{st.session_state.cv_data['personal_info']['nama'].replace(' ', '_')}.pdf",
                mime="application/pdf",
                type="primary",
                use_container_width=True
            )
            
        with col_act2:
            st.subheader("Backup Data")
            json_str = json.dumps(st.session_state.cv_data, indent=2)
            st.download_button(
                label="💾 Simpan Data CV (JSON)",
                data=json_str,
                file_name="my_cv_data.json",
                mime="application/json",
                use_container_width=True
            )

# Footer
st.markdown("---")
st.caption("© 2024 CV Builder Pro Ultra. Dibangun dengan Streamlit & FPDF.")
