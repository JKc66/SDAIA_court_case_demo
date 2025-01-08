import streamlit as st
import json
import base64
from pathlib import Path
import time
import os
import json
import time
import google.generativeai as genai
from random import randint
import datetime

NUM_KEYS = 5
#------------------------------------------------------------------------------
# PAGE CONFIGURATION
#------------------------------------------------------------------------------
st.set_page_config(
    layout="wide",
    page_title="ناظر",
    page_icon="⚖️",
    menu_items={'Get Help': None, 'Report a bug': None, 'About': None}
)

#------------------------------------------------------------------------------
# STYLES AND SCRIPTS
#------------------------------------------------------------------------------
def load_css():
    """Load external CSS file"""
    css_file = Path(__file__).parent / "static" / "style.css"
    with open(css_file, 'r', encoding='utf-8') as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

def load_js():
    """Load external JavaScript file"""
    js_file = Path(__file__).parent / "static" / "script.js"
    with open(js_file, 'r', encoding='utf-8') as f:
        st.markdown(f'<script>{f.read()}</script>', unsafe_allow_html=True)

# Load CSS and JavaScript
load_css()
load_js()

#------------------------------------------------------------------------------
# UTILITY FUNCTIONS
#------------------------------------------------------------------------------
def load_history():
    """Load classification history from JSON file"""
    try:
        history_file = Path("history.json")
        if not history_file.exists():
            return []
        with open(history_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_history(history):
    """Save classification history to JSON file"""
    try:
        with open('history.json', 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=4)
    except Exception as e:
        st.error(f"Failed to save history: {e}")

def get_base64_logo(filename):
    """Load and encode logo files to base64"""
    try:
        current_dir = Path(__file__).parent
        file_path = current_dir / "static" / filename
        with open(file_path, "rb") as f:
            data = f.read()
            return base64.b64encode(data).decode()
    except Exception as e:
        st.warning(f"Could not load logo: {filename}")
        return ""

#------------------------------------------------------------------------------
# Gemini Communication
#------------------------------------------------------------------------------

def upload_to_gemini(path, mime_type=None):
    """Uploads the given file to Gemini.

    See https://ai.google.dev/gemini-api/docs/prompting_with_media
    """
    file = genai.upload_file(path, mime_type=mime_type)
    print(f"Uploaded file '{file.display_name}' as: {file.uri}")
    return file

def wait_for_files_active(files):
    """Waits for the given files to be active.

    Some files uploaded to the Gemini API need to be processed before they can be
    used as prompt inputs. The status can be seen by querying the file's "state"
    field.

    This implementation uses a simple blocking polling loop. Production code
    should probably employ a more sophisticated approach.
    """
    print("Waiting for file processing...")
    for name in (file.name for file in files):
        file = genai.get_file(name)
        while file.state.name == "PROCESSING":
            print(".", end="", flush=True)
        time.sleep(10)
        file = genai.get_file(name)
        if file.state.name != "ACTIVE":
            raise Exception(f"File {file.name} failed to process")
    print("...all files ready")
    print()

@st.cache_data(ttl=datetime.timedelta(days=2))
def initialize_gemini(key_id):
    genai.configure(api_key=os.environ[f"GEMINI_API_KEY_{key_id}"])
    # Create the model
    generation_config = {
    "temperature": 0,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 8192,
    "response_mime_type": "application/json",
    }

    model = genai.GenerativeModel(
    model_name="gemini-2.0-flash-exp",
    generation_config=generation_config,
    system_instruction="according to the categories mentinoed. which category does the provided text fit in the most. what is the most appropriate subcategory? and what is the most appropriate type? the output should be in arabic. make the output in json format. the keys are: category, subcategory, type, explanation.",
    )

    # TODO Make these files available on the local file system
    # You may need to update the file paths
    files = [
    upload_to_gemini("details.pdf", mime_type="application/pdf"),
    ]

    # Some files have a processing delay. Wait for them to be ready.
    wait_for_files_active(files)

    chat_session = model.start_chat(
    history=[
        {
        "role": "user",
        "parts": [
            files[0],
        ],
        },
    ]
    )
    return chat_session

#response = chat_session.send_message("INSERT_INPUT_HERE")
    

#------------------------------------------------------------------------------
# MAIN APPLICATION
#------------------------------------------------------------------------------
def main():
    # Add new session state for delete operations
    if "delete_clicked" not in st.session_state:
        st.session_state.delete_clicked = False
    if "delete_index" not in st.session_state:
        st.session_state.delete_index = None
    if "key_id" not in st.session_state:
        st.session_state.key_id = randint(1, NUM_KEYS)
        
    # Initialize session state
    if "history" not in st.session_state:
        st.session_state.history = load_history()
    if "case_submitted" not in st.session_state:
        st.session_state.case_submitted = False
    if "clear_input" not in st.session_state:
        st.session_state.clear_input = False
    if "loading" not in st.session_state:
        st.session_state.loading = False
    if "current_results" not in st.session_state:
        st.session_state.current_results = None
    if "progress" not in st.session_state:
        st.session_state.progress = None

    # Load logos
    logos = {
        'najiz': get_base64_logo("logo_najiz.svg"),
        'justice': get_base64_logo("justice.svg"),
        'sdaia': get_base64_logo("SDAIA.svg"),
        'gov': get_base64_logo("DigitaGov.png.svg")
    }

    notification_icon = "✅"

    # Render header
    st.markdown(f'''
        <div class="header-container">
            <div class="logo-container left-logos">
                <img src="data:image/svg+xml;base64,{logos['najiz']}" alt="Najiz Logo">
                <img src="data:image/svg+xml;base64,{logos['sdaia']}" alt="SDAIA Logo">
            </div>
            <div class="app-title">
                <h1>نـاظـر</h1>
                <p>نظام تصنيف القضايا الذكي</p>
            </div>
            <div class="logo-container right-logos">
                <img src="data:image/svg+xml;base64,{logos['justice']}" alt="Justice Logo">
                <img src="data:image/svg+xml;base64,{logos['gov']}" alt="Digital Gov Logo">
            </div>
        </div>
    ''', unsafe_allow_html=True)

    # Create main layout
    col_input, col_results = st.columns([1, 1])

    # Input section
    with col_input:
        st.markdown('<div class="content-section">', unsafe_allow_html=True)
        st.markdown("## 📝 نص الدعوى ")
        
        if "chat_session" in st.session_state:
            user_input = st.text_area(
                label=" ",
                height=300,
                key="rtl_input",
                placeholder="الرجاء إدخال النص هنا للتصنيف...",
                disabled=st.session_state.case_submitted,
                value="" if st.session_state.clear_input else None
            )
        else:
            st.markdown("""
                <div class="loading-message">
                    <h3>يتم تهيئة النظام...</h3>
                </div>
            """, unsafe_allow_html=True)
            st.session_state.loading = True
            st.session_state.chat_session = initialize_gemini(st.session_state.key_id)
            st.session_state.loading = False
            
        if st.session_state.clear_input:
            st.session_state.clear_input = False

        col1, col2 = st.columns(2)
        with col1:
            if st.button("⚖️ تصنيف الدعوى", type="primary", disabled=st.session_state.case_submitted):
                if user_input and user_input.strip():  # Check if input is not empty
                    st.session_state.loading = True
                    st.session_state.current_results = None  # Clear current results while loading

        with col2:
            def handle_new_case():
                st.session_state.case_submitted = False
                st.session_state.clear_input = True
                st.session_state.current_results = None
                st.session_state.loading = False
                if "rtl_input" in st.session_state:
                    del st.session_state.rtl_input  # Clear the input state completely

            if st.button("🔄 حالة جديدة", type="secondary", on_click=handle_new_case):
                pass

    # Results section
    with col_results:
        st.markdown('<div class="content-section">', unsafe_allow_html=True)
        st.markdown("## ⚡ نتائج التصنيف")
        
        # Show progress bar when loading
        if st.session_state.loading:
            st.markdown("""
                <div class="loading-message">
                    <h3>جاري تحليل وتصنيف الدعوى...</h3>
                </div>
            """, unsafe_allow_html=True)
            
            #progress_bar = st.progress(0)
            print("Sending message to Gemini...")
            response = st.session_state.chat_session.send_message(user_input)
            try:
                data = json.loads(response.text)
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON: {e}")
                data = False
            # for i in range(100):
            #     time.sleep(0.01)
            #     progress_bar.progress(i + 1)
            
            # After progress completes
            if data == False:
                m_calss_example = "-"
                s_calss_example = "-"
                case_type_example = "-"
            else:
                m_calss_example = data['category']
                s_calss_example = data['subcategory']
                case_type_example = data['type']

            new_entry = {
                "input": user_input,
                "main_classification": m_calss_example,
                "sub_classification": s_calss_example,
                "case_type": case_type_example,
                "id": len(st.session_state.history)
            }
            
            st.session_state.current_results = new_entry
            st.session_state.history.append(new_entry)
            save_history(st.session_state.history)
            st.session_state.case_submitted = True
            st.session_state.loading = False
            st.rerun()  # Refresh to show results

        elif st.session_state.current_results:
            latest_entry = st.session_state.current_results
            
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
                <div class="results-card empty-results-card">
                    <img src="https://img.icons8.com/fluency/96/000000/search.png">
                    <h3>أدخل نص الدعوى للحصول على التصنيف</h3>
                </div>
            """, unsafe_allow_html=True)

    # History section
    with st.expander("📜 **سجل التصنيفات السابقة**"):
        if not st.session_state.history:
            st.info("لا يوجد سجل تصنيفات سابقة")
        else:
            def handle_delete(index):
                st.session_state.delete_clicked = True
                st.session_state.delete_index = index
                st.session_state.history.pop(index)
                save_history(st.session_state.history)
                st.toast("تم حذف العنصر بنجاح", icon=notification_icon)

            # Reverse the history list for display
            for i, entry in enumerate(reversed(st.session_state.history)):
                real_index = len(st.session_state.history) - 1 - i

                # Show divider
                if i > 0:
                    st.markdown("""
                        <div class="custom-divider">
                            <span>•••</span>
                        </div>
                    """, unsafe_allow_html=True)

                with st.container():
                    col_content, col_delete = st.columns([0.95, 0.05])
                    
                    with col_content:
                        st.markdown(f"""
                        <div class="case-text">
                            <strong>البحث:</strong> {entry["input"]}
                        </div>
                        """, 
                        unsafe_allow_html=True)


                        
                    with col_delete:
                        st.markdown('<div class="delete-button-container">', unsafe_allow_html=True)
                        if st.button("🗑️", key=f"delete_{real_index}", on_click=handle_delete, args=(real_index,)):
                            pass
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

            # Clear all history button
            def handle_clear_all():
                st.session_state.history = []
                st.session_state.current_results = None
                save_history([])
                st.toast("تم مسح السجل بالكامل", icon=notification_icon)

            if st.button("مسح السجل بالكامل", type="secondary", on_click=handle_clear_all):
                pass

if __name__ == "__main__":
    main()