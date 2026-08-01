import re

file_path = 'model.drawio'

# Color Palette
purple_style = 'fillColor=#E1D5E7;strokeColor=#9673A6;'
pink_style = 'fillColor=#F8CECC;strokeColor=#B85450;'
orange_style = 'fillColor=#FFCC99;strokeColor=#CC6600;'
yellow_style = 'fillColor=#FFF2CC;strokeColor=#D6B656;'

id_to_style = {
    '3': purple_style,
    '4': purple_style,
    '5': purple_style,
    '10': purple_style,
    '13': purple_style,
    '15': purple_style,
    '24': purple_style,
    '30': pink_style,
    '31': pink_style,
    '32': pink_style,
    '53': orange_style,
    '68': yellow_style,
    '116': purple_style,
    '136': pink_style,
    '137': orange_style,
    '138': yellow_style,
    '139': yellow_style,
}

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.read().splitlines() # Remove newlines to be safe

new_lines = []
for line in lines:
    if 'id="3"' in line:
        print(f"Found ID 3 line: {line}")

    if '<mxCell' in line:
        id_match = re.search(r'id="(\d+)"', line)
        if id_match:
            obj_id = id_match.group(1)
            # print(f"Found ID: {obj_id}")
            if obj_id in id_to_style:
                style_match = re.search(r'style="([^"]*)"', line)
                if style_match:
                    current_style = style_match.group(1)
                    if 'fillColor' not in current_style:
                        new_style_content = current_style + id_to_style[obj_id]
                        line = line.replace(f'style="{current_style}"', f'style="{new_style_content}"')
                        print(f"Updated ID {obj_id}")
                    else:
                        print(f"ID {obj_id} already has color")
                else:
                    print(f"ID {obj_id} has no style attribute")

    new_lines.append(line)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write('\n'.join(new_lines))
