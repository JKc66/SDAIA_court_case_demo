import streamlit as st
import json
import base64
from pathlib import Path
import time
import os
import google.generativeai as genai
from random import randint
import datetime
import pandas as pd
import io
import openpyxl

NUM_KEYS = 1
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

# Load CSS and JavaScript
load_css()

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
    """Uploads the given file to Gemini."""
    try:
        # Resolve the file path relative to the app directory
        file_path = Path(__file__).parent / path
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        file = genai.upload_file(str(file_path), mime_type=mime_type)
        print(f"Uploaded file '{file.display_name}' as: {file.uri}")
        return file
    except Exception as e:
        st.error(f"Failed to upload file: {e}")
        return None

def wait_for_files_active(files):
    """Waits for the given files to be active."""
    print("Waiting for file processing...")
    try:
        for file in files:
            if file is None:
                raise Exception("Invalid file object")

            name = file.name
            file = genai.get_file(name)
            while file.state.name == "PROCESSING":
                print(".", end="", flush=True)
                time.sleep(10)
                file = genai.get_file(name)
            if file.state.name != "ACTIVE":
                raise Exception(f"File {file.name} failed to process")
        print("...all files ready")
        print()
    except Exception as e:
        st.error(f"File processing failed: {e}")
        return False
    return True

@st.cache_resource(ttl=datetime.timedelta(days=2), show_spinner=False)
def initialize_gemini(key_id):
    try:
        # Verify if the API key exists
        api_key = os.environ.get(f"GEMINI_API_KEY_{key_id}")
        if not api_key:
            st.error(f"API key {key_id} not found. Please check your configuration.")
            return None

        genai.configure(api_key=api_key)

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
            system_instruction=(
                "according to the categories mentinoed. which category does the provided text fit in the most? "
                "what is the most appropriate subcategory? and what is the most appropriate type? "
                "you must use a category, subcategory, and type from the file only, choose from them what fits the case the most. "
                "the output should be in arabic. make the a json object. "
                "the keys are: category, subcategory, type, explanation. "
                "if none of the types fit the case at all, return 'لا يوجد' for the type."
            )
        )

        # Upload and process the categories file
        files = [
            upload_to_gemini(Path("classes") / "Classes.txt", mime_type="text/plain"),
        ]

        # Check if file upload was successful
        if None in files:
            raise Exception("Failed to upload required files")

        # Wait for files to be processed
        if not wait_for_files_active(files):
            raise Exception("File processing failed")

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
    except Exception as e:
        st.error(f"Failed to initialize Gemini: {e}")
        return None

#------------------------------------------------------------------------------
# MAIN APPLICATION
#------------------------------------------------------------------------------
def main():
    # Add new session state for delete operations
    if "delete_triggered" not in st.session_state:
        st.session_state.delete_triggered = False
    if "clear_triggered" not in st.session_state:
        st.session_state.clear_triggered = False
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
    if "loading" not in st.session_state:
        st.session_state.loading = False
    if "current_results" not in st.session_state:
        st.session_state.current_results = None
    if "progress" not in st.session_state:
        st.session_state.progress = None

    # Load logos
    logos = {
        'Injaz': get_base64_logo("logoH.png"),
        'justice': get_base64_logo("justice.svg"),
        'sdaia': get_base64_logo("SDAIA.svg"),
        'gov': get_base64_logo("DigitaGov.png.svg"),
        'main': get_base64_logo("LOGO.svg")
    }

    notification_icon = "✅"

    # Render header
    st.markdown(f'''
        <div class="header-container">
            <div class="logo-container left-logos">
                <img src="data:image/png;base64,{logos['Injaz']}" alt="Injaz Logo">
                <img src="data:image/svg+xml;base64,{logos['sdaia']}" alt="SDAIA Logo">
            </div>
            <div class="app-title">
                <img src="data:image/svg+xml;base64,{logos['main']}" alt="Main Logo" class="main-logo">
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
                disabled=st.session_state.case_submitted
            )
        else:
            st.markdown("""
                <div class="loading-message">
                    <h3>يتم تهيئة النظام...</h3>
                </div>
            """, unsafe_allow_html=True)
            st.session_state.loading = True

            # Try to initialize with current key
            initialization = initialize_gemini(st.session_state.key_id)

            # If initialization fails, try other keys
            if initialization is None:
                for i in range(1, NUM_KEYS + 1):
                    if i != st.session_state.key_id:
                        st.session_state.key_id = i
                        initialization = initialize_gemini(i)
                        if initialization is not None:
                            break

                if initialization is None:
                    st.error("Failed to initialize the system. Please contact support.")
                    st.session_state.loading = False
                    return

            st.session_state.chat_session = initialization
            st.session_state.loading = False
            st.rerun()

        col1, col2 = st.columns(2)
        with col1:
            if st.button("⚖️ تصنيف الدعوى", type="primary", disabled=st.session_state.case_submitted):
                if user_input and user_input.strip():
                    st.session_state.loading = True
                    st.session_state.current_results = None

        with col2:
            def handle_new_case():
                st.session_state.case_submitted = False
                st.session_state.current_results = None
                st.session_state.loading = False
                if "rtl_input" in st.session_state:
                    st.session_state.rtl_input = ""  # Just clear the input value instead of deleting the key

            if st.button("🔄 حالة جديدة", type="secondary", on_click=handle_new_case):
                pass

    # Results section
    with col_results:
        st.markdown('<div class="content-section">', unsafe_allow_html=True)
        st.markdown("## ⚡ نتائج التصنيف")

        if st.session_state.loading:
            st.markdown("""
                <div class="custom-spinner-container">
                    <div class="custom-spinner"></div>
                    <div class="spinner-text">جاري تحليل وتصنيف الدعوى...</div>
                </div>
            """, unsafe_allow_html=True)

            with st.spinner(''):
                print("Sending message to Gemini...")
                start_time = time.time()  # Start timing
                response = st.session_state.chat_session.send_message(user_input)
                end_time = time.time()  # End timing
                duration = end_time - start_time
                print(f"Gemini API response took {duration:.2f} seconds")
                try:
                    data = json.loads(response.text)
                except json.JSONDecodeError as e:
                    print(f"Error decoding JSON: {e}")
                    data = False

            # After progress
            if data == False:
                m_calss_example = "-"
                s_calss_example = "-"
                case_type_example = "-"
                explanation = "-"
            else:
                m_calss_example = data['category']
                s_calss_example = data['subcategory']
                case_type_example = data['type']
                explanation = data.get('explanation', '-') # Handle cases where explanation might be missing

            new_entry = {
                "input": user_input,
                "main_classification": m_calss_example,
                "sub_classification": s_calss_example,
                "case_type": case_type_example,
                "explanation": explanation,
                "id": len(st.session_state.history)
            }

            st.session_state.current_results = new_entry
            st.session_state.history.append(new_entry)
            save_history(st.session_state.history)
            st.session_state.case_submitted = True
            st.session_state.loading = False
            st.rerun()

        elif st.session_state.current_results:
            latest_entry = st.session_state.current_results

            st.markdown(f"""
                <div class="classification-item main-classification">
                    <div class="classification-label">
                        <span class="classification-icon">📊</span>
                        التصنيف الرئيسي
                    </div>
                    <div class="classification-value">{latest_entry["main_classification"]}</div>
                </div>
            """, unsafe_allow_html=True)

            st.markdown(f"""
                <div class="classification-item sub-classification">
                    <div class="classification-label">
                        <span class="classification-icon">🔍</span>
                        التصنيف الفرعي
                    </div>
                    <div class="classification-value">{latest_entry["sub_classification"]}</div>
                </div>
            """, unsafe_allow_html=True)

            st.markdown(f"""
                <div class="classification-item case-type">
                    <div class="classification-label">
                        <span class="classification-icon">⚖️</span>
                        نوع الدعوى
                    </div>
                    <div class="classification-value">{latest_entry["case_type"]}</div>
                </div>
            """, unsafe_allow_html=True)

            if latest_entry["explanation"]:
                st.markdown(f"""
                    <div class="info-link-container">
                        <a href="#" class="info-link">
                            شرح اضافي
                            <span class="info-icon">i</span>
                        </a>
                        <div class="info-bubble">
                            {latest_entry["explanation"]}
                        </div>
                    </div>
                """, unsafe_allow_html=True)

        else:
            st.markdown("""
                <div class="results-card empty-results-card">
                    <img src="https://img.icons8.com/fluency/96/000000/search.png">
                    <h3>أدخل نص الدعوى للحصول على التصنيف</h3>
                </div>
            """, unsafe_allow_html=True)

    # History Section
    st.markdown("""
        <div class="history-title">
            <h2>📜 سجل التصنيفات</h2>
        </div>
    """, unsafe_allow_html=True)

    # Download functionality
    if st.session_state.history:
        # Convert history to DataFrame for display
        df_display = pd.DataFrame(st.session_state.history)
        df_display = df_display[['case_type', 'sub_classification', 'main_classification', 'input', 'explanation']]
        df_display.columns = ['نوع الدعوى', 'التصنيف الفرعي', 'التصنيف الرئيسي', 'نص الدعوى', 'شرح']

        # Create a different DataFrame for download with original order
        df_download = pd.DataFrame(st.session_state.history)
        df_download = df_download[['input', 'main_classification', 'sub_classification', 'case_type', 'explanation']]
        df_download.columns = ['نص الدعوى', 'التصنيف الرئيسي', 'التصنيف الفرعي', 'نوع الدعوى', 'شرح']

        # Create Excel file in memory
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_download.to_excel(writer, index=False, sheet_name='Sheet1')

            worksheet = writer.sheets['Sheet1']

            # Set RTL direction
            worksheet.sheet_view.rightToLeft = True

            # Auto-fit columns
            for column in worksheet.columns:
                max_length = 0
                column = [cell for cell in column]
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = (max_length + 2)
                worksheet.column_dimensions[column[0].column_letter].width = adjusted_width

            # Set font for better Arabic display
            for row in worksheet.rows:
                for cell in row:
                    cell.font = openpyxl.styles.Font(name='Arial', size=11)
                    cell.alignment = openpyxl.styles.Alignment(horizontal='right', vertical='center', wrap_text=True)

        # Create download button with custom styling
        excel_data = output.getvalue()

        # Create columns for download buttons
        col1, col2 = st.columns(2)

        # Excel download in first column
        with col1:
            st.download_button(
                label="⬇️ تحميل سجل التصنيفات (Excel)",
                data=excel_data,
                file_name="history.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )

        # JSON download in second column
        with col2:
            json_str = json.dumps(st.session_state.history, ensure_ascii=False, indent=2)
            st.download_button(
                label="⬇️ تحميل سجل التصنيفات (JSON)",
                data=json_str,
                file_name="history.json",
                mime="application/json",
                use_container_width=True
            )

        # Create tabs for different views
        tab1, tab2 = st.tabs(["🗂️ عرض تفصيلي", "📊 عرض جدولي"])

        with tab1:
            # Display history in detailed view
            notification_icon = "✅"

            # Initialize visibility states for each history item
            for i in range(len(st.session_state.history)):
                if f"item_visible_{i}" not in st.session_state:
                    st.session_state[f"item_visible_{i}"] = True

            def handle_delete(index):
                st.session_state[f"item_visible_{index}"] = False
                st.session_state.history.pop(index)
                save_history(st.session_state.history)
                st.toast("تم حذف العنصر بنجاح", icon=notification_icon)

            # Reverse the history list for display
            visible_count = 0
            for i, entry in enumerate(reversed(st.session_state.history)):
                real_index = len(st.session_state.history) - 1 - i

                if st.session_state.get(f"item_visible_{real_index}", True):
                    if visible_count > 0:
                        st.markdown("""
                            <div class="custom-divider">
                                <span>•••</span>
                            </div>
                        """, unsafe_allow_html=True)
                    visible_count += 1

                    with st.container():
                        st.markdown('<div class="flex-95-5">', unsafe_allow_html=True)
                        col_content, col_delete = st.columns([0.95, 0.05])

                        with col_content:
                            st.markdown(f"""
                            <div class="case-text">
                                <strong>البحث:</strong> {entry["input"]}
                            </div>
                            """,
                            unsafe_allow_html=True)

                            if entry["explanation"]:
                                st.markdown(f"""
                                    <div class="info-link-container">
                                        <a href="#" class="info-link">
                                            شرح اضافي
                                            <span class="info-icon">i</span>
                                        </a>
                                        <div class="info-bubble">
                                            {entry["explanation"]}
                                        </div>
                                    </div>
                                """, unsafe_allow_html=True)

                        with col_delete:
                            st.markdown('<div class="delete-button-wrapper">', unsafe_allow_html=True)
                            if st.button("🗑️", key=f"delete_{real_index}", on_click=handle_delete, args=(real_index,)):
                                pass
                            st.markdown('</div>', unsafe_allow_html=True)
                        st.markdown('</div>', unsafe_allow_html=True)

                        # Classifications
                        st.markdown(f"""
                            <div class="classification-item main-classification">
                                <div class="classification-label">
                                    <span class="classification-icon">📊</span>
                                    التصنيف الرئيسي
                                </div>
                                <div class="classification-value">{entry["main_classification"]}</div>
                            </div>
                        """, unsafe_allow_html=True)

                        st.markdown(f"""
                            <div class="classification-item sub-classification">
                                <div class="classification-label">
                                    <span class="classification-icon">🔍</span>
                                    التصنيف الفرعي
                                </div>
                                <div class="classification-value">{entry["sub_classification"]}</div>
                            </div>
                        """, unsafe_allow_html=True)

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
                if not st.session_state.get('clear_triggered'):
                    st.session_state.history = []
                    save_history([])
                    st.toast("تم مسح السجل بالكامل", icon=notification_icon)
                    st.session_state.clear_triggered = True

            st.markdown('<div class="clear-all-button-container">', unsafe_allow_html=True)
            if st.button("مسح السجل بالكامل", type="secondary", on_click=handle_clear_all):
                pass
            st.markdown('</div>', unsafe_allow_html=True)

        with tab2:
            # Display history in table format using the display DataFrame
            st.markdown("""
                <style>
                    .stDataFrame {
                        font-family: 'Noto Kufi Arabic', sans-serif;
                    }
                    .stDataFrame td, .stDataFrame th {
                        text-align: right !important;
                        direction: rtl !important;
                    }
                </style>
            """, unsafe_allow_html=True)
            st.dataframe(
                df_display,
                use_container_width=True,
                hide_index=True
            )

    else:
        st.markdown('<div class="info-message">لا يوجد سجل تصنيفات سابقة</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()