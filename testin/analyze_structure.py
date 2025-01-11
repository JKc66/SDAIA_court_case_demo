import yaml
import json
import os
from collections import defaultdict

def read_yaml_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return yaml.safe_load(file)

def read_json_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return json.load(file)

def count_structure(data):
    main_count = len(data)
    sub_count = 0
    types_count = 0
    
    structure_details = {}
    
    for main_category, main_data in data.items():
        if 'subcategories' in main_data:
            current_subs = len(main_data['subcategories'])
            sub_count += current_subs
            
            sub_details = {}
            for sub_name, sub_data in main_data['subcategories'].items():
                if 'types' in sub_data:
                    current_types = len(sub_data['types'])
                    types_count += current_types
                    sub_details[sub_name] = current_types
                else:
                    sub_details[sub_name] = 0
                    
            structure_details[main_category] = sub_details
    
    return main_count, sub_count, types_count, structure_details

def write_detailed_structure(file, structure_details):
    file.write("\nDetailed Structure Analysis:\n")
    file.write("=" * 50 + "\n")
    
    for main_category, subs in structure_details.items():
        total_subs = len(subs)
        file.write(f"\nMain Category: {main_category}\n")
        file.write(f"├── Number of subcategories: {total_subs}\n")
        
        for sub_name, type_count in subs.items():
            file.write(f"│   ├── Subcategory: {sub_name}\n")
            file.write(f"│   │   └── Number of types: {type_count}\n")

def main():
    # Get the directory where the script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_file = os.path.join(script_dir, 'structure_analysis.txt')
    
    # Ensure the directory exists
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        # Analyze YAML file
        yaml_data = read_yaml_file('details.yaml')
        yaml_main, yaml_sub, yaml_types, yaml_structure = count_structure(yaml_data)
        
        f.write("\nYAML File Analysis:\n")
        f.write("=" * 50 + "\n")
        f.write(f"Main categories: {yaml_main}\n")
        f.write(f"Subcategories: {yaml_sub}\n")
        f.write(f"Types: {yaml_types}\n")
        
        write_detailed_structure(f, yaml_structure)
        
        # Analyze JSON file
        json_data = read_json_file('details.json')
        json_main, json_sub, json_types, json_structure = count_structure(json_data)
        
        f.write("\nJSON File Analysis:\n")
        f.write("=" * 50 + "\n")
        f.write(f"Main categories: {json_main}\n")
        f.write(f"Subcategories: {json_sub}\n")
        f.write(f"Types: {json_types}\n")
        
        write_detailed_structure(f, json_structure)
        
        print(f"Analysis has been written to {output_file}")

if __name__ == "__main__":
    main() 