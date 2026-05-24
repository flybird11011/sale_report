import pandas as pd

# 读取源文件1
file_path = 'EXPORT_20260520134027.xlsx'
df = pd.read_excel(file_path)

descs = list(df['Material Description'].dropna().unique())

print('Material Description 完整6列验证:')
print('=' * 180)

for i, desc in enumerate(descs[:50]):
    parts = str(desc).split('_')
    n = len(parts)
    
    product = parts[0] if n > 0 else ''
    drawing = parts[1] if n > 1 and product == 'FMPE' else ''
    
    # Spec.: 第2段之后，最后一段之前，去掉尾部 -CTL
    if n >= 3:
        spec = '_'.join(parts[1:-1])  # 从第2段到倒数第二段（后面还要处理）
    else:
        spec = ''
    
    # 尾部清理：去掉 -CTL
    if spec.endswith('-CTL'):
        spec = spec[:-4]  # 去掉 "-CTL" 4个字符
    
    # Alloy
    last_part = parts[-1] if n > 0 else ''
    second_last = parts[-2] if n > 1 else ''
    
    alloy = last_part
    if n >= 2:
        # FMPE 系列：如果最后一段是 H112/H11/O，合并最后两段（如 9153A_H112 / 3003_H112）
        if product == 'FMPE' and last_part in ['H112', 'H11', 'O']:
            alloy = second_last + '_' + last_part
        # FPDT 系列：最后一段是长数字（>4位）的 Alloy 就是最后一段；短的3003牌号也是最后一段
        # （310377 这种直接取最后一段）
    
    has_zn = '-ZN' in str(desc)
    item_cat = product + '-ZN' if has_zn else product
    length = 'coil' if 'coil' in str(desc).lower() else 'CTL'
    
    print(f'{i+1:2}. {desc}')
    print(f'    Product:  {product}')
    print(f'    Drawing:  {drawing}')
    print(f'    Spec.:    {spec}  (已去掉尾部-CTL)')
    print(f'    Alloy:    {alloy}')
    print(f'    Item Cat: {item_cat}')
    print(f'    Length:   {length}')
    print('-' * 180)
