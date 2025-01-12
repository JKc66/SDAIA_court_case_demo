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
import uuid
from contextlib import contextmanager
import streamlit.components.v1 as components

NUM_KEYS = 1

@contextmanager
def file_lock(file_path):
    """Simple file handling context manager for cloud environment."""
    try:
        with open(file_path, 'r+' if os.path.exists(file_path) else 'w+') as f:
            yield f
    except IOError as e:
        st.error(f"Error accessing history file: {e}")
        yield None

def get_user_id():
    """Get or create a unique user ID for the current session."""
    if 'user_id' not in st.session_state:
        st.session_state.user_id = str(uuid.uuid4())
    return st.session_state.user_id

def validate_json(content):
    """Validate JSON content."""
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        return None

def backup_history_file():
    """Create a backup of the history file."""
    history_file = Path("history.json")
    backup_file = Path("history.json.backup")
    if history_file.exists():
        try:
            with open(history_file, 'r', encoding='utf-8') as source:
                content = source.read()
                if validate_json(content):  # Only backup valid JSON
                    with open(backup_file, 'w', encoding='utf-8') as target:
                        target.write(content)
        except Exception:
            pass

def load_history():
    """Load classification history from JSON file with robust error handling."""
    history_file = Path("history.json")
    backup_file = Path("history.json.backup")
    
    try:
        # Try loading main file
        if history_file.exists():
            with open(history_file, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if content:
                    data = validate_json(content)
                    if data is not None:
                        return data
                    
        # If main file fails, try backup
        if backup_file.exists():
            with open(backup_file, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if content:
                    data = validate_json(content)
                    if data is not None:
                        # Restore from backup
                        save_history(data)
                        return data
        
        # If both files fail, start fresh
        return []
        
    except Exception as e:
        st.error(f"Error loading history: {e}")
        return []

def save_history(history):
    """Save classification history to JSON file with backup."""
    history_file = Path("history.json")
    backup_file = Path("history.json.backup")
    try:
        # Create backup of existing file first
        backup_history_file()
        
        # Write to temporary file
        temp_file = history_file.with_suffix('.tmp')
        with open(temp_file, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=4)
        
        # Validate the written content
        with open(temp_file, 'r', encoding='utf-8') as f:
            content = f.read()
            if validate_json(content) is None:
                raise ValueError("Failed to write valid JSON")
        
        # If validation passes, move temp file to actual file
        temp_file.replace(history_file)
        
    except Exception as e:
        st.error(f"Error saving history: {e}")
        # Try to restore from backup if save fails
        if backup_file.exists():
            try:
                backup_file.replace(history_file)
            except:
                pass

def inject_custom_css():
    """Load external CSS file"""
    css_file = Path(__file__).parent / "static" / "style.css"
    with open(css_file, 'r', encoding='utf-8') as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

def hide_streamlit_elements():
    """Inject JavaScript to hide Streamlit elements"""
    hide_streamlit_script = """
        <script>
            function hideElements() {
                // Hide all Streamlit elements
                const elementsToHide = [
                    '.stDeployButton',
                    'footer',
                    '#MainMenu',
                    '[data-testid="stToolbar"]',
                    '.css-1dp5vir',
                    '.css-14xtw13',
                    '.css-1kyxreq',
                    '.css-1q1n0ol',
                    '[data-testid="stHeader"]',
                    '[data-testid="stDecoration"]',
                    '.viewerBadge_container__1QSob',
                    '.css-1avcm0n',
                    '.css-18ni7ap',
                    '.element-container iframe[src*="github.com"]',
                    '._profilePreview_gzau3_63',
                    'div._profilePreview_gzau3_63',
                    '._profilePreview_gzau3_63 a',
                    '._profilePreview_gzau3_63 img',
                    '.stAppHeader',
                    '._profileImage_gzau3_78',
                    '._link_gzau3_10',
                    '._profileContainer_gzau3_53'
                ];

                // Create a MutationObserver to handle dynamically added elements
                const observer = new MutationObserver((mutations) => {
                    mutations.forEach((mutation) => {
                        if (mutation.addedNodes.length) {
                            elementsToHide.forEach((selector) => {
                                document.querySelectorAll(selector).forEach((el) => {
                                    el.style.display = 'none';
                                    el.style.visibility = 'hidden';
                                    el.style.opacity = '0';
                                    el.style.pointerEvents = 'none';
                                });
                            });
                        }
                    });
                });

                // Start observing the document with the configured parameters
                observer.observe(document.body, { childList: true, subtree: true });

                // Initial hide
                elementsToHide.forEach((selector) => {
                    document.querySelectorAll(selector).forEach((el) => {
                        el.style.display = 'none';
                        el.style.visibility = 'hidden';
                        el.style.opacity = '0';
                        el.style.pointerEvents = 'none';
                    });
                });
            }

            // Run on load and after any dynamic content changes
            if (document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', hideElements);
            } else {
                hideElements();
            }
        </script>
    """
    components.html(hide_streamlit_script)

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
inject_custom_css()
hide_streamlit_elements()

#------------------------------------------------------------------------------
# UTILITY FUNCTIONS
#------------------------------------------------------------------------------
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
    # Initialize history at startup
    if 'history' not in st.session_state:
        st.session_state.history = load_history()
    
    # Ensure history is never None
    if st.session_state.history is None:
        st.session_state.history = []
    
    # Remove the periodic refresh and replace with event-based updates
    if "history_needs_refresh" not in st.session_state:
        st.session_state.history_needs_refresh = False
    
    if st.session_state.history_needs_refresh:
        st.session_state.history = load_history()
        st.session_state.history_needs_refresh = False

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
    if "last_update" not in st.session_state:
        st.session_state.last_update = time.time()

    # Remove duplicate history initialization
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
                """Handle new case while preserving history."""
                # Only reset current case related states
                st.session_state.case_submitted = False
                st.session_state.current_results = None
                st.session_state.loading = False
                # Clear only the input field
                if "rtl_input" in st.session_state:
                    st.session_state.rtl_input = ""
                # Ensure history is loaded
                if 'history' not in st.session_state:
                    st.session_state.history = load_history()

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
                "id": len(st.session_state.history),
                "timestamp": time.time(),
                "user_id": get_user_id()
            }

            # Update history both in session state and file
            st.session_state.history.append(new_entry)
            save_history(st.session_state.history)
            st.session_state.current_results = new_entry
            st.session_state.case_submitted = True
            st.session_state.loading = False
            st.rerun()  # Force refresh to show new entry

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
            notification_icon = "✅"
            
            # Add Bootstrap dependencies
            st.markdown("""
                <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/4.0.0/css/bootstrap.min.css">
                <script src="https://code.jquery.com/jquery-3.2.1.slim.min.js"></script>
                <script src="https://maxcdn.bootstrapcdn.com/bootstrap/4.0.0/js/bootstrap.min.js"></script>
                <style>
                    .card-header button { text-align: right; width: 100%; }
                    .card-header button:hover { text-decoration: none; }
                    .card-body { text-align: right; direction: rtl; }
                    .accordion .card { margin-bottom: 5px; }
                    .delete-btn { float: left; }
                </style>
            """, unsafe_allow_html=True)
            
            # Initialize visibility states for each history item
            for i in range(len(st.session_state.history)):
                if f"item_visible_{i}" not in st.session_state:
                    st.session_state[f"item_visible_{i}"] = True

            def handle_delete(index):
                st.session_state[f"item_visible_{index}"] = False
                st.session_state.history.pop(index)
                save_history(st.session_state.history)
                st.toast("تم حذف العنصر بنجاح", icon=notification_icon)
                st.rerun()  # Force refresh after deletion
            
            # Initialize accordion container
            st.markdown('<div id="historyAccordion" class="accordion">', unsafe_allow_html=True)
            
            # Display history items as accordion cards
            visible_count = 0
            for i, entry in enumerate(reversed(st.session_state.history)):
                real_index = len(st.session_state.history) - 1 - i
                
                if st.session_state.get(f"item_visible_{real_index}", True):
                    st.markdown(f"""
                        <div class="card">
                            <div class="card-header" id="heading{real_index}">
                                <h5 class="mb-0 d-flex justify-content-between align-items-center">
                                    <button class="btn btn-link" data-toggle="collapse" data-target="#collapse{real_index}">
                                        {entry["input"][:100]}...
                                    </button>
                                    <button class="btn btn-sm btn-danger delete-btn" onclick="deleteHistoryItem({real_index})">🗑️</button>
                                </h5>
                            </div>
                            <div id="collapse{real_index}" class="collapse" data-parent="#historyAccordion">
                                <div class="card-body">
                                    <div class="classification-item main-classification">
                                        <div class="classification-label">
                                            <span class="classification-icon">📊</span>
                                            التصنيف الرئيسي
                                        </div>
                                        <div class="classification-value">{entry["main_classification"]}</div>
                                    </div>
                                    <div class="classification-item sub-classification">
                                        <div class="classification-label">
                                            <span class="classification-icon">🔍</span>
                                            التصنيف الفرعي
                                        </div>
                                        <div class="classification-value">{entry["sub_classification"]}</div>
                                    </div>
                                    <div class="classification-item case-type">
                                        <div class="classification-label">
                                            <span class="classification-icon">⚖️</span>
                                            نوع الدعوى
                                        </div>
                                        <div class="classification-value">{entry["case_type"]}</div>
                                    </div>
                                    {"" if not entry["explanation"] else f'''
                                    <div class="explanation-section mt-3">
                                        <h6>شرح اضافي:</h6>
                                        <p>{entry["explanation"]}</p>
                                    </div>
                                    '''}
                                </div>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
            
            # Close accordion container
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Add JavaScript for delete functionality
            st.markdown("""
                <script>
                    function deleteHistoryItem(index) {
                        // Use Streamlit's component-to-parent communication
                        window.parent.postMessage({
                            type: 'streamlit:delete',
                            index: index
                        }, '*');
                    }
                </script>
            """, unsafe_allow_html=True)
            
            # Handle delete message in Python
            if st.session_state.get('delete_triggered'):
                index = st.session_state.get('delete_index')
                if index is not None:
                    handle_delete(index)
                    st.session_state.delete_triggered = False
                    st.session_state.delete_index = None

            # Clear all history button
            def handle_clear_all():
                if not st.session_state.get('clear_triggered'):
                    st.session_state.history = []
                    save_history([])
                    st.toast("تم مسح السجل بالكامل", icon=notification_icon)
                    st.session_state.clear_triggered = True
                    st.rerun()  # Force refresh after clearing

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