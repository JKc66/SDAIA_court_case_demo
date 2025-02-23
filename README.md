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
├── Data/                
│   └── Classes.txt         # cases classes
│
├── app.py                   # Main Streamlit application
└── requirements.txt         # Project dependencies
```
