import pandas as pd
df = pd.read_excel('EXPORT_20260520134027.xlsx')
descs = list(df['Material Description'].dropna().unique())

print('Material Description 样本:')
print('=' * 120)
for i, desc in enumerate(descs[:12]):
    parts = str(desc).split('_')
    product = parts[0] if len(parts) > 0 else ''
    drawing = parts[1] if len(parts) > 1 and product == 'FMPE' else ''
    has_zn = '-ZN' in desc
    item_cat = product + '-ZN' if has_zn else product
    length = 'coil' if 'coil' in desc.lower() else 'CTL'
    
    print(f'{i+1:2}. {desc}')
    print(f'    -> Product   : {product}')
    print(f'    -> Drawing   : {drawing}')
    print(f'    -> Item Cat  : {item_cat}  (含-ZN: {has_zn})')
    print(f'    -> Length    : {length}')
    print('-' * 120)
