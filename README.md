# Enjaz - ناظر Case Classification App
<p align="center">
  <img src="static/LOGO.png" alt="Enjaz Project Logo" width="200"/>
</p>

**Enjaz (ناظر)** is a Streamlit-based web application developed for the Enjaz Hackathon. This intelligent tool leverages the power of Google's Gemini AI to automatically classify legal cases. Users can input case text, and the application provides a main classification, sub-classification, and case type, along with an explanation, streamlining the initial assessment process for legal documents. The app also maintains a history of classifications for review and export.

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
├── Data/                
│   └── Classes.txt         # cases classes
│
├── app.py                   # Main Streamlit application
└── requirements.txt         # Project dependencies
```
