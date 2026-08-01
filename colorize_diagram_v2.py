import re

file_path = 'model.drawio'

# Color Palette
purple_style = 'fillColor=#E1D5E7;strokeColor=#9673A6;'
pink_style = 'fillColor=#F8CECC;strokeColor=#B85450;'
orange_style = 'fillColor=#FFCC99;strokeColor=#CC6600;'
yellow_style = 'fillColor=#FFF2CC;strokeColor=#D6B656;'

# Mapping ID -> Style to append
id_to_style = {
    # Purple: dPL
    '3': purple_style,
    '4': purple_style,
    '5': purple_style,
    # Purple: H nodes
    '10': purple_style,
    '13': purple_style,
    '15': purple_style,
    '24': purple_style,
    
    # Red/Pink: J nodes
    '30': pink_style,
    '31': pink_style,
    '32': pink_style,
    
    # Orange: Rule-aware
    '53': orange_style,
    
    # Yellow: Softmax
    '68': yellow_style,
    
    # Bar Chart 
    '116': purple_style,
    '136': pink_style,
    '137': orange_style,
    '138': yellow_style,
    '139': yellow_style,
}

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    # Check if line has mxCell and an ID we care about
    # <mxCell id="3" ...
    if '<mxCell' in line:
        id_match = re.search(r'id="(\d+)"', line)
        if id_match:
            obj_id = id_match.group(1)
            if obj_id in id_to_style:
                # Find style="..."
                style_match = re.search(r'style="([^"]*)"', line)
                if style_match:
                    current_style = style_match.group(1)
                    # Avoid double applying
                    if 'fillColor' not in current_style:
                        new_style_content = current_style + id_to_style[obj_id]
                        # Replace only the style content part
                        # Use strictly scoped replace to avoid replacing other things
                        line = line.replace(f'style="{current_style}"', f'style="{new_style_content}"')
                        print(f"Updated ID {obj_id}")

    new_lines.append(line)

with open(file_path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
