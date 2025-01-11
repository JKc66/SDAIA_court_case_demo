import json
import re

def parse_text_to_json(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.readlines()

    result = {}
    current_main = None
    current_sub = None
    current_type = None
    current_section = None
    
    description = []
    hints = []
    exceptions = []
    
    def save_current_section():
        nonlocal description, hints, exceptions
        
        # Determine which level we're saving to
        if current_type and current_sub and current_main:
            # Type level
            if current_main not in result:
                result[current_main] = {"items": {}}
            if current_sub not in result[current_main]["items"]:
                result[current_main]["items"][current_sub] = {"items": {}}
            
            target = result[current_main]["items"][current_sub]["items"]
            if current_type not in target:
                target[current_type] = {}
            target = target[current_type]
            
        elif current_sub and current_main:
            # Sub level
            if current_main not in result:
                result[current_main] = {"items": {}}
            if current_sub not in result[current_main]["items"]:
                result[current_main]["items"][current_sub] = {"items": {}}
            
            target = result[current_main]["items"][current_sub]
            
        elif current_main:
            # Main level
            if current_main not in result:
                result[current_main] = {"items": {}}
            
            target = result[current_main]
        else:
            return
            
        if description:
            target["description"] = " ".join(description).strip()
        if hints:
            target["hints"] = [h.strip() for h in hints]
        if exceptions:
            target["exceptions"] = [e.strip() for e in exceptions]
            
        description.clear()
        hints.clear()
        exceptions.clear()

    for line in content:
        line = line.strip()
        if not line:
            continue

        # Check for headers
        if line.startswith('# '):
            save_current_section()
            current_main = line[2:].strip()
            current_sub = None
            current_type = None
        elif line.startswith('## '):
            save_current_section()
            current_sub = line[3:].strip()
            current_type = None
        elif line.startswith('### '):
            save_current_section()
            current_type = line[4:].strip()
        # Check for content sections
        elif line.startswith('الوصف:'):
            current_section = 'description'
            description.append(line[6:].strip())
        elif line.startswith('التلميحات:'):
            current_section = 'hints'
        elif line.startswith('الاستثناءات:'):
            current_section = 'exceptions'
        # Handle content lines
        elif line.startswith('- '):
            if current_section == 'hints':
                hints.append(line[2:])
            elif current_section == 'exceptions':
                exceptions.append(line[2:])
        elif current_section == 'description':
            description.append(line)

    # Save the last section
    save_current_section()
    
    return result

def main():
    input_file = 'testin/details.txt'
    output_file = 'testin/converted_structure.json'
    
    result = parse_text_to_json(input_file)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main() 