# Enjaz Streamlit Project

A Streamlit-based web application for Enjaz Hackathon.

## Project Structure

```
.
├── .streamlit/              # Streamlit configuration
│   ├── config.toml         # Streamlit configuration settings
│   └── secrets.toml        # Secure configuration and API keys
│
├── static/                  # Static assets
│   ├── style.css          # Custom styling
│   └── LOGO.svg           # Project logo
│
├── testin/                  # Data processing and conversion utilities
│   ├── convert_formats.py             # Format conversion utilities
│   ├── yaml_to_csv_converter.py       # YAML to CSV converter
│   ├── text_to_json_converter.py      # Text to JSON converter
│   ├── analyze_structure.py           # Data structure analysis
│   └── various data files (.json, .yaml, .csv, .txt)
│
├── classes/                 # Class-related data
│   └── Classes.txt         # Class information
│
├── app.py                   # Main Streamlit application
└── requirements.txt         # Project dependencies
```

## Key Components

1. **Main Application**
   - `app.py`: The main Streamlit application entry point
   - `requirements.txt`: Lists all project dependencies

2. **Configuration**
   - `.streamlit/`: Contains Streamlit-specific configuration files
   - Configuration for both app settings and secure variables

3. **Static Assets**
   - `static/`: Houses styling and visual assets
   - Custom CSS for application styling
   - Project logo and other static resources

4. **Data Processing**
   - `testin/`: Contains various data processing utilities
   - Multiple format converters (YAML, JSON, CSV, Text)
   - Data analysis and structure validation tools

5. **Class Data**
   - `classes/`: Stores class-related information
   - Contains raw and processed class data in various formats

## Getting Started

1. Set up Gemini API:
   - Get a Gemini API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
   - Create or edit `.streamlit/secrets.toml`
   - Add your API key:
     ```toml
     GOOGLE_API_KEY = "your-api-key-here"
     ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the application:
   ```bash
   streamlit run app.py
   ``` 