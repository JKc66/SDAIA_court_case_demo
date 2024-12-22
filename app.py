import streamlit as st
import json
import base64

# Configure page settings
st.set_page_config(layout="wide")

# Custom CSS with fixes
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Kufi+Arabic:wght@400;700&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=Amiri&family=Scheherazade+New:wght@700&display=swap');

    /* Global RTL settings */
    body {
        direction: rtl;
        text-align: right;
        font-family: 'Noto Kufi Arabic', sans-serif;
    }
    
    /* Fixed header layout */
    .header-container {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 0 20px;
        margin: 0;
        width: 100%;
    }
    
    /* Logo styling */
    .logo-container {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 30px;  /* Increased space between logos */
    }
    
    .logo-container.left-logos,
    .logo-container.right-logos {
        flex: 0 0 450px;  /* Increased width to accommodate larger logos */
        display: flex;
        align-items: center;
        justify-content: space-between;  /* Distribute space between logos */
    }
    
    /* Reset base image styles */
    .logo-container img {
        height: auto;
        width: auto;
        object-fit: contain;
    }
    
    /* Specific logo sizes */
    .logo-container.left-logos img:nth-child(1) {
        width: 260px; /* Najiz logo */
    }
    
    .logo-container.left-logos img:nth-child(2) {
        width: 230px; /* SDAIA logo */
    }
    
    .logo-container.right-logos img:nth-child(1) {
        width: 200px; /* Justice logo */
    }
    
    .logo-container.right-logos img:nth-child(2) {
        width: 250px; /* Gov logo */
    }
    
    /* Ensure the title stays centered */
    .app-title {
        flex: 1;
        text-align: center;
        padding: 0;
        margin: 0 auto;
        position: relative;
        width: 200px;
        height: 200px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        transition: transform 0.3s ease;
    }
    
    .app-title:hover {
        transform: scale(1.05);
    }
    
    .app-title::before {
        content: '';
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        width: 180px;
        height: 180px;
        background: radial-gradient(circle, 
            rgba(219,234,254,0.2) 0%,
            rgba(219,234,254,0.1) 70%,
            rgba(219,234,254,0) 100%);
        border-radius: 50%;
        z-index: 0;
        transition: all 0.3s ease;
    }
    
    .app-title:hover::before {
        background: radial-gradient(circle, 
            rgba(219,234,254,0.3) 0%,
            rgba(219,234,254,0.2) 70%,
            rgba(219,234,254,0) 100%);
        width: 190px;
        height: 190px;
    }
    
    .app-title h1 {
        font-family: 'Scheherazade New', serif;
        font-size: 5em;
        font-weight: 700;
        margin: 0;
        position: relative;
        z-index: 1;
        background: linear-gradient(120deg, 
            #1a365d 0%, 
            #3b82f6 50%,
            #1a365d 100%);
        background-size: 200% auto;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        transition: all 0.3s ease;
    }
    
    .app-title:hover h1 {
        background-position: right center;
    }
    
    .app-title p {
        font-family: 'Noto Kufi Arabic', sans-serif;
        font-size: 1em;
        color: #4a5568;
        margin: 5px 0 0;
        position: relative;
        z-index: 1;
        transition: all 0.3s ease;
    }
    
    .app-title:hover p {
        color: #2d3748;
    }
    
    /* Content section */
    .content-section {
        margin-top: 1rem;
    }
    
    /* Align text area and results */
    .stTextArea {
        margin-top: -1rem;
    }
    
    .results-section {
        margin-top: 0.5rem;
        background-color: #f8fafc;
        border-radius: 10px;
        padding: 1.5rem;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
    }
    
    /* Centered title styling */
    .app-title {
        flex: 1;
        text-align: center;
        padding: 0;
        margin: 0 auto;
    }
    
    .app-title h1 {
        font-family: 'Scheherazade New', serif;
        font-size: 6em;
        font-weight: 700;
        margin: 0;
        letter-spacing: 2px;
        position: relative;
        background: linear-gradient(120deg, 
            #1a365d 0%, 
            #3b82f6 25%,
            #60a5fa 50%,
            #3b82f6 75%,
            #1a365d 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        animation: shine 3s linear infinite;
        text-shadow: 
            2px 2px 4px rgba(0, 0, 0, 0.1),
            -2px 2px 4px rgba(255, 255, 255, 0.1);
    }
    
    .app-title h1::after {
        content: "نـاظـر";
        position: absolute;
        top: 2px;
        left: 0;
        right: 0;
        z-index: -1;
        background: linear-gradient(120deg, #1e40af, #3b82f6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        opacity: 0.4;
    }
    
    @keyframes shine {
        0% {
            background-position: -200% center;
        }
        100% {
            background-position: 200% center;
        }
    }
    
    .app-title p {
        font-family: 'Noto Kufi Arabic', sans-serif;
        font-size: 1.2em;
        color: #4a5568;
        margin: 5px 0 0;
        text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.1);
    }
    
    /* Main container */
    .main-container {
        padding: 5px 10px;
        max-width: 1200px;
        margin: 0 auto;
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(135deg, #ef4444 0%, #3b82f6 100%);
        color: white;
        font-family: 'Noto Kufi Arabic', sans-serif;
        font-weight: 600;
        padding: 0.5rem 2rem;
        border-radius: 8px;
        border: none;
        transition: all 0.3s ease;
        width: 100%;
        position: relative;
        overflow: hidden;
    }

    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
        background: linear-gradient(135deg, #dc2626 0%, #2563eb 100%);
    }

    .stButton > button:active {
        transform: translateY(0);
        box-shadow: 0 2px 8px rgba(59, 130, 246, 0.2);
    }

    /* Content section headers */
    .content-section h2 {
        font-family: 'Noto Kufi Arabic', sans-serif !important;
        font-weight: 700;
        color: #1f2937;
        margin-bottom: 1rem;
    }
    
    /* Text area styling */
    .stTextArea textarea {
        direction: rtl;
        text-align: right;
        margin-bottom: 0;
        font-family: 'Amiri', serif !important;
        font-size: 1.2em !important;
        line-height: 1.6 !important;
        padding: 1rem !important;
    }

    /* Add specific styling for the text area placeholder */
    .stTextArea textarea::placeholder {
        font-family: 'Amiri', serif !important;
        font-size: 1.2em !important;
        color: #6b7280 !important;
    }
    
    /* Remove spacing */
    .block-container {
        padding-top: 2rem;
        margin-top: 0;
    }
    
    .main .block-container {
        padding: 1rem 4rem;
        margin-top: 0;
    }
    
    /* Minimal header */
    header {
        padding: 1rem !important;
        margin: 0 !important;
    }
    
    /* Entry container */
    .entry-container {
        border: 1px solid #e5e7eb;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        background-color: #ffffff;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
        transition: all 0.3s ease;
    }
    
    .entry-container:hover {
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        transform: translateY(-2px);
    }
    
    .case-text {
        background-color: #f8fafc;
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 1rem;
        border: 1px solid #e5e7eb;
        line-height: 1.6;
    }
    
    /* Results Card Container */
    .results-card {
        background: white;
        border-radius: 16px;
        margin-top: .7rem;
        padding: 1.5rem;
        box-shadow: 0 7px 10px rgba(0, 0, 0, 0.1);
        margin-bottom: 1rem;
    }
    
    /* Classification Item */
    .classification-item {
        padding: 1rem;
        border-radius: 12px;
        margin: 0.75rem 0;
        position: relative;
        overflow: hidden;
        transition: all 0.3s ease;
        border: 1px solid red;
    }
    
    .classification-item:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
    }
    
    /* Main Classification */
    .main-classification {
        background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
        border: 1px solid #fbbf24;
    }
    
    /* Sub Classification */
    .sub-classification {
        background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%);
        border: 1px solid #60a5fa;
    }
    
    /* Case Type */
    .case-type {
        background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%);
        border: 1px solid #34d399;
    }
    
    /* Classification Label */
    .classification-label {
        font-family: 'Noto Kufi Arabic', sans-serif;
        font-weight: 700;
        color: #1f2937;
        margin-bottom: 0.5rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    /* Classification Value */
    .classification-value {
        font-family: 'Noto Kufi Arabic', sans-serif;
        color: #374151;
        font-size: 1.1em;
    }
    
    /* Icons */
    .classification-icon {
        width: 24px;
        height: 24px;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        background: rgba(255, 255, 255, 0.5);
        border-radius: 50%;
        margin-left: 0.5rem;
    }

    /* Delete button container */
    .delete-button-container {
        display: flex;
        align-items: start;
        padding-top: 10px;
    }
    
    .delete-button-container .stButton button {
        padding: 0 10px;
        height: 40px;
        line-height: 40px;
        background-color: transparent;
        color: #dc2626;
    }
</style>
""", unsafe_allow_html=True)

def load_history():
    try:
        with open('history.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_history(history):
    with open('history.json', 'w', encoding='utf-8') as f:
        json.dump(history, f, ensure_ascii=False, indent=4)

def get_base64_logo(file_path):
    with open(file_path, "rb") as f:
        data = f.read()
        return base64.b64encode(data).decode()

def main():
    # Initialize session state
    if "history" not in st.session_state:
        st.session_state.history = load_history()
    if "case_submitted" not in st.session_state:
        st.session_state.case_submitted = False
    if "clear_input" not in st.session_state:
        st.session_state.clear_input = False

    # Load all logos
    najiz_logo = get_base64_logo(r"assets\logo_najiz.svg")
    justice_logo = get_base64_logo(r"assets\justice.svg")
    sdaia_logo = get_base64_logo(r"assets\SDAIA.svg")
    gov_logo = get_base64_logo(r"assets\DigitaGov.png.svg")

    # Updated header structure with all logos
    st.markdown(f'''
        <div class="header-container">
            <div class="logo-container left-logos">
                <img src="data:image/svg+xml;base64,{najiz_logo}" alt="Najiz Logo">
                <img src="data:image/svg+xml;base64,{sdaia_logo}" alt="SDAIA Logo">
            </div>
            <div class="app-title">
                <h1>نـاظـر</h1>
                <p>نظام تصنيف القضايا الذكي</p>
            </div>
            <div class="logo-container right-logos">
                <img src="data:image/svg+xml;base64,{justice_logo}" alt="Justice Logo">
                <img src="data:image/svg+xml;base64,{gov_logo}" alt="Digital Gov Logo">
            </div>
        </div>
    ''', unsafe_allow_html=True)

    col_input, col_results = st.columns([1, 1])

    with col_input:
        st.markdown('<div class="content-section">', unsafe_allow_html=True)
        st.markdown("## 📝 البحث ")

        user_input = st.text_area(
            label=" ",
            height=300,
            key="rtl_input",
            placeholder="الرجاء إدخال نص البحث هنا للتصنيف...",
            disabled=st.session_state.case_submitted,
            value=" " if st.session_state.clear_input else None
        )
        
        if st.session_state.clear_input:
            st.session_state.clear_input = False

        col1, col2 = st.columns(2)
        with col1:
            submit_clicked = st.button("⚖️ تصنيف البحث", type="primary", disabled=st.session_state.case_submitted)
            if submit_clicked and user_input and not st.session_state.case_submitted:
                st.session_state.case_submitted = True
                m_calss_example = "أحوال شخصية"
                s_calss_example = "دعاوى الولاية"
                case_type_example = "حجر أو رفعه"

                new_entry = {
                    "input": user_input,
                    "main_classification": m_calss_example,  # Store raw value
                    "sub_classification": s_calss_example,   # Store raw value
                    "case_type": case_type_example,         # Store raw value
                    "id": len(st.session_state.history)
                }
                st.session_state.history.append(new_entry)
                save_history(st.session_state.history)
                st.rerun()

        with col2:
            if st.button("🔄 حالة جديدة", type="secondary"):
                st.session_state.case_submitted = False
                st.session_state.clear_input = True
                st.rerun()

    with col_results:
        st.markdown('<div class="content-section">', unsafe_allow_html=True)
        st.markdown("## ⚡ نتائج التصنيف")
        
        if st.session_state.case_submitted and st.session_state.history:
            latest_entry = st.session_state.history[-1]
            
            # Main Classification
            st.markdown(f"""
                <div class="classification-item main-classification">
                    <div class="classification-label">
                        <span class="classification-icon">📊</span>
                        التصنيف الرئيسي
                    </div>
                    <div class="classification-value">{latest_entry["main_classification"]}</div>
                </div>
            """, unsafe_allow_html=True)
            
            # Sub Classification
            st.markdown(f"""
                <div class="classification-item sub-classification">
                    <div class="classification-label">
                        <span class="classification-icon">🔍</span>
                        التصنيف الفرعي
                    </div>
                    <div class="classification-value">{latest_entry["sub_classification"]}</div>
                </div>
            """, unsafe_allow_html=True)
            
            # Case Type
            st.markdown(f"""
                <div class="classification-item case-type">
                    <div class="classification-label">
                        <span class="classification-icon">⚖️</span>
                        نوع الدعوى
                    </div>
                    <div class="classification-value">{latest_entry["case_type"]}</div>
                </div>
            """, unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.markdown("""
                <div class="results-card" style="text-align: center; padding: 3rem;">
                    <img src="https://img.icons8.com/fluency/96/000000/search.png" style="width: 64px; margin-bottom: 1rem;">
                    <h3 style="color: #6b7280; font-family: 'Noto Kufi Arabic', sans-serif;">أدخل نص البحث للحصول على التصنيف</h3>
                </div>
            """, unsafe_allow_html=True)

    with st.expander("📜 **سجل التصنيفات السابقة**"):
        if not st.session_state.history:
            st.info("لا يوجد سجل تصنيفات سابقة")
        else:
            for i, entry in enumerate(st.session_state.history):
                if i > 0:  # Add horizontal line before each entry except the first one
                    st.markdown("""
                        <style>
                            .custom-divider {
                                display: flex;
                                align-items: center;
                                margin: 20px 0; /* Adjust spacing */
                            }
                            .custom-divider::before, .custom-divider::after {
                                content: '';
                                flex: 1;
                                border-bottom: 1px solid #ddd;
                                margin: 0 10px;
                            }

                            .custom-divider span {
                                font-family: 'Amiri', serif;
                                font-size: 1.2em;
                                color: #888;
                                white-space: nowrap;
                            }
                        </style>
                        <div class="custom-divider">
                            <span>•••</span>
                        </div>
                    """, unsafe_allow_html=True)

                    
                with st.container():
                    col_content, col_delete = st.columns([0.95, 0.05])
                    
                    with col_content:
                        st.markdown(f"""
                        <style>
                            @import url('https://fonts.googleapis.com/css2?family=Amiri&display=swap');

                            .case-text {{
                                background: linear-gradient(135deg, #ffffff, #f9f9f9); 
                                border: 1px solid #ddd; 
                                border-radius: 10px; 
                                padding: 15px; 
                                margin-bottom: 15px;
                                font-family: 'Amiri', serif;
                                color: #444;
                                font-size: 18px;
                                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                                transition: transform 0.2s ease, box-shadow 0.2s ease;
                            }}
                            .case-text:hover {{
                                transform: scale(1.02);
                                box-shadow: 0 6px 10px rgba(0, 0, 0, 0.15);
                            }}
                            .case-text strong {{
                                color: #333;
                                font-size: 20px;
                            }}
                        </style>
                        <div class="case-text">
                            <strong>البحث:</strong> {entry["input"]}
                        </div>
                        """, 
                        unsafe_allow_html=True)


                        
                    with col_delete:
                        st.markdown('<div class="delete-button-container">', unsafe_allow_html=True)
                        if st.button("🗑️", key=f"delete_{i}"):
                            st.session_state.history.pop(i)
                            save_history(st.session_state.history)
                            st.rerun()
                        st.markdown('</div>', unsafe_allow_html=True)

                    # Continue with the classifications...
                    st.markdown(f"""
                        <div class="classification-item main-classification">
                            <div class="classification-label">
                                <span class="classification-icon">📊</span>
                                التصنيف الرئيسي
                            </div>
                            <div class="classification-value">{entry["main_classification"]}</div>
                        </div>
                    """, unsafe_allow_html=True)
                        
                    # Sub Classification
                    st.markdown(f"""
                        <div class="classification-item sub-classification">
                            <div class="classification-label">
                                <span class="classification-icon">🔍</span>
                                التصنيف الفرعي
                            </div>
                            <div class="classification-value">{entry["sub_classification"]}</div>
                        </div>
                    """, unsafe_allow_html=True)
                        
                    # Case Type
                    st.markdown(f"""
                        <div class="classification-item case-type">
                            <div class="classification-label">
                                <span class="classification-icon">⚖️</span>
                                نوع الدعوى
                            </div>
                            <div class="classification-value">{entry["case_type"]}</div>
                        </div>
                    """, unsafe_allow_html=True)

            if st.button("مسح السجل بالكامل", type="secondary"):
                st.session_state.history = []
                save_history([])
                st.rerun()

if __name__ == "__main__":
    main()