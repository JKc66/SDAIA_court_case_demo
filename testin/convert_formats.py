import json
import yaml
import re
from typing import Dict, List, Any

def parse_text_file(file_path: str) -> Dict[str, Any]:
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()

    # Initialize the data structure
    data = {}
    current_main = None
    current_sub = None
    current_type = None
    current_section = None  # Track current section (tips or exceptions)
    
    # Split the content into lines
    lines = content.split('\n')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Main category (#)
        if line.startswith('# '):
            current_main = line[2:]
            data[current_main] = {
                'description': '',
                'subcategories': {}
            }
            current_sub = None
            current_type = None
            current_section = None
            
        # Subcategory (##)
        elif line.startswith('## '):
            current_sub = line[3:]
            if current_main:
                data[current_main]['subcategories'][current_sub] = {
                    'description': '',
                    'types': {}
                }
            current_type = None
            current_section = None

        # Type (###)
        elif line.startswith('### '):
            current_type = line[4:]
            if current_main and current_sub:
                data[current_main]['subcategories'][current_sub]['types'][current_type] = {
                    'description': ''
                }
            current_section = None
                
        # Description (الوصف:)
        elif line.startswith('الوصف:'):
            description = line[6:].strip()
            if current_type:
                data[current_main]['subcategories'][current_sub]['types'][current_type]['description'] = description
            elif current_sub:
                data[current_main]['subcategories'][current_sub]['description'] = description
            elif current_main:
                data[current_main]['description'] = description
            current_section = None
                
        # Tips (التلميحات:)
        elif line.startswith('التلميحات:'):
            current_section = 'tips'
            continue
            
        # Exceptions (الاستثناءات:)
        elif line.startswith('الاستثناءات:'):
            current_section = 'exceptions'
            continue
            
        # Handle content lines
        elif not line.startswith('#') and not line.startswith('الوصف:'):
            if current_section == 'tips':
                if current_type:
                    if 'tips' not in data[current_main]['subcategories'][current_sub]['types'][current_type]:
                        data[current_main]['subcategories'][current_sub]['types'][current_type]['tips'] = []
                    data[current_main]['subcategories'][current_sub]['types'][current_type]['tips'].append(line)
                elif current_sub:
                    if 'tips' not in data[current_main]['subcategories'][current_sub]:
                        data[current_main]['subcategories'][current_sub]['tips'] = []
                    data[current_main]['subcategories'][current_sub]['tips'].append(line)
                elif current_main:
                    if 'tips' not in data[current_main]:
                        data[current_main]['tips'] = []
                    data[current_main]['tips'].append(line)
            elif current_section == 'exceptions':
                if current_type:
                    if 'exceptions' not in data[current_main]['subcategories'][current_sub]['types'][current_type]:
                        data[current_main]['subcategories'][current_sub]['types'][current_type]['exceptions'] = []
                    data[current_main]['subcategories'][current_sub]['types'][current_type]['exceptions'].append(line)
                elif current_sub:
                    if 'exceptions' not in data[current_main]['subcategories'][current_sub]:
                        data[current_main]['subcategories'][current_sub]['exceptions'] = []
                    data[current_main]['subcategories'][current_sub]['exceptions'].append(line)
                elif current_main:
                    if 'exceptions' not in data[current_main]:
                        data[current_main]['exceptions'] = []
                    data[current_main]['exceptions'].append(line)
    
    return data

def save_as_json(data: Dict[str, Any], output_file: str):
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def save_as_yaml(data: Dict[str, Any], output_file: str):
    with open(output_file, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, allow_unicode=True, sort_keys=False)

def convert_file(input_file: str):
    # Parse the data
    data = parse_text_file(input_file)
    
    # Save in different formats
    save_as_json(data, input_file.replace('.txt', '.json'))
    save_as_yaml(data, input_file.replace('.txt', '.yaml'))

if __name__ == "__main__":
    convert_file("details.txt") 