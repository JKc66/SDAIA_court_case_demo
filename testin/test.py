def transform_headings(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    transformed_lines = []
    current_section = None
    
    for line in lines:
        line = line.strip()
        if not line:
            transformed_lines.append(line)
            continue
        
        # Main categories (e.g., "1. أحوال شخصية")
        if line[0].isdigit() and '. ' in line[:4] and not current_section == "sub_category":
            heading = line[line.find('.')+2:]
            transformed_lines.append(f'# {heading}')
            current_section = "main"
            
        # Sub-categories with letters or words like "التصنيف العام"
        elif (line.startswith('##') or 
              any(line.startswith(f"{letter}. ") for letter in 'أبجدهوزحطيكلمنسعفصقرشتثخذضظغ') or
              line.startswith('دعاوى') or
              line.startswith('التصنيف')):
            if line.startswith('##'):
                heading = line[2:].strip()
            else:
                heading = line[line.find('.')+2:] if '. ' in line else line
            transformed_lines.append(f'## {heading}')
            current_section = "sub_category"
            
        # Types under sub-categories (numbered items under sub-categories)
        elif (line[0].isdigit() and '. ' in line[:4] and current_section == "sub_category") or line.startswith('#'):
            if line.startswith('#'):
                heading = line[1:].strip()
            else:
                heading = line[line.find('.')+2:]
            transformed_lines.append(f'### {heading}')
            
        # Keep other lines unchanged (descriptions, notes, etc.)
        else:
            transformed_lines.append(line)
    
    # Write the transformed content
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(transformed_lines))

if __name__ == '__main__':
    input_file = 'testin/details_for_test.txt'
    output_file = 'testin/details_transformed.txt'
    transform_headings(input_file, output_file)
