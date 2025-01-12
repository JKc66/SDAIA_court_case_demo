import yaml
import csv
import os

def process_item(writer, main_cat, current_path, data):
    # Get metadata for current item
    description = ''
    hints = []
    exceptions = []
    
    if isinstance(data, dict):
        description = data.get('description', '')
        hints = data.get('hints', [])
        exceptions = data.get('exceptions', [])
        
        # Write current item's metadata if it exists
        if description or hints or exceptions:
            writer.writerow([
                main_cat,
                ' - '.join(current_path) if current_path else '',
                description,
                '; '.join(hints),
                '; '.join(exceptions)
            ])
        
        # Process nested items
        for key, value in data.items():
            if isinstance(value, dict) and key not in ['description', 'hints', 'exceptions']:
                new_path = current_path + [key] if current_path else [key]
                process_item(writer, main_cat, new_path, value)

def flatten_yaml_to_csv(yaml_file_path, csv_file_path):
    # Read YAML file
    print(f"Reading YAML file from: {yaml_file_path}")
    with open(yaml_file_path, 'r', encoding='utf-8') as file:
        data = yaml.safe_load(file)
    
    print(f"YAML data loaded. Top-level keys: {list(data.keys())}")
    
    # Prepare CSV file
    with open(csv_file_path, 'w', encoding='utf-8', newline='') as file:
        writer = csv.writer(file)
        # Write header
        writer.writerow(['Main Category', 'Subcategory', 'Description', 'Hints', 'Exceptions'])
        
        # Process each main category
        for main_cat, main_data in data.items():
            print(f"Processing main category: {main_cat}")
            process_item(writer, main_cat, [], main_data)

if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    yaml_file = os.path.join(script_dir, "Clasess_with_hints.yaml")
    csv_file = os.path.join(script_dir, "classes_converted.csv")
    
    print(f"Starting conversion...")
    print(f"YAML file path: {yaml_file}")
    print(f"CSV file path: {csv_file}")
    
    if not os.path.exists(yaml_file):
        print(f"Error: YAML file not found at {yaml_file}")
    else:
        flatten_yaml_to_csv(yaml_file, csv_file)
        print(f"Conversion completed. CSV file saved as: {csv_file}") 