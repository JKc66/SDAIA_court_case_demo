import streamlit as st
import json
import base64
from pathlib import Path
import time
import os
from google import genai
from google.genai import types
from random import randint
import datetime
import pandas as pd
import uuid
import sqlite3
import traceback # Added for more detailed error logging

NUM_KEYS = 1

# --- File Caching Helper Functions ---
FILE_CACHE_PATH = Path(__file__).parent / 'file_cache.json'

def load_file_cache():
    """Load the file cache from JSON."""
    if not FILE_CACHE_PATH.exists():
        return {}
    try:
        with open(FILE_CACHE_PATH, 'r') as f:
            # Handle empty file case
            content = f.read()
            if not content:
                return {}
            return json.loads(content)
    except json.JSONDecodeError: # Handle corrupted cache file
        print("Error decoding file_cache.json, returning empty cache.")
        return {}
    except FileNotFoundError: # Should be caught by .exists() but as a safeguard
        return {}

def save_file_cache(cache):
    """Save the file cache to JSON."""
    with open(FILE_CACHE_PATH, 'w') as f:
        json.dump(cache, f, indent=4)

def calculate_file_size(file_path: Path):
    """Calculate file size in bytes."""
    return file_path.stat().st_size

def wait_for_single_file_active(client, file_obj, max_attempts=12, delay=5): # Increased attempts slightly
    """Wait for a single file to become active, with timeout."""
    current_file = file_obj
    print(f"Waiting for file {getattr(current_file, 'name', 'N/A')} to become active...")
    for attempt in range(max_attempts):
        # Ensure current_file is the most up-to-date object
        try:
            # It's crucial to get the latest status of the file object by its name
            refreshed_file = client.files.get(name=current_file.name)
        except Exception as e:
            st.error(f"Error refreshing file status for {current_file.name}: {e}")
            print(f"Error refreshing file status for {current_file.name}: {e}")
            # Depending on the error, might want to retry or raise
            if attempt < max_attempts -1: # if not the last attempt
                time.sleep(delay)
                continue
            raise Exception(f"Could not refresh file status for {current_file.name} after an error: {e}")


        file_state_name = getattr(getattr(refreshed_file, 'state', None), 'name', None)

        if file_state_name == "ACTIVE":
            print(f"File {refreshed_file.name} is ACTIVE.")
            return True # Return the refreshed, active file object
        elif file_state_name == "PROCESSING":
            print(f". (Attempt {attempt + 1}/{max_attempts} for {refreshed_file.name})", end="", flush=True)
            time.sleep(delay)
            current_file = refreshed_file # Continue with the refreshed object
            continue
        else:
            error_message = f"File {refreshed_file.name} failed to process or has an unexpected state."
            if file_state_name:
                error_message += f" State: {file_state_name}"
            else:
                error_message += f" Current file object state unknown: {refreshed_file}"
            st.error(error_message)
            print(error_message)
            raise Exception(error_message)
            
    final_file_state = getattr(getattr(client.files.get(name=current_file.name), 'state', None), 'name', 'UNKNOWN')
    timeout_message = f"Timeout waiting for file {current_file.name} (last known state: {final_file_state}) to become active after {max_attempts} attempts."
    st.error(timeout_message)
    print(timeout_message)
    raise Exception(timeout_message)
# --- End File Caching Helper Functions ---

def init_db():
    """Initialize SQLite database and create tables if they don't exist."""
    conn = sqlite3.connect('history.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS classifications (
            id TEXT PRIMARY KEY,
            input_text TEXT NOT NULL,
            main_classification TEXT NOT NULL,
            sub_classification TEXT NOT NULL,
            case_type TEXT NOT NULL,
            explanation TEXT,
            duration TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    return conn

def get_db():
    """Get database connection, creating it if necessary."""
    if 'db_conn' not in st.session_state:
        st.session_state.db_conn = init_db()
    return st.session_state.db_conn

def load_history_from_db():
    """Load classification history from SQLite database."""
    conn = get_db()
    df = pd.read_sql_query(
        'SELECT * FROM classifications ORDER BY created_at DESC',
        conn
    )
    if df.empty:
        return []
    return df.to_dict('records')

def save_to_db(entry):
    """Save a single classification entry to the database."""
    conn = get_db()
    c = conn.cursor()
    c.execute('''
        INSERT INTO classifications 
        (id, input_text, main_classification, sub_classification, case_type, explanation, duration)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        entry['id'],
        entry['input'],
        entry['main_classification'],
        entry['sub_classification'],
        entry['case_type'],
        entry['explanation'],
        entry['duration']
    ))
    conn.commit()

def delete_from_db(entry_id):
    """Delete a single entry from the database."""
    conn = get_db()
    c = conn.cursor()
    c.execute('DELETE FROM classifications WHERE id = ?', (entry_id,))
    conn.commit()

def clear_history_db():
    """Clear all history from the database."""
    conn = get_db()
    c = conn.cursor()
    c.execute('DELETE FROM classifications')
    conn.commit()

def get_user_id():
    """Get or create a unique user ID for the current session."""
    if 'user_id' not in st.session_state:
        st.session_state.user_id = str(uuid.uuid4())
    return st.session_state.user_id

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

def upload_to_gemini(client, path: Path, mime_type: str | None = None):
    """Upload file with checking for existing files based on size and state."""
    try:
        file_path = Path(__file__).parent / path
        if not file_path.exists():
            st.error(f"File not found: {file_path}")
            raise FileNotFoundError(f"File not found: {file_path}")

        file_size = calculate_file_size(file_path)
        cache = load_file_cache()

        # Check cache first
        # Use a combination of path and size for a more robust cache key, or just size if path can change but content is same
        # For this use case, Classes.txt path is fixed, so path+size is good.
        # However, the example used file_size as key. Let's stick to file_size for now but add original_path check.
        
        cached_entry_key = str(file_size) # Or a hash of content if sizes can collide often for different files
        
        if cached_entry_key in cache:
            cached_file_info = cache[cached_entry_key]
            # Verify if the cached entry is for the same original file path
            if cached_file_info.get('original_path') == str(file_path):
                cached_file_id = cached_file_info['file_id']
                try:
                    print(f"Cache hit for {file_path} (size: {file_size}), checking status of {cached_file_id}...")
                    existing_file = client.files.get(name=cached_file_id)
                    if existing_file.state.name == 'ACTIVE' and getattr(existing_file, 'size_bytes', -1) == file_size:
                        print(f"Using cached and active file: {existing_file.name} ({existing_file.uri})")
                        return existing_file
                    else:
                        print(f"Cached file {cached_file_id} (for {file_path}) is not active or size mismatch. State: {existing_file.state.name}, API Size: {getattr(existing_file, 'size_bytes', -1)}, Expected Size: {file_size}")
                except Exception as e: 
                    print(f"Error checking cached file {cached_file_id} for {file_path}: {e}. Will try to find by size or re-upload.")
            else:
                print(f"Cache entry for size {file_size} exists, but original path mismatch. Cached: {cached_file_info.get('original_path')}, Current: {str(file_path)}")


        print(f"Checking existing files on API for {file_path} (size: {file_size})...")
        try:
            existing_files_list = client.files.list() 
            for file_on_api in existing_files_list:
                if file_on_api.state.name == 'ACTIVE' and getattr(file_on_api, 'size_bytes', -1) == file_size:
                    # Heuristic: if an active file of the same size exists, assume it's the one.
                    # This could be problematic if multiple distinct files have the exact same size.
                    # For Classes.txt, this risk is lower.
                    print(f"Found matching active file on API by size: {file_on_api.name} ({file_on_api.uri}) for {file_path}")
                    cache[cached_entry_key] = {
                        'file_id': file_on_api.name,
                        'file_uri': file_on_api.uri,
                        'mime_type': getattr(file_on_api, 'mime_type', mime_type or 'text/plain'),
                        'original_path': str(file_path)
                    }
                    save_file_cache(cache)
                    return file_on_api
        except Exception as e:
            st.error(f"Error listing files from API: {e}")
            print(f"Error listing files from API: {e}")
            # Decide if to proceed with upload or raise

        print(f"No suitable existing file found for {file_path}. Uploading anew...")
        uploaded_file_obj = client.files.upload(
            file=file_path, # Pass Path object directly
            display_name=file_path.name # Good practice to set display name
        )
        print(f"Uploaded '{file_path.name}' as {uploaded_file_obj.name}, waiting for it to become active...")
        
        if not wait_for_single_file_active(client, uploaded_file_obj):
             raise Exception(f"Uploaded file {uploaded_file_obj.name} did not become active.")

        # Refresh file object to get all attributes like size_bytes and mime_type after activation
        final_file_obj = client.files.get(name=uploaded_file_obj.name)

        print(f"File {final_file_obj.name} is active. URI: {final_file_obj.uri}, Size: {getattr(final_file_obj, 'size_bytes', 'N/A')}, MimeType: {getattr(final_file_obj, 'mime_type', 'N/A')}")
        
        cache[cached_entry_key] = {
            'file_id': final_file_obj.name,
            'file_uri': final_file_obj.uri,
            'mime_type': getattr(final_file_obj, 'mime_type', mime_type or 'text/plain'),
            'original_path': str(file_path)
        }
        save_file_cache(cache)
        
        return final_file_obj
    except Exception as e:
        st.error(f"Failed during file handling for {path}: {e}")
        print(f"Error in upload_to_gemini for {path}: {e}") 
        traceback.print_exc()
        return None

def wait_for_files_active(client, files_list):
    """Waits for the given files to be active."""
    print("Waiting for file processing...")
    try:
        for file_obj in files_list:
            if file_obj is None:
                raise Exception("Invalid file object")

            name = file_obj.name
            retrieved_file = client.files.get(name=name)
            while retrieved_file.state.name == "PROCESSING":
                print(".", end="", flush=True)
                time.sleep(5)
                retrieved_file = client.files.get(name=name)
            if retrieved_file.state.name != "ACTIVE":
                raise Exception(f"File {retrieved_file.name} failed to process")
        print("...all files ready")
        print()
    except Exception as e:
        st.error(f"File processing failed: {e}")
        return False
    return True

@st.cache_resource(ttl=datetime.timedelta(days=2), show_spinner=False)
def initialize_gemini(key_id):
    try:
        api_key = os.environ.get(f"GEMINI_API_KEY_{key_id}")
        if not api_key:
            st.error(f"API key {key_id} not found. Please check your configuration.")
            return None, None, None, None # client, model_name, config, file_obj

        client = genai.Client(api_key=api_key)

        system_instruction_text = """
You are an expert legal text classifier. Your primary function is to analyze the provided input text and classify it according to a strict, predefined hierarchical structure.
This classification scheme (categories, subcategories, and types) is **exclusively defined** in the content of the 'Classes.txt' file provided to you.

**Critical Instructions:**
*   **Strict Adherence:** You MUST select classifications *only* from the options listed in 'Classes.txt'. Do NOT invent, modify, or infer any classifications.
*   **Best Fit:** Choose the most appropriate option at each level (category, subcategory, type) even if the match isn't perfect, as long as it's from the provided list in 'Classes.txt'.

**Classification Steps (using 'Classes.txt'):**
1.  **Category:** Identify the single MOST appropriate 'category'.
2.  **Subcategory:** Within the chosen 'category', identify the single MOST appropriate 'subcategory'.
3.  **Type:** Within the chosen 'subcategory', identify the single MOST appropriate 'type'.
    *   **Specific Fallback for 'type':** If, and ONLY if, *none* of the 'type' options listed under the chosen subcategory in 'Classes.txt' are a suitable match for the input text, you MUST use the exact Arabic string "لا يوجد" for the "type" value.

**Output Requirements:**
*   **Format:** Your response MUST be a single, valid JSON object.
*   **Language:** All string values within the JSON object MUST be in ARABIC.
*   **Structure:** The JSON object MUST contain the following keys, exactly as named:
    *   `"category"`: The selected Arabic name of the category (from 'Classes.txt').
    *   `"subcategory"`: The selected Arabic name of the subcategory (from 'Classes.txt').
    *   `"type"`: The selected Arabic name of the type (from 'Classes.txt'), or "لا يوجد" as per the fallback rule.
    *   `"explanation"`: A concise but informative explanation in ARABIC, justifying your choices for category, subcategory, and type. This should briefly state *why* the selected classifications fit the input text.
"""
        
        model_name = "gemini-2.5-flash-preview-04-17" # Using existing model name

        classes_file_path = Path("Data") / "Classes.txt"
        # Mime type is optional for upload_to_gemini, it will try to get from API or use default
        classes_file_obj = upload_to_gemini(client, classes_file_path) 

        if classes_file_obj is None:
            error_msg = "Failed to upload or retrieve 'Classes.txt'. Cannot proceed with Gemini initialization."
            st.error(error_msg)
            raise Exception(error_msg)

        # classes_file_obj is now guaranteed to be active if returned (or an exception was raised)

        gen_content_config = types.GenerateContentConfig(
            temperature=0.0, 
            top_p=0.95, 
            top_k=40, 
            max_output_tokens=8192, 
            response_mime_type="application/json", 
            system_instruction=system_instruction_text
        )
        
        print("Gemini initialized successfully for generate_content.")
        return client, model_name, gen_content_config, classes_file_obj

    except Exception as e:
        st.error(f"Failed to initialize Gemini: {e}")
        traceback.print_exc() # Print stack trace for server logs
        return None, None, None, None

#------------------------------------------------------------------------------
# MAIN APPLICATION
#------------------------------------------------------------------------------
def main():
    # Initialize history from database at startup
    if 'history' not in st.session_state:
        st.session_state.history = load_history_from_db()
    
    # Add deletion tracking to session state initialization
    if "deletion_triggered" not in st.session_state:
        st.session_state.deletion_triggered = False
    
    # Event-based history updates
    if "history_needs_refresh" not in st.session_state:
        st.session_state.history_needs_refresh = False
    
    if st.session_state.history_needs_refresh:
        st.session_state.history = load_history_from_db()
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

    # Session state for Gemini client and config
    if "gemini_client" not in st.session_state:
        st.session_state.gemini_client = None
    if "model_name" not in st.session_state:
        st.session_state.model_name = None
    if "generation_config" not in st.session_state: # Renamed from chat_generation_config
        st.session_state.generation_config = None
    if "classes_file_obj" not in st.session_state: # For storing the Classes.txt file object
        st.session_state.classes_file_obj = None


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

        if st.session_state.gemini_client: # Check if client is initialized
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
            st.session_state.loading = True # Keep this to show loading message

            # Try to initialize Gemini
            client, model_name, gen_config, classes_file = initialize_gemini(st.session_state.key_id)

            if client is None: # If first attempt fails, try other keys
                for i in range(1, NUM_KEYS + 1):
                    if i != st.session_state.key_id:
                        st.session_state.key_id = i # Update key_id for next attempt
                        client, model_name, gen_config, classes_file = initialize_gemini(i)
                        if client is not None:
                            break
            
            if client is None:
                # This error is already shown by initialize_gemini, but good to have a fallback
                st.error("Critical: Failed to initialize the Gemini system after trying all keys. Please contact support.")
                st.session_state.loading = False # Stop loading indicator
                return # Stop further execution in this run

            # Store initialized components in session state
            st.session_state.gemini_client = client
            st.session_state.model_name = model_name
            st.session_state.generation_config = gen_config
            st.session_state.classes_file_obj = classes_file
            
            st.session_state.loading = False # Clear loading state
            st.rerun() # Rerun to reflect the initialized state

        col1, col2 = st.columns(2)
        with col1:
            if st.button("⚖️ تصنيف الدعوى", type="primary", disabled=st.session_state.case_submitted):
                if user_input and user_input.strip():
                    st.session_state.loading = True
                    st.session_state.current_results = None

        with col2:
            def handle_new_case():
                """Handle new case while preserving history."""
                st.session_state.case_submitted = False
                st.session_state.current_results = None
                st.session_state.loading = False
                if "rtl_input" in st.session_state:
                    st.session_state.rtl_input = ""
                st.session_state.history = load_history_from_db()

            if st.button("🔄 حالة جديدة", type="secondary", on_click=handle_new_case):
                pass

    # Results section
    with col_results:
        st.markdown('<div class="content-section">', unsafe_allow_html=True)
        
        if st.session_state.current_results:
            st.markdown(f"""
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                    <h2 style="margin: 0;">⚡ نتائج التصنيف</h2>
                    <div style="display: flex; align-items: center; color: #666; font-size: 0.9em;">
                        <span>⏱️ {st.session_state.current_results.get("duration", "-")} ثانية</span>
                    </div>
                </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("<h2>⚡ نتائج التصنيف</h2>", unsafe_allow_html=True)

        if st.session_state.loading: # This is True when "تصنيف الدعوى" button is clicked
            st.markdown("""
                <div class="custom-spinner-container">
                    <div class="custom-spinner"></div>
                    <div class="spinner-text">جاري تحليل وتصنيف الدعوى...</div>
                </div>
            """, unsafe_allow_html=True)

            with st.spinner(''): # Streamlit's built-in spinner
                print("Sending request to Gemini using generate_content...")
                start_time = time.time()
                
                # Prepare contents for generate_content
                # The system_instruction is in st.session_state.generation_config
                # Classes.txt file object is st.session_state.classes_file_obj
                request_contents = [
                    st.session_state.classes_file_obj, # The File object for Classes.txt
                    user_input  # The user's text input for classification
                ]

                # --- Add Enhanced Debugging ---
                print("--- Debug: Preparing for Gemini API call ---")
                print(f"Model Name: {st.session_state.model_name}")
                print(f"Request Contents (type of 1st item): {type(request_contents[0])}")
                print(f"Request Contents (1st item details): {request_contents[0]}")
                print(f"User Input (length): {len(user_input)}")
                print(f"Generation Config: {st.session_state.generation_config}")
                print("--- End Debug ---")
                # --- End Enhanced Debugging ---

                response_text = None
                data = False # Default to False

                try:
                    # Ensure all necessary components are available
                    if not all([st.session_state.gemini_client, 
                                st.session_state.model_name, 
                                request_contents[0], # classes_file_obj
                                st.session_state.generation_config]):
                        st.error("Gemini client or necessary configuration is missing. Cannot proceed.")
                        raise Exception("Gemini client/config missing.")

                    api_response = st.session_state.gemini_client.models.generate_content(
                        model=st.session_state.model_name,
                        contents=request_contents,
                        config=st.session_state.generation_config 
                    )
                    response_text = api_response.text
                except Exception as e:
                    st.error(f"Error calling Gemini API: {e}")
                    print(f"Error calling Gemini API: {e}")
                    traceback.print_exc()
                    # data remains False

                end_time = time.time()
                duration = end_time - start_time
                print(f"Gemini API call took {duration:.2f} seconds")

                if response_text:
                    try:
                        parsed_json = json.loads(response_text)
                        if isinstance(parsed_json, list) and len(parsed_json) > 0:
                            # Assuming the API might return a list with one item
                            data = parsed_json[0] 
                        elif isinstance(parsed_json, dict):
                            data = parsed_json
                        else: # Unexpected structure
                            print(f"Unexpected JSON structure from API: {parsed_json}")
                            data = False


                        if not isinstance(data, dict) or not all(key in data for key in ['category', 'subcategory', 'type']):
                            print(f"Invalid response structure after parsing: {data}")
                            data = False # Reset to False if structure is not as expected
                    except json.JSONDecodeError as e:
                        print(f"Error decoding JSON from Gemini response: {e}")
                        print(f"Received text: {response_text}")
                        data = False
                else: # If response_text is None due to API error
                    data = False


            if not data: # Simplified check
                m_calss_example = "-"
                s_calss_example = "-"
                case_type_example = "-"
                explanation = "-"
            else:
                m_calss_example = data['category']
                s_calss_example = data['subcategory']
                case_type_example = data['type']
                explanation = data.get('explanation', '-')

            # Save new entry to database
            new_entry = {
                "id": str(uuid.uuid4()),
                "input": user_input, # Ensure user_input is captured correctly
                "main_classification": m_calss_example,
                "sub_classification": s_calss_example,
                "case_type": case_type_example,
                "explanation": explanation,
                "duration": f"{duration:.2f}"
            }

            save_to_db(new_entry)
            st.session_state.history = load_history_from_db()
            st.session_state.current_results = new_entry
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

    # # History Section
    # st.markdown("""
    #     <div class="history-title">
    #         <h2>📜 سجل التصنيفات</h2>
    #     </div>
    # """, unsafe_allow_html=True)

    # # Download functionality
    # if st.session_state.history:
    #     # Convert history to DataFrame for display
    #     df_display = pd.DataFrame(st.session_state.history)
    #     df_display = df_display[['case_type', 'sub_classification', 'main_classification', 'input_text', 'explanation']]
    #     df_display.columns = ['نوع الدعوى', 'التصنيف الفرعي', 'التصنيف الرئيسي', 'نص الدعوى', 'شرح']

    #     # Create a different DataFrame for download with original order
    #     df_download = pd.DataFrame(st.session_state.history)
    #     df_download = df_download[['input_text', 'main_classification', 'sub_classification', 'case_type', 'explanation']]
    #     df_download.columns = ['نص الدعوى', 'التصنيف الرئيسي', 'التصنيف الفرعي', 'نوع الدعوى', 'شرح']

    #     # Create Excel file in memory
    #     output = io.BytesIO()
    #     with pd.ExcelWriter(output, engine='openpyxl') as writer:
    #         df_download.to_excel(writer, index=False, sheet_name='Sheet1')

    #         worksheet = writer.sheets['Sheet1']
    #         worksheet.sheet_view.rightToLeft = True

    #         for column in worksheet.columns:
    #             max_length = 0
    #             column = [cell for cell in column]
    #             for cell in column:
    #                 try:
    #                     if len(str(cell.value)) > max_length:
    #                         max_length = len(str(cell.value))
    #                 except:
    #                     pass
    #             adjusted_width = (max_length + 2)
    #             worksheet.column_dimensions[column[0].column_letter].width = adjusted_width

    #         for row in worksheet.rows:
    #             for cell in row:
    #                 cell.font = openpyxl.styles.Font(name='Arial', size=11)
    #                 cell.alignment = openpyxl.styles.Alignment(horizontal='right', vertical='center', wrap_text=True)

    #     excel_data = output.getvalue()

    #     col1, col2 = st.columns(2)

    #     with col1:
    #         st.download_button(
    #             label="⬇️ تحميل سجل التصنيفات (Excel)",
    #             data=excel_data,
    #             file_name="history.xlsx",
    #             mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    #             use_container_width=True
    #         )

    #     with col2:
    #         # Convert history to JSON for download
    #         json_str = json.dumps(st.session_state.history, ensure_ascii=False, indent=2)
    #         st.download_button(
    #             label="⬇️ تحميل سجل التصنيفات (JSON)",
    #             data=json_str,
    #             file_name="export.json",
    #             mime="application/json",
    #             use_container_width=True
    #         )

    #     tab1, tab2 = st.tabs(["🗂️ عرض تفصيلي", "📊 عرض جدولي"])

    #     with tab1:
    #         for i in range(len(st.session_state.history)):
    #             if f"item_visible_{i}" not in st.session_state:
    #                 st.session_state[f"item_visible_{i}"] = True

    #         def handle_delete(entry_id):
    #             delete_from_db(entry_id)
    #             st.session_state.history = load_history_from_db()
    #             st.toast("تم حذف العنصر بنجاح", icon="✅") # Used icon directly
    #             st.session_state.deletion_triggered = True

    #         visible_count = 0
    #         for i, entry in enumerate(st.session_state.history[:5]):  # Show only last 5 entries
    #             if visible_count > 0:
    #                 st.markdown("""
    #                     <div class="custom-divider">
    #                         <span>•••</span>
    #                     </div>
    #                 """, unsafe_allow_html=True)
    #             visible_count += 1

    #             with st.container():
    #                 st.markdown('<div class="flex-95-5">', unsafe_allow_html=True)
    #                 col_content, col_delete = st.columns([0.95, 0.05])

    #                 with col_content:
    #                     st.markdown(f"""
    #                     <div class="case-text">
    #                         <strong>البحث:</strong> {entry["input_text"]}
    #                     </div>
    #                     """,
    #                     unsafe_allow_html=True)

    #                     if entry["explanation"]:
    #                         st.markdown(f"""
    #                             <div class="info-link-container">
    #                                 <a href="#" class="info-link">
    #                                     شرح اضافي
    #                                     <span class="info-icon">i</span>
    #                                 </a>
    #                                 <div class="info-bubble">
    #                                     {entry["explanation"]}
    #                                 </div>
    #                             </div>
    #                         """, unsafe_allow_html=True)

    #                 with col_delete:
    #                     st.markdown('<div class="delete-button-wrapper">', unsafe_allow_html=True)
    #                     if st.button("🗑️", key=f"delete_{entry['id']}", on_click=handle_delete, args=(entry['id'],)):
    #                         pass
    #                     st.markdown('</div>', unsafe_allow_html=True)
    #                 st.markdown('</div>', unsafe_allow_html=True)

    #                 st.markdown(f"""
    #                     <div class="classification-item main-classification">
    #                         <div class="classification-label">
    #                             <span class="classification-icon">📊</span>
    #                             التصنيف الرئيسي
    #                         </div>
    #                         <div class="classification-value">{entry["main_classification"]}</div>
    #                     </div>
    #                 """, unsafe_allow_html=True)

    #                 st.markdown(f"""
    #                     <div class="classification-item sub-classification">
    #                         <div class="classification-label">
    #                             <span class="classification-icon">🔍</span>
    #                             التصنيف الفرعي
    #                         </div>
    #                         <div class="classification-value">{entry["sub_classification"]}</div>
    #                     </div>
    #                 """, unsafe_allow_html=True)

    #                 st.markdown(f"""
    #                     <div class="classification-item case-type">
    #                         <div class="classification-label">
    #                             <span class="classification-icon">⚖️</span>
    #                             نوع الدعوى
    #                         </div>
    #                         <div class="classification-value">{entry["case_type"]}</div>
    #                     </div>
    #                 """, unsafe_allow_html=True)

    #                 st.markdown(f"""
    #                     <div class="classification-item response-time">
    #                         <div class="classification-label">
    #                             <span class="classification-icon">⏱️</span>
    #                             زمن الاستجابة
    #                         </div>
    #                         <div class="classification-value">{entry.get("duration", "-")} ثانية</div>
    #                     </div>
    #                 """, unsafe_allow_html=True)

    #         def handle_clear_all():
    #             if not st.session_state.get('clear_triggered'):
    #                 clear_history_db()
    #                 st.session_state.history = []
    #                 st.toast("تم مسح السجل بالكامل", icon="✅") # Used icon directly
    #                 st.session_state.clear_triggered = True
    #                 st.session_state.deletion_triggered = True

    #         st.markdown('<div class="clear-all-button-container">', unsafe_allow_html=True)
    #         if st.button("مسح السجل بالكامل", type="secondary", on_click=handle_clear_all):
    #             pass
    #         st.markdown('</div>', unsafe_allow_html=True)

    #     with tab2:
    #         if st.session_state.deletion_triggered:
    #             st.session_state.deletion_triggered = False
    #             st.rerun()
                
    #         st.markdown("""
    #             <style>
    #                 .stDataFrame {
    #                     font-family: 'Noto Kufi Arabic', sans-serif;
    #                 }
    #                 .stDataFrame td, .stDataFrame th {
    #                     text-align: right !important;
    #                     direction: rtl !important;
    #                 }
    #             </style>
    #         """, unsafe_allow_html=True)
    #         st.dataframe(
    #             df_display,
    #             use_container_width=True,
    #             hide_index=True
    #         )

    # else:
    #     st.markdown('<div class="info-message">لا يوجد سجل تصنيفات سابقة</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()