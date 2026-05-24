import pandas as pd
import re

def split_material_description(desc):
    if pd.isna(desc):
        return ('', '', '', '', '', '')
    desc = str(desc)
    parts = desc.split('_')
    n = len(parts)
    
    product = parts[0] if n > 0 else ''
    drawing = parts[1] if n > 1 and product == 'FMPE' else ''
    has_zn = '-ZN' in desc
    item_cat = product + '-ZN' if has_zn else product
    length = 'coil' if 'coil' in desc.lower() else 'CTL'
    
    spec = ''
    alloy = ''
    matched = False
    
    markers = []
    for marker in ['MM_', 'CTL_', 'JUMBO_']:
        idx = desc.rfind(marker)
        if idx >= 0:
            markers.append((idx, marker))
    
    if markers:
        markers.sort(reverse=True)
        last_idx, last_marker = markers[0]
        alloy = desc[last_idx + len(last_marker):]
        product_end = desc.find('_')
        if product_end > 0:
            spec = desc[product_end+1:last_idx]
        matched = True
    
    if not matched:
        alloy = parts[-1]
        if n >= 3:
            spec = '_'.join(parts[1:-1])
    
    if spec.endswith('_'):
        spec = spec[:-1]
    for tail in ['-COIL-', '-COIL', '-CTL']:
        if spec.endswith(tail):
            spec = spec[:-len(tail)]
    
    return (product, drawing, spec, alloy, item_cat, length)

df = pd.read_excel('EXPORT_20260520134027.xlsx', nrows=70)
df = df[df['Sales Document'].notna()]

pd.set_option('display.width', 200, 'display.max_colwidth', 40)
df[['Product','Drawing','Spec.','Alloy','Item Cat','Length']] = \
    df['Material Description'].apply(lambda x: pd.Series(split_material_description(x)))

print(df[['Material Description','Product','Drawing','Spec.','Alloy','Item Cat','Length']].head(50).to_string())
