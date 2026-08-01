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
    
    # Bar Chart (Purple -> Pink -> Orange -> Yellow)
    '116': purple_style,
    '136': pink_style,
    '137': orange_style,
    '138': yellow_style,
    '139': yellow_style,
}

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

def replace_style(match):
    full_tag = match.group(0)
    obj_id = match.group(1)
    current_style = match.group(2)
    
    if obj_id in id_to_style:
        new_style_fragment = id_to_style[obj_id]
        # Check if style already has these colors to avoid duplication (simple check)
        if 'fillColor' not in current_style:
             # Reconstruct the tag with new style
             # The regex captures: 
             # 1: id
             # 2: current style content
             
             # We need to replace the style="..." part
             # It acts on the full_tag because style might be anywhere
             
             new_style = current_style + new_style_fragment
             new_tag = full_tag.replace(f'style="{current_style}"', f'style="{new_style}"')
             return new_tag
             
    return full_tag

# Regex to find mxCell with id and style
# Use a pattern that is robust to attribute order, but assuming standard draw.io format
# <mxCell id="3" value="dPL" style="rounded=1;whiteSpace=wrap;html=1;" ...
# We match the whole tag to do the replacement correctly
pattern = re.compile(r'<mxCell[^>]*id="(\d+)"[^>]*style="([^"]+)"[^>]*>')

new_content = pattern.sub(replace_style, content)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(new_content)

print("Updates applied.")
